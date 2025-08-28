# Trusted Devices API - Documentation

## Vue d'ensemble

Cette documentation explique comment l'API gère les trusted devices pour éviter la création de doublons et améliorer la sécurité.

## Problème résolu

**Avant** : L'API créait un nouveau trusted device à chaque connexion, même si l'appareil était déjà enregistré, ce qui causait des doublons.

**Après** : L'API vérifie d'abord si l'appareil existe déjà avant d'en créer un nouveau.

## Logique de vérification

### 1. Vérification primaire (IP + User-Agent)

L'API vérifie d'abord si un appareil avec la même IP et le même User-Agent est déjà enregistré :

```python
existing_device = TrustedDevice.objects.filter(
    user=user,
    ip_address=ip,
    user_agent=user_agent[:255]
).first()
```

**Avantages** :
- Évite les doublons pour le même appareil
- Fonctionne même si le cookie a été supprimé
- Plus fiable que la vérification par cookie

### 2. Gestion des appareils existants

Si l'appareil existe déjà :

```python
if existing_device:
    # Mise à jour des informations
    existing_device.last_used_at = timezone.now()
    if location:
        existing_device.location = location
    existing_device.save()
    
    # Vérification du cookie
    if not trusted_tokens:
        # Création d'un nouveau cookie si nécessaire
        # (cas où l'utilisateur a supprimé ses cookies)
```

### 3. Vérification secondaire (par cookie)

Si aucun appareil n'est trouvé par IP+User-Agent, l'API vérifie les cookies existants :

```python
trusted_tokens = [
    value for key, value in request.COOKIES.items()
    if key.startswith(f"trusted_device_{user.pk}")
]

for token in trusted_tokens:
    hashed_token = hash_token(token)
    device = TrustedDevice.objects.filter(
        user=user, device_token=hashed_token
    ).first()
    if device:
        break
```

### 4. Création d'un nouvel appareil

Un nouvel appareil n'est créé que si :
- Aucun appareil existant n'est trouvé par IP+User-Agent
- Aucun appareil existant n'est trouvé par cookie

## Flux de connexion

```
1. Utilisateur se connecte avec "remember_device = true"
2. Vérification par IP + User-Agent
   ├─ Si trouvé : Mise à jour de l'appareil existant
   └─ Si non trouvé : Vérification par cookie
       ├─ Si trouvé : Mise à jour de l'appareil existant
       └─ Si non trouvé : Création d'un nouvel appareil
3. Envoi des informations du trusted device dans la réponse
4. Client stocke le cookie localement
```

## Réponse API

### Avec trusted device créé/mis à jour

```json
{
    "success": true,
    "message": "Welcome User!",
    "user": {...},
    "tokens": {...},
    "requires_2fa": false,
    "login_complete": true,
    "trusted_device": {
        "token": "1-abc123...",
        "cookie_name": "trusted_device_1",
        "max_age": 2592000,
        "expires_in_days": 30
    }
}
```

### Sans trusted device

```json
{
    "success": true,
    "message": "Welcome User!",
    "user": {...},
    "tokens": {...},
    "requires_2fa": false,
    "login_complete": true
}
```

## Gestion côté client

Le client Swift doit :

1. **Vérifier la présence de `trusted_device`** dans la réponse
2. **Stocker le cookie** avec les informations reçues
3. **Envoyer le cookie** lors des prochaines requêtes

### Exemple de gestion côté client

```swift
if let trustedDevice = response.trusted_device {
    // Stocker le cookie localement
    let cookie = HTTPCookie(properties: [
        .name: trustedDevice.cookieName,
        .value: trustedDevice.token,
        .expires: Date().addingTimeInterval(TimeInterval(trustedDevice.maxAge)),
        .path: "/",
        .secure: true,
        .httpOnly: true
    ])
    
    // Ajouter le cookie au stockage
    HTTPCookieStorage.shared.setCookie(cookie!)
}
```

## Sécurité

- **Cookies sécurisés** : `secure=true`, `httponly=true`
- **Expiration automatique** : 30 jours par défaut
- **Tokens uniques** : Combinaison user_id + UUID
- **Hachage des tokens** : Stockage sécurisé en base

## Tests

Utilisez le script `test_trusted_devices.py` pour tester la logique :

```bash
python test_trusted_devices.py
```

Ce script simule :
- Première connexion d'un appareil
- Reconnexion du même appareil
- Vérification de l'absence de doublons

## Maintenance

### Nettoyage des appareils expirés

Les appareils expirés peuvent être nettoyés avec :

```python
from django.utils import timezone
from users.models import TrustedDevice

# Supprimer les appareils expirés
TrustedDevice.objects.filter(expires_at__lt=timezone.now()).delete()
```

### Statistiques

```python
# Nombre total d'appareils par utilisateur
user.trusted_devices.count()

# Appareils actifs (non expirés)
user.trusted_devices.filter(expires_at__gt=timezone.now()).count()
```
