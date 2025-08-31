# HTMX + PhotoSearch Integration

Cette solution combine HTMX pour la navigation sans rechargement et PhotoSearch pour la recherche en temps réel des photos.

## 🚀 Fonctionnalités

- **Navigation HTMX** : Changement de type de post sans rechargement de page
- **Recherche en temps réel** : Recherche instantanée dans les photos (titre, description, tags, date)
- **Interface fluide** : Transitions smooth entre les différents types de posts
- **Réutilisable** : Composant PhotoSearch facilement intégrable dans d'autres templates

## 📁 Fichiers

- `photo-search.js` - Composant JavaScript réutilisable pour la recherche de photos
- `photo-search-demo.html` - Démonstration du composant PhotoSearch
- `htmx-photo-search-demo.html` - Démonstration complète HTMX + PhotoSearch

## 🔧 Installation

### 1. Inclure HTMX dans votre base template

```html
<!-- Dans votre base.html -->
<script src="https://unpkg.com/htmx.org@1.9.10"></script>
```

### 2. Inclure le composant PhotoSearch

```html
<!-- Dans votre template -->
<script src="{% static 'js/photo-search.js' %}"></script>
```

### 3. Ajouter les attributs HTMX

```html
<div class="post-type-option" 
     hx-get="{% url 'posts:post_create' %}?type=single_photo"
     hx-target="#post-content-area"
     hx-push-url="true"
     hx-swap="innerHTML"
     hx-indicator="#loading-indicator">
    <!-- contenu -->
</div>
```

### 4. Configurer la zone de contenu

```html
<!-- Indicateur de chargement -->
<div id="loading-indicator" class="htmx-indicator text-center py-4" style="display: none;">
    <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
    </div>
    <p class="mt-2 text-muted">Loading post type...</p>
</div>

<!-- Zone de contenu -->
<div id="post-content-area">
    <!-- Le contenu sera mis à jour par HTMX -->
</div>
```

## 🎯 Utilisation

### Initialisation du composant PhotoSearch

```javascript
// Initialisation de base
const photoSearch = new PhotoSearch();

// Avec options personnalisées
const photoSearch = new PhotoSearch({
    searchInputSelector: '.photo-search-input',
    resultsContainerSelector: '.photo-search-results',
    photoGridSelector: '.photo-grid',
    searchDelay: 300,
    minSearchLength: 2
});
```

### Gestion des événements HTMX

```javascript
// Ré-initialiser la recherche après les mises à jour HTMX
document.body.addEventListener('htmx:afterSwap', function(event) {
    if (event.target.id === 'post-content-area') {
        setTimeout(() => {
            initializePhotoSearch();
        }, 100);
    }
});
```

## 🎨 Personnalisation

### Options du composant PhotoSearch

```javascript
{
    searchInputSelector: '.photo-search-input',     // Sélecteur de l'input de recherche
    resultsContainerSelector: '.photo-search-results', // Sélecteur du conteneur de résultats
    photoGridSelector: '.photo-grid',               // Sélecteur de la grille de photos
    searchDelay: 300,                              // Délai de debounce en ms
    minSearchLength: 2,                            // Nombre minimum de caractères pour rechercher
    highlightClass: 'search-highlight',            // Classe CSS pour les termes surlignés
    noResultsClass: 'no-search-results',           // Classe CSS pour aucun résultat
    loadingClass: 'search-loading'                 // Classe CSS pour l'état de chargement
}
```

### Styles CSS personnalisés

Le composant utilise automatiquement les variables CSS de votre `base.scss` :

```css
:root {
    --text-default: hsl(86, 17%, 8%);
    --background-default: hsl(80, 5%, 88%);
    --primary-default: hsl(81, 31%, 52%);
    --text-100: hsl(87, 18%, 90%);
    --text-200: hsl(87, 18%, 80%);
    /* ... autres variables ... */
}
```

## 🔄 Méthodes publiques

```javascript
photoSearch.refresh();        // Rafraîchir la collection de photos
photoSearch.clearSearch();    // Effacer la recherche actuelle
photoSearch.destroy();        // Nettoyer les event listeners
```

## 📱 Responsive Design

Le composant s'adapte automatiquement aux différentes tailles d'écran :

- **Desktop** : Interface complète avec tous les éléments visibles
- **Tablet** : Optimisations pour les écrans moyens
- **Mobile** : Interface adaptée aux petits écrans

## 🎭 États et animations

- **Recherche** : Indicateur de chargement avec spinner
- **Résultats** : Mise en surbrillance des termes recherchés
- **Navigation** : Transitions smooth entre les types de posts
- **Feedback** : Messages d'erreur et de succès

## 🚨 Gestion des erreurs

Le composant gère automatiquement :

- Photos non trouvées
- Erreurs de chargement
- Échecs de requêtes HTMX
- État de chargement

## 🔧 Intégration avec Django

### Vue modifiée

```python
class PostCreateView(LoginRequiredMixin, CreateView):
    def get_template_names(self):
        """Retourner le template approprié selon le type de requête"""
        if self.request.headers.get('HX-Request'):
            return ["posts/partials/post_content.html"]
        return [self.template_name]
```

### Template partiel

Créez `posts/partials/post_content.html` pour le contenu HTMX.

## 📚 Exemples d'utilisation

### Recherche simple

```html
<div class="photo-search-container">
    <input type="text" 
           class="photo-search-input" 
           placeholder="Rechercher des photos...">
    <div class="photo-search-results"></div>
</div>
```

### Grille de photos avec attributs de données

```html
<div class="photo-grid">
    <div class="photo-item" 
         data-photo-id="{{ photo.id }}"
         data-description="{{ photo.description }}"
         data-tags="{{ photo.tags }}"
         data-date="{{ photo.date }}">
        <!-- contenu de la photo -->
    </div>
</div>
```

## 🎯 Cas d'usage

1. **Création de posts** : Navigation fluide entre types de posts
2. **Galerie photos** : Recherche instantanée dans les collections
3. **Dashboard utilisateur** : Interface réactive pour la gestion de contenu
4. **Applications mobiles** : Expérience native sans rechargements

## 🚀 Performance

- **Debouncing** : Recherche optimisée avec délai configurable
- **Lazy loading** : Chargement des résultats à la demande
- **Cache DOM** : Réutilisation des éléments existants
- **Event delegation** : Gestion efficace des événements

## 🔍 Débogage

### Console

```javascript
// Activer les logs de débogage
console.log('PhotoSearch initialized:', photoSearch);

// Vérifier l'état
console.log('Current search term:', photoSearch.currentSearchTerm);
console.log('Filtered photos:', photoSearch.filteredPhotos);
```

### Événements HTMX

```javascript
// Écouter tous les événements HTMX
document.body.addEventListener('htmx:beforeRequest', console.log);
document.body.addEventListener('htmx:afterRequest', console.log);
document.body.addEventListener('htmx:afterSwap', console.log);
```

## 📖 Support

Pour toute question ou problème :

1. Vérifiez la console du navigateur pour les erreurs
2. Assurez-vous que HTMX est correctement chargé
3. Vérifiez que les sélecteurs CSS correspondent à votre HTML
4. Testez avec le fichier de démonstration

## 🔄 Mises à jour

Le composant est conçu pour être facilement extensible :

- Ajout de nouveaux champs de recherche
- Support de filtres avancés
- Intégration avec d'autres composants
- Personnalisation des animations

---

**Note** : Cette solution est compatible avec Django 3.2+ et utilise les fonctionnalités modernes du navigateur.
