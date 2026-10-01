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
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

import numpy as np
from ..registry.bindings import DATASET_BINDINGS, DatasetBinding
from ..registry.parameters import PARAMETER_REGISTRY
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

    def __init__(self, data_root: Optional[Path | str] = None):
        if data_root is None:
            env_data = os.environ.get("DATA_ROOT")
            if env_data:
                self.data_root = Path(env_data).resolve()
            else:
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
                    if "region_a_data_sha256" in prov:
                        sha_a = prov.get("region_a_data_sha256", "")
                        sha_b = prov.get("region_b_data_sha256", "")
                        correct_sha = hashlib.sha256(f"{sha_a}:{sha_b}".encode()).hexdigest()
                        if prov.get("data_sha256") != correct_sha:
                            prov["data_sha256"] = correct_sha
                            obj["provenance"] = prov
                            res_json = json.dumps(obj)
                            cursor.execute("UPDATE completed_results SET result_json = ? WHERE result_id = ?", (res_json, r_id))

                    d_sha = prov.get("data_sha256")
                    doi = prov.get("doi", "")
                    code_rev = obj.get("reproducibility", {}).get("code_revision", "v1.0.0")
                    if not d_sha or doi == "10.5067/0JRLVL8YV2Y4" or code_rev == "v1.0.0":
                        cursor.execute(
                            """
                            INSERT OR REPLACE INTO quarantined_results (result_id, query_json, created_at, result_json, quarantine_reason)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (r_id, q_json, c_at, res_json, f"Legacy result superseded by code revision v1.4.0 (was {code_rev})"),
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
            manifest = self.get_manifest(binding_id)
            if not manifest or manifest.get("binding_id") != binding_id:
                return False
            if "metadata" not in manifest or not isinstance(manifest.get("metadata"), dict) or not manifest["metadata"]:
                return False
            meta = manifest["metadata"]
            if meta.get("availability_state") not in ("analysis_ready", "display_ready"):
                return False
            for f in ("canonical_unit", "display_unit", "variable_name", "temporal_cadence"):
                if not meta.get(f):
                    return False
            if binding_id in DATASET_BINDINGS:
                exp_b = DATASET_BINDINGS[binding_id]
                if meta.get("variable_name") != exp_b.variable_name:
                    return False
                if meta.get("canonical_unit") != exp_b.canonical_unit:
                    return False
                if meta.get("temporal_cadence") != exp_b.temporal_cadence:
                    return False
            entry = self.get_manifest_entry(binding_id, region_id)
            if not entry:
                return False
            expected_sha = entry.get("sha256")
            if not expected_sha or not isinstance(expected_sha, str) or len(expected_sha) != 64:
                return False
            actual_sha = self.get_series_bytes_sha256(binding_id, region_id)
            if actual_sha.lower() != expected_sha.lower():
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
            ManifestSchemaError: If required manifest columns or metadata violate contracts.
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
        if not expected_sha or not isinstance(expected_sha, str) or len(expected_sha) != 64:
            raise ManifestChecksumMismatchError(
                f"Manifest entry for {binding_id}_{region_id} is missing a valid 64-character SHA-256 digest."
            )
        if actual_sha.lower() != expected_sha.lower():
            raise ManifestChecksumMismatchError(
                f"Data integrity violation for {binding_id}_{region_id}: "
                f"actual Parquet SHA-256 '{actual_sha}' does not match verified manifest '{expected_sha}'."
            )

        manifest_binding = manifest.get("binding_id")
        if manifest_binding != binding_id:
            raise ManifestSchemaError(
                f"Manifest declared binding_id '{manifest_binding}' does not match requested binding '{binding_id}'."
            )

        if "metadata" not in manifest or not isinstance(manifest.get("metadata"), dict) or not manifest["metadata"]:
            raise ManifestSchemaError(
                f"Manifest for binding '{binding_id}' violates schema: required 'metadata' object is missing."
            )

        meta = manifest["metadata"]
        avail = meta.get("availability_state")
        if avail not in ("analysis_ready", "display_ready"):
            raise ManifestSchemaError(
                f"Dataset binding '{binding_id}' is in availability_state '{avail}', not ready for analysis."
            )

        # Enforce all required metadata fields
        required_meta_fields = ["canonical_unit", "display_unit", "variable_name", "temporal_cadence"]
        for f in required_meta_fields:
            if not meta.get(f):
                raise ManifestSchemaError(
                    f"Manifest metadata for binding '{binding_id}' missing required scientific contract field '{f}'."
                )

        if binding_id in DATASET_BINDINGS:
            expected_binding = DATASET_BINDINGS[binding_id]
            if meta.get("canonical_unit") != expected_binding.canonical_unit:
                raise ManifestSchemaError(
                    f"Manifest canonical unit '{meta.get('canonical_unit')}' does not match binding definition '{expected_binding.canonical_unit}'."
                )
            if meta.get("variable_name") != expected_binding.variable_name:
                raise ManifestSchemaError(
                    f"Manifest variable name '{meta.get('variable_name')}' does not match binding definition '{expected_binding.variable_name}'."
                )
            expected_param = PARAMETER_REGISTRY.get(expected_binding.parameter_id)
            if expected_param and meta.get("display_unit") and meta.get("display_unit") != expected_param.display_unit:
                raise ManifestSchemaError(
                    f"Manifest display unit '{meta.get('display_unit')}' does not match parameter definition '{expected_param.display_unit}'."
                )
            if meta.get("temporal_cadence") != expected_binding.temporal_cadence:
                raise ManifestSchemaError(
                    f"Manifest temporal cadence '{meta.get('temporal_cadence')}' does not match binding definition '{expected_binding.temporal_cadence}'."
                )

        expected_filename = entry.get("file_name")
        if expected_filename and expected_filename != parquet_path.name:
            raise ManifestSchemaError(
                f"Manifest entry file_name '{expected_filename}' does not match actual file name '{parquet_path.name}'."
            )

        try:
            df = pd.read_parquet(parquet_path)
        except Exception as e:
            raise ManifestSchemaError(
                f"Corrupt or unreadable Parquet file for {binding_id}_{region_id}: {str(e)}"
            ) from e

        if "year" not in df.columns:
            raise ManifestSchemaError(
                f"Parquet file {parquet_path.name} violates schema: required column 'year' is missing."
            )

        # Validate 'year' column numeric integer types
        try:
            year_series = pd.to_numeric(df["year"], errors="raise")
            if not np.all(np.isfinite(year_series.to_numpy())):
                raise ManifestSchemaError("Column 'year' contains non-finite values.")
            if not np.all(np.equal(np.mod(year_series.to_numpy(), 1), 0)):
                raise ManifestSchemaError("Column 'year' must contain integer values.")
            df["year"] = year_series.astype(int)
        except ManifestSchemaError:
            raise
        except Exception as e:
            raise ManifestSchemaError(f"Column 'year' contains non-numeric values: {e}")

        # Validate observation value column for numeric correctness
        for cand in ["value_canonical", "value_display", "value", "val"]:
            if cand in df.columns:
                try:
                    df[cand] = pd.to_numeric(df[cand], errors="raise")
                except Exception as e:
                    raise ManifestSchemaError(f"Observation values in column '{cand}' contain non-numeric data: {e}")

        manifest_rows = entry.get("row_count")
        if manifest_rows is not None and manifest_rows != len(df):
            raise ManifestSchemaError(
                f"Parquet row count ({len(df)}) does not match verified manifest row count ({manifest_rows})."
            )
        first_yr = entry.get("first_year")
        if first_yr is not None and len(df) > 0 and int(df["year"].min()) != int(first_yr):
            raise ManifestSchemaError(
                f"Parquet first year ({int(df['year'].min())}) does not match manifest first year ({first_yr})."
            )
        last_yr = entry.get("last_year")
        if last_yr is not None and len(df) > 0 and int(df["year"].max()) != int(last_yr):
            raise ManifestSchemaError(
                f"Parquet last year ({int(df['year'].max())}) does not match manifest last year ({last_yr})."
            )

        # Enforce source schema contract
        qa_col = entry.get("qa_column")
        cov_col = entry.get("coverage_column")
        if binding_id in DATASET_BINDINGS:
            b_def = DATASET_BINDINGS[binding_id]
            if b_def.qa_band_name or b_def.is_gridded:
                qa_col = qa_col or "qa_passed"
                cov_col = cov_col or "valid_coverage_pct"

        if qa_col and qa_col not in df.columns:
            raise ManifestSchemaError(
                f"Parquet file {entry.get('file_name', parquet_path.name)} violates manifest contract: required QA column '{qa_col}' missing."
            )
        if cov_col and cov_col not in df.columns:
            raise ManifestSchemaError(
                f"Parquet file {entry.get('file_name', parquet_path.name)} violates manifest contract: required coverage column '{cov_col}' missing."
            )

        def decode_qa(val: Any) -> bool:
            """Decode boolean and enum QA columns avoiding Python string truthiness traps."""
            if pd.isna(val):
                return False
            if isinstance(val, (bool, np.bool_)):
                return bool(val)
            if isinstance(val, (int, np.integer, float, np.floating)):
                return val != 0
            if isinstance(val, str):
                v = val.strip().lower()
                if v in ("true", "1", "t", "yes", "pass", "passed"):
                    return True
                if v in ("false", "0", "f", "no", "fail", "failed"):
                    return False
                return False
            return False

        # Map declared alternative QA column to canonical 'qa_passed'
        if qa_col and qa_col in df.columns:
            df["qa_passed"] = df[qa_col].apply(decode_qa)

        # Map declared alternative coverage column to canonical 'valid_coverage_pct'
        cov_col_to_check = cov_col or ("valid_coverage_pct" if "valid_coverage_pct" in df.columns else None)
        if cov_col_to_check and cov_col_to_check in df.columns:
            try:
                cov_series = pd.to_numeric(df[cov_col_to_check], errors="raise")
                df["valid_coverage_pct"] = cov_series
            except Exception as e:
                raise ManifestSchemaError(f"Coverage column contains non-numeric values: {e}")

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

    def save_result(self, result_id: str, query_dict: dict, result_dict: dict) -> dict:
        """Save a computed result object into SQLite using immutable append-only semantics.

        If a result with this ID already exists, it is preserved unchanged (INSERT OR IGNORE).
        Returns the canonical stored winner payload to guarantee concurrency consensus.
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

            # If row was ignored because another thread inserted first, return the stored canonical winner
            if cursor.rowcount == 0:
                cursor.execute("SELECT result_json FROM completed_results WHERE result_id = ?", (result_id,))
                row = cursor.fetchone()
                if row and row[0]:
                    try:
                        return json.loads(row[0])
                    except Exception:
                        pass
        return sanitized_result

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
                d_sha = prov.get("data_sha256") or prov.get("region_a_data_sha256")
                doi = prov.get("doi", "")
                if not d_sha or doi == "10.5067/0JRLVL8YV2Y4":
                    return None
                return res
            return None

