from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    database_url: str = f"sqlite:///{ROOT / 'storage' / 'studio.db'}"
    storage_dir: Path = ROOT / "storage"
    brands_dir: Path = ROOT / "backend" / "brands"
    prompts_dir: Path = ROOT / "backend" / "prompts"
    workflows_dir: Path = ROOT / "backend" / "workflows"

    ollama_url: str = "http://localhost:11434"
    llm_model: str = "qwen3.5:9b-q4_K_M"  # q4_K_M build: supports JSON schema output in Ollama
    llm_context: int = 16384  # tokens; research prompts include page text
    comfy_url: str = "http://localhost:8188"
    search_url: str = "http://localhost:8080"  # SearXNG
    ffmpeg_bin: str = "ffmpeg"


settings = Settings()
