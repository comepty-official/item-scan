"""Connectivity check used to enable/disable the USDA lookup."""

from __future__ import annotations

import socket


def has_internet(host: str = "8.8.8.8", port: int = 53, timeout: float = 2.0) -> bool:
    """Return ``True`` when a raw TCP connection to a public DNS server succeeds.

    A socket probe is used instead of an HTTP request because it is fast, needs
    no third-party library and never blocks the UI for long.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False
