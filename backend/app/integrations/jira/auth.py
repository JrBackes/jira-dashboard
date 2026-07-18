import httpx

from app.core.config import JiraSiteSettings


def basic_auth(site_settings: JiraSiteSettings) -> httpx.BasicAuth:
    return httpx.BasicAuth(username=site_settings.email, password=site_settings.api_token)
