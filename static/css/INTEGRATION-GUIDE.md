# PhotoSearch - Guide d'Intégration Complet

Ce guide explique comment intégrer le composant PhotoSearch avec filtres inline dans vos templates Django.

## 📋 Table des matières

1. [Installation](#installation)
2. [Intégration Basique](#intégration-basique)
3. [Intégration Avancée](#intégration-avancée)
4. [Exemples d'Utilisation](#exemples-dutilisation)
5. [Options de Configuration](#options-de-configuration)
6. [Personnalisation](#personnalisation)
7. [Troubleshooting](#troubleshooting)

## 🛠 Installation

### 1. Fichiers requis

Copiez ces fichiers dans votre projet :

```
static/
├── css/
│   └── photo-search.css
└── js/
    └── photo-search.js
```

### 2. Dépendances

- **Font Awesome** (pour les icônes)
- **Variables CSS** pour le thème (voir section Variables)

## 🚀 Intégration Basique

### Template Django minimal

```django
{% load static %}
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link rel="stylesheet" href="{% static 'css/photo-search.css' %}">
</head>
<body>
    <!-- Container de recherche -->
    <div class="photo-search-container">
        <input type="text" class="photo-search-input" placeholder="Rechercher des photos...">
    </div>
    
    <!-- Grille de photos -->
    <div class="photo-grid">
        {% for photo in photos %}
        <div class="photo-item" 
             data-photo-id="{{ photo.id }}"
             data-camera="{{ photo.get_camera_display|default:'' }}"
             data-raw="{{ photo.is_raw|yesno:'true,false' }}">
            <img src="{% if photo.thumbnail %}{{ photo.thumbnail.url }}{% else %}{{ photo.original_file.url }}{% endif %}" 
                 alt="{{ photo.title|default:'Photo' }}">
            <div class="photo-info">
                <small>{{ photo.title|default:'Untitled' }}</small>
            </div>
        </div>
        {% endfor %}
    </div>
    
    <script src="{% static 'js/photo-search.js' %}"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            new PhotoSearch({
                searchInputSelector: '.photo-search-input',
                photoGridSelector: '.photo-grid',
                showFilters: true
            });
        });
    </script>
</body>
</html>
```

## ⚙️ Intégration Avancée

### 1. Multiple instances

```javascript
// Pour plusieurs sections avec des recherches indépendantes
const photoSearchInstances = {};

// Section photos personnelles
photoSearchInstances.personal = new PhotoSearch({
    searchInputSelector: '#personal-search',
    photoGridSelector: '#personal-photos',
    showFilters: true,
    navbarMode: false
});

// Section photos publiques
photoSearchInstances.public = new PhotoSearch({
    searchInputSelector: '#public-search',
    photoGridSelector: '#public-photos',
    showFilters: true,
    navbarMode: false
});

// Gestion des onglets
function switchSection(sectionName) {
    // Cacher toutes les sections
    document.querySelectorAll('.photo-section').forEach(section => {
        section.style.display = 'none';
    });
    
    // Afficher la section active
    document.getElementById(sectionName + '-section').style.display = 'block';
    
    // Rafraîchir la recherche de la section active
    if (photoSearchInstances[sectionName]) {
        photoSearchInstances[sectionName].refresh();
    }
}
```

### 2. Mode Navbar

```javascript
// Pour une barre de recherche dans la navbar
new PhotoSearch({
    searchInputSelector: '.navbar-search-input',
    photoGridSelector: '.main-photo-grid',
    showFilters: false,        // Pas de filtres dans la navbar
    navbarMode: true,         // Mode navbar (pas de spinner)
    showLoadingInInput: false // Pas d'indicateur de chargement
});
```

### 3. Intégration avec des API

```javascript
class APIPhotoSearch extends PhotoSearch {
    constructor(options) {
        super(options);
        this.apiEndpoint = options.apiEndpoint;
    }
    
    async performSearch(searchTerm) {
        if (this.apiEndpoint && searchTerm.length >= this.options.minSearchLength) {
            try {
                const response = await fetch(`${this.apiEndpoint}?search=${encodeURIComponent(searchTerm)}`);
                const data = await response.json();
                this.updateGridWithAPIResults(data.photos);
            } catch (error) {
                console.error('Search API error:', error);
                super.performSearch(searchTerm);
            }
        } else {
            super.performSearch(searchTerm);
        }
    }
    
    updateGridWithAPIResults(photos) {
        // Logique pour mettre à jour la grille avec les résultats API
    }
}

// Utilisation
new APIPhotoSearch({
    searchInputSelector: '.api-search-input',
    photoGridSelector: '.api-photo-grid',
    apiEndpoint: '/api/photos/search/',
    showFilters: true
});
```

## 📖 Exemples d'Utilisation

### 1. Galerie de photos utilisateur

```django
<!-- Template: user_gallery.html -->
{% extends "base.html" %}
{% load static %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/photo-search.css' %}">
{% endblock %}

{% block content %}
<div class="container">
    <h1>Ma Galerie</h1>
    
    <!-- Barre de recherche -->
    <div class="photo-search-container">
        <input type="text" class="photo-search-input" placeholder="Rechercher dans ma galerie...">
    </div>
    
    <!-- Grille de photos -->
    <div class="photo-grid">
        {% for photo in user_photos %}
        <div class="photo-item" 
             data-photo-id="{{ photo.id }}"
             data-camera="{{ photo.get_camera_display|default:'' }}"
             data-raw="{{ photo.is_raw|yesno:'true,false' }}"
             data-description="{{ photo.description|default:'' }}"
             data-tags="{{ photo.tags|default:'' }}">
            <img src="{{ photo.thumbnail.url }}" alt="{{ photo.title }}">
            <div class="photo-info">
                <small>{{ photo.title }}</small>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/photo-search.js' %}"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
    new PhotoSearch({
        searchInputSelector: '.photo-search-input',
        photoGridSelector: '.photo-grid',
        showFilters: true,
        minSearchLength: 1 // Recherche dès le premier caractère
    });
});
</script>
{% endblock %}
```

### 2. Page d'exploration

```django
<!-- Template: explore.html -->
{% extends "base.html" %}
{% load static %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/photo-search.css' %}">
<style>
    .explore-filters {
        margin-bottom: 2rem;
    }
    .category-tabs {
        margin-bottom: 1rem;
    }
</style>
{% endblock %}

{% block content %}
<div class="container">
    <h1>Explorer</h1>
    
    <!-- Onglets de catégories -->
    <div class="category-tabs">
        <button class="tab-btn active" onclick="switchCategory('recent')">Récentes</button>
        <button class="tab-btn" onclick="switchCategory('popular')">Populaires</button>
        <button class="tab-btn" onclick="switchCategory('featured')">Sélectionnées</button>
    </div>
    
    <!-- Section photos récentes -->
    <div id="recent-section" class="photo-section">
        <div class="photo-search-container">
            <input type="text" id="recent-search" class="photo-search-input" placeholder="Rechercher dans les photos récentes...">
        </div>
        <div id="recent-photos" class="photo-grid">
            {% for photo in recent_photos %}
            <!-- Structure photo -->
            {% endfor %}
        </div>
    </div>
    
    <!-- Section photos populaires -->
    <div id="popular-section" class="photo-section" style="display: none;">
        <div class="photo-search-container">
            <input type="text" id="popular-search" class="photo-search-input" placeholder="Rechercher dans les photos populaires...">
        </div>
        <div id="popular-photos" class="photo-grid">
            {% for photo in popular_photos %}
            <!-- Structure photo -->
            {% endfor %}
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/photo-search.js' %}"></script>
<script>
const exploreSearches = {};

document.addEventListener('DOMContentLoaded', function() {
    // Initialiser les recherches pour chaque section
    exploreSearches.recent = new PhotoSearch({
        searchInputSelector: '#recent-search',
        photoGridSelector: '#recent-photos',
        showFilters: true
    });
    
    exploreSearches.popular = new PhotoSearch({
        searchInputSelector: '#popular-search',
        photoGridSelector: '#popular-photos',
        showFilters: true
    });
});

function switchCategory(category) {
    // Gestion des onglets
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Afficher/cacher les sections
    document.querySelectorAll('.photo-section').forEach(section => {
        section.style.display = 'none';
    });
    document.getElementById(category + '-section').style.display = 'block';
    
    // Rafraîchir la recherche active
    if (exploreSearches[category]) {
        exploreSearches[category].refresh();
    }
}
</script>
{% endblock %}
```

### 3. Interface d'administration

```django
<!-- Template: admin_photos.html -->
{% extends "admin/base.html" %}
{% load static %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/photo-search.css' %}">
<style>
    .admin-photo-grid {
        margin-top: 2rem;
    }
    .admin-photo-item {
        position: relative;
    }
    .admin-controls {
        position: absolute;
        top: 5px;
        right: 5px;
        display: none;
    }
    .admin-photo-item:hover .admin-controls {
        display: block;
    }
</style>
{% endblock %}

{% block content %}
<div class="admin-container">
    <h1>Gestion des Photos</h1>
    
    <!-- Statistiques -->
    <div class="stats-row">
        <div class="stat-card">
            <h3>{{ total_photos }}</h3>
            <p>Photos totales</p>
        </div>
        <div class="stat-card">
            <h3>{{ raw_photos }}</h3>
            <p>Fichiers RAW</p>
        </div>
    </div>
    
    <!-- Recherche administrative -->
    <div class="photo-search-container">
        <input type="text" class="admin-photo-search" placeholder="Rechercher des photos à modérer...">
    </div>
    
    <!-- Grille administrative -->
    <div class="admin-photo-grid photo-grid">
        {% for photo in photos %}
        <div class="photo-item admin-photo-item" 
             data-photo-id="{{ photo.id }}"
             data-camera="{{ photo.get_camera_display|default:'' }}"
             data-raw="{{ photo.is_raw|yesno:'true,false' }}"
             data-user="{{ photo.user.username }}">
            <img src="{{ photo.thumbnail.url }}" alt="{{ photo.title }}">
            <div class="photo-info">
                <small>{{ photo.title }} - {{ photo.user.username }}</small>
            </div>
            <div class="admin-controls">
                <button class="btn-edit" onclick="editPhoto({{ photo.id }})">✏️</button>
                <button class="btn-delete" onclick="deletePhoto({{ photo.id }})">🗑️</button>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/photo-search.js' %}"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
    new PhotoSearch({
        searchInputSelector: '.admin-photo-search',
        photoGridSelector: '.admin-photo-grid',
        showFilters: true,
        minSearchLength: 1
    });
});

function editPhoto(photoId) {
    // Logique d'édition
    window.location.href = `/admin/photos/${photoId}/edit/`;
}

function deletePhoto(photoId) {
    if (confirm('Supprimer cette photo ?')) {
        // Logique de suppression
    }
}
</script>
{% endblock %}
```

## 🔧 Options de Configuration

### Options principales

```javascript
new PhotoSearch({
    // Sélecteurs (requis)
    searchInputSelector: '.photo-search-input',    // Sélecteur du champ de recherche
    photoGridSelector: '.photo-grid',              // Sélecteur de la grille de photos
    resultsContainerSelector: '.search-results',   // Sélecteur pour les résultats dropdown (optionnel)
    
    // Comportement de recherche
    searchDelay: 300,                              // Délai en ms avant recherche (debounce)
    minSearchLength: 2,                            // Nombre minimum de caractères
    
    // Filtres
    showFilters: true,                             // Afficher les filtres inline
    
    // Interface
    showLoadingInInput: true,                      // Afficher le spinner dans l'input
    navbarMode: false,                             // Mode navbar (simplifié)
    
    // Classes CSS
    highlightClass: 'search-highlight',            // Classe pour surligner les résultats
    noResultsClass: 'no-search-results',          // Classe pour "aucun résultat"
    loadingClass: 'search-loading'                // Classe pendant le chargement
});
```

### Méthodes publiques

```javascript
const photoSearch = new PhotoSearch(options);

// Rafraîchir les données
photoSearch.refresh();

// Effectuer une recherche programmatique
photoSearch.performSearch('ma recherche');

// Réinitialiser les filtres
photoSearch.resetFilters();

// Nettoyer et détruire l'instance
photoSearch.destroy();

// Afficher/masquer tous les éléments
photoSearch.showAllPhotos();
photoSearch.clearSearch();
```

## 🎨 Personnalisation

### Variables CSS à définir

```css
:root {
    /* Couleurs principales */
    --primary-default: #007aff;
    --primary-100: #cce7ff;
    --primary-200: #99d0ff;
    
    /* Texte */
    --text-default: #1d1d1f;
    --text-100: #f5f5f7;
    --text-200: #e5e5e7;
    --text-300: #d2d2d7;
    --text-400: #8e8e93;
    --text-500: #636366;
    
    /* Arrière-plan */
    --background-default: #ffffff;
}
```

### Styles personnalisés

```css
/* Personnaliser l'apparence des filtres */
.photo-search-filters-inline {
    background: var(--primary-100);
    border-radius: 0.5rem;
    padding: 0.5rem;
}

/* Style personnalisé pour les photos sélectionnées */
.photo-item.search-match {
    transform: scale(1.02);
    box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
}

/* Adaptation pour mode sombre */
@media (prefers-color-scheme: dark) {
    :root {
        --background-default: #1d1d1f;
        --text-default: #ffffff;
        /* ... autres variables mode sombre */
    }
}
```

### Extension du composant

```javascript
class CustomPhotoSearch extends PhotoSearch {
    constructor(options) {
        super(options);
        this.customOptions = {
            enableFavorites: true,
            ...options.custom
        };
    }
    
    collectAllPhotos() {
        super.collectAllPhotos();
        
        // Ajouter des données personnalisées
        this.allPhotos = this.allPhotos.map(photo => ({
            ...photo,
            isFavorite: photo.element.dataset.favorite === 'true',
            rating: parseInt(photo.element.dataset.rating) || 0
        }));
    }
    
    createFiltersContainer() {
        const container = super.createFiltersContainer();
        
        // Ajouter un filtre personnalisé
        if (this.customOptions.enableFavorites) {
            const favoriteFilter = document.createElement('div');
            favoriteFilter.className = 'inline-filter';
            favoriteFilter.innerHTML = `
                <input type="checkbox" id="filter-favorite-${this.instanceId}">
                <label for="filter-favorite-${this.instanceId}">
                    <i class="fas fa-heart"></i> Favoris
                </label>
            `;
            container.appendChild(favoriteFilter);
        }
        
        return container;
    }
}
```

## 🔍 Troubleshooting

### Problèmes courants

#### 1. Les filtres ne s'affichent pas
```javascript
// Vérifiez que showFilters est activé
new PhotoSearch({
    showFilters: true  // ← Important !
});

// Vérifiez la console pour les erreurs
console.log('PhotoSearch initialized');
```

#### 2. Les options de camera sont vides
```html
<!-- Assurez-vous que data-camera contient une valeur -->
<div class="photo-item" data-camera="{{ photo.get_camera_display|default:'' }}">
```

#### 3. La recherche ne fonctionne pas
```javascript
// Vérifiez les sélecteurs CSS
const photoSearch = new PhotoSearch({
    searchInputSelector: '.correct-selector',  // Vérifiez que l'élément existe
    photoGridSelector: '.correct-grid-selector'
});
```

#### 4. Styles cassés
```html
<!-- Assurez-vous d'inclure le CSS -->
<link rel="stylesheet" href="{% static 'css/photo-search.css' %}">

<!-- Et Font Awesome pour les icônes -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
```

#### 5. Problèmes de performance
```javascript
// Augmentez le délai de recherche pour de gros datasets
new PhotoSearch({
    searchDelay: 500,        // Plus de délai
    minSearchLength: 3       // Plus de caractères minimum
});
```

### Debug

```javascript
// Mode debug activé
new PhotoSearch({
    // ... options
    debug: true  // Si vous ajoutez cette option
});

// Vérification manuelle
const photoSearch = new PhotoSearch(options);
console.log('Photos collectées:', photoSearch.allPhotos.length);
console.log('Cameras trouvées:', Array.from(photoSearch.cameraChoices));
```

## 📝 Changelog

### v2.0.0 - Filtres Inline
- ✅ Filtres intégrés dans la barre de recherche
- ✅ Design responsive amélioré
- ✅ Séparation CSS/JavaScript
- ✅ Support multi-instances

### v1.0.0 - Version initiale
- ✅ Recherche en temps réel
- ✅ Filtres dans panneau déroulant
- ✅ Support des cameras et format RAW

## 🤝 Contribution

Pour contribuer au composant PhotoSearch :

1. Respectez la structure modulaire
2. Ajoutez des tests pour les nouvelles fonctionnalités
3. Mettez à jour cette documentation
4. Suivez les conventions de nommage CSS BEM

---

📍 **Dernière mise à jour** : $(date)
🔗 **Support** : Ouvrir une issue sur le repository du projet
