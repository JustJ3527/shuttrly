# PhotoSearch Component

Composant de recherche avancée pour photos avec filtres inline.

## 📚 Documentation

- **[INTEGRATION-GUIDE.md](./INTEGRATION-GUIDE.md)** : Guide complet d'intégration pour vos templates
- **[README-photo-search.md](./README-photo-search.md)** : Documentation technique des styles CSS

## 🚀 Démarrage rapide

```html
<link rel="stylesheet" href="{% static 'css/photo-search.css' %}">
<script src="{% static 'js/photo-search.js' %}"></script>

<div class="photo-search-container">
    <input type="text" class="photo-search-input" placeholder="Rechercher...">
</div>
<div class="photo-grid"><!-- vos photos --></div>

<script>
new PhotoSearch({
    searchInputSelector: '.photo-search-input',
    photoGridSelector: '.photo-grid',
    showFilters: true
});
</script>
```

## Organisation des Styles

### Fichiers
- **`photo-search.css`** : Styles principaux du composant
- **`photo-search.js`** : Logique JavaScript (styles extraits)

### Structure des classes

#### Container principal
- `.photo-search-container` : Container de base
- `.photo-search-container.has-inline-filters` : Container avec filtres inline

#### Champ de recherche
- `.photo-search-input` : Input de recherche
- `.has-inline-filters .photo-search-input` : Input avec filtres
- `.photo-search-container.loading::after` : Spinner de chargement

#### Résultats de recherche
- `.photo-search-results` : Container des résultats
- `.search-result-item` : Élément de résultat individuel
- `.search-result-thumbnail` : Miniature
- `.search-result-info` : Informations textuelles
- `.search-highlight` : Texte surligné

#### Filtres inline
- `.photo-search-filters-inline` : Container des filtres
- `.inline-filter` : Groupe de filtre individuel
- `.filter-checkbox-inline` : Checkbox RAW
- `.filter-label-inline` : Label du checkbox
- `.filter-select-inline` : Select des cameras
- `.btn-clear-filters-inline` : Bouton clear

#### Utilitaires
- `.photo-search-stats` : Statistiques de recherche
- `.search-clear-btn` : Bouton clear général
- `.no-search-results` : Message pas de résultats
- `.search-loading` : État de chargement

## Variables CSS requises

Le composant utilise les variables CSS suivantes (définies dans votre thème) :

```css
--primary-default
--primary-100
--primary-200
--text-default
--text-100
--text-200
--text-300
--text-400
--text-500
--background-default
```

## Responsive Design

### Breakpoints
- **768px** : Passage en mode colonne pour les filtres
- **480px** : Adaptation mobile complète

### Adaptations mobiles
- Filtres passent sous la barre de recherche
- Select cameras devient flexible
- Tailles réduites pour les éléments

## Intégration

### Dans les templates Django
```django
{% load static %}
<link rel="stylesheet" href="{% static 'css/photo-search.css' %}">
```

### Avec le composant JavaScript
```javascript
// Le CSS doit être chargé avant l'initialisation
const photoSearch = new PhotoSearch({
    searchInputSelector: '.photo-search-input',
    photoGridSelector: '.photo-grid',
    showFilters: true
});
```

## Migration depuis les styles inline

Les styles ont été extraits du fichier `photo-search.js` vers ce fichier CSS externe pour :
- Meilleure séparation des responsabilités
- Performance améliorée (pas de styles injectés en JS)
- Facilité de maintenance et personnalisation
- Cache navigateur pour les styles

L'ancienne méthode `setupStyles()` est conservée pour la compatibilité mais ne fait plus rien.
