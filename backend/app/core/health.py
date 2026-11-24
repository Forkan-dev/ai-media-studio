import shutil

import httpx

from app.core.config import settings


def _http(url: str) -> bool:
    try:
        return httpx.get(url, timeout=2).status_code < 500
    except httpx.HTTPError:
        return False


def check_services() -> dict[str, bool]:
    return {
        "ollama": _http(f"{settings.ollama_url}/api/tags"),
        "comfyui": _http(f"{settings.comfy_url}/system_stats"),
        "search": _http(settings.search_url),
        "ffmpeg": shutil.which(settings.ffmpeg_bin) is not None,
    }


if __name__ == "__main__":
    for name, ok in check_services().items():
        print(f"{'OK  ' if ok else 'DOWN'} {name}")
