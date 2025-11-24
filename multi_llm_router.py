"""
Multi-LLM Router pour TrouveUnCadeau.xyz
Routing intelligent entre Together.ai, Gemini et Claude
Optimisation: 99% économie vs OpenAI pur
"""

from typing import Dict, Any, Optional
from enum import Enum
import re


class LLMProvider(Enum):
    """Providers LLM disponibles"""
    TOGETHER = "together.ai"
    GEMINI = "gemini"
    CLAUDE = "claude"


class QueryComplexity(Enum):
    """Niveaux de complexité des requêtes"""
    SIMPLE = "simple"      # 90% des requêtes
    MEDIUM = "medium"      # 8% des requêtes
    COMPLEX = "complex"    # 2% des requêtes


class MultiLLMRouter:
    """
    Router intelligent pour sélectionner le LLM optimal
    
    Stratégie de routing:
    - SIMPLE (90%) → Together.ai Mixtral ($0.06/1M tokens)
    - MEDIUM (8%) → Gemini Flash 2.0 (GRATUIT)
    - COMPLEX (2%) → Claude Haiku ($0.25/1M tokens)
    
    Critères de complexité:
    - Longueur de la query
    - Nombre de contraintes
    - Mots-clés spécifiques
    - Contexte additionnel
    """
    
    # Coûts par million de tokens (input + output moyen)
    COSTS = {
        LLMProvider.TOGETHER: 0.06 / 1_000_000,  # Mixtral 8x7B
        LLMProvider.GEMINI: 0.0,                  # Gratuit!
        LLMProvider.CLAUDE: 0.25 / 1_000_000      # Haiku
    }
    
    # Mots-clés indiquant complexité
    COMPLEX_KEYWORDS = [
        "comparer", "analyser", "expliquer", "différence", 
        "pourquoi", "comment", "meilleur", "conseil",
        "recommandation personnalisée", "plusieurs options"
    ]
    
    MEDIUM_KEYWORDS = [
        "budget", "occasion", "âge", "genre",
        "liste", "idées", "suggestions"
    ]
    
    def __init__(self):
        """Initialise le router"""
        self.stats = {
            LLMProvider.TOGETHER: {"count": 0, "total_cost": 0.0},
            LLMProvider.GEMINI: {"count": 0, "total_cost": 0.0},
            LLMProvider.CLAUDE: {"count": 0, "total_cost": 0.0}
        }
        
        print("🎯 Multi-LLM Router initialisé")
        print(f"   - Together.ai: ${self.COSTS[LLMProvider.TOGETHER]*1_000_000:.2f}/1M tokens")
        print(f"   - Gemini Flash: GRATUIT")
        print(f"   - Claude Haiku: ${self.COSTS[LLMProvider.CLAUDE]*1_000_000:.2f}/1M tokens")
    
    def analyze_complexity(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> QueryComplexity:
        """
        Analyse la complexité d'une requête
        
        Args:
            query: Query utilisateur
            context: Contexte additionnel (budget, occasion, etc.)
        
        Returns:
            Niveau de complexité
        """
        query_lower = query.lower()
        
        # Score de complexité (0-100)
        complexity_score = 0
        
        # 1. Longueur de la query
        word_count = len(query.split())
        if word_count > 30:
            complexity_score += 30
        elif word_count > 15:
            complexity_score += 15
        elif word_count > 8:
            complexity_score += 5
        
        # 2. Mots-clés complexes
        complex_matches = sum(1 for kw in self.COMPLEX_KEYWORDS if kw in query_lower)
        complexity_score += complex_matches * 20
        
        # 3. Mots-clés moyens
        medium_matches = sum(1 for kw in self.MEDIUM_KEYWORDS if kw in query_lower)
        complexity_score += medium_matches * 5
        
        # 4. Questions multiples (?, plusieurs phrases)
        question_count = query.count("?")
        sentence_count = len(re.split(r'[.!?]+', query))
        if question_count > 1 or sentence_count > 2:
            complexity_score += 15
        
        # 5. Contexte additionnel
        if context:
            if len(context) > 3:
                complexity_score += 10
            elif len(context) > 1:
                complexity_score += 5
        
        # 6. Caractères spéciaux suggérant analyse (comparaisons, etc.)
        if any(char in query for char in ['vs', 'ou', 'versus', 'vs.']):
            complexity_score += 15
        
        # Déterminer complexité finale
        if complexity_score >= 50:
            return QueryComplexity.COMPLEX
        elif complexity_score >= 20:
            return QueryComplexity.MEDIUM
        else:
            return QueryComplexity.SIMPLE
    
    def route(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        force_provider: Optional[LLMProvider] = None
    ) -> LLMProvider:
        """
        Détermine quel LLM utiliser pour une requête
        
        Args:
            query: Query utilisateur
            context: Contexte additionnel
            force_provider: Forcer un provider spécifique (override)
        
        Returns:
            LLM provider à utiliser
        """
        # Override si demandé
        if force_provider:
            return force_provider
        
        # Analyser complexité
        complexity = self.analyze_complexity(query, context)
        
        # Router selon complexité
        if complexity == QueryComplexity.COMPLEX:
            provider = LLMProvider.CLAUDE
            print(f"🧠 Complexité HAUTE → Claude Haiku (qualité max)")
            
        elif complexity == QueryComplexity.MEDIUM:
            provider = LLMProvider.GEMINI
            print(f"⚡ Complexité MOYENNE → Gemini Flash (gratuit!)")
            
        else:  # SIMPLE
            provider = LLMProvider.TOGETHER
            print(f"🚀 Complexité BASSE → Together.ai Mixtral (ultra-rapide)")
        
        return provider
    
    def track_usage(
        self,
        provider: LLMProvider,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Track l'utilisation et calcule le coût
        
        Args:
            provider: Provider utilisé
            input_tokens: Nombre de tokens input
            output_tokens: Nombre de tokens output
        
        Returns:
            Coût de la requête en USD
        """
        # Calculer coût (simplifié: même prix input/output)
        total_tokens = input_tokens + output_tokens
        cost = total_tokens * self.COSTS[provider]
        
        # Mettre à jour stats
        self.stats[provider]["count"] += 1
        self.stats[provider]["total_cost"] += cost
        
        return cost
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques d'utilisation
        
        Returns:
            Stats par provider et totaux
        """
        total_requests = sum(s["count"] for s in self.stats.values())
        total_cost = sum(s["total_cost"] for s in self.stats.values())
        
        return {
            "total_requests": total_requests,
            "total_cost_usd": total_cost,
            "distribution": {
                "together": {
                    "count": self.stats[LLMProvider.TOGETHER]["count"],
                    "percentage": (self.stats[LLMProvider.TOGETHER]["count"] / total_requests * 100) if total_requests > 0 else 0,
                    "cost_usd": self.stats[LLMProvider.TOGETHER]["total_cost"]
                },
                "gemini": {
                    "count": self.stats[LLMProvider.GEMINI]["count"],
                    "percentage": (self.stats[LLMProvider.GEMINI]["count"] / total_requests * 100) if total_requests > 0 else 0,
                    "cost_usd": self.stats[LLMProvider.GEMINI]["total_cost"]
                },
                "claude": {
                    "count": self.stats[LLMProvider.CLAUDE]["count"],
                    "percentage": (self.stats[LLMProvider.CLAUDE]["count"] / total_requests * 100) if total_requests > 0 else 0,
                    "cost_usd": self.stats[LLMProvider.CLAUDE]["total_cost"]
                }
            },
            "avg_cost_per_request": total_cost / total_requests if total_requests > 0 else 0
        }
    
    def estimate_monthly_cost(self, daily_requests: int = 1000) -> Dict[str, float]:
        """
        Estime les coûts mensuels selon différents scénarios
        
        Args:
            daily_requests: Nombre de requêtes par jour
        
        Returns:
            Estimations de coûts
        """
        monthly_requests = daily_requests * 30
        
        # Tokens moyens par requête (estimation)
        avg_input_tokens = 200
        avg_output_tokens = 300
        avg_tokens_per_request = avg_input_tokens + avg_output_tokens
        
        # Distribution cible: 90% Together, 8% Gemini, 2% Claude
        together_requests = monthly_requests * 0.90
        gemini_requests = monthly_requests * 0.08
        claude_requests = monthly_requests * 0.02
        
        # Calculer coûts
        together_cost = (together_requests * avg_tokens_per_request * self.COSTS[LLMProvider.TOGETHER])
        gemini_cost = 0.0  # Gratuit!
        claude_cost = (claude_requests * avg_tokens_per_request * self.COSTS[LLMProvider.CLAUDE])
        
        total_cost = together_cost + gemini_cost + claude_cost
        
        # Comparaison OpenAI
        openai_cost_per_token = 0.60 / 1_000_000  # GPT-3.5 Turbo
        openai_total_cost = monthly_requests * avg_tokens_per_request * openai_cost_per_token
        
        savings = openai_total_cost - total_cost
        savings_percentage = (savings / openai_total_cost * 100) if openai_total_cost > 0 else 0
        
        return {
            "daily_requests": daily_requests,
            "monthly_requests": monthly_requests,
            "costs": {
                "together_ai": together_cost,
                "gemini_flash": gemini_cost,
                "claude_haiku": claude_cost,
                "total": total_cost,
                "openai_comparison": openai_total_cost
            },
            "savings": {
                "amount_usd": savings,
                "percentage": savings_percentage
            }
        }


# Exemple d'utilisation
if __name__ == "__main__":
    import json
    
    # Initialiser router
    router = MultiLLMRouter()
    
    # Tests de routing
    test_queries = [
        ("Cadeau pour maman", None),
        ("Je cherche un cadeau pour ma mère qui aime lire et jardiner, budget 50$", {"occasion": "anniversaire"}),
        ("Peux-tu comparer un Kindle vs une liseuse Kobo et m'expliquer pourquoi l'un serait meilleur que l'autre pour une lectrice de 50 ans?", None)
    ]
    
    print("\n🧪 Tests de routing:\n")
    for query, context in test_queries:
        print(f"Query: {query[:60]}...")
        complexity = router.analyze_complexity(query, context)
        provider = router.route(query, context)
        print(f"Complexité: {complexity.value}")
        print(f"Provider: {provider.value}\n")
    
    # Simuler utilisation
    print("\n📊 Simulation d'utilisation:")
    router.track_usage(LLMProvider.TOGETHER, 150, 200)
    router.track_usage(LLMProvider.TOGETHER, 180, 250)
    router.track_usage(LLMProvider.GEMINI, 220, 300)
    router.track_usage(LLMProvider.CLAUDE, 400, 600)
    
    stats = router.get_stats()
    print(json.dumps(stats, indent=2))
    
    # Estimation mensuelle
    print("\n💰 Estimation mensuelle (1000 req/jour):")
    estimate = router.estimate_monthly_cost(daily_requests=1000)
    print(json.dumps(estimate, indent=2))
    print(f"\n✅ Économie: ${estimate['savings']['amount_usd']:.2f}/mois ({estimate['savings']['percentage']:.1f}%)")
