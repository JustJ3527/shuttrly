/**
 * Photo Statistics JavaScript
 * Handles photo statistics display and Chart.js integration
 */

class PhotoStats {
    constructor() {
        this.charts = {};
        this.chartData = {};
        
        this.init();
    }
    
    init() {
        this.initializeCharts();
        this.setupInteractiveElements();
        this.setupResponsiveCharts();
        this.animateProgressBars();
    }
    
    initializeCharts() {
        // Initialize trend chart (line chart)
        this.initTrendChart();
        
        // Initialize format distribution chart (doughnut chart)
        this.initFormatChart();
        
        // Initialize camera usage chart (bar chart)
        this.initCameraChart();
        
        // Initialize lens usage chart (bar chart)
        this.initLensChart();
        
        // Initialize ISO usage chart (bar chart)
        this.initISOChart();
        
        // Initialize aperture usage chart (bar chart)
        this.initApertureChart();
    }
    
    initTrendChart() {
        const trendCtx = document.getElementById('trend-chart');
        if (!trendCtx) return;
        
        // Get data from template
        const monthlyData = this.getMonthlyData();
        
        if (monthlyData.labels.length === 0) {
            this.showNoDataMessage(trendCtx, 'No upload data available');
            return;
        }
        
        this.charts.trend = new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: monthlyData.labels,
                datasets: [{
                    label: 'Photos Uploaded',
                    data: monthlyData.data,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#667eea',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#667eea',
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        ticks: {
                            color: '#666',
                            font: {
                                size: 12
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        ticks: {
                            color: '#666',
                            font: {
                                size: 12
                            },
                            stepSize: 1
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }
    
    initFormatChart() {
        const formatCtx = document.getElementById('format-chart');
        if (!formatCtx) return;
        
        const formatData = this.getFormatData();
        
        if (formatData.length === 0) {
            this.showNoDataMessage(formatCtx, 'No format data available');
            return;
        }
        
        this.charts.format = new Chart(formatCtx, {
            type: 'doughnut',
            data: {
                labels: formatData.map(item => item.label),
                datasets: [{
                    data: formatData.map(item => item.value),
                    backgroundColor: [
                        '#667eea',
                        '#764ba2',
                        '#f093fb',
                        '#f5576c',
                        '#4facfe',
                        '#00f2fe',
                        '#43e97b',
                        '#38f9d7',
                        '#fa709a',
                        '#fee140'
                    ],
                    borderWidth: 0,
                    hoverBorderWidth: 2,
                    hoverBorderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: {
                                size: 12
                            },
                            color: '#666'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#667eea',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                cutout: '60%',
                animation: {
                    animateRotate: true,
                    animateScale: true
                }
            }
        });
    }
    
    initCameraChart() {
        const cameraCtx = document.getElementById('camera-chart');
        if (!cameraCtx) return;
        
        const cameraData = this.getCameraData();
        
        if (cameraData.length === 0) {
            this.showNoDataMessage(cameraCtx, 'No camera data available');
            return;
        }
        
        this.charts.camera = new Chart(cameraCtx, {
            type: 'bar',
            data: {
                labels: cameraData.map(item => item.label),
                datasets: [{
                    label: 'Photos',
                    data: cameraData.map(item => item.value),
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: '#667eea',
                    borderWidth: 1,
                    borderRadius: 4,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#667eea',
                        borderWidth: 1,
                        cornerRadius: 8
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#666',
                            font: {
                                size: 11
                            },
                            maxRotation: 45
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        ticks: {
                            color: '#666',
                            font: {
                                size: 12
                            },
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
    
    initLensChart() {
        const lensCtx = document.getElementById('lens-chart');
        if (!lensCtx) return;
        
        const lensData = this.getLensData();
        
        if (lensData.length === 0) {
            this.showNoDataMessage(lensCtx, 'No lens data available');
            return;
        }
        
        this.charts.lens = new Chart(lensCtx, {
            type: 'bar',
            data: {
                labels: lensData.map(item => item.label),
                datasets: [{
                    label: 'Photos',
                    data: lensData.map(item => item.value),
                    backgroundColor: 'rgba(118, 75, 162, 0.8)',
                    borderColor: '#764ba2',
                    borderWidth: 1,
                    borderRadius: 4,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#764ba2',
                        borderWidth: 1,
                        cornerRadius: 8
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#666',
                            font: {
                                size: 11
                            },
                            maxRotation: 45
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        ticks: {
                            color: '#666',
                            font: {
                                size: 12
                            },
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
    
    initISOChart() {
        const isoCtx = document.getElementById('iso-chart');
        if (!isoCtx) return;
        
        const isoData = this.getISOData();
        
        if (isoData.length === 0) {
            this.showNoDataMessage(isoCtx, 'No ISO data available');
            return;
        }
        
        this.charts.iso = new Chart(isoCtx, {
            type: 'bar',
            data: {
                labels: isoData.map(item => item.label),
                datasets: [{
                    label: 'Photos',
                    data: isoData.map(item => item.value),
                    backgroundColor: 'rgba(255, 193, 7, 0.8)',
                    borderColor: '#ffc107',
                    borderWidth: 1,
                    borderRadius: 4,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#ffc107',
                        borderWidth: 1,
                        cornerRadius: 8
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#666',
                            font: {
                                size: 11
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        ticks: {
                            color: '#666',
                            font: {
                                size: 12
                            },
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
    
    initApertureChart() {
        const apertureCtx = document.getElementById('aperture-chart');
        if (!apertureCtx) return;
        
        const apertureData = this.getApertureData();
        
        if (apertureData.length === 0) {
            this.showNoDataMessage(apertureCtx, 'No aperture data available');
            return;
        }
        
        this.charts.aperture = new Chart(apertureCtx, {
            type: 'bar',
            data: {
                labels: apertureData.map(item => item.label),
                datasets: [{
                    label: 'Photos',
                    data: apertureData.map(item => item.value),
                    backgroundColor: 'rgba(255, 140, 0, 0.8)',
                    borderColor: '#ff8c00',
                    borderWidth: 1,
                    borderRadius: 4,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#ff8c00',
                        borderWidth: 1,
                        cornerRadius: 8
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#666',
                            font: {
                                size: 11
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        ticks: {
                            color: '#666',
                            font: {
                                size: 12
                            },
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
    
    showNoDataMessage(container, message) {
        container.innerHTML = `
            <div class="no-data">
                <i class="fas fa-chart-bar"></i>
                <p>${message}</p>
            </div>
        `;
    }
    
    getMonthlyData() {
        // This would typically come from the Django template
        // For now, we'll create sample data
        const monthlyStats = window.monthlyStats || [];
        
        if (monthlyStats.length === 0) {
            return { labels: [], data: [] };
        }
        
        return {
            labels: monthlyStats.map(item => item.month),
            data: monthlyStats.map(item => item.count)
        };
    }
    
    getFormatData() {
        // This would typically come from the Django template
        // For now, we'll create sample data
        const totalPhotos = parseInt(document.querySelector('[data-total-photos]')?.dataset.totalPhotos) || 0;
        const rawPhotos = parseInt(document.querySelector('[data-raw-photos]')?.dataset.rawPhotos) || 0;
        
        if (totalPhotos === 0) return [];
        
        const processedPhotos = totalPhotos - rawPhotos;
        
        return [
            { label: 'RAW', value: rawPhotos },
            { label: 'Processed', value: processedPhotos }
        ];
    }
    
    getCameraData() {
        // This would typically come from the Django template
        const cameraStats = window.cameraStats || [];
        
        return cameraStats.map(item => ({
            label: `${item.camera_make || 'Unknown'} ${item.camera_model || ''}`.trim() || 'Unknown',
            value: item.count
        }));
    }
    
    getLensData() {
        // This would typically come from the Django template
        const lensStats = window.lensStats || [];
        
        return lensStats.map(item => ({
            label: item.lens_model || 'Unknown',
            value: item.count
        }));
    }
    
    getISOData() {
        // This would typically come from the Django template
        const isoStats = window.isoStats || [];
        
        return isoStats.map(item => ({
            label: `ISO ${item.iso}`,
            value: item.count
        }));
    }
    
    getApertureData() {
        // This would typically come from the Django template
        const apertureStats = window.apertureStats || [];
        
        return apertureStats.map(item => ({
            label: `f/${item.aperture}`,
            value: item.count
        }));
    }
    
    setupInteractiveElements() {
        // Add click handlers for stat cards
        document.querySelectorAll('.stat-card').forEach(card => {
            card.addEventListener('click', () => {
                this.highlightStatCard(card);
            });
        });
        
        // Add hover effects for progress bars
        this.setupProgressBarHover();
        
        // Add export functionality
        this.setupExportButtons();
    }
    
    highlightStatCard(card) {
        // Remove highlight from other cards
        document.querySelectorAll('.stat-card').forEach(c => {
            c.classList.remove('highlighted');
        });
        
        // Add highlight to clicked card
        card.classList.add('highlighted');
        
        // Auto-remove highlight after 2 seconds
        setTimeout(() => {
            card.classList.remove('highlighted');
        }, 2000);
    }
    
    setupProgressBarHover() {
        document.querySelectorAll('.camera-bar, .lens-bar, .iso-bar, .aperture-bar').forEach(bar => {
            bar.addEventListener('mouseenter', () => {
                bar.style.transform = 'scaleY(1.2)';
                bar.style.transition = 'transform 0.3s ease';
            });
            
            bar.addEventListener('mouseleave', () => {
                bar.style.transform = 'scaleY(1)';
            });
        });
    }
    
    setupExportButtons() {
        // Add export button to each chart container
        Object.keys(this.charts).forEach(chartName => {
            const chartContainer = this.charts[chartName].canvas.parentElement;
            const exportButton = document.createElement('button');
            exportButton.className = 'btn btn-sm btn-outline-secondary export-chart-btn';
            exportButton.innerHTML = '<i class="fas fa-download"></i> Export';
            exportButton.style.cssText = 'position: absolute; top: 10px; right: 10px; z-index: 10;';
            
            exportButton.addEventListener('click', () => {
                this.exportChart(chartName);
            });
            
            chartContainer.style.position = 'relative';
            chartContainer.appendChild(exportButton);
        });
    }
    
    exportChart(chartName) {
        const chart = this.charts[chartName];
        if (!chart) return;
        
        const canvas = chart.canvas;
        const link = document.createElement('a');
        link.download = `${chartName}-chart.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();
    }
    
    setupResponsiveCharts() {
        // Handle window resize
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.resizeCharts();
            }, 250);
        });
    }
    
    resizeCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.resize) {
                chart.resize();
            }
        });
    }
    
    animateProgressBars() {
        // Animate progress bars on scroll
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const progressBar = entry.target;
                    const fill = progressBar.querySelector('.camera-bar-fill, .lens-bar-fill, .iso-bar-fill, .aperture-bar-fill');
                    if (fill) {
                        const percentage = progressBar.dataset.percentage || '0';
                        fill.style.setProperty('--final-width', `${percentage}%`);
                        fill.style.width = `${percentage}%`;
                    }
                }
            });
        }, { threshold: 0.5 });
        
        // Observe all progress bars
        document.querySelectorAll('.camera-bar, .lens-bar, .iso-bar, .aperture-bar').forEach(bar => {
            observer.observe(bar);
        });
    }
    
    // Utility methods
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }
    
    animateValue(element, start, end, duration) {
        const startTime = performance.now();
        const startValue = start;
        const change = end - start;
        
        function updateValue(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const currentValue = startValue + (change * progress);
            element.textContent = Math.round(currentValue);
            
            if (progress < 1) {
                requestAnimationFrame(updateValue);
            }
        }
        
        requestAnimationFrame(updateValue);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize photo stats
    window.photoStats = new PhotoStats();
    
    // Animate stat numbers
    animateStatNumbers();
    
    // Setup additional interactions
    setupAdditionalInteractions();
});

// Animate stat numbers on page load
function animateStatNumbers() {
    const statNumbers = document.querySelectorAll('.stat-number');
    
    statNumbers.forEach(statNumber => {
        const finalValue = parseInt(statNumber.textContent);
        if (!isNaN(finalValue)) {
            statNumber.textContent = '0';
            window.photoStats.animateValue(statNumber, 0, finalValue, 1500);
        }
    });
}

// Setup additional interactions
function setupAdditionalInteractions() {
    // Add loading states to stat cards
    document.querySelectorAll('.stat-card').forEach(card => {
        card.addEventListener('click', () => {
            card.classList.add('loading');
            setTimeout(() => {
                card.classList.remove('loading');
            }, 1000);
        });
    });
    
    // Add keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
            document.querySelectorAll('.stat-card').forEach(card => {
                card.style.outline = '2px solid #667eea';
            });
        }
    });
    
    // Add print functionality
    const printButton = document.createElement('button');
    printButton.className = 'btn btn-outline-primary print-stats-btn';
    printButton.innerHTML = '<i class="fas fa-print"></i> Print Stats';
    printButton.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 1000;';
    
    printButton.addEventListener('click', () => {
        window.print();
    });
    
    document.body.appendChild(printButton);
}

// Export class for global access
window.PhotoStats = PhotoStats;
