"""
Cache Manager pour TrouveUnCadeau.xyz
Gestion intelligente du cache Redis pour réduire les coûts LLM de 80%+
"""

import hashlib
import json
import redis
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class CacheManager:
    """
    Gestionnaire de cache Redis pour les requêtes LLM
    - Hit rate cible: 80%+
    - TTL: 7 jours (configurable)
    - Génération de clés MD5 uniques
    - Stats en temps réel
    """
    
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_password: Optional[str] = None,
        redis_db: int = 0,
        ttl_days: int = 7,
        enabled: bool = True
    ):
        """
        Initialise le gestionnaire de cache
        
        Args:
            redis_host: Hôte Redis (default: localhost)
            redis_port: Port Redis (default: 6379)
            redis_password: Mot de passe Redis (optionnel)
            redis_db: Base de données Redis (default: 0)
            ttl_days: Durée de vie du cache en jours (default: 7)
            enabled: Activer/désactiver le cache (default: True)
        """
        self.enabled = enabled
        self.ttl_seconds = ttl_days * 24 * 60 * 60
        
        # Stats
        self.stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "last_hit": None,
            "last_miss": None
        }
        
        if not self.enabled:
            print("⚠️  Cache désactivé")
            self.redis_client = None
            return
        
        try:
            # Connexion Redis
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                db=redis_db,
                decode_responses=True,
                socket_timeout=2,
                socket_connect_timeout=2
            )
            
            # Test connexion
            self.redis_client.ping()
            print(f"✅ Cache Redis connecté ({redis_host}:{redis_port})")
            
        except Exception as e:
            print(f"⚠️  Impossible de se connecter à Redis: {e}")
            print("   Le système fonctionnera sans cache (coût plus élevé)")
            self.redis_client = None
            self.enabled = False
    
    def _generate_cache_key(self, query: str, context: Optional[Dict] = None) -> str:
        """
        Génère une clé de cache unique basée sur la query et le contexte
        
        Args:
            query: Query utilisateur
            context: Contexte additionnel (budget, occasion, etc.)
        
        Returns:
            Clé MD5 unique
        """
        # Créer une représentation unique de la requête
        cache_data = {
            "query": query.lower().strip(),
            "context": context or {}
        }
        
        # Générer hash MD5
        cache_string = json.dumps(cache_data, sort_keys=True)
        cache_key = hashlib.md5(cache_string.encode()).hexdigest()
        
        return f"trouveuncadeau:llm:{cache_key}"
    
    def get(self, query: str, context: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Récupère une réponse du cache
        
        Args:
            query: Query utilisateur
            context: Contexte additionnel
        
        Returns:
            Réponse cachée ou None si pas trouvée
        """
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(query, context)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                # Cache HIT
                self.stats["hits"] += 1
                self.stats["last_hit"] = datetime.now().isoformat()
                
                result = json.loads(cached_data)
                result["cached"] = True
                result["cache_hit_at"] = datetime.now().isoformat()
                
                print(f"🎯 Cache HIT ({self.get_hit_rate():.1%})")
                return result
            else:
                # Cache MISS
                self.stats["misses"] += 1
                self.stats["last_miss"] = datetime.now().isoformat()
                print(f"💨 Cache MISS ({self.get_hit_rate():.1%})")
                return None
                
        except Exception as e:
            self.stats["errors"] += 1
            print(f"⚠️  Erreur cache.get(): {e}")
            return None
    
    def set(
        self,
        query: str,
        response: Dict[str, Any],
        context: Optional[Dict] = None,
        ttl_override: Optional[int] = None
    ) -> bool:
        """
        Sauvegarde une réponse dans le cache
        
        Args:
            query: Query utilisateur
            response: Réponse à cacher
            context: Contexte additionnel
            ttl_override: Override du TTL en secondes
        
        Returns:
            True si succès, False sinon
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(query, context)
            
            # Ajouter metadata
            cache_data = {
                **response,
                "cached_at": datetime.now().isoformat(),
                "cache_key": cache_key
            }
            
            # Sauvegarder avec TTL
            ttl = ttl_override if ttl_override else self.ttl_seconds
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(cache_data)
            )
            
            print(f"💾 Réponse cachée (TTL: {ttl//86400} jours)")
            return True
            
        except Exception as e:
            self.stats["errors"] += 1
            print(f"⚠️  Erreur cache.set(): {e}")
            return False
    
    def invalidate(self, query: str, context: Optional[Dict] = None) -> bool:
        """
        Invalide une entrée du cache
        
        Args:
            query: Query à invalider
            context: Contexte additionnel
        
        Returns:
            True si succès, False sinon
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(query, context)
            deleted = self.redis_client.delete(cache_key)
            
            if deleted:
                print(f"🗑️  Cache invalidé: {cache_key[:16]}...")
                return True
            else:
                print(f"⚠️  Clé non trouvée: {cache_key[:16]}...")
                return False
                
        except Exception as e:
            self.stats["errors"] += 1
            print(f"⚠️  Erreur cache.invalidate(): {e}")
            return False
    
    def clear_all(self) -> bool:
        """
        Vide tout le cache TrouveUnCadeau
        
        Returns:
            True si succès, False sinon
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            # Trouver toutes les clés TrouveUnCadeau
            keys = self.redis_client.keys("trouveuncadeau:llm:*")
            
            if keys:
                deleted = self.redis_client.delete(*keys)
                print(f"🗑️  {deleted} entrées supprimées du cache")
                return True
            else:
                print("ℹ️  Cache déjà vide")
                return True
                
        except Exception as e:
            self.stats["errors"] += 1
            print(f"⚠️  Erreur cache.clear_all(): {e}")
            return False
    
    def get_hit_rate(self) -> float:
        """
        Calcule le taux de hit du cache
        
        Returns:
            Hit rate entre 0 et 1
        """
        total = self.stats["hits"] + self.stats["misses"]
        if total == 0:
            return 0.0
        return self.stats["hits"] / total
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du cache
        
        Returns:
            Dict avec stats détaillées
        """
        return {
            **self.stats,
            "hit_rate": self.get_hit_rate(),
            "enabled": self.enabled,
            "ttl_days": self.ttl_seconds // 86400
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Vérifie la santé du cache Redis
        
        Returns:
            Status et métriques
        """
        if not self.enabled or not self.redis_client:
            return {
                "status": "disabled",
                "message": "Cache désactivé"
            }
        
        try:
            # Test ping
            self.redis_client.ping()
            
            # Stats Redis
            info = self.redis_client.info()
            
            return {
                "status": "healthy",
                "connected": True,
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "used_memory_mb": info.get("used_memory", 0) / (1024 * 1024),
                "total_keys": len(self.redis_client.keys("trouveuncadeau:llm:*")),
                **self.get_stats()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }


# Exemple d'utilisation
if __name__ == "__main__":
    # Initialiser cache
    cache = CacheManager(
        redis_host="localhost",
        redis_port=6379,
        ttl_days=7
    )
    
    # Test query
    query = "cadeau pour maman qui aime lire, budget 50$"
    context = {"occasion": "anniversaire", "age": 50}
    
    # Essayer de récupérer du cache
    cached = cache.get(query, context)
    if cached:
        print(f"✅ Réponse trouvée dans le cache: {cached}")
    else:
        # Simuler appel LLM
        response = {
            "llm_used": "together.ai",
            "recommendations": "Kindle Paperwhite...",
            "cost_usd": 0.00006
        }
        
        # Sauvegarder dans cache
        cache.set(query, response, context)
    
    # Afficher stats
    print("\n📊 Statistiques:")
    print(json.dumps(cache.get_stats(), indent=2))
    
    # Health check
    print("\n🏥 Health Check:")
    print(json.dumps(cache.health_check(), indent=2))
