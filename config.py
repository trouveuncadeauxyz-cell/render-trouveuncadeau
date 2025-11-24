"""
Configuration centralisée pour TrouveUnCadeau.xyz
Validation avec Pydantic, gestion des environnements
"""

import os
from typing import Optional
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Charger .env
load_dotenv()


class LLMConfig(BaseModel):
    """Configuration des LLMs"""
    
    # Together.ai
    together_api_key: str = Field(default="")
    together_model: str = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    
    # Gemini
    gemini_api_key: str = Field(default="")
    gemini_model: str = "gemini-2.0-flash-exp"
    
    # Claude
    claude_api_key: str = Field(default="")
    claude_model: str = "claude-3-5-haiku-20241022"
    
    # OpenAI (embeddings uniquement)
    openai_api_key: str = Field(default="")
    openai_embedding_model: str = "text-embedding-3-small"
    
    # Paramètres généraux
    default_temperature: float = 0.7
    default_max_tokens: int = 1024
    timeout_seconds: int = 30


class RedisConfig(BaseModel):
    """Configuration Redis"""
    
    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    password: Optional[str] = Field(default=None)
    db: int = Field(default=0)
    ttl_days: int = Field(default=7)
    enabled: bool = Field(default=True)
    
    @validator("port")
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Port doit être entre 1 et 65535")
        return v


class FAISSConfig(BaseModel):
    """Configuration FAISS vector store"""
    
    index_path: str = Field(default="./faiss_index")
    dimension: int = Field(default=1536)  # text-embedding-3-small
    metric_type: str = Field(default="cosine")
    rebuild_on_startup: bool = Field(default=False)


class AirtableConfig(BaseModel):
    """Configuration Airtable"""
    
    api_key: str = Field(default="")
    base_id: str = Field(default="")
    table_name: str = Field(default="Products")
    view_name: str = Field(default="In Stock")


class AppConfig(BaseModel):
    """Configuration application"""
    
    environment: str = Field(default="production")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    cors_origins: list[str] = Field(default=["*"])
    
    @validator("environment")
    def validate_environment(cls, v):
        if v not in ["development", "staging", "production"]:
            raise ValueError("Environment doit être: development, staging ou production")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        if v not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("Log level invalide")
        return v


class Settings(BaseSettings):
    """
    Settings principal de l'application
    Charge les variables d'environnement et valide la configuration
    """
    
    # Sous-configurations
    llm: LLMConfig = Field(default_factory=LLMConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    faiss: FAISSConfig = Field(default_factory=FAISSConfig)
    airtable: AirtableConfig = Field(default_factory=AirtableConfig)
    app: AppConfig = Field(default_factory=AppConfig)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Charger depuis variables d'environnement
        self.llm.together_api_key = os.getenv("TOGETHER_API_KEY", "")
        self.llm.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.llm.claude_api_key = os.getenv("CLAUDE_API_KEY", "")
        self.llm.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
        self.redis.host = os.getenv("REDIS_HOST", "localhost")
        self.redis.port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis.password = os.getenv("REDIS_PASSWORD")
        self.redis.enabled = os.getenv("REDIS_ENABLED", "true").lower() == "true"
        
        self.airtable.api_key = os.getenv("AIRTABLE_API_KEY", "")
        self.airtable.base_id = os.getenv("AIRTABLE_BASE_ID", "")
        
        self.app.environment = os.getenv("ENVIRONMENT", "production")
        self.app.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.app.log_level = os.getenv("LOG_LEVEL", "INFO")
    
    def validate_required_keys(self) -> tuple[bool, list[str]]:
        """
        Valide que toutes les clés API requises sont présentes
        
        Returns:
            (is_valid, missing_keys)
        """
        missing = []
        
        # Clés requises pour fonctionnement minimal
        if not self.llm.together_api_key:
            missing.append("TOGETHER_API_KEY")
        
        if not self.llm.openai_api_key:
            missing.append("OPENAI_API_KEY")
        
        if not self.airtable.api_key:
            missing.append("AIRTABLE_API_KEY")
        
        if not self.airtable.base_id:
            missing.append("AIRTABLE_BASE_ID")
        
        return (len(missing) == 0, missing)
    
    def get_summary(self) -> dict:
        """
        Retourne un résumé de la configuration (sans les secrets)
        
        Returns:
            Dict avec config sanitizée
        """
        return {
            "environment": self.app.environment,
            "debug": self.app.debug,
            "log_level": self.app.log_level,
            "llm": {
                "together_configured": bool(self.llm.together_api_key),
                "gemini_configured": bool(self.llm.gemini_api_key),
                "claude_configured": bool(self.llm.claude_api_key),
                "openai_configured": bool(self.llm.openai_api_key),
                "default_model": self.llm.together_model
            },
            "redis": {
                "enabled": self.redis.enabled,
                "host": self.redis.host,
                "port": self.redis.port,
                "ttl_days": self.redis.ttl_days
            },
            "faiss": {
                "index_path": self.faiss.index_path,
                "dimension": self.faiss.dimension
            },
            "airtable": {
                "configured": bool(self.airtable.api_key and self.airtable.base_id),
                "table_name": self.airtable.table_name
            }
        }


# Instance globale
_settings: Optional[Settings] = None


def get_settings(reload: bool = False) -> Settings:
    """
    Retourne l'instance Settings (singleton)
    
    Args:
        reload: Force le rechargement de la config
    
    Returns:
        Instance Settings configurée
    """
    global _settings
    
    if _settings is None or reload:
        _settings = Settings()
        
        # Valider les clés requises
        is_valid, missing = _settings.validate_required_keys()
        
        if not is_valid:
            print("⚠️  ATTENTION: Clés API manquantes!")
            print(f"   Manquantes: {', '.join(missing)}")
            print("   L'application pourrait ne pas fonctionner correctement.")
        else:
            print("✅ Configuration validée avec succès")
    
    return _settings


# Exemple d'utilisation
if __name__ == "__main__":
    import json
    
    # Charger settings
    settings = get_settings()
    
    # Afficher résumé
    print("📋 Configuration TrouveUnCadeau.xyz:")
    print(json.dumps(settings.get_summary(), indent=2))
    
    # Valider
    is_valid, missing = settings.validate_required_keys()
    print(f"\n{'✅' if is_valid else '⚠️ '} Validation: {'OK' if is_valid else f'Manquant: {missing}'}")
