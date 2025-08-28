# Users API - Documentation Technique

## Architecture et Structure

### Modèles de Données

#### CustomUser
```python
class CustomUser(AbstractUser):
    # Champs de base
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=40)
    date_of_birth = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True)
    is_private = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    
    # Vérification email
    is_email_verified = models.BooleanField(default=False)
    email_verification_code = models.CharField(max_length=6, null=True, blank=True)
    verification_code_sent_at = models.DateTimeField(null=True, blank=True)
    
    # 2FA
    email_2fa_enabled = models.BooleanField(default=False)
    email_2fa_code = models.CharField(max_length=6, null=True, blank=True)
    email_2fa_sent_at = models.DateTimeField(null=True, blank=True)
    totp_enabled = models.BooleanField(default=False)
    twofa_totp_secret = models.CharField(max_length=32, null=True, blank=True)
    
    # Statut et sécurité
    is_online = models.BooleanField(default=False)
    is_anonymized = models.BooleanField(default=False)
    last_login_date = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.CharField(max_length=45, null=True, blank=True)
    ip_address = models.CharField(max_length=45, null=True, blank=True)
    
    # Métadonnées
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
```

#### TrustedDevice
```python
class TrustedDevice(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="trusted_devices")
    device_token = models.CharField(max_length=255, unique=True)
    user_agent = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    location = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    # Informations sur l'appareil
    device_type = models.CharField(max_length=50)
    device_family = models.CharField(max_length=50)
    browser_family = models.CharField(max_length=50)
    browser_version = models.CharField(max_length=20, blank=True)
    os_family = models.CharField(max_length=50)
    os_version = models.CharField(max_length=20, blank=True)
```

### Sérialiseurs

#### UserSerializer
```python
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'date_of_birth', 'bio', 'is_private', 'profile_picture', 
            'is_email_verified', 'date_joined', 'is_active'
        ]
        read_only_fields = ['id', 'date_joined', 'is_email_verified', 'is_active']
```

#### LoginSerializer
```python
class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=255)  # email ou username
    password = serializers.CharField(write_only=True)
    remember_device = serializers.BooleanField(default=False)
    
    def validate(self, data):
        identifier = data.get('identifier')
        password = data.get('password')
        
        user = authenticate(username=identifier, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        
        if not user.is_email_verified:
            raise serializers.ValidationError("Please verify your email address.")
        
        data["user"] = user
        return data
```

## Flux de Connexion

### Diagramme de Séquence

```
Client                    API                    Base de Données
  |                        |                           |
  |-- POST /login/ ------->|                           |
  |   (credentials)         |                           |
  |                         |-- authenticate() -------->|
  |                         |<-- user -----------------|
  |                         |                           |
  |                         |-- check 2FA ------------->|
  |                         |<-- 2FA status -----------|
  |                         |                           |
  |<-- 2FA required -------|                           |
  |                         |                           |
  |-- POST /login/ ------->|                           |
  |   (2FA choice)          |                           |
  |                         |-- send 2FA code --------->|
  |                         |<-- code sent ------------|
  |                         |                           |
  |<-- code sent ----------|                           |
  |                         |                           |
  |-- POST /login/ ------->|                           |
  |   (2FA code)            |                           |
  |                         |-- verify 2FA ----------->|
  |                         |<-- verified -------------|
  |                         |                           |
  |                         |-- create tokens --------->|
  |                         |-- handle trusted device ->|
  |                         |<-- device info ----------|
  |                         |                           |
  |<-- login success ------|                           |
  |   + tokens              |                           |
  |   + trusted_device      |                           |
```

### Gestion des Sessions

#### Initialisation des Données de Session
```python
def initialize_login_session_data(request, user, code=None):
    """Initialise les données de session pour le processus de connexion"""
    session_data = {
        "user_id": user.id,
        "login_started_at": timezone.now().isoformat(),
        "current_step": "credentials",
        "verification_code": code,
        "code_sent_at": timezone.now().isoformat() if code else None,
        "code_attempts": 0,
    }
    request.session["login_data"] = session_data
    return session_data
```

#### Nettoyage des Sessions
```python
# Nettoyage après connexion réussie
request.session.pop("login_data", None)
request.session.pop("pre_2fa_user_id", None)
request.session.pop("current_login_step", None)

# Nettoyage des données trusted device
del request.session["trusted_device_token"]
del request.session["trusted_device_cookie_name"]
del request.session["trusted_device_max_age"]
```

## Sécurité

### Validation des Mots de Passe

#### CustomPasswordValidator
```python
class CustomPasswordValidator:
    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        
        if not any(c.isupper() for c in password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        
        if not any(c.islower() for c in password):
            raise ValidationError("Password must contain at least one lowercase letter.")
        
        if not any(c.isdigit() for c in password):
            raise ValidationError("Password must contain at least one digit.")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            raise ValidationError("Password must contain at least one special character.")
    
    def get_help_text(self):
        return "Password must be at least 8 characters long and contain uppercase, lowercase, digit, and special character."
```

### Validation des Noms d'Utilisateur

#### UsernameValidator
```python
class UsernameValidator:
    def __init__(self):
        self.min_length = 3
        self.max_length = 30
        self.allowed_chars = re.compile(r'^[a-zA-Z0-9_-]+$')
    
    def validate(self, username):
        if len(username) < self.min_length:
            raise ValidationError(f"Username must be at least {self.min_length} characters long.")
        
        if len(username) > self.max_length:
            raise ValidationError(f"Username must be at most {self.max_length} characters long.")
        
        if not self.allowed_chars.match(username):
            raise ValidationError("Username can only contain letters, numbers, hyphens, and underscores.")
        
        # Conversion en minuscules pour l'unicité
        return username.lower()
```

### Protection contre les Attaques

#### Limitation des Tentatives 2FA
```python
# Vérification du nombre de tentatives
attempts = session_data.get("code_attempts", 0)
if attempts >= 3:
    return Response({
        'success': False,
        'message': 'Too many attempts. Request a new code.',
        'errors': {'twofa_code': 'Too many attempts'}
    }, status=status.HTTP_400_BAD_REQUEST)

# Incrémentation du compteur
attempts += 1
session_data["code_attempts"] = attempts
request.session["login_data"] = session_data
```

#### Expiration des Codes
```python
# Vérification de l'expiration (10 minutes)
if code_sent_at:
    sent_time = datetime.fromisoformat(code_sent_at)
    if timezone.is_naive(sent_time):
        sent_time = timezone.make_aware(sent_time)
    
    if (timezone.now() - sent_time).total_seconds() > 600:  # 10 minutes
        return Response({
            'success': False,
            'message': 'Code has expired. Request a new code.',
            'errors': {'twofa_code': 'Code expired'}
        }, status=status.HTTP_400_BAD_REQUEST)
```

## Trusted Devices

### Logique de Vérification

#### Vérification Primaire (IP + User-Agent)
```python
def check_existing_device_by_ip_useragent(user, ip, user_agent):
    """Vérifie si un appareil existe déjà par IP et User-Agent"""
    return TrustedDevice.objects.filter(
        user=user,
        ip_address=ip,
        user_agent=user_agent[:255]
    ).first()
```

#### Vérification Secondaire (Cookie)
```python
def check_existing_device_by_cookie(user, cookies):
    """Vérifie si un appareil existe déjà par cookie"""
    trusted_tokens = [
        value for key, value in cookies.items()
        if key.startswith(f"trusted_device_{user.pk}")
    ]
    
    for token in trusted_tokens:
        hashed_token = hash_token(token)
        device = TrustedDevice.objects.filter(
            user=user, device_token=hashed_token
        ).first()
        if device:
            return device
    
    return None
```

### Création d'Appareil

#### Génération de Token
```python
def generate_device_token(user_id):
    """Génère un token unique pour l'appareil"""
    return f"{user_id}-{uuid.uuid4().hex}"
```

#### Analyse du User-Agent
```python
def _get_device_info_from_user_agent(user_agent):
    """Extrait les informations sur l'appareil depuis le User-Agent"""
    try:
        ua_info = analyze_user_agent(user_agent)
        return {
            "device_type": ua_info.get("device_type", "Unknown Device"),
            "device_family": ua_info.get("device_family", "Unknown"),
            "browser_family": ua_info.get("browser_family", "Unknown"),
            "browser_version": ua_info.get("browser_version", ""),
            "os_family": ua_info.get("os_family", "Unknown"),
            "os_version": ua_info.get("os_version", ""),
        }
    except Exception:
        # Fallback si l'analyse échoue
        return {
            "device_type": "Unknown Device",
            "device_family": "Unknown",
            "browser_family": "Unknown",
            "browser_version": "",
            "os_family": "Unknown",
            "os_version": "",
        }
```

## Logs et Audit

### Structure des Logs

#### Format JSON
```python
def log_user_action_json(user, action, request, ip_address, extra_info=None):
    """Enregistre une action utilisateur au format JSON"""
    log_data = {
        "timestamp": timezone.now().isoformat(),
        "user_id": user.id,
        "username": user.username,
        "action": action,
        "ip_address": ip_address,
        "user_agent": get_user_agent(request),
        "session_id": request.session.session_key,
        "extra_info": extra_info or {}
    }
    
    # Écriture dans le fichier de log
    with open("logs/user_logs.json", "a") as f:
        json.dump(log_data, f)
        f.write("\n")
```

#### Actions Loggées
- `register_api` : Inscription d'un nouvel utilisateur
- `login_api` : Connexion réussie
- `profile_update_api` : Mise à jour du profil
- `logout_api` : Déconnexion
- `2fa_verification` : Vérification 2FA
- `trusted_device_creation` : Création d'appareil de confiance

## Gestion des Erreurs

### Exceptions Personnalisées

#### ValidationError
```python
class ValidationError(Exception):
    """Exception personnalisée pour les erreurs de validation"""
    def __init__(self, message, field=None):
        self.message = message
        self.field = field
        super().__init__(self.message)
```

#### AuthenticationError
```python
class AuthenticationError(Exception):
    """Exception personnalisée pour les erreurs d'authentification"""
    def __init__(self, message, code=None):
        self.message = message
        self.code = code
        super().__init__(self.message)
```

### Gestion des Erreurs dans les Vues

#### Try-Catch Pattern
```python
try:
    # Logique métier
    user = CustomUser.objects.get(pk=user_id)
    # ... traitement ...
except CustomUser.DoesNotExist:
    return Response({
        'success': False,
        'message': 'User not found.',
        'errors': {'user': 'User not found'}
    }, status=status.HTTP_400_BAD_REQUEST)
except Exception as e:
    return Response({
        'success': False,
        'message': f'An error occurred: {str(e)}',
        'errors': {'general': 'Unexpected error'}
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

## Tests

### Tests Unitaires

#### Test des Sérialiseurs
```python
class LoginSerializerTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
    
    def test_valid_login(self):
        data = {
            'identifier': 'testuser',
            'password': 'TestPass123!',
            'remember_device': True
        }
        serializer = LoginSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['user'], self.user)
    
    def test_invalid_password(self):
        data = {
            'identifier': 'testuser',
            'password': 'WrongPassword',
            'remember_device': False
        }
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
```

#### Test des Vues
```python
class LoginAPITest(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
    
    def test_login_success(self):
        data = {
            'step': 'credentials',
            'identifier': 'testuser',
            'password': 'TestPass123!',
            'remember_device': True
        }
        response = self.client.post('/api/v1/users/login/', data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
```

### Tests d'Intégration

#### Test du Flux Complet
```python
class CompleteLoginFlowTest(APITestCase):
    def test_complete_login_with_2fa(self):
        # 1. Créer un utilisateur avec 2FA activé
        user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        user.email_2fa_enabled = True
        user.save()
        
        # 2. Première étape - identifiants
        response = self.client.post('/api/v1/users/login/', {
            'step': 'credentials',
            'identifier': 'testuser',
            'password': 'TestPass123!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['requires_2fa'])
        
        # 3. Deuxième étape - choix 2FA
        response = self.client.post('/api/v1/users/login/', {
            'step': 'choose_2fa',
            'twofa_method': 'email'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['next_step'], 'email_2fa')
        
        # 4. Troisième étape - vérification 2FA
        # Récupérer le code depuis la session ou la base de données
        # ... logique de test ...
```

## Performance et Optimisation

### Requêtes de Base de Données

#### Sélection des Champs
```python
# Optimisation : sélectionner seulement les champs nécessaires
user = CustomUser.objects.only(
    'id', 'username', 'email', 'first_name', 'last_name'
).get(pk=user_id)
```

#### Préchargement des Relations
```python
# Préchargement des trusted devices
user = CustomUser.objects.prefetch_related('trusted_devices').get(pk=user_id)

# Préchargement des collections avec photos
collections = Collection.objects.prefetch_related('photos').filter(owner=user)
```

### Cache

#### Mise en Cache des Profils
```python
from django.core.cache import cache

def get_user_profile_cached(user_id):
    """Récupère le profil utilisateur depuis le cache ou la base de données"""
    cache_key = f"user_profile_{user_id}"
    profile = cache.get(cache_key)
    
    if profile is None:
        user = CustomUser.objects.get(pk=user_id)
        profile = UserSerializer(user).data
        cache.set(cache_key, profile, timeout=300)  # 5 minutes
    
    return profile
```

## Déploiement et Configuration

### Variables d'Environnement

#### Configuration de Base
```bash
# Django settings
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=your-domain.com

# Base de données
DATABASE_URL=postgresql://user:password@localhost/shuttrly

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_LIFETIME=5 minutes
JWT_REFRESH_TOKEN_LIFETIME=1 day

# Trusted Devices
TRUSTED_DEVICE_EXPIRY_DAYS=30
```

### Configuration de Production

#### Sécurité
```python
# settings.py
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Headers de sécurité
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

#### Logs
```python
# Configuration des logs
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/django.log',
        },
    },
    'loggers': {
        'users': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## Maintenance et Monitoring

### Nettoyage des Données

#### Suppression des Appareils Expirés
```python
from django.utils import timezone
from users.models import TrustedDevice

def cleanup_expired_devices():
    """Supprime les appareils de confiance expirés"""
    expired_devices = TrustedDevice.objects.filter(
        expires_at__lt=timezone.now()
    )
    count = expired_devices.count()
    expired_devices.delete()
    return count
```

#### Nettoyage des Utilisateurs Temporaires
```python
def cleanup_temp_users():
    """Supprime les utilisateurs temporaires non vérifiés"""
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(hours=24)
    temp_users = CustomUser.objects.filter(
        is_active=False,
        date_joined__lt=cutoff_date
    )
    count = temp_users.count()
    temp_users.delete()
    return count
```

### Monitoring

#### Métriques Clés
- Nombre de connexions par jour
- Taux de succès des connexions 2FA
- Nombre d'appareils de confiance actifs
- Temps de réponse des endpoints critiques

#### Alertes
- Taux d'erreur élevé (>5%)
- Temps de réponse lent (>2s)
- Nombre de tentatives de connexion échouées élevé
- Espace disque faible pour les logs

---

*Documentation technique - Dernière mise à jour : 28 août 2025*
