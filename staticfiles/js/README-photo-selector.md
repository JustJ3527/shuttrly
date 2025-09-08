# Photo Selector Module

Un module JavaScript réutilisable pour la sélection de photos avec une interface utilisateur intuitive.

## 🎯 **Fonctionnalités**

- ✅ **Clic direct sur les photos** pour sélectionner/désélectionner
- ✅ **Checkboxes masquées** mais accessibles pour la soumission de formulaire
- ✅ **Support des modes simple et multiple** (radio buttons et checkboxes)
- ✅ **Feedback visuel** pour l'état sélectionné
- ✅ **Navigation clavier** (Entrée et Espace)
- ✅ **Callbacks personnalisables** pour les changements de sélection
- ✅ **API complète** pour contrôler la sélection programmatiquement
- ✅ **Facilement réutilisable** dans d'autres templates

## 📦 **Installation**

### 1. Inclure le script dans votre template

```html
<script src="{% static 'js/photo-selector.js' %}"></script>
```

### 2. Structure HTML requise

```html
<div class="photo-grid-container" id="my-photo-grid">
    <div class="photo-item">
        <img src="photo1.jpg" alt="Photo 1" class="photo-thumbnail">
        <input type="radio" name="selected_photo" value="1">
        <!-- ou -->
        <input type="checkbox" name="selected_photos" value="1">
    </div>
    <!-- Plus de photos... -->
</div>
```

## 🚀 **Utilisation de base**

### Initialisation simple

```javascript
// Sélection simple (une seule photo)
const selector = new PhotoSelector({
    containerSelector: '#my-photo-grid',
    singleSelection: true
});

// Sélection multiple (plusieurs photos)
const selector = new PhotoSelector({
    containerSelector: '#my-photo-grid',
    singleSelection: false
});
```

### Utilisation avec la fonction utilitaire

```javascript
// Plus simple encore
const selector = createPhotoSelector('my-photo-grid', {
    singleSelection: true
});
```

## ⚙️ **Options de configuration**

| Option | Type | Défaut | Description |
|--------|------|--------|-------------|
| `containerSelector` | string | `.photo-grid-container` | Sélecteur CSS du conteneur |
| `photoItemSelector` | string | `.photo-item` | Sélecteur CSS des éléments photo |
| `checkboxSelector` | string | `input[type="radio"], input[type="checkbox"]` | Sélecteur des inputs |
| `selectedClass` | string | `selected` | Classe CSS pour l'état sélectionné |
| `singleSelection` | boolean | `false` | Mode sélection unique ou multiple |
| `onSelectionChange` | function | `null` | Callback appelé lors des changements |

## 🔧 **API et méthodes**

### Méthodes principales

```javascript
const selector = new PhotoSelector({...});

// Obtenir les éléments sélectionnés
const selectedValues = selector.getSelectedItems();        // ['1', '3']
const selectedElements = selector.getSelectedElements();   // [DOMElement, DOMElement]

// Contrôler la sélection
selector.selectByValue(['1', '2']);    // Sélectionner des éléments spécifiques
selector.clearSelection();              // Effacer toute la sélection
selector.selectAll();                   // Sélectionner tout (mode multiple uniquement)

// Gestion du cycle de vie
selector.destroy();                     // Nettoyer et afficher les checkboxes
selector.showCheckboxes();              // Afficher les checkboxes (debug)
selector.hideCheckboxes();              // Masquer les checkboxes
```

### Exemple d'utilisation complète

```javascript
const photoSelector = new PhotoSelector({
    containerSelector: '#gallery',
    singleSelection: false,
    selectedClass: 'photo-selected',
    onSelectionChange: (selectedItems) => {
        console.log('Photos sélectionnées:', selectedItems);
        
        // Mettre à jour un champ caché
        const hiddenField = document.querySelector('input[name="photo_ids"]');
        if (hiddenField) {
            hiddenField.value = selectedItems.join(',');
        }
        
        // Mettre à jour l'interface
        updateSelectionCount(selectedItems.length);
    }
});

// Utiliser les méthodes
document.getElementById('select-all').onclick = () => photoSelector.selectAll();
document.getElementById('clear-all').onclick = () => photoSelector.clearSelection();
```

## 🎨 **Personnalisation CSS**

### Classes CSS importantes

```css
.photo-grid-container {
    /* Grille compacte style Apple */
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 0.5rem;  /* Espacement réduit */
}

.photo-item {
    /* État normal - pas de bordures, design carré */
    border: none;
    border-radius: 0;
    transition: all 0.3s ease;
}

.photo-item:hover {
    /* État survol - ombre légère */
    transform: scale(1.02);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.photo-item.selected {
    /* État sélectionné - overlay complet + checkbox visible */
    border: none;
    box-shadow: none;
    transform: scale(1.02);
}

.photo-item.selected::before {
    /* Overlay sombre complet sur toute la photo */
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.3);
    z-index: 5;
    pointer-events: none;
}

.photo-item.selected::after {
    /* Checkbox visible bleue avec checkmark */
    content: '✓';
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    width: 24px;
    height: 24px;
    background: #007aff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 14px;
    font-weight: bold;
    z-index: 10;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}
```

## 🔄 **Intégration avec Django**

### Dans votre template Django

```html
{% for photo in photos %}
<div class="photo-item" data-photo-id="{{ photo.id }}">
    <img src="{{ photo.thumbnail.url }}" alt="{{ photo.title }}" class="photo-thumbnail">
    <input type="checkbox" name="selected_photos" value="{{ photo.id }}" style="display: none;">
</div>
{% endfor %}

<script>
document.addEventListener('DOMContentLoaded', function() {
    const selector = new PhotoSelector({
        containerSelector: '#photo-gallery',
        singleSelection: false,
        onSelectionChange: (selectedItems) => {
            // Mettre à jour le champ caché pour la soumission du formulaire
            document.querySelector('input[name="photo_ids"]').value = selectedItems.join(',');
        }
    });
});
</script>
```

### Dans votre vue Django

```python
def create_post(request):
    if request.method == 'POST':
        photo_ids = request.POST.get('photo_ids', '').split(',')
        photo_ids = [int(id) for id in photo_ids if id.isdigit()]
        
        # Créer le post avec les photos sélectionnées
        post = Post.objects.create(
            author=request.user,
            title=request.POST.get('title'),
            description=request.POST.get('description')
        )
        
        # Ajouter les photos sélectionnées
        for photo_id in photo_ids:
            PostPhoto.objects.create(post=post, photo_id=photo_id)
```

## 🧪 **Exemples d'utilisation avancée**

### Gestion des erreurs

```javascript
const selector = new PhotoSelector({
    containerSelector: '#gallery',
    onSelectionChange: (selectedItems) => {
        if (selectedItems.length === 0) {
            showError('Veuillez sélectionner au moins une photo');
            return;
        }
        
        if (selectedItems.length > 10) {
            showError('Maximum 10 photos autorisées');
            selector.clearSelection();
            return;
        }
        
        hideError();
        updateForm(selectedItems);
    }
});
```

### Intégration avec d'autres composants

```javascript
// Intégration avec un composant de recherche
const searchComponent = new PhotoSearch('#search-input');
const photoSelector = new PhotoSelector({
    containerSelector: '#gallery',
    onSelectionChange: (selectedItems) => {
        searchComponent.updateSelectedCount(selectedItems.length);
    }
});

// Intégration avec un composant de pagination
const pagination = new PhotoPagination('#pagination');
photoSelector.onSelectionChange = (selectedItems) => {
    pagination.updateSelectionInfo(selectedItems);
};
```

## 🐛 **Dépannage**

### Problèmes courants

1. **Les photos ne sont pas cliquables**
   - Vérifiez que le `containerSelector` correspond à votre HTML
   - Assurez-vous que les éléments ont la classe `photo-item`

2. **Les checkboxes sont visibles**
   - Le module les masque automatiquement
   - Utilisez `selector.hideCheckboxes()` si nécessaire

3. **La sélection ne fonctionne pas**
   - Vérifiez que les inputs ont des `name` et `value` valides
   - Assurez-vous que le mode `singleSelection` correspond à vos inputs

### Mode debug

```javascript
// Afficher les checkboxes pour le débogage
selector.showCheckboxes();

// Vérifier l'état
console.log('Sélection actuelle:', selector.getSelectedItems());
console.log('Éléments sélectionnés:', selector.getSelectedElements());
```

## 📚 **Référence complète**

### Événements

- `onSelectionChange(selectedItems)` - Appelé à chaque changement de sélection

### Propriétés

- `options` - Configuration actuelle
- `selectedItems` - Set des éléments sélectionnés
- `container` - Référence au conteneur DOM

### Méthodes utilitaires

- `createPhotoSelector(id, options)` - Créer un sélecteur par ID
- `initializePhotoSelectors()` - Initialiser tous les sélecteurs par défaut

## 🤝 **Contribution**

Ce module est conçu pour être facilement extensible. N'hésitez pas à :

- Ajouter de nouvelles fonctionnalités
- Améliorer la documentation
- Signaler des bugs
- Proposer des améliorations

## 📄 **Licence**

Ce module fait partie du projet Shuttrly et suit les mêmes conditions d'utilisation.
