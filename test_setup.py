#!/usr/bin/env python3
"""
Script de test rapide pour vérifier l'installation
TrouveUnCadeau.xyz
"""

import sys
import os

def test_imports():
    """Test que toutes les dépendances sont installées"""
    print("🧪 Test des imports...")
    
    required_packages = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
        ("redis", "Redis"),
        ("langchain", "LangChain"),
    ]
    
    missing = []
    
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} - MANQUANT")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Packages manquants: {', '.join(missing)}")
        print("   Installer avec: pip install -r requirements.txt")
        return False
    
    print("✅ Tous les packages sont installés!\n")
    return True


def test_config():
    """Test que la configuration est valide"""
    print("🔧 Test de la configuration...")
    
    try:
        from config import get_settings
        
        settings = get_settings()
        is_valid, missing = settings.validate_required_keys()
        
        if not is_valid:
            print(f"   ⚠️  Clés API manquantes: {', '.join(missing)}")
            print("   Copier .env.example vers .env et remplir les clés")
            return False
        
        summary = settings.get_summary()
        print(f"   ✅ Environment: {summary['environment']}")
        print(f"   ✅ Cache: {'Activé' if summary['redis']['enabled'] else 'Désactivé'}")
        print(f"   ✅ LLMs configurés: {sum(1 for v in summary['llm'].values() if isinstance(v, bool) and v)}")
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    print("✅ Configuration valide!\n")
    return True


def test_cache():
    """Test que Redis fonctionne"""
    print("💾 Test du cache Redis...")
    
    try:
        from cache_manager import CacheManager
        from config import get_settings
        
        settings = get_settings()
        
        if not settings.redis.enabled:
            print("   ⚠️  Cache désactivé dans la config")
            return True
        
        cache = CacheManager(
            redis_host=settings.redis.host,
            redis_port=settings.redis.port,
            redis_password=settings.redis.password,
            enabled=settings.redis.enabled
        )
        
        # Test health check
        health = cache.health_check()
        
        if health["status"] == "healthy":
            print(f"   ✅ Redis connecté ({settings.redis.host}:{settings.redis.port})")
            print(f"   ✅ Uptime: {health['uptime_seconds']}s")
        elif health["status"] == "disabled":
            print("   ℹ️  Cache désactivé")
        else:
            print(f"   ⚠️  Redis unhealthy: {health.get('error', 'Unknown')}")
            return False
        
    except Exception as e:
        print(f"   ⚠️  Erreur Redis: {e}")
        print("   L'application fonctionnera sans cache (coûts plus élevés)")
        return True  # Non-bloquant
    
    print("✅ Cache fonctionnel!\n")
    return True


def test_router():
    """Test que le router LLM fonctionne"""
    print("🎯 Test du router Multi-LLM...")
    
    try:
        from multi_llm_router import MultiLLMRouter, QueryComplexity
        
        router = MultiLLMRouter()
        
        # Test queries
        test_cases = [
            ("Cadeau pour maman", QueryComplexity.SIMPLE),
            ("Je cherche un cadeau pour ma mère qui aime lire et jardiner", QueryComplexity.MEDIUM),
            ("Compare différentes options et explique pourquoi", QueryComplexity.COMPLEX)
        ]
        
        for query, expected in test_cases:
            complexity = router.analyze_complexity(query)
            provider = router.route(query)
            
            if complexity == expected:
                print(f"   ✅ '{query[:40]}...' → {provider.value}")
            else:
                print(f"   ⚠️  Complexité inattendue pour '{query[:40]}...'")
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    print("✅ Router fonctionnel!\n")
    return True


def test_api():
    """Test que l'API peut démarrer"""
    print("🚀 Test de l'API...")
    
    try:
        from app import app
        
        # Vérifier que l'app FastAPI est créée
        if app is None:
            print("   ❌ App FastAPI non créée")
            return False
        
        print(f"   ✅ App FastAPI créée: {app.title}")
        print(f"   ✅ Version: {app.version}")
        
        # Vérifier les routes
        routes = [route.path for route in app.routes]
        expected_routes = ["/", "/health", "/api/recommendations", "/api/stats"]
        
        for route in expected_routes:
            if route in routes:
                print(f"   ✅ Route: {route}")
            else:
                print(f"   ⚠️  Route manquante: {route}")
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    print("✅ API prête!\n")
    return True


def main():
    """Exécute tous les tests"""
    print("=" * 60)
    print("🧪 TESTS DE VÉRIFICATION - TrouveUnCadeau.xyz")
    print("=" * 60)
    print()
    
    results = {
        "Imports": test_imports(),
        "Configuration": test_config(),
        "Cache Redis": test_cache(),
        "Router LLM": test_router(),
        "API FastAPI": test_api()
    }
    
    print("=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 Tous les tests passent! L'application est prête.")
        print("\nPour démarrer:")
        print("  python app.py")
        print("\nOu avec uvicorn:")
        print("  uvicorn app:app --reload")
        return 0
    else:
        print("\n⚠️  Certains tests ont échoué. Vérifier les erreurs ci-dessus.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
