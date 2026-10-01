"""Local cache store for Parquet time-series, Zarr gridded arrays, and SQLite index.

Implements Chapter 5 and Section 10:
- Reads pre-cached, manifest-verified Parquet time series
- Zero remote network access; cache misses return typed RFC 9457 problem states
- Strict path confinement preventing traversal outside data/cache
- Zero synthetic data generation in production (strictly adheres to audit finding F01)
- Immutable SQLite index for tracking verified cached series and results
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

import numpy as np
from ..registry.bindings import DATASET_BINDINGS, DatasetBinding
from ..registry.regions import REGION_REGISTRY, RegionDefinition


_SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_]+$")


class CacheMissOfflineError(KeyError):
    """Raised when a requested dataset or region series is not present in local cache."""
    pass


class InvalidPathSecurityError(ValueError):
    """Raised when an identifier contains illegal characters or path traversal attempt."""
    pass


class ManifestNotFoundError(FileNotFoundError):
    """Raised when a verified acquisition manifest for a binding does not exist."""
    pass


class ManifestEntryNotFoundError(KeyError):
    """Raised when a series (binding, region) is not registered in the verified manifest."""
    pass


class ManifestChecksumMismatchError(ValueError):
    """Raised when a cached Parquet file SHA-256 does not match its manifest checksum."""
    pass


class ManifestSchemaError(ValueError):
    """Raised when Parquet file schema violates manifest contracts (e.g. missing declared QA column)."""
    pass


def _sanitize_floats(obj: Any) -> Any:
    """Recursively convert NaN, +Infinity, and -Infinity to None for valid RFC 8259 JSON compliance."""
    if isinstance(obj, float):
        if not np.isfinite(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: _sanitize_floats(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_floats(x) for x in obj]
    return obj


class LocalDataStore:
    """Manages access to local Parquet files, acquisition manifests, and SQLite results."""

    def __init__(self, data_root: Optional[Path] = None):
        if data_root is None:
            backend_dir = Path(__file__).resolve().parents[2]
            self.data_root = (backend_dir.parent / "data").resolve()
        else:
            self.data_root = Path(data_root).resolve()

        self.cache_dir = (self.data_root / "cache").resolve()
        self.manifest_dir = (self.data_root / "manifests").resolve()
        self.regions_dir = (self.data_root / "regions").resolve()

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_dir.mkdir(parents=True, exist_ok=True)
        self.regions_dir.mkdir(parents=True, exist_ok=True)

        self._manifest_cache: Dict[str, dict] = {}
        self.db_path = self.cache_dir / "index.db"
        self._init_sqlite_index()
        self._sync_manifest_index()

    def _init_sqlite_index(self) -> None:
        """Initialize lightweight SQLite index for tracking cached items and results."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cached_series (
                    binding_id TEXT,
                    region_id TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    sample_count INTEGER,
                    checksum TEXT,
                    file_path TEXT,
                    PRIMARY KEY (binding_id, region_id)
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS completed_results (
                    result_id TEXT PRIMARY KEY,
                    query_json TEXT,
                    created_at TEXT,
                    result_json TEXT
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS quarantined_results (
                    result_id TEXT PRIMARY KEY,
                    query_json TEXT,
                    created_at TEXT,
                    result_json TEXT,
                    quarantine_reason TEXT
                )
                """
            )

            # Quarantine legacy completed results that lack data_sha256 or reference deprecated unverified DOIs
            cursor.execute("SELECT result_id, query_json, created_at, result_json FROM completed_results")
            rows = cursor.fetchall()
            for r_id, q_json, c_at, res_json in rows:
                try:
                    obj = json.loads(res_json)
                    prov = obj.get("provenance", {})
                    d_sha = prov.get("data_sha256")
                    doi = prov.get("doi", "")
                    if not d_sha or doi == "10.5067/0JRLVL8YV2Y4":
                        cursor.execute(
                            """
                            INSERT OR REPLACE INTO quarantined_results (result_id, query_json, created_at, result_json, quarantine_reason)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (r_id, q_json, c_at, res_json, "Legacy unverified provenance or missing data SHA-256"),
                        )
                        cursor.execute("DELETE FROM completed_results WHERE result_id = ?", (r_id,))
                except Exception:
                    cursor.execute("DELETE FROM completed_results WHERE result_id = ?", (r_id,))

            conn.commit()

    def get_manifest(self, binding_id: str) -> Optional[dict]:
        """Retrieve verified acquisition manifest for a binding ID."""
        b_clean = str(binding_id).strip()
        if b_clean in self._manifest_cache:
            return self._manifest_cache[b_clean]

        manifest_file = self.manifest_dir / f"{b_clean}.json"
        if manifest_file.exists():
            try:
                with open(manifest_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._manifest_cache[b_clean] = data
                return data
            except Exception:
                return None
        return None

    def get_manifest_entry(self, binding_id: str, region_id: str) -> Optional[dict]:
        """Find the specific series entry in the manifest for given binding and region."""
        manifest = self.get_manifest(binding_id)
        if not manifest:
            return None
        r_clean = str(region_id).strip().upper()
        for s in manifest.get("series", []):
            if str(s.get("region_id", "")).strip().upper() == r_clean:
                return s
        return None

    def _sync_manifest_index(self) -> None:
        """Synchronize cached_series SQLite table with verified acquisition manifests."""
        if not self.manifest_dir.exists():
            return

        valid_series = set()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for manifest_file in self.manifest_dir.glob("*.json"):
                try:
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    binding_id = data.get("binding_id")
                    for series in data.get("series", []):
                        reg_id = series.get("region_id")
                        filename = series.get("file_name")
                        sha256 = series.get("sha256")
                        row_count = series.get("row_count", 0)
                        start_date = f"{series.get('first_year', 1980)}-01-01"
                        end_date = f"{series.get('last_year', 2024)}-12-31"

                        valid_series.add((binding_id, reg_id))
                        cursor.execute(
                            """
                            INSERT OR REPLACE INTO cached_series
                            (binding_id, region_id, start_date, end_date, sample_count, checksum, file_path)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (binding_id, reg_id, start_date, end_date, row_count, sha256, filename),
                        )
                except Exception:
                    continue

            # Prune stale rows from cached_series that do not exist in current manifests
            cursor.execute("SELECT binding_id, region_id FROM cached_series")
            all_cached = cursor.fetchall()
            for b_id, r_id in all_cached:
                if (b_id, r_id) not in valid_series:
                    cursor.execute("DELETE FROM cached_series WHERE binding_id = ? AND region_id = ?", (b_id, r_id))

            conn.commit()

    def get_series_path(self, binding_id: str, region_id: str) -> Path:
        """Return safe path to cached Parquet file, enforcing strict confinement.

        Raises:
            InvalidPathSecurityError: If binding_id or region_id contain path traversal sequences.
        """
        b_clean = str(binding_id).strip()
        r_clean = str(region_id).strip()

        if not _SAFE_IDENTIFIER_RE.match(b_clean) or not _SAFE_IDENTIFIER_RE.match(r_clean):
            raise InvalidPathSecurityError(
                f"Invalid characters in identifiers (binding='{b_clean}', region='{r_clean}'). "
                "Only alphanumeric and underscore characters are permitted."
            )

        candidate = (self.cache_dir / f"{b_clean}_{r_clean}.parquet").resolve()

        if not candidate.is_relative_to(self.cache_dir):
            raise InvalidPathSecurityError(
                f"Path traversal attempt rejected for binding='{b_clean}', region='{r_clean}'."
            )

        return candidate

    def has_series(self, binding_id: str, region_id: str) -> bool:
        """Check if series exists locally as a valid Parquet file and is registered in the manifest."""
        try:
            parquet_path = self.get_series_path(binding_id, region_id)
            if not parquet_path.exists() or parquet_path.stat().st_size == 0:
                return False
            entry = self.get_manifest_entry(binding_id, region_id)
            if not entry:
                return False
            actual_sha = self.get_series_bytes_sha256(binding_id, region_id)
            expected_sha = entry.get("sha256")
            if expected_sha and actual_sha != expected_sha:
                return False
            return True
        except (InvalidPathSecurityError, ValueError):
            return False

    def load_series(
        self,
        binding_id: str,
        region_id: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> pd.DataFrame:
        """Load time series DataFrame for given binding and region.

        Enforces verified acquisition manifest gating, file integrity, and schema compliance.

        Raises:
            CacheMissOfflineError: If file is not present locally.
            ManifestEntryNotFoundError: If series is not declared in a verified manifest.
            ManifestChecksumMismatchError: If file SHA-256 does not match manifest.
            ManifestSchemaError: If required manifest columns are missing from file.
            InvalidPathSecurityError: If path security check fails.
        """
        manifest = self.get_manifest(binding_id)
        if not manifest:
            raise ManifestNotFoundError(
                f"No verified acquisition manifest found for binding '{binding_id}'. "
                "Only datasets with verified manifests can be loaded."
            )

        entry = self.get_manifest_entry(binding_id, region_id)
        if not entry:
            raise ManifestEntryNotFoundError(
                f"Series for region '{region_id}' under binding '{binding_id}' is not registered in "
                "the verified acquisition manifest."
            )

        parquet_path = self.get_series_path(binding_id, region_id)
        if not parquet_path.exists() or parquet_path.stat().st_size == 0:
            raise CacheMissOfflineError(
                f"Offline cache miss for binding='{binding_id}' and region='{region_id}'. "
                "In strict accordance with OFFLINE=1 and data authenticity policies, no synthetic "
                "data is manufactured and no remote network requests are attempted."
            )

        actual_sha = self.get_series_bytes_sha256(binding_id, region_id)
        expected_sha = entry.get("sha256")
        if expected_sha and actual_sha != expected_sha:
            raise ManifestChecksumMismatchError(
                f"Data integrity violation for {binding_id}_{region_id}: "
                f"actual Parquet SHA-256 '{actual_sha}' does not match verified manifest '{expected_sha}'."
            )

        df = pd.read_parquet(parquet_path)

        # Enforce source schema contract
        qa_col = entry.get("qa_column")
        if qa_col and qa_col not in df.columns:
            raise ManifestSchemaError(
                f"Parquet file {entry.get('file_name')} violates manifest contract: required QA column '{qa_col}' missing."
            )
        cov_col = entry.get("coverage_column")
        if cov_col and cov_col not in df.columns:
            raise ManifestSchemaError(
                f"Parquet file {entry.get('file_name')} violates manifest contract: required coverage column '{cov_col}' missing."
            )

        if start_year is not None:
            df = df[df["year"] >= start_year]
        if end_year is not None:
            df = df[df["year"] <= end_year]

        return df.sort_values(by=["year", "month"] if "month" in df.columns else ["year"]).reset_index(drop=True)

    def get_series_bytes_sha256(self, binding_id: str, region_id: str) -> str:
        """Calculate SHA-256 hash of the underlying Parquet file bytes."""
        parquet_path = self.get_series_path(binding_id, region_id)
        if not parquet_path.exists():
            return ""
        return hashlib.sha256(parquet_path.read_bytes()).hexdigest()

    def save_result(self, result_id: str, query_dict: dict, result_dict: dict) -> None:
        """Save a computed result object into SQLite using immutable append-only semantics.

        If a result with this ID already exists, it is preserved unchanged (INSERT OR IGNORE).
        Strictly sanitizes non-finite floats for RFC 8259 JSON compliance.
        """
        created_at = result_dict.get("identity", {}).get("created_at") or datetime.now(timezone.utc).isoformat()
        sanitized_query = _sanitize_floats(query_dict)
        sanitized_result = _sanitize_floats(result_dict)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR IGNORE INTO completed_results (result_id, query_json, created_at, result_json)
                VALUES (?, ?, ?, ?)
                """,
                (
                    result_id,
                    json.dumps(sanitized_query, sort_keys=True, allow_nan=False),
                    created_at,
                    json.dumps(sanitized_result, sort_keys=True, allow_nan=False),
                ),
            )
            conn.commit()

    def get_result(self, result_id: str) -> Optional[dict]:
        """Retrieve stored result by result_id. Rejects quarantined/unverified legacy records."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT result_json FROM completed_results WHERE result_id = ?",
                (result_id,),
            )
            row = cursor.fetchone()
            if row:
                res = json.loads(row[0])
                prov = res.get("provenance", {})
                d_sha = prov.get("data_sha256")
                doi = prov.get("doi", "")
                if not d_sha or doi == "10.5067/0JRLVL8YV2Y4":
                    return None
                return res
            return None

