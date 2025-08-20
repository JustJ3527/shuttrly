/**
 * Animation Demo Script
 * Permet de tester manuellement les animations de chargement
 */

class AnimationDemo {
    constructor() {
        this.demoContainer = null;
        this.init();
    }

    init() {
        this.createDemoContainer();
        this.createDemoImages();
        this.addDemoControls();
        console.log('Animation Demo initialized! 🎨');
    }

    createDemoContainer() {
        // Créer un conteneur de démonstration
        this.demoContainer = document.createElement('div');
        this.demoContainer.className = 'animation-demo-container';
        this.demoContainer.innerHTML = `
            <div class="demo-header">
                <h3>🎨 Démonstration des Animations de Chargement</h3>
                <p>Testez les différents états des images</p>
            </div>
            <div class="demo-controls">
                <button class="btn btn-primary" id="demo-placeholder">Placeholder</button>
                <button class="btn btn-warning" id="demo-loading">Chargement</button>
                <button class="btn btn-success" id="demo-loaded">Chargé</button>
                <button class="btn btn-info" id="demo-cycle">Cycle Complet</button>
                <button class="btn btn-secondary" id="demo-reset">Reset</button>
            </div>
            <div class="demo-grid" id="demo-grid"></div>
        `;

        // Ajouter au début de la page
        const galleryContainer = document.querySelector('.gallery-container');
        if (galleryContainer) {
            galleryContainer.parentNode.insertBefore(this.demoContainer, galleryContainer);
        }
    }

    createDemoImages() {
        const demoGrid = document.getElementById('demo-grid');
        if (!demoGrid) return;

        // Créer 6 images de démonstration
        for (let i = 1; i <= 6; i++) {
            const demoItem = document.createElement('div');
            demoItem.className = 'demo-photo-item';
            demoItem.innerHTML = `
                <div class="photo-wrapper">
                    <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 300'%3E%3Crect width='300' height='300' fill='%23f0f0f0'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%23999' font-size='14'%3EDemo ${i}%3C/text%3E%3C/svg%3E" 
                         class="photo-image lazy-image demo-image"
                         data-src="https://picsum.photos/300/300?random=${i}"
                         alt="Demo Image ${i}">
                    
                    <div class="photo-overlay">
                        <div class="overlay-header">
                            <div class="exposure-info">
                                <div class="exposure-item">
                                    <span class="label">ISO</span>
                                    <span class="value">100</span>
                                </div>
                                <div class="exposure-item">
                                    <span class="label">Shutter</span>
                                    <span class="value">1/100</span>
                                </div>
                                <div class="exposure-item">
                                    <span class="label">Aperture</span>
                                    <span class="value">f/2.8</span>
                                </div>
                            </div>
                        </div>
                        <div class="overlay-footer">
                            <div class="photo-info">
                                <div class="photo-actions">
                                    <button class="btn btn-sm btn-outline-light">
                                        <i class="fas fa-eye"></i>
                                    </button>
                                    <button class="btn btn-sm btn-outline-light">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="btn btn-sm btn-outline-light">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            demoGrid.appendChild(demoItem);
        }
    }

    addDemoControls() {
        // Placeholder state
        document.getElementById('demo-placeholder').addEventListener('click', () => {
            this.setDemoState('placeholder');
        });

        // Loading state
        document.getElementById('demo-loading').addEventListener('click', () => {
            this.setDemoState('loading');
        });

        // Loaded state
        document.getElementById('demo-loaded').addEventListener('click', () => {
            this.setDemoState('loaded');
        });

        // Cycle complet
        document.getElementById('demo-cycle').addEventListener('click', () => {
            this.runDemoCycle();
        });

        // Reset
        document.getElementById('demo-reset').addEventListener('click', () => {
            this.resetDemo();
        });
    }

    setDemoState(state) {
        const demoImages = document.querySelectorAll('.demo-image');
        
        demoImages.forEach((img, index) => {
            // Retirer toutes les classes d'état
            img.classList.remove('loading', 'loaded');
            
            // Appliquer l'état demandé
            switch (state) {
                case 'placeholder':
                    // État initial - rien à faire
                    break;
                    
                case 'loading':
                    img.classList.add('loading');
                    break;
                    
                case 'loaded':
                    img.classList.add('loaded');
                    // Simuler une vraie image
                    setTimeout(() => {
                        img.src = img.getAttribute('data-src');
                    }, 100);
                    break;
            }
        });

        console.log(`Demo state set to: ${state}`);
    }

    async runDemoCycle() {
        console.log('Starting demo cycle... 🔄');
        
        const demoImages = document.querySelectorAll('.demo-image');
        
        for (let i = 0; i < demoImages.length; i++) {
            const img = demoImages[i];
            
            // 1. Placeholder
            img.classList.remove('loading', 'loaded');
            await this.delay(500);
            
            // 2. Loading
            img.classList.add('loading');
            await this.delay(2000);
            
            // 3. Loaded
            img.classList.remove('loading');
            img.classList.add('loaded');
            img.src = img.getAttribute('data-src');
            await this.delay(1000);
        }
        
        console.log('Demo cycle completed! ✅');
    }

    resetDemo() {
        const demoImages = document.querySelectorAll('.demo-image');
        
        demoImages.forEach(img => {
            img.classList.remove('loading', 'loaded');
            img.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 300'%3E%3Crect width='300' height='300' fill='%23f0f0f0'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%23999' font-size='14'%3EDemo%3C/text%3E%3C/svg%3E";
        });
        
        console.log('Demo reset! 🔄');
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Initialiser la démo quand le DOM est chargé
document.addEventListener('DOMContentLoaded', function() {
    // Attendre que la galerie soit chargée
    setTimeout(() => {
        if (document.querySelector('.gallery-container')) {
            new AnimationDemo();
        }
    }, 1000);
});

// Export pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AnimationDemo;
}
