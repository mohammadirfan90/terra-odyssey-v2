"""Test verifying strict offline network egress blocking."""

import os
import socket
import pytest
from src.cache.guard import install_offline_guard, remove_offline_guard, OfflineEgressBlockedError


def test_offline_guard_blocks_remote_socket():
    os.environ["OFFLINE"] = "1"
    install_offline_guard()

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with pytest.raises(OfflineEgressBlockedError) as exc_info:
            # Attempt to connect to Google Public DNS
            s.connect(("8.8.8.8", 53))

        assert "[OFFLINE=1 ENFORCED]" in str(exc_info.value)
    finally:
        remove_offline_guard()
