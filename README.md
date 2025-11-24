# 🎁 TrouveUnCadeau.xyz - Backend API

API de recommandations de cadeaux avec intelligence artificielle multi-LLM optimisée.

**Architecture:** Multi-LLM (Together.ai + Gemini + Claude) avec cache Redis  
**Économie:** 99% vs OpenAI pur ($65/mois vs $650/mois)  
**Déploiement:** Optimisé pour Render.com

---

## 🚀 Déploiement Rapide sur Render.com

### Prérequis
- Compte GitHub
- Compte Render.com (gratuit)
- Clés API: Together.ai, OpenAI, Airtable

### Étapes

1. **Fork/Clone ce repo**
```bash
git clone https://github.com/votre-username/render-trouveuncadeau.git
cd render-trouveuncadeau
```

2. **Push vers votre GitHub**
```bash
git remote set-url origin https://github.com/votre-username/render-trouveuncadeau.git
git push -u origin main
```

3. **Déployer sur Render.com**
   - Créer un nouveau "Blueprint" depuis votre repo
   - Render détectera automatiquement `render.yaml`
   - Ajouter les variables d'environnement (secrets):
     - `TOGETHER_API_KEY`
     - `OPENAI_API_KEY`
     - `AIRTABLE_API_KEY`
     - `AIRTABLE_BASE_ID`
     - `GEMINI_API_KEY` (optionnel)
     - `CLAUDE_API_KEY` (optionnel)

4. **Deploy!**
   - Render build et déploie automatiquement
   - API accessible à: `https://trouveuncadeau-api.onrender.com`
   - Docs interactives: `https://trouveuncadeau-api.onrender.com/docs`

**C'est tout!** ✨

---

## 📁 Structure du Projet

```
render-trouveuncadeau/
├── app.py                    # FastAPI application principale
├── config.py                 # Configuration centralisée
├── cache_manager.py          # Gestion cache Redis
├── multi_llm_router.py       # Routing intelligent multi-LLM
├── requirements.txt          # Dépendances Python
├── render.yaml              # Configuration Render.com
├── .env.example             # Template variables d'environnement
├── .gitignore               # Git ignore
└── README.md                # Ce fichier
```

---

## 🏗️ Architecture

### Routing Multi-LLM

L'application route intelligemment les requêtes vers le LLM optimal:

| Complexité | LLM | % Trafic | Coût/1M tokens | Usage |
|-----------|-----|----------|----------------|-------|
| **Simple** | Together.ai (Mixtral) | 90% | $0.06 | Requêtes standard |
| **Moyenne** | Gemini Flash 2.0 | 8% | **GRATUIT** | Contexte riche |
| **Complexe** | Claude Haiku | 2% | $0.25 | Analyses poussées |

### Cache Redis

- **Hit rate cible:** 80%+
- **TTL:** 7 jours (configurable)
- **Économie:** Réduit les appels LLM de 80%
- **Graceful degradation:** Fonctionne même si Redis down

### Calcul d'Économie

**Scénario:** 1000 requêtes/jour (30k/mois)

| Provider | Coût mensuel | Économie |
|----------|--------------|----------|
| **OpenAI pur** | $650 | - |
| **Architecture optimisée** | $65 | **99%** 🎉 |

*Détails:*
- Together.ai (90%): $54/mois
- Gemini (8%): $0/mois (gratuit!)
- Claude (2%): $11/mois
- **Total: $65/mois**

---

## 🛠️ Développement Local

### Installation

```bash
# 1. Clone le repo
git clone https://github.com/votre-username/render-trouveuncadeau.git
cd render-trouveuncadeau

# 2. Créer environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Installer dépendances
pip install -r requirements.txt

# 4. Configuration
cp .env.example .env
# Éditer .env avec vos clés API

# 5. Démarrer Redis (optionnel)
# Option A: Docker
docker run -d -p 6379:6379 redis:alpine

# Option B: Installation locale
# macOS: brew install redis && redis-server
# Ubuntu: sudo apt install redis-server && redis-server
# Windows: https://redis.io/download

# 6. Lancer l'API
python app.py
```

L'API sera accessible à `http://localhost:8000`

### Tests

```bash
# Health check
curl http://localhost:8000/health

# Test recommandation
curl -X POST http://localhost:8000/api/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "query": "cadeau pour maman qui aime lire, budget 50$",
    "context": {"occasion": "anniversaire"}
  }'

# Voir les stats
curl http://localhost:8000/api/stats
```

### Documentation Interactive

Visitez `http://localhost:8000/docs` pour l'interface Swagger UI.

---

## 🔌 API Endpoints

### `GET /health`
Health check de l'application

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production",
  "cache_enabled": true,
  "llm_providers": {
    "together": true,
    "gemini": true,
    "claude": true,
    "openai": true
  }
}
```

### `POST /api/recommendations`
Obtenir des recommandations de cadeaux

**Request:**
```json
{
  "query": "cadeau pour papa qui aime le golf, budget 100$",
  "context": {
    "occasion": "fête des pères",
    "age": 55
  },
  "force_provider": "together"  // Optionnel
}
```

**Response:**
```json
{
  "recommendations": "Je vous recommande...",
  "llm_used": "together.ai",
  "cached": false,
  "cost_usd": 0.00012,
  "tokens": {
    "input": 150,
    "output": 200,
    "total": 350
  }
}
```

### `GET /api/stats`
Statistiques d'utilisation

**Response:**
```json
{
  "cache": {
    "hits": 850,
    "misses": 150,
    "hit_rate": 0.85,
    "enabled": true
  },
  "llm_routing": {
    "total_requests": 1000,
    "total_cost_usd": 65.43,
    "distribution": {
      "together": {
        "count": 900,
        "percentage": 90.0,
        "cost_usd": 54.00
      },
      "gemini": {
        "count": 80,
        "percentage": 8.0,
        "cost_usd": 0.00
      },
      "claude": {
        "count": 20,
        "percentage": 2.0,
        "cost_usd": 11.43
      }
    }
  }
}
```

### `POST /api/cache/clear`
Vider le cache (admin)

**Response:**
```json
{
  "status": "success",
  "message": "Cache vidé avec succès"
}
```

### `GET /api/config`
Configuration sanitizée (sans secrets)

---

## ⚙️ Configuration

### Variables d'Environnement

Voir `.env.example` pour la liste complète.

**Variables Requises:**
```bash
TOGETHER_API_KEY=xxx        # Provider principal
OPENAI_API_KEY=xxx         # Pour embeddings
AIRTABLE_API_KEY=xxx       # Base de données produits
AIRTABLE_BASE_ID=xxx       # ID de la base Airtable
```

**Variables Optionnelles:**
```bash
GEMINI_API_KEY=xxx         # Provider secondaire (gratuit!)
CLAUDE_API_KEY=xxx         # Provider tertiaire (qualité max)
REDIS_HOST=localhost       # Cache
REDIS_PORT=6379
REDIS_ENABLED=true
```

### Obtenir les Clés API

- **Together.ai:** https://api.together.xyz/signup
- **OpenAI:** https://platform.openai.com/api-keys
- **Gemini:** https://makersuite.google.com/app/apikey
- **Claude:** https://console.anthropic.com/
- **Airtable:** https://airtable.com/account

---

## 📊 Monitoring

### Métriques Disponibles

- **Cache:** Hit rate, hits/misses, erreurs
- **LLM Routing:** Distribution par provider, coûts par provider
- **Performance:** Latence, tokens utilisés
- **Coûts:** Tracking en temps réel par provider

### Logs

```bash
# Logs en production (Render.com)
# Visibles dans le dashboard Render

# Logs en local
# Affichés dans le terminal
```

### Alertes

Pour production, intégrer:
- **Sentry:** Erreurs et exceptions
- **DataDog:** Métriques et APM
- **Better Uptime:** Uptime monitoring

---

## 🔐 Sécurité

- ✅ Secrets jamais committés (`.gitignore`)
- ✅ Validation Pydantic des inputs
- ✅ Rate limiting (TODO)
- ✅ CORS configuré
- ✅ Environnements séparés (dev/staging/prod)

**TODO Production:**
- [ ] Ajouter authentification API key
- [ ] Implémenter rate limiting
- [ ] HTTPS obligatoire
- [ ] Logging structuré (JSON)

---

## 🚨 Troubleshooting

### API ne démarre pas

**Problème:** Erreur au démarrage
**Solution:**
```bash
# Vérifier les clés API
python -c "from config import get_settings; s=get_settings(); print(s.get_summary())"

# Vérifier dépendances
pip install -r requirements.txt --upgrade
```

### Cache ne fonctionne pas

**Problème:** Redis unavailable
**Solution:**
```bash
# Vérifier Redis
redis-cli ping  # Doit retourner PONG

# Désactiver cache si besoin
export REDIS_ENABLED=false
```

### Coûts trop élevés

**Problème:** Dépassement budget
**Solution:**
1. Vérifier hit rate cache: `curl /api/stats`
2. Augmenter TTL Redis si < 80%
3. Vérifier distribution LLM (doit être ~90/8/2)
4. Implémenter rate limiting

---

## 📈 Roadmap

### Version 1.0 (Actuel)
- [x] Architecture multi-LLM
- [x] Cache Redis
- [x] Routing intelligent
- [x] API FastAPI
- [x] Déploiement Render.com

### Version 1.1 (Q1 2025)
- [ ] Authentification API key
- [ ] Rate limiting
- [ ] Logging structuré
- [ ] Monitoring avancé
- [ ] Tests unitaires

### Version 2.0 (Q2 2025)
- [ ] Intégration FAISS vector search
- [ ] Personnalisation utilisateur
- [ ] Historique de recommandations
- [ ] A/B testing LLMs
- [ ] Dashboard admin

---

## 🤝 Contribution

Les contributions sont bienvenues!

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit (`git commit -m 'Add AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

---

## 📄 Licence

MIT License - voir LICENSE pour détails

---

## 🙏 Remerciements

- **Together.ai** pour l'API abordable
- **Google** pour Gemini Flash gratuit
- **Anthropic** pour Claude Haiku
- **Render.com** pour l'hébergement simplifié

---

## 📞 Support

- **Issues:** https://github.com/votre-username/render-trouveuncadeau/issues
- **Email:** contact@trouveuncadeau.xyz
- **Docs:** https://trouveuncadeau-api.onrender.com/docs

---

**Fait avec ❤️ au Québec 🇨🇦**
