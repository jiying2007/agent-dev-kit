def limit_items(items, limit):
    """None means unlimited; zero means no items."""
    if limit is None:
        return items
    return items[:limit]
