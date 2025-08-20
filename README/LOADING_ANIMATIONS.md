# 🎨 Animations de Chargement - Effets de Couleur Gris

## 🎯 **Objectif**

Créer des **animations de chargement élégantes** avec des **effets de couleur grise en boucle** pour donner un feedback visuel pendant le chargement des images.

## ✨ **Animations Implémentées**

### **1. Effet Shimmer Principal**

```css
.lazy-image.loading {
  background: linear-gradient(90deg, #f8f9fa 25%, #e9ecef 50%, #f8f9fa 75%);
  background-size: 200% 100%;
  animation: loadingShimmer 1.5s infinite;
}
```

**Résultat** : Effet de vague grise qui se déplace horizontalement en continu

### **2. Effet Pulse avec Overlay**

```css
.lazy-image.loading::before {
  background: linear-gradient(
    90deg,
    rgba(248, 249, 250, 0.8) 0%,
    rgba(233, 236, 239, 0.9) 25%,
    rgba(248, 249, 250, 0.8) 50%,
    rgba(233, 236, 239, 0.9) 75%,
    rgba(248, 249, 250, 0.8) 100%
  );
  animation: loadingPulse 2s ease-in-out infinite;
}
```

**Résultat** : Pulsation douce avec variation d'opacité et de position

### **3. Spinner Rotatif Centré**

```css
.lazy-image.loading::after {
  border: 2px solid #dee2e6;
  border-top: 2px solid #6c757d;
  animation: loadingSpinner 1s linear infinite;
}
```

**Résultat** : Cercle de chargement rotatif au centre de l'image

### **4. Barre de Progression**

```css
.lazy-image.loading::before {
  height: 3px;
  background: linear-gradient(90deg, #6c757d 0%, #adb5bd 50%, #6c757d 100%);
  animation: progressBar 1.5s ease-in-out infinite;
}
```

**Résultat** : Barre de progression animée en bas de l'image

## 🎭 **États Visuels**

### **État Initial (Placeholder)**

- **Couleur** : `#f8f9fa` (gris très clair)
- **Effet** : Gradient subtil avec shimmer
- **Animation** : `placeholderShimmer` en boucle

### **État de Chargement**

- **Couleur** : `#e9ecef` (gris moyen)
- **Effet** : Multiple animations simultanées
- **Filtres** : Grayscale + brightness réduit

### **État Chargé**

- **Couleur** : Transparent (image visible)
- **Effet** : Fade-in avec ombre portée
- **Animation** : `fadeIn` avec scale et translation

## 🔧 **Configuration des Animations**

### **Timing des Animations**

```css
/* Shimmer principal */
animation: loadingShimmer 1.5s infinite;

/* Pulse overlay */
animation: loadingPulse 2s ease-in-out infinite;

/* Spinner rotatif */
animation: loadingSpinner 1s linear infinite;

/* Barre de progression */
animation: progressBar 1.5s ease-in-out infinite;
```

### **Palette de Couleurs Grises**

```css
/* Gris très clair */
--gray-100: #f8f9fa;

/* Gris clair */
--gray-200: #e9ecef;

/* Gris moyen */
--gray-300: #dee2e6;

/* Gris foncé */
--gray-500: #adb5bd;

/* Gris très foncé */
--gray-600: #6c757d;
```

## 📱 **Responsive Design**

### **Mobile (< 768px)**

```css
@media (max-width: 768px) {
  .lazy-image.loading::after {
    width: 16px;
    height: 16px;
    border-width: 1.5px;
  }
}
```

### **Tablette et Desktop**

```css
.lazy-image.loading::after {
  width: 20px;
  height: 20px;
  border-width: 2px;
}
```

## ♿ **Accessibilité**

### **Mode Contraste Élevé**

```css
@media (prefers-contrast: high) {
  .lazy-image.loading {
    background: linear-gradient(90deg, #d1d3d4 25%, #adb5bd 50%, #d1d3d4 75%);
  }
}
```

### **Réduction des Mouvements**

```css
@media (prefers-reduced-motion: reduce) {
  .lazy-image.loading,
  .lazy-image.loading::before,
  .lazy-image.loading::after {
    animation: none;
  }
}
```

## 🎨 **Personnalisation des Couleurs**

### **Changer la Palette de Couleurs**

```css
/* Pour un thème bleu */
.lazy-image.loading {
  background: linear-gradient(90deg, #e3f2fd 25%, #bbdefb 50%, #e3f2fd 75%);
}

/* Pour un thème vert */
.lazy-image.loading {
  background: linear-gradient(90deg, #e8f5e8 25%, #c8e6c9 50%, #e8f5e8 75%);
}

/* Pour un thème sombre */
.lazy-image.loading {
  background: linear-gradient(90deg, #424242 25%, #616161 50%, #424242 75%);
}
```

### **Ajuster la Vitesse**

```css
/* Animation plus rapide */
animation: loadingShimmer 0.8s infinite;

/* Animation plus lente */
animation: loadingShimmer 3s infinite;
```

## 🚀 **Performance et Optimisations**

### **CSS Containment**

```css
.photo-item {
  contain: layout style paint;
}
```

### **Transitions Optimisées**

```css
.lazy-image {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
```

### **Animations GPU**

```css
.lazy-image.loading::after {
  transform: translateZ(0); /* Force GPU acceleration */
}
```

## 🧪 **Test des Animations**

### **Vérifier le Chargement**

1. **Aller sur** `/photos/gallery/`
2. **Observer** les placeholders avec shimmer
3. **Scroller** pour déclencher le lazy loading
4. **Voir** les animations de chargement

### **Console de Debug**

```javascript
// Vérifier les états des images
console.log(
  "Images en cours:",
  document.querySelectorAll(".lazy-image.loading").length
);
console.log(
  "Images chargées:",
  document.querySelectorAll(".lazy-image.loaded").length
);

// Tester une animation manuellement
const img = document.querySelector(".lazy-image");
img.classList.add("loading");
```

## 📊 **Résultats Attendus**

### **Avant le Chargement**

- ✅ Placeholders avec effet shimmer gris
- ✅ Animations fluides et continues
- ✅ Feedback visuel clair

### **Pendant le Chargement**

- ✅ Multiple effets simultanés
- ✅ Spinner rotatif centré
- ✅ Barre de progression animée

### **Après le Chargement**

- ✅ Fade-in élégant
- ✅ Ombre portée subtile
- ✅ Transition fluide vers l'état final

---

_Les animations de chargement sont maintenant visuellement attrayantes et donnent un excellent feedback utilisateur !_ 🎉
