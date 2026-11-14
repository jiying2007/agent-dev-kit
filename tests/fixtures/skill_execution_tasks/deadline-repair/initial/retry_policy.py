def retry_allowed(elapsed_ms: int, timeout_ms: int) -> bool:
    """A request at its deadline has expired."""
    if elapsed_ms < 0 or timeout_ms <= 0:
        raise ValueError("invalid clock budget")
    return elapsed_ms <= timeout_ms
