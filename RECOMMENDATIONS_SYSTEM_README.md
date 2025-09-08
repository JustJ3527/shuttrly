# Système de Recommandations Intelligent

## Vue d'ensemble

Le système de recommandations a été complètement refondu pour fonctionner en arrière-plan avec Celery et Redis, générant un top 30 de recommandations et affichant intelligemment 4 recommandations avec rotation.

## Fonctionnalités

### 🔄 Calcul en Arrière-plan
- **Top 30** : Génère 30 recommandations par utilisateur stockées en base
- **Tâches périodiques** : Mise à jour automatique toutes les 30 minutes
- **Triggers** : Recalcul automatique après follow/unfollow/request

### 🎯 Rotation Intelligente
- **4 recommandations** affichées à la fois
- **Rotation aléatoire** : Chaque refresh montre des recommandations différentes
- **Évitement des doublons** : Système de tracking pour éviter de montrer les mêmes comptes
- **Priorité intelligente** : Score + récence + fréquence d'affichage

### 📊 Algorithme de Scoring
- **Score de base** : 0.2 pour tous les utilisateurs
- **Activité récente** : Boost jusqu'à 10x pour l'activité des 30 derniers jours
- **Activité totale** : Boost jusqu'à 3x pour photos + posts
- **Amis mutuels** : +30% par ami mutuel
- **Comptes publics** : +10% de boost
- **Nouveaux comptes** : +10% pour les comptes de moins de 30 jours

## Architecture

### Modèles
```python
class UserRecommendation(models.Model):
    user = models.ForeignKey(CustomUser, ...)
    recommended_user = models.ForeignKey(CustomUser, ...)
    score = models.FloatField(default=0.0)
    position = models.PositiveIntegerField(default=0)  # 1-30
    last_shown = models.DateTimeField(null=True, blank=True)
    show_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Tâches Celery
- `build_user_recommendations_for_user()` : Génère le top 30
- `get_user_recommendations_for_display()` : Récupère 4 avec rotation
- `periodic_recommendations_update()` : Mise à jour périodique
- `trigger_recommendation_update_after_relationship_change()` : Trigger après follow/unfollow
- `cleanup_old_recommendations()` : Nettoyage des anciennes recommandations

## Utilisation

### 1. Démarrer Celery Beat
```bash
python start_celery_beat.py
```

### 2. Tester le système
```bash
python test_recommendations_system.py
```

### 3. API Endpoints
- `GET /ajax/get-recommendations/` : Récupérer les recommandations actuelles
- `POST /ajax/refresh-recommendations/` : Rafraîchir avec rotation

## Configuration

### Tâches Périodiques
```python
CELERY_BEAT_SCHEDULE = {
    'periodic-recommendations-update': {
        'task': 'users.tasks.periodic_recommendations_update',
        'schedule': crontab(minute='*/30'),  # Toutes les 30 minutes
    },
    'cleanup-old-recommendations': {
        'task': 'users.tasks.cleanup_old_recommendations',
        'schedule': crontab(minute=0),  # Toutes les heures
    },
}
```

### Paramètres de Rotation
- **Seuil minimum** : 0.05 (très permissif pour nouveaux utilisateurs)
- **Score de base** : 0.2
- **Pénalité récence** : Max 0.5 (24h)
- **Pénalité fréquence** : Max 0.3 (10 affichages)

## Avantages

### 🚀 Performance
- **Calcul asynchrone** : Pas de blocage de l'interface
- **Cache intelligent** : Top 30 pré-calculé
- **Rotation rapide** : Affichage instantané

### 🎯 Expérience Utilisateur
- **Variété** : Toujours de nouvelles recommandations
- **Pertinence** : Algorithme intelligent basé sur l'activité
- **Réactivité** : Mise à jour automatique après actions

### 🔧 Maintenabilité
- **Modulaire** : Séparation claire des responsabilités
- **Configurable** : Paramètres facilement ajustables
- **Testable** : Scripts de test inclus

## Monitoring

### Logs
- Génération des recommandations
- Rotation et affichage
- Erreurs et performances

### Métriques
- Nombre de recommandations générées
- Taux de rotation
- Performance des tâches

## Déploiement

1. **Migrer la base de données** :
   ```bash
   python manage.py migrate
   ```

2. **Démarrer Celery Worker** :
   ```bash
   celery -A shuttrly worker --loglevel=info
   ```

3. **Démarrer Celery Beat** :
   ```bash
   python start_celery_beat.py
   ```

4. **Tester le système** :
   ```bash
   python test_recommendations_system.py
   ```

## Dépannage

### Problèmes Courants
- **Pas de recommandations** : Vérifier que Celery fonctionne
- **Même recommandations** : Vérifier la clé de rotation
- **Performance lente** : Vérifier Redis et la base de données

### Commandes Utiles
```bash
# Vérifier les tâches Celery
celery -A shuttrly inspect active

# Nettoyer les anciennes recommandations
python manage.py shell -c "from users.tasks import cleanup_old_recommendations; cleanup_old_recommendations()"

# Forcer la mise à jour d'un utilisateur
python manage.py shell -c "from users.tasks import build_user_recommendations_for_user; build_user_recommendations_for_user(USER_ID)"
```
