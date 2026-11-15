from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Información de la API (aparecerá en la interfaz /docs)
    PROJECT_NAME: str = "SmartDoc AI Extractor API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = (
        "Microservicio de extracción estructurada de datos desde documentos PDF "
        "utilizando FastAPI, Pydantic v2 y Gemini Structured Outputs."
    )

    # Seguridad y Entorno
    GEMINI_API_KEY: str
    ENVIRONMENT: str = "development"

    # Reglas de negocio / Límites para proteger tu capa gratuita
    MAX_FILE_SIZE_MB: int = 5
    RATE_LIMIT: str = "5/minute"  # Máximo 5 peticiones por minuto por IP

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Instancia única que importaremos en toda la app
settings = Settings()