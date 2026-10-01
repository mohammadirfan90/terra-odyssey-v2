"""Strict offline enforcement guard and network egress interceptor.

Implements Section 5.2 and Nonnegotiable Rule 6:
- Scientific requests and compute jobs never call an upstream network service
- OFFLINE=1 rejects remote stores, imagery, MCP, and external requests
- Allows loopback (127.0.0.1, ::1) for local frontend-backend IPC
"""

from __future__ import annotations

import os
import socket


class OfflineEgressBlockedError(PermissionError):
    """Raised when any code attempts outbound non-loopback network communication in offline mode."""
    pass


_ORIGINAL_SOCKET_CONNECT = socket.socket.connect


def is_loopback_host(host: str) -> bool:
    """Return True if host is a local loopback interface."""
    host_str = str(host).lower().strip()
    return host_str in ("127.0.0.1", "localhost", "::1", "0.0.0.0")


def patched_connect(self, address):
    """Interception hook blocking non-loopback outbound socket connections."""
    offline_env = os.environ.get("OFFLINE", "1").strip().lower()
    if offline_env in ("1", "true", "yes"):
        host = address[0] if isinstance(address, tuple) and len(address) > 0 else str(address)
        if not is_loopback_host(host):
            raise OfflineEgressBlockedError(
                f"[OFFLINE=1 ENFORCED] Outbound network egress blocked to: {address}. "
                "Scientific runtime is strictly isolated from upstream internet access."
            )
    return _ORIGINAL_SOCKET_CONNECT(self, address)


def install_offline_guard() -> None:
    """Install the offline network egress guard into standard Python socket."""
    socket.socket.connect = patched_connect


def remove_offline_guard() -> None:
    """Restore original socket connect."""
    socket.socket.connect = _ORIGINAL_SOCKET_CONNECT
