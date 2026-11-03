import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "")
    openalex_institution_id: str = os.getenv("UNILA_OPENALEX_ID", "")
    openalex_api_key: str = os.getenv("OPENALEX_API_KEY", "")

    def require_database_url(self) -> str:
        if not self.database_url:
            raise RuntimeError("DATABASE_URL não definida. Preencha o arquivo .env.")
        return self.database_url


settings = Settings()