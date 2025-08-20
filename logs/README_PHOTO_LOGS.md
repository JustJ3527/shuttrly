# Photo Logging System

Ce système de logs permet de tracer toutes les actions liées aux photos dans l'application Shuttrly.

## 📁 Fichiers

- **`photo_logs.json`** : Fichier principal contenant tous les logs de photos
- **`utils.py`** : Fonctions utilitaires pour la création des logs
- **`README_PHOTO_LOGS.md`** : Cette documentation

## 🔧 Fonctions disponibles

### Logs d'upload

```python
from logs.utils import log_photo_upload_json

log_photo_upload_json(
    user=request.user,
    photo=photo_object,
    request=request,
    upload_details={
        "batch_number": 1,
        "photo_number_in_batch": 1,
        "total_photos": 5,
        "file_original_name": "IMG_1234.JPG",
        "processing_errors": None
    },
    processing_status=photo.get_processing_status(),
    extra_info={"upload_method": "batch_upload"}
)
```

### Logs de suppression

```python
from logs.utils import log_photo_delete_json

log_photo_delete_json(
    user=request.user,
    photo=photo_object,
    request=request,
    extra_info={"photo_title": "My Photo"}
)
```

### Logs d'édition

```python
from logs.utils import log_photo_edit_json

log_photo_edit_json(
    user=request.user,
    photo=photo_object,
    request=request,
    changes={"title": ["Old Title", "New Title"]},
    extra_info={"edit_method": "form_edit"}
)
```

### Logs de visualisation

```python
from logs.utils import log_photo_view_json

log_photo_view_json(
    user=request.user,
    photo=photo_object,
    request=request,
    view_type="detail",  # detail, gallery, public_gallery
    extra_info={"referrer": "gallery_page"}
)
```

### Logs d'actions en lot

```python
from logs.utils import log_photo_bulk_action_json

log_photo_bulk_action_json(
    user=request.user,
    action="delete",  # delete, make_public, make_private, add_tags
    photo_ids=[330, 331, 332],
    request=request,
    results={"deleted_count": 3},
    extra_info={"bulk_action_type": "delete"}
)
```

## 📊 Structure des logs

### Log d'upload de photo

```json
{
  "log_id": "uuid-unique",
  "user": "nom_utilisateur",
  "user_id": 4,
  "action": "photo_upload",
  "timestamp": "2025-08-19T21:48:37.123456+00:00",
  "ip_address": "127.0.0.1",
  "user_agent": "User-Agent string",
  "location": {
    "city": "Paris",
    "region": "Île-de-France",
    "country": "France"
  },
  "photo_info": {
    "photo_id": 336,
    "filename": "IMG_1566.JPG",
    "file_size_mb": 8.55,
    "file_extension": "jpg",
    "is_raw": false,
    "dimensions": "6000x4000",
    "camera": "Canon Canon EOS R10"
  },
  "extra_info": {
    "upload_method": "batch_upload",
    "upload_details": {
      "batch_number": 1,
      "photo_number_in_batch": 1,
      "total_photos": 1,
      "file_original_name": "IMG_1566.JPG",
      "processing_errors": null
    },
    "processing_status": {
      "has_dimensions": true,
      "has_thumbnail": true,
      "has_camera_info": true,
      "has_exposure_info": true,
      "has_location": false,
      "has_date": true
    }
  },
  "restored": false
}
```

### Log de suppression de photo

```json
{
  "log_id": "uuid-unique",
  "user": "nom_utilisateur",
  "user_id": 4,
  "action": "photo_delete",
  "timestamp": "2025-08-19T22:00:00.123456+00:00",
  "ip_address": "127.0.0.1",
  "user_agent": "User-Agent string",
  "location": {
    "city": null,
    "region": null,
    "country": null
  },
  "photo_info": {
    "photo_id": 335,
    "filename": "IMG_1569.CR3",
    "file_size_mb": 36.03,
    "file_extension": "cr3",
    "is_raw": true,
    "dimensions": "6000x4000",
    "camera": "Canon Canon EOS R10"
  },
  "extra_info": {
    "photo_title": "Untitled",
    "delete_method": "single_delete"
  },
  "restored": false
}
```

### Log d'action en lot

```json
{
  "log_id": "uuid-unique",
  "user": "nom_utilisateur",
  "user_id": 4,
  "action": "bulk_delete",
  "timestamp": "2025-08-19T22:15:00.123456+00:00",
  "ip_address": "127.0.0.1",
  "user_agent": "User-Agent string",
  "location": {
    "city": null,
    "region": null,
    "country": null
  },
  "photo_info": null,
  "extra_info": {
    "bulk_action_type": "delete",
    "photo_titles": ["Photo 1", "Photo 2", "Photo 3"],
    "photo_ids": [330, 331, 332],
    "photo_count": 3,
    "results": {
      "deleted_count": 3
    }
  },
  "restored": false
}
```

## 🚀 Actions loggées automatiquement

### Upload de photos

- ✅ **Upload simple** : Une photo
- ✅ **Upload en lot** : Plusieurs photos
- ✅ **Détails du traitement** : Statut EXIF, dimensions, thumbnail
- ✅ **Gestion des erreurs** : Erreurs de traitement enregistrées

### Suppression de photos

- ✅ **Suppression simple** : Une photo
- ✅ **Suppression en lot** : Plusieurs photos
- ✅ **Métadonnées** : Titre, ID, informations de la photo

### Actions en lot

- ✅ **Suppression en lot** : `bulk_delete`
- ✅ **Rendre public** : `bulk_make_public`
- ✅ **Rendre privé** : `bulk_make_private`
- ✅ **Ajouter des tags** : `bulk_add_tags`

### Informations collectées

- **Utilisateur** : Nom et ID
- **Action** : Type d'action effectuée
- **Timestamp** : Date et heure précise
- **IP et User-Agent** : Informations de connexion
- **Localisation** : Ville, région, pays (si disponible)
- **Photo** : ID, nom de fichier, taille, format, dimensions, appareil
- **Contexte** : Détails spécifiques à l'action

## 🔍 Utilisation

### Dans les vues Django

```python
from logs.utils import log_photo_upload_json

def photo_upload(request):
    # ... code d'upload ...

    # Log de l'upload
    log_photo_upload_json(
        user=request.user,
        photo=photo,
        request=request,
        upload_details=upload_details,
        processing_status=photo.get_processing_status()
    )
```

### Gestion des erreurs

```python
try:
    log_photo_upload_json(user=user, photo=photo, request=request)
    print(f"Photo upload logged for {photo.filename}")
except Exception as log_error:
    print(f"Warning: Failed to log photo upload: {log_error}")
    # Continue sans échouer l'upload
```

## 📈 Avantages

1. **Traçabilité complète** : Toutes les actions sur les photos sont enregistrées
2. **Audit de sécurité** : IP, User-Agent, localisation
3. **Débogage** : Statut de traitement, erreurs, métadonnées
4. **Analytics** : Statistiques d'usage, tendances
5. **Conformité** : Historique des modifications et suppressions
6. **Performance** : Logs asynchrones, pas d'impact sur l'upload

## 🛡️ Sécurité

- **IP anonymisée** : Pas de stockage d'IP complète
- **Données sensibles** : Pas de stockage de contenu des photos
- **Accès restreint** : Logs stockés localement
- **Rotation** : Possibilité d'implémenter une rotation des logs

## 🔧 Configuration

Le système utilise automatiquement :

- **Django settings** : `BASE_DIR`, `MEDIA_ROOT`
- **Détection IP** : Support des proxies et load balancers
- **Géolocalisation** : Service ipinfo.io (optionnel)
- **Encodage** : UTF-8 pour les caractères internationaux
