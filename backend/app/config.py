from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ollama_host: str = "http://localhost:11434"
    model_provider: str = "openrouter"
    ollama_model: str = "stealth/ox-alpha"
    openrouter_api_key: str | None = None
    allowed_origins: str = "http://localhost:3000"
    #allowed_origins: str = "https://sdlc-reverse-engineer.vercel.app"
    phases_per_batch: int = 1
    # number_of_batches is derived from selected phases and phases_per_batch.
    # number_of_batches: int = 1
    batch_mode: str = "sequence"
    analysis_results_dir: str = "output-content"
    pipeline_smoke_test: bool = False
    resource_diagnostics_enabled: bool = False
    resource_diagnostics_interval_seconds: float = 2.0
    resource_diagnostics_dir: str = "resource-diagnostics"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    smoke_test_repo_url: str = "https://github.com/nmuru/continuous-delivery-cloud-native-java-apps-2423655"

    @property
    def opencode_model(self) -> str:
        return f"{self.model_provider}/{self.ollama_model}"


settings = Settings()
