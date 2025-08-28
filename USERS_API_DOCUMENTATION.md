# API Documentation - Users Module

## Vue d'ensemble

Cette documentation couvre l'API complète du module utilisateurs de Shuttrly, incluant l'inscription, la connexion, la gestion des profils et la sécurité.

## Base URL

```
http://your-domain.com/api/v1/
```

## Authentification

L'API utilise JWT (JSON Web Tokens) pour l'authentification. Les tokens sont retournés lors de la connexion et doivent être inclus dans l'en-tête `Authorization` des requêtes protégées.

```
Authorization: Bearer <access_token>
```

## Endpoints

### 🔐 Inscription

#### 1. Vérification Email (Étape 1)

**POST** `/users/register/step1/`

Vérifie l'email et envoie un code de vérification.

**Request Body:**
```json
{
    "email": "user@example.com"
}
```

**Response (200):**
```json
{
    "success": true,
    "message": "Verification code sent to your mail: user@example.com",
    "email": "user@example.com",
    "temp_user_id": 123
}
```

**Response (400):**
```json
{
    "success": false,
    "message": "An account with this email already exists."
}
```

#### 2. Vérification du Code (Étape 2)

**POST** `/users/register/step2/`

Vérifie le code de vérification envoyé par email.

**Request Body:**
```json
{
    "email": "user@example.com",
    "verification_code": "123456"
}
```

**Response (200):**
```json
{
    "success": true,
    "message": "Email verification successful",
    "email_verified": true
}
```

**Response (400):**
```json
{
    "success": false,
    "message": "Verification code has expired"
}
```

#### 3. Informations Personnelles (Étape 3)

**POST** `/users/register/step3/`

Enregistre les informations personnelles de l'utilisateur.

**Request Body:**
```json
{
    "first_name": "John",
    "last_name": "Doe",
    "date_of_birth": "1990-01-01"
}
```

**Validation:**
- Âge minimum : 16 ans
- Champs obligatoires : `first_name`, `last_name`, `date_of_birth`

#### 4. Nom d'utilisateur (Étape 4)

**POST** `/users/register/step4/`

Vérifie et enregistre le nom d'utilisateur.

**Request Body:**
```json
{
    "username": "johndoe"
}
```

**Validation:**
- Longueur : 3-30 caractères
- Caractères autorisés : lettres, chiffres, tirets, underscores
- Doit être unique (insensible à la casse)

#### 5. Mot de passe (Étape 5)

**POST** `/users/register/step5/`

Enregistre le mot de passe de l'utilisateur.

**Request Body:**
```json
{
    "password1": "SecurePassword123!",
    "password2": "SecurePassword123!"
}
```

**Validation:**
- Les deux mots de passe doivent correspondre
- Respect des règles de complexité (majuscules, minuscules, chiffres, caractères spéciaux)
- Longueur minimum : 8 caractères

#### 6. Inscription Complète

**POST** `/users/register/complete/`

Inscription complète en une seule requête (toutes les étapes).

**Request Body:**
```json
{
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "date_of_birth": "1990-01-01",
    "username": "johndoe",
    "password1": "SecurePassword123!",
    "password2": "SecurePassword123!"
}
```

**Response (201):**
```json
{
    "success": true,
    "message": "Account created successfully!",
    "user": {
        "id": 1,
        "username": "johndoe",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01",
        "is_email_verified": true,
        "date_joined": "2025-08-28T17:30:00Z"
    },
    "tokens": {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
}
```

### 🔑 Connexion

#### Connexion avec Support 2FA

**POST** `/users/login/`

Système de connexion en plusieurs étapes avec support 2FA et trusted devices.

**Request Body (Étape 1 - Identifiants):**
```json
{
    "step": "credentials",
    "identifier": "user@example.com", // ou username
    "password": "SecurePassword123!",
    "remember_device": true
}
```

**Response (200) - 2FA requis:**
```json
{
    "success": true,
    "message": "2FA required. Please choose your method.",
    "next_step": "choose_2fa",
    "requires_2fa": true,
    "available_methods": ["email", "totp"]
}
```

**Response (200) - Connexion directe (trusted device):**
```json
{
    "success": true,
    "message": "Welcome John!",
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

#### Choix de la Méthode 2FA

**POST** `/users/login/`

**Request Body:**
```json
{
    "step": "choose_2fa",
    "twofa_method": "email" // ou "totp"
}
```

#### Vérification Email 2FA

**POST** `/users/login/`

**Request Body:**
```json
{
    "step": "email_2fa",
    "twofa_code": "123456"
}
```

**Request Body (renvoi de code):**
```json
{
    "step": "email_2fa",
    "resend_code": true
}
```

#### Vérification TOTP 2FA

**POST** `/users/login/`

**Request Body:**
```json
{
    "step": "totp_2fa",
    "twofa_code": "123456"
}
```

### 👤 Profil Utilisateur

#### Profil Basique

**GET** `/users/profile/`

Récupère les informations de base du profil utilisateur.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
    "id": 1,
    "username": "johndoe",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "date_of_birth": "1990-01-01",
    "bio": "Photographe passionné",
    "is_private": false,
    "profile_picture": "/media/profiles/default.jpg",
    "is_email_verified": true,
    "date_joined": "2025-08-28T17:30:00Z",
    "is_active": true
}
```

#### Profil Complet

**GET** `/users/profile/full/`

Récupère toutes les informations du profil utilisateur, y compris les statistiques et les appareils de confiance.

**Response (200):**
```json
{
    "user_id": 1,
    "basic_info": {
        "username": "johndoe",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "full_name": "John Doe",
        "date_of_birth": "1990-01-01",
        "age": 35,
        "bio": "Photographe passionné",
        "is_private": false
    },
    "profile_picture": {
        "url": "http://domain.com/media/profiles/photo.jpg",
        "filename": "profiles/photo.jpg",
        "is_default": false
    },
    "account_status": {
        "is_active": true,
        "is_staff": false,
        "is_superuser": false,
        "is_online": true,
        "is_anonymized": false
    },
    "verification_status": {
        "is_email_verified": true,
        "email_verification_code": null,
        "verification_code_sent_at": null,
        "can_send_verification_code": true
    },
    "two_factor_auth": {
        "email_2fa_enabled": false,
        "email_2fa_code": null,
        "email_2fa_sent_at": null,
        "totp_enabled": false,
        "twofa_totp_secret": null
    },
    "timestamps": {
        "date_joined": "2025-08-28T17:30:00Z",
        "last_login_date": "2025-08-28T18:00:00Z",
        "last_login_ip": "192.168.1.100",
        "ip_address": "192.168.1.100"
    },
    "permissions": {
        "user_permissions": [],
        "groups": [],
        "is_staff": false,
        "is_superuser": false
    },
    "photo_statistics": {
        "total_photos": 25,
        "total_size_bytes": 52428800,
        "total_size_mb": 50.0,
        "raw_photos": 5,
        "jpeg_photos": 20,
        "recent_photos": 3
    },
    "collection_statistics": {
        "total_collections": 3,
        "private_collections": 1,
        "public_collections": 2,
        "collections": [
            {
                "id": 1,
                "name": "Vacances 2025",
                "description": "Photos de mes vacances",
                "is_private": false,
                "photo_count": 15,
                "created_at": "2025-08-28T17:30:00Z"
            }
        ]
    },
    "trusted_devices": {
        "count": 2,
        "devices": [
            {
                "device_token": "abc123...",
                "device_type": "Desktop",
                "device_family": "Mac",
                "browser_family": "Safari",
                "browser_version": "15.0",
                "os_family": "macOS",
                "os_version": "10.15.7",
                "ip_address": "192.168.1.100",
                "location": "Paris, France",
                "created_at": "2025-08-28T17:30:00Z",
                "last_used_at": "2025-08-28T18:00:00Z",
                "expires_at": "2025-09-27T17:30:00Z"
            }
        ]
    },
    "api_endpoints": {
        "profile": "http://domain.com/api/v1/user/profile/",
        "profile_full": "http://domain.com/api/v1/user/profile/full/",
        "update_profile": "http://domain.com/api/v1/user/update/",
        "photos": "http://domain.com/photos/api/photos/",
        "collections": "http://domain.com/photos/api/collections/",
        "stats": "http://domain.com/photos/api/stats/"
    },
    "web_urls": {
        "profile_page": "http://domain.com/profile/",
        "photos_page": "http://domain.com/photos/gallery/",
        "collections_page": "http://domain.com/photos/collections/",
        "settings_page": "http://domain.com/settings/dashboard/"
    },
    "security_info": {
        "password_changed": null,
        "failed_login_attempts": 0,
        "account_locked_until": null
    },
    "gdpr_compliance": {
        "is_anonymized": false,
        "data_retention_policy": "User data is retained according to GDPR requirements",
        "right_to_be_forgotten": "Available through account anonymization",
        "data_portability": "Available through API endpoints"
    }
}
```

#### Mise à Jour du Profil

**PUT** `/users/update/`

Met à jour les informations du profil utilisateur.

**Request Body:**
```json
{
    "first_name": "John",
    "last_name": "Smith",
    "bio": "Nouvelle bio",
    "is_private": true
}
```

**Response (200):**
```json
{
    "success": true,
    "message": "Profile updated successfully.",
    "user": {
        "id": 1,
        "username": "johndoe",
        "first_name": "John",
        "last_name": "Smith",
        "bio": "Nouvelle bio",
        "is_private": true
    }
}
```

### 🔒 Déconnexion

#### Déconnexion

**POST** `/users/logout/`

Déconnecte l'utilisateur et met à jour son statut.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
    "success": true,
    "message": "Logout successful."
}
```

### 🔍 Utilitaires

#### Vérification de Disponibilité du Nom d'Utilisateur

**POST** `/users/check-username/`

Vérifie en temps réel si un nom d'utilisateur est disponible.

**Request Body:**
```json
{
    "username": "johndoe"
}
```

**Response (200):**
```json
{
    "available": true,
    "message": "Available"
}
```

**Response (200) - Non disponible:**
```json
{
    "available": false,
    "message": "Already taken"
}
```

#### Renvoi de Code de Vérification

**POST** `/users/resend-code/`

Renvoie un nouveau code de vérification par email.

**Request Body:**
```json
{
    "email": "user@example.com"
}
```

**Response (200):**
```json
{
    "success": true,
    "message": "New code sent successfully."
}
```

**Response (429) - Trop de demandes:**
```json
{
    "success": false,
    "message": "Please wait 60 seconds before requesting a new code."
}
```

## Gestion des Erreurs

### Codes de Statut HTTP

- **200** : Succès
- **201** : Créé avec succès
- **400** : Requête invalide
- **401** : Non authentifié
- **403** : Accès interdit
- **404** : Ressource non trouvée
- **429** : Trop de requêtes
- **500** : Erreur serveur

### Format des Erreurs

```json
{
    "success": false,
    "message": "Description de l'erreur",
    "errors": {
        "field_name": "Détail de l'erreur pour ce champ"
    }
}
```

## Sécurité

### Authentification 2FA

- **Email 2FA** : Code à 6 chiffres envoyé par email
- **TOTP 2FA** : Code à 6 chiffres généré par une application d'authentification
- **Trusted Devices** : Appareils de confiance pour éviter la 2FA répétée

### Trusted Devices

- **Expiration** : 30 jours par défaut
- **Identification** : Par IP + User-Agent + Token unique
- **Prévention des doublons** : Un seul appareil par combinaison IP/User-Agent
- **Cookies sécurisés** : HTTP-only, Secure, SameSite=Lax

### Validation des Données

- **Mots de passe** : Complexité requise (majuscules, minuscules, chiffres, caractères spéciaux)
- **Noms d'utilisateur** : 3-30 caractères, caractères alphanumériques et tirets
- **Âge minimum** : 16 ans pour l'inscription
- **Emails** : Validation et vérification obligatoire

## Rate Limiting

- **Codes de vérification** : 60 secondes entre les envois
- **Tentatives de connexion** : Limitation pour prévenir les attaques par force brute
- **Vérification 2FA** : Maximum 3 tentatives avant blocage

## Logs et Audit

Toutes les actions importantes sont loggées avec :
- Timestamp
- Adresse IP
- User-Agent
- Action effectuée
- Informations contextuelles

## Exemples d'Utilisation

### Inscription Complète

```bash
# 1. Vérification email
curl -X POST http://domain.com/api/v1/users/register/step1/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'

# 2. Vérification du code
curl -X POST http://domain.com/api/v1/users/register/step2/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "verification_code": "123456"}'

# 3. Inscription complète
curl -X POST http://domain.com/api/v1/users/register/complete/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "date_of_birth": "1990-01-01",
    "username": "johndoe",
    "password1": "SecurePassword123!",
    "password2": "SecurePassword123!"
  }'
```

### Connexion avec 2FA

```bash
# 1. Identifiants
curl -X POST http://domain.com/api/v1/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "step": "credentials",
    "identifier": "user@example.com",
    "password": "SecurePassword123!",
    "remember_device": true
  }'

# 2. Vérification 2FA
curl -X POST http://domain.com/api/v1/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "step": "email_2fa",
    "twofa_code": "123456"
  }'
```

### Gestion du Profil

```bash
# Récupération du profil
curl -X GET http://domain.com/api/v1/users/profile/full/ \
  -H "Authorization: Bearer <access_token>"

# Mise à jour du profil
curl -X PUT http://domain.com/api/v1/users/update/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"bio": "Nouvelle bio"}'
```

## Support et Contact

Pour toute question concernant l'API, consultez :
- La documentation technique
- Les logs d'erreur
- L'équipe de développement

---

*Dernière mise à jour : 28 août 2025*
