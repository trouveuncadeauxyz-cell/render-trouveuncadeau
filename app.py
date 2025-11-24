"""
TrouveUnCadeau.xyz - API principale
FastAPI backend avec architecture multi-LLM optimisée
"""

import logging
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from config import get_settings
from cache_manager import CacheManager
from multi_llm_router import MultiLLMRouter, LLMProvider

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Charger settings
settings = get_settings()

# Instances globales
cache_manager: Optional[CacheManager] = None
llm_router: Optional[MultiLLMRouter] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events: startup et shutdown"""
    # Startup
    logger.info("🚀 Démarrage de TrouveUnCadeau.xyz...")
    
    global cache_manager, llm_router
    
    # Initialiser cache
    cache_manager = CacheManager(
        redis_host=settings.redis.host,
        redis_port=settings.redis.port,
        redis_password=settings.redis.password,
        redis_db=settings.redis.db,
        ttl_days=settings.redis.ttl_days,
        enabled=settings.redis.enabled
    )
    
    # Initialiser router
    llm_router = MultiLLMRouter()
    
    # Valider configuration
    is_valid, missing = settings.validate_required_keys()
    if not is_valid:
        logger.warning(f"⚠️  Clés API manquantes: {missing}")
    
    logger.info("✅ Application prête!")
    logger.info(f"   Environment: {settings.app.environment}")
    logger.info(f"   Cache: {'Activé' if settings.redis.enabled else 'Désactivé'}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Arrêt de l'application...")


# Créer app FastAPI
app = FastAPI(
    title="TrouveUnCadeau.xyz API",
    description="API de recommandations de cadeaux avec IA multi-LLM",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Models ===

class RecommendationRequest(BaseModel):
    """Requête de recommandation"""
    query: str = Field(..., description="Description du cadeau recherché")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Contexte additionnel")
    force_provider: Optional[str] = Field(default=None, description="Forcer un provider LLM")


class RecommendationResponse(BaseModel):
    """Réponse de recommandation"""
    recommendations: str
    llm_used: str
    cached: bool
    cost_usd: float
    tokens: Dict[str, int]


class HealthResponse(BaseModel):
    """Réponse health check"""
    status: str
    version: str
    environment: str
    cache_enabled: bool
    llm_providers: Dict[str, bool]


# === Routes ===

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "service": "TrouveUnCadeau.xyz API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    Vérifie le statut de l'application et des services
    """
    # Vérifier cache
    cache_health = cache_manager.health_check() if cache_manager else {"status": "disabled"}
    
    return HealthResponse(
        status="healthy" if cache_health["status"] in ["healthy", "disabled"] else "degraded",
        version="1.0.0",
        environment=settings.app.environment,
        cache_enabled=settings.redis.enabled and cache_health["status"] == "healthy",
        llm_providers={
            "together": bool(settings.llm.together_api_key),
            "gemini": bool(settings.llm.gemini_api_key),
            "claude": bool(settings.llm.claude_api_key),
            "openai": bool(settings.llm.openai_api_key)
        }
    )


@app.post("/api/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """
    Obtenir des recommandations de cadeaux
    
    Args:
        request: Requête avec query et contexte
    
    Returns:
        Recommandations avec métadonnées
    """
    try:
        # Vérifier cache d'abord
        cached_result = cache_manager.get(request.query, request.context) if cache_manager else None
        
        if cached_result:
            logger.info(f"Cache HIT pour: {request.query[:50]}...")
            return RecommendationResponse(**cached_result)
        
        # Cache MISS - Router vers le bon LLM
        force_provider = None
        if request.force_provider:
            try:
                force_provider = LLMProvider[request.force_provider.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Provider invalide: {request.force_provider}"
                )
        
        provider = llm_router.route(request.query, request.context, force_provider)
        
        # TODO: Implémenter appel réel aux LLMs
        # Pour l'instant, retourner un mock
        recommendations = f"[Mock] Recommandations pour: {request.query}"
        input_tokens = 150
        output_tokens = 200
        
        # Calculer coût
        cost = llm_router.track_usage(provider, input_tokens, output_tokens)
        
        # Créer réponse
        response_data = {
            "recommendations": recommendations,
            "llm_used": provider.value,
            "cached": False,
            "cost_usd": cost,
            "tokens": {
                "input": input_tokens,
                "output": output_tokens,
                "total": input_tokens + output_tokens
            }
        }
        
        # Sauvegarder dans cache
        if cache_manager:
            cache_manager.set(request.query, response_data, request.context)
        
        return RecommendationResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Erreur lors de la recommandation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )


@app.get("/api/stats")
async def get_stats():
    """
    Obtenir les statistiques d'utilisation
    
    Returns:
        Stats cache et routing LLM
    """
    stats = {
        "cache": cache_manager.get_stats() if cache_manager else {"enabled": False},
        "llm_routing": llm_router.get_stats() if llm_router else {},
        "environment": settings.app.environment
    }
    
    return JSONResponse(content=stats)


@app.post("/api/cache/clear")
async def clear_cache():
    """
    Vider le cache (admin uniquement en production)
    
    Returns:
        Statut de l'opération
    """
    if not cache_manager or not cache_manager.enabled:
        return {"status": "cache_disabled"}
    
    success = cache_manager.clear_all()
    
    return {
        "status": "success" if success else "error",
        "message": "Cache vidé avec succès" if success else "Erreur lors du vidage"
    }


@app.get("/api/config")
async def get_config():
    """
    Obtenir la configuration (sanitizée)
    
    Returns:
        Résumé de la config sans secrets
    """
    return JSONResponse(content=settings.get_summary())


# === Error Handlers ===

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handler pour HTTPException"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handler pour exceptions générales"""
    logger.error(f"Erreur non gérée: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Erreur interne du serveur",
            "detail": str(exc) if settings.app.debug else "Une erreur est survenue"
        }
    )


# === Main ===

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
        log_level=settings.app.log_level.lower()
    )
