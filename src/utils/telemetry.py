_last_image_provider = "unknown"

def set_last_image_provider(name: str) -> None:
    global _last_image_provider
    _last_image_provider = name

def get_last_image_provider() -> str:
    return _last_image_provider
