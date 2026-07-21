from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class JiraSiteSettings(BaseSettings):
    base_url: str
    email: str
    api_token: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    database_url: str

    jira_tec_base_url: str = ""
    jira_tec_email: str = ""
    jira_tec_api_token: str = ""

    jira_cap_base_url: str = ""
    jira_cap_email: str = ""
    jira_cap_api_token: str = ""

    # Mapa de Tecnologia: sem credencial nenhuma do Google (Cloud fora de alcance, planilha não
    # pode ficar com link público) — importado por colar/paste manual, ver tech_map_service.py.
    # Só um rótulo padrão pra identificar a aba importada, não uma credencial de acesso.
    tech_map_sheet_name: str = "[Desenvolvimento] Planejamento Q3"

    def jira_site_settings(self, site_key: str) -> JiraSiteSettings:
        site_key = site_key.upper()
        prefix = f"jira_{site_key.lower()}_"
        base_url = getattr(self, f"{prefix}base_url")
        email = getattr(self, f"{prefix}email")
        api_token = getattr(self, f"{prefix}api_token")
        if not (base_url and email and api_token):
            raise ValueError(f"Credenciais do Jira não configuradas para o site '{site_key}' (.env)")
        return JiraSiteSettings(base_url=base_url, email=email, api_token=api_token)


@lru_cache
def get_settings() -> Settings:
    return Settings()
