# Photos API Documentation

Cette API permet de gérer les photos et collections de photos pour l'application Shuttrly iOS.

## Endpoints

### Photos

#### Liste des photos
- **URL:** `GET /photos/api/photos/`
- **Description:** Récupère la liste paginée des photos de l'utilisateur connecté
- **Paramètres de requête:**
  - `page`: Numéro de page (défaut: 1)
  - `page_size`: Taille de la page (défaut: 20, max: 100)
  - `sort_by`: Tri par date ou titre
- **Réponse:** Liste paginée des photos avec métadonnées

#### Détail d'une photo
- **URL:** `GET /photos/api/photos/{id}/`
- **Description:** Récupère les détails complets d'une photo
- **Réponse:** Toutes les informations de la photo incluant EXIF et couleurs dominantes

#### Upload de photo
- **URL:** `POST /photos/api/photos/upload/`
- **Description:** Télécharge une nouvelle photo
- **Corps de la requête:** Données de la photo (titre, description, tags, fichier)
- **Réponse:** Photo créée avec ID

#### Suppression de photo
- **URL:** `DELETE /photos/api/photos/{id}/delete/`
- **Description:** Supprime une photo
- **Réponse:** 204 No Content

### Galerie

#### Galerie principale
- **URL:** `GET /photos/api/gallery/`
- **Description:** Récupère la galerie de l'utilisateur avec filtres
- **Paramètres de requête:**
  - `tags`: Filtrage par tags (séparés par des virgules)
  - `camera_make`: Filtrage par marque d'appareil
  - `camera_model`: Filtrage par modèle d'appareil
  - `date_from`: Date de début (YYYY-MM-DD)
  - `date_to`: Date de fin (YYYY-MM-DD)
  - `sort_by`: Tri (date_desc, date_asc, alphabetical_asc, alphabetical_desc)

#### Galerie utilisateur
- **URL:** `GET /photos/api/gallery/user/{user_id}/`
- **Description:** Récupère la galerie publique d'un utilisateur spécifique

#### Galerie publique
- **URL:** `GET /photos/api/gallery/public/`
- **Description:** Récupère les photos publiques de tous les utilisateurs

### Collections

#### Liste des collections
- **URL:** `GET /photos/api/collections/`
- **Description:** Récupère les collections de l'utilisateur connecté

#### Détail d'une collection
- **URL:** `GET /photos/api/collections/{id}/`
- **Description:** Récupère les détails d'une collection

#### Photos d'une collection
- **URL:** `GET /photos/api/collections/{id}/photos/`
- **Description:** Récupère les photos d'une collection spécifique

### Recherche et filtres

#### Recherche de photos
- **URL:** `GET /photos/api/photos/search/`
- **Description:** Recherche dans les photos par mot-clé
- **Paramètres de requête:**
  - `query`: Terme de recherche
  - `tags`: Filtrage par tags

#### Liste des tags
- **URL:** `GET /photos/api/photos/tags/`
- **Description:** Récupère tous les tags utilisés par l'utilisateur

#### Photos par tag
- **URL:** `GET /photos/api/photos/tags/{tag_name}/`
- **Description:** Récupère les photos ayant un tag spécifique

### Statistiques

#### Statistiques photos
- **URL:** `GET /photos/api/stats/`
- **Description:** Récupère les statistiques des photos de l'utilisateur
- **Réponse:** Nombre total, tailles, appareils utilisés, etc.

#### Statistiques utilisateur
- **URL:** `GET /photos/api/stats/user/{user_id}/`
- **Description:** Récupère les statistiques publiques d'un utilisateur

## Authentification

L'API utilise l'authentification Django REST Framework. La plupart des endpoints nécessitent que l'utilisateur soit connecté.

**Exceptions:**
- Galerie publique
- Statistiques publiques des utilisateurs

## Pagination

Tous les endpoints de liste utilisent la pagination standard avec les paramètres suivants :
- `count`: Nombre total d'éléments
- `next`: URL de la page suivante (null si dernière page)
- `previous`: URL de la page précédente (null si première page)
- `results`: Liste des éléments de la page actuelle

## Format des réponses

### Photo
```json
{
  "id": 1,
  "title": "Titre de la photo",
  "description": "Description de la photo",
  "tags": "tag1, tag2, tag3",
  "thumbnail_url": "http://example.com/media/thumb.jpg",
  "original_url": "http://example.com/media/original.jpg",
  "file_size": 5242880,
  "file_extension": "jpg",
  "is_raw": false,
  "width": 4000,
  "height": 3000,
  "dominant_colors": ["#FF6B35", "#F7931E", "#FFD23F"],
  "camera_make": "Canon",
  "camera_model": "EOS R5",
  "lens_make": "Canon",
  "lens_model": "RF 24-70mm f/2.8L",
  "focal_length": 50.0,
  "focal_length_35mm": 50,
  "shutter_speed": "1/125",
  "aperture": 2.8,
  "iso": 100,
  "exposure_bias": 0.0,
  "exposure_mode": "Aperture Priority",
  "metering_mode": "Evaluative",
  "created_at": "2025-08-26T10:00:00Z",
  "updated_at": "2025-08-26T10:00:00Z"
}
```

### Collection
```json
{
  "id": 1,
  "name": "Nom de la collection",
  "description": "Description de la collection",
  "collection_type": "personal",
  "is_private": false,
  "user": {
    "id": 1,
    "username": "username",
    "first_name": "Prénom",
    "last_name": "Nom",
    "email": "email@example.com"
  },
  "photo_count": 5,
  "created_at": "2025-08-26T10:00:00Z",
  "updated_at": "2025-08-26T10:00:00Z"
}
```

## Codes d'erreur

- `200 OK`: Requête réussie
- `201 Created`: Ressource créée avec succès
- `204 No Content`: Suppression réussie
- `400 Bad Request`: Données de requête invalides
- `401 Unauthorized`: Authentification requise
- `403 Forbidden`: Accès refusé
- `404 Not Found`: Ressource non trouvée
- `500 Internal Server Error`: Erreur serveur

## Utilisation avec l'app iOS

L'API est conçue pour fonctionner avec l'application iOS Shuttrly. Les endpoints retournent les données dans un format optimisé pour l'affichage mobile, incluant :

- URLs complètes pour les images
- Métadonnées EXIF pour l'affichage technique
- Couleurs dominantes pour les arrière-plans dynamiques
- Pagination pour le chargement progressif
- Filtrage et recherche en temps réel

## Tests

Pour exécuter les tests de l'API :

```bash
python manage.py test photos.api.tests
```

## Développement

L'API est construite avec Django REST Framework et suit les bonnes pratiques :

- Sérialiseurs pour la validation des données
- Permissions personnalisées pour la sécurité
- Pagination standardisée
- Gestion d'erreurs cohérente
- Tests complets pour tous les endpoints
