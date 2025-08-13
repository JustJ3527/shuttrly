# JavaScript Architecture - Shuttrly

## Vue d'ensemble

Ce projet utilise une architecture JavaScript modulaire moderne pour une meilleure maintenabilité, réutilisabilité et performance. L'ancien code monolithique a été refactorisé en modules spécialisés.

## Structure des fichiers

### 🎨 Core Modules (Modules principaux)

#### `ui-utils.js`
**Utilitaires d'interface utilisateur**
- Manipulation du DOM avec animations
- Gestion des événements
- Utilitaires de formulaire (password toggles, auto-resize textarea)
- Animations (fade, slide, etc.)
- Gestion du scroll
- Fonctions utilitaires (debounce, throttle, etc.)

**Utilisation :**
```javascript
// Créer un élément avec animation
window.uiUtils.createElement('div', { className: 'alert' }, 'Message');

// Toggle d'élément avec animation
window.uiUtils.toggleElement(element, true, { animate: true });

// Scroll smooth
window.uiUtils.smoothScrollTo('#section');
```

#### `form-validation.js`
**Système de validation des formulaires**
- Validation automatique des champs
- Gestion des erreurs avec animations
- Validateurs personnalisables
- Gestion des boutons de soumission
- Support pour différents types de validation

**Utilisation :**
```javascript
// Initialiser la validation d'un formulaire
window.formValidator.initializeFormValidation('my-form', {
    'username': [{ type: 'required' }, { type: 'username' }],
    'password': [{ type: 'required' }, { type: 'password' }]
});

// Valider un champ spécifique
window.formValidator.validateField(field, rules);

// Afficher une erreur
window.formValidator.showFieldError('fieldId', 'Message d\'erreur', 'error');
```

#### `countdown.js`
**Système de gestion des countdowns**
- Timers pour la 2FA email
- Countdowns génériques
- Gestion des délais de renvoi
- Progress bars animées
- Support pour différents types de countdown

**Utilisation :**
```javascript
// Initialiser un countdown email
window.countdownManager.initializeEmailCountdown({
    timeUntilResend: 60,
    timerId: 'timer',
    countdownId: 'countdown',
    resendFormId: 'resend-form',
    canResend: false
});

// Créer un countdown générique
window.countdownManager.createGenericCountdown({
    duration: 30,
    onTick: (timeLeft) => console.log(timeLeft),
    onComplete: () => console.log('Terminé!')
});
```

#### `2fa.js`
**Système de gestion de la 2FA**
- Gestion complète de la 2FA email et TOTP
- Validation des codes de vérification
- Gestion des appareils de confiance
- Copie des URI TOTP
- Animations et transitions

**Utilisation :**
```javascript
// Les fonctions sont automatiquement disponibles globalement
showEnableEmail2FA();
hideEnableEmail2FA();
showEnableTOTP2FA();
toggleDeviceDetails(header);

// Ou via l'instance principale
window.twoFactorAuth.showEnableEmail2FA();
```

### 🔐 Authentication Module

#### `auth-modern.js`
**Système d'authentification moderne**
- Architecture basée sur la configuration
- Détection automatique des pages et étapes
- Intégration avec tous les modules
- Validation des formulaires
- Gestion des countdowns

**Utilisation :**
```javascript
// Le système s'initialise automatiquement
// Configuration basée sur la page détectée

// Accéder à l'instance
window.modernAuth.currentPage; // 'login', 'register', etc.
window.modernAuth.currentStep; // '1', '2', 'email_2fa', etc.
```

### 📚 Legacy Support (Support de l'ancien code)

#### `utils_scripts.js`, `auth.js`, etc.
**Anciens fichiers conservés pour la compatibilité**
- Fonctions existantes maintenues
- Intégration progressive avec les nouveaux modules
- Support des anciennes fonctionnalités

## Configuration

### Configuration des countdowns
```javascript
const COUNTDOWN_CONFIG = {
    email: {
        resendDelay: 60,        // Délai en secondes
        warningThreshold: 10,   // Seuil d'avertissement
        autoResend: false       // Renvoi automatique
    }
};
```

### Configuration de validation
```javascript
const VALIDATION_CONFIG = {
    password: {
        minLength: 8,
        requireUppercase: true,
        requireLowercase: true,
        requireNumbers: true
    }
};
```

### Configuration UI
```javascript
const UI_CONFIG = {
    animation: {
        duration: 300,          // Durée des animations
        easing: 'ease',         // Type d'easing
        fadeInDelay: 100        // Délai entre animations
    }
};
```

## Migration depuis l'ancien code

### 1. Remplacer les fonctions inline
**Avant :**
```html
<script>
function toggleDetails(summary) {
    const details = summary.nextElementSibling;
    details.style.display = details.style.display === 'none' ? 'block' : 'none';
}
</script>
```

**Après :**
```html
<!-- Utiliser la fonction globale -->
<button onclick="toggleDeviceDetails(this)">Toggle</button>
```

### 2. Remplacer les countdowns inline
**Avant :**
```html
<script>
let timeLeft = 60;
setInterval(() => {
    timeLeft--;
    document.getElementById('timer').textContent = timeLeft;
}, 1000);
</script>
```

**Après :**
```html
<div data-countdown-type="email" data-time-until-resend="60" data-can-resend="false">
    Temps restant: <span id="timer">60</span> secondes
</div>
```

### 3. Utiliser la validation automatique
**Avant :**
```javascript
// Validation manuelle
if (!password || password.length < 8) {
    showError('Password too short');
}
```

**Après :**
```javascript
// Validation automatique via configuration
window.formValidator.initializeFormValidation('form', {
    'password': [{ type: 'password' }]
});
```

## Bonnes pratiques

### 1. Utiliser les modules appropriés
- **UI** : `ui-utils.js` pour les manipulations DOM et animations
- **Validation** : `form-validation.js` pour la validation des formulaires
- **Timers** : `countdown.js` pour tous les countdowns
- **2FA** : `2fa.js` pour la gestion de la 2FA

### 2. Configuration vs Code
Privilégier la configuration plutôt que le code personnalisé :
```javascript
// ✅ Bon : Configuration
const config = { duration: 300, easing: 'ease' };
window.uiUtils.fadeIn(element, config);

// ❌ Éviter : Code personnalisé
element.style.transition = 'all 300ms ease';
```

### 3. Gestion des erreurs
Utiliser le système de gestion d'erreurs intégré :
```javascript
// ✅ Bon : Utiliser le système de validation
window.formValidator.showFieldError('fieldId', 'Message', 'error');

// ❌ Éviter : Gestion manuelle
const errorDiv = document.createElement('div');
errorDiv.innerHTML = 'Error message';
```

### 4. Nettoyage automatique
Les modules gèrent automatiquement le nettoyage des timers et événements. Pas besoin de cleanup manuel dans la plupart des cas.

## Debug et développement

### Mode debug automatique
En développement (localhost), les modules affichent automatiquement des informations de debug dans la console.

### Fonctions de debug
```javascript
// Debug du système 2FA
window.debug2FAFunctions();

// Debug du système de countdown
window.debugCountdownSystem();

// Debug du système de validation
window.debugValidationSystem();

// Debug du système UI
window.debugUISystem();

// Debug du système d'authentification
window.debugModernAuth();
```

### Vérification des modules
```javascript
// Vérifier que tous les modules sont chargés
console.log('2FA System:', !!window.twoFactorAuth);
console.log('Countdown System:', !!window.countdownManager);
console.log('Form Validator:', !!window.formValidator);
console.log('UI Utils:', !!window.uiUtils);
console.log('Modern Auth:', !!window.modernAuth);
```

## Performance

### Chargement asynchrone
Les modules sont chargés de manière synchrone pour maintenir la compatibilité, mais peuvent être facilement convertis en modules ES6 pour le chargement asynchrone.

### Lazy loading
Les fonctionnalités sont initialisées uniquement quand nécessaire, réduisant l'empreinte mémoire.

### Gestion des événements
Les événements sont gérés de manière optimisée avec nettoyage automatique pour éviter les fuites mémoire.

## Support des navigateurs

### Navigateurs modernes
- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

### Fallbacks
- Support des anciennes API (clipboard, intersection observer)
- Polyfills automatiques pour les fonctionnalités manquantes

## Contribution

### Ajouter un nouveau module
1. Créer le fichier dans `static/js/`
2. Suivre la structure des modules existants
3. Ajouter la documentation dans ce README
4. Mettre à jour `base.html` si nécessaire

### Modifier un module existant
1. Maintenir la compatibilité avec l'API existante
2. Ajouter des tests si possible
3. Mettre à jour la documentation

### Tests
Les modules incluent des fonctions de debug automatiques pour faciliter les tests en développement.

---

**Note :** Cette architecture remplace progressivement l'ancien système. Les anciens fichiers sont conservés pour la compatibilité et seront supprimés une fois la migration terminée.