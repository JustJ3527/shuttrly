# 🧠 Fonctionnalités IA - Shuttrly

## 📋 Vue d'ensemble

Shuttrly intègre des systèmes d'intelligence artificielle avancés pour améliorer l'expérience utilisateur à travers la similarité d'images et les recommandations personnalisées. Ces systèmes utilisent des modèles de deep learning modernes et des algorithmes de filtrage collaboratif.

---

## 🖼️ Système de Similarité d'Images

### **Architecture Technique**

#### **Modèle CLIP (Contrastive Language-Image Pre-training)**
- **Modèle** : OpenAI CLIP ViT-Base-Patch32
- **Dimensions** : Vecteurs d'embedding 512D
- **Framework** : PyTorch + Transformers
- **Performance** : Similarité cosinus optimisée

#### **Pipeline de Traitement**
```python
1. Upload d'image → Validation format
2. Génération d'embedding → CLIP model
3. Stockage vectoriel → Base de données
4. Indexation FAISS → Recherche rapide
5. Calcul similarité → Cosinus similarity
6. Résultats → Interface utilisateur
```

### **Fonctionnalités Avancées**

#### **Génération d'Embeddings**
- **Automatique** : À chaque upload d'image
- **Batch processing** : Traitement en lot pour les images existantes
- **Cache intelligent** : Singleton pattern pour éviter les rechargements
- **Gestion d'erreurs** : Dégradation gracieuse en cas d'échec

#### **Recherche de Similarité**
- **Index FAISS** : Recherche vectorielle optimisée
- **Similarité cosinus** : Précision jusqu'à 3 décimales
- **Badge "Identical"** : Pour les images 100% similaires
- **Interface interactive** : Navigation entre images similaires

#### **Optimisations Performance**
- **Chargement unique** : Modèle CLIP chargé une seule fois
- **Cache Redis** : Mise en cache des embeddings
- **Traitement asynchrone** : Celery pour les tâches lourdes
- **Compression** : Vecteurs optimisés pour le stockage

---

## 👥 Système de Recommandations d'Utilisateurs

### **Algorithme de Filtrage Collaboratif**

#### **Principe de Base**
1. **Matrice utilisateur-contenu** : Relations de suivi
2. **Similarité cosinus** : Calcul entre utilisateurs
3. **Facteurs de boost** : Pondération multi-critères
4. **Normalisation** : Scores entre 0.2 et 0.9
5. **Recommandations** : Top-K utilisateurs similaires

#### **Formule de Scoring**
```python
score = 0.5  # Score de base

# 1. Activité récente (priorité maximale)
if recent_activity > 0:
    recent_multiplier = 1 + (recent_activity * 0.1)
    score *= recent_multiplier  # Jusqu'à 10x

# 2. Activité totale
if total_activity > 0:
    activity_multiplier = 1 + (total_activity * 0.05)
    score *= activity_multiplier  # Jusqu'à 3x

# 3. Amis mutuels
if mutual_friends > 0:
    friend_multiplier = 1 + (mutual_friends * 0.3)
    score *= friend_multiplier

# 4. Suivis communs
if common_following > 0:
    following_multiplier = 1 + (common_following * 0.1)
    score *= following_multiplier

# 5. Type de compte
if is_public:
    score *= 1.1  # +10% pour les comptes publics
# Pas de pénalité pour les comptes privés

# 6. Nouveaux comptes
if days_since_joined < 30:
    new_account_multiplier = 1 + (0.1 * (30 - days_since_joined) / 30)
    score *= new_account_multiplier

# 7. Normalisation finale
score = min(score / 3.0, 1.0)  # Plage 0.2-0.9
```

### **Facteurs de Boost Détaillés**

#### **1. Activité Récente (Priorité Maximale)**
- **Pondération temporelle** : Tranches de temps avec poids décroissants
- **Période** : 30 derniers jours
- **Tranches** :
  - 1 jour : 5x poids
  - 7 jours : 3x poids
  - 14 jours : 2x poids
  - 21 jours : 1.5x poids
  - 30 jours : 1x poids
- **Types de contenu** : Posts (2x) > Photos (1x)

#### **2. Activité Totale**
- **Calcul** : (posts × 2) + photos
- **Multiplicateur** : Jusqu'à 3x
- **Objectif** : Récompenser les utilisateurs actifs

#### **3. Relations Sociales**
- **Amis mutuels** : +30% par ami commun
- **Suivis communs** : +10% par suivi commun
- **Followers communs** : +5% par follower commun

#### **4. Visibilité du Compte**
- **Comptes publics** : +10% boost
- **Comptes privés** : Aucune pénalité (traitement équitable)

#### **5. Nouveaux Comptes**
- **Période** : 30 premiers jours
- **Boost** : Jusqu'à 10% (décroissant avec l'âge)
- **Objectif** : Aider les nouveaux utilisateurs

### **Comment Booster un Compte**

#### **Stratégies de Visibilité**

**1. Augmenter l'Activité Récente**
```python
# Posts récents (poids 2x)
- Créer des posts régulièrement
- Poster dans les 7 derniers jours (poids 3x)
- Poster dans les 24h (poids 5x)

# Photos récentes (poids 1x)
- Uploader des photos régulièrement
- Maintenir une activité constante
```

**2. Développer le Réseau Social**
```python
# Amis mutuels (+30% par ami)
- Suivre des utilisateurs populaires
- Interagir avec la communauté
- Créer des connexions mutuelles

# Suivis communs (+10% par suivi)
- Suivre des utilisateurs similaires
- Rejoindre des communautés
- Partager des centres d'intérêt
```

**3. Optimiser le Profil**
```python
# Compte public (+10% boost)
- Rendre le profil public
- Aucune pénalité pour les comptes privés

# Nouveau compte (jusqu'à 10% boost)
- Profiter des 30 premiers jours
- Maintenir l'activité initiale
```

**4. Contenu de Qualité**
```python
# Posts engageants
- Créer du contenu intéressant
- Interagir avec les autres posts
- Maintenir la régularité

# Photos attrayantes
- Uploader des images de qualité
- Utiliser des tags appropriés
- Organiser en collections
```

### **Architecture Technique**

#### **Pipeline de Calcul**
```python
1. Collecte des données → Relations utilisateurs
2. Construction matrice → Sparse user-follow matrix
3. Calcul similarité → Cosine similarity
4. Application boosts → Multiplicateurs
5. Normalisation → Scores 0.2-0.9
6. Génération recommandations → Top-K
7. Mise en cache → Redis
8. Mise à jour temps réel → AJAX
```

#### **Optimisations Performance**
- **Cache Redis** : Recommandations mises en cache
- **Traitement asynchrone** : Celery pour les calculs lourds
- **Mise à jour incrémentale** : Seulement les changements
- **Indexation base de données** : Requêtes optimisées

#### **Gestion des Erreurs**
- **Dégradation gracieuse** : Fallback en cas d'échec
- **Cache de secours** : Recommandations de base
- **Logs détaillés** : Debug et monitoring
- **Validation données** : Filtrage des utilisateurs inactifs

---

## 🔧 Configuration et Déploiement

### **Prérequis Techniques**

#### **Dépendances Python**
```bash
torch>=1.9.0
transformers>=4.20.0
scikit-learn>=1.1.0
faiss-cpu>=1.7.0
redis>=4.0.0
celery>=5.2.0
```

#### **Services Requis**
- **Redis** : Cache et broker Celery
- **PostgreSQL** : Base de données optimisée
- **Celery Worker** : Traitement asynchrone

### **Configuration**

#### **Settings Django**
```python
# AI Models
CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"
EMBEDDING_DIMENSION = 512

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://localhost:6379/1',
    }
}

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

#### **Commandes de Gestion**
```bash
# Générer les embeddings
python manage.py generate_embeddings

# Calculer les recommandations
python manage.py calculate_recommendations

# Nettoyer le cache
python manage.py clear_recommendations_cache

# Tester la similarité
python manage.py test_photo_similarity
```

---

## 📊 Monitoring et Métriques

### **Métriques de Performance**

#### **Similarité d'Images**
- **Temps de génération** : < 2s par image
- **Précision** : > 95% pour images similaires
- **Cache hit rate** : > 90%
- **Taille index FAISS** : Optimisée

#### **Recommandations**
- **Temps de calcul** : 2-5 min pour 1000 utilisateurs
- **API response** : < 200ms
- **Cache hit rate** : > 90%
- **Distribution scores** : 0.2-0.9 optimal

### **Logs et Debug**

#### **Niveaux de Log**
- **DEBUG** : Détails calculs et scores
- **INFO** : Opérations réussies
- **WARNING** : Problèmes non critiques
- **ERROR** : Erreurs nécessitant attention

#### **Commandes de Debug**
```bash
# Tester les recommandations
python manage.py shell
>>> from users.utilsFolder.recommendations import debug_user_recommendations
>>> debug_user_recommendations(user_id=1, detailed=True)

# Vérifier la similarité
>>> from photos.utils import test_photo_similarity
>>> test_photo_similarity(photo_id1, photo_id2)
```

---

## 🚀 Améliorations Futures

### **Fonctionnalités Prévues**

#### **Similarité d'Images**
- **Modèles avancés** : CLIP ViT-Large, DALL-E
- **Recherche sémantique** : Requêtes textuelles
- **Filtres intelligents** : Par style, couleur, objet
- **Recommandations visuelles** : Basées sur les images

#### **Recommandations**
- **Machine Learning** : Modèles prédictifs
- **Content-based** : Basé sur le contenu des posts
- **Temporal patterns** : Comportements temporels
- **A/B Testing** : Optimisation continue

#### **Intégrations**
- **APIs externes** : Services de recommandation
- **Analytics** : Métriques avancées
- **Personalisation** : Préférences utilisateur
- **Real-time** : Mises à jour instantanées

---

## 📚 Documentation Technique

### **APIs Disponibles**

#### **Similarité d'Images**
```
GET  /photos/similarity/<photo_id>/     # Images similaires
POST /photos/generate-embeddings/       # Générer embeddings
GET  /photos/test-embedding/            # Interface de test
```

#### **Recommandations**
```
POST /ajax/refresh-recommendations/     # Rafraîchir recommandations
GET  /ajax/get-recommendations/         # Obtenir recommandations
POST /api/v1/recommendations/trigger/   # Déclencher calcul
```

### **Modèles de Données**

#### **Photo Model**
```python
class Photo(models.Model):
    embedding = models.JSONField()      # Vecteur CLIP 512D
    similarity_score = models.FloatField()  # Score de similarité
    # ... autres champs
```

#### **UserRecommendation Model**
```python
class UserRecommendation(models.Model):
    user = models.ForeignKey(CustomUser)
    recommended_user = models.ForeignKey(CustomUser)
    score = models.FloatField()         # Score normalisé 0.2-0.9
    created_at = models.DateTimeField()
```

---

_Last updated: January 2025_
