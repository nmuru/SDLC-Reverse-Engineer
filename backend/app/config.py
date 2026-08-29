from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ollama_host: str = "http://localhost:11434"
    model_provider: str = "openrouter"
    ollama_model: str = "stealth/ox-alpha"
    openrouter_api_key: str | None = None
    allowed_origins: str = "http://localhost:3000"
    phases_per_batch: int = 3
    # number_of_batches is derived from selected phases and phases_per_batch.
    # number_of_batches: int = 1
    batch_mode: str = "parallel"
    analysis_results_dir: str = "output-content"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def opencode_model(self) -> str:
        return f"{self.model_provider}/{self.ollama_model}"


settings = Settings()
