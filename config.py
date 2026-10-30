from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file = ".env", extra = "ignore")
    supabase_url : str
    supabase_service_role_key : str
    supabase_db_url : str
    supabase_storage_bucket : str
    google_api_key : str
    gemini_chat_model : str
    gemini_embedding_model : str
    frontend_origin : str

settings = Settings()
