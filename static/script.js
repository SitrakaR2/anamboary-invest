document.addEventListener('DOMContentLoaded', function() {
    // ====== INVESTISSEMENT AVEC FETCH ======
    const investForm = document.querySelector('form[action="/invest"]');
    if (investForm) {
        investForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const amountInput = document.getElementById('amount');
            const amount = amountInput.value;
            const button = this.querySelector('button[type="submit"]');
            const originalText = button.innerHTML;

            // Validation côté client
            if (!amount || amount <= 0) {
                showAlert('Veuillez entrer un montant valide.', 'error');
                return;
            }

            try {
                // Désactiver le bouton pendant la requête
                button.disabled = true;
                button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Investissement en cours...';

                const response = await fetch('/invest', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: new URLSearchParams({ amount })
                });

                const data = await response.json();

                if (data.success) {
                    showAlert(data.message, 'success');
                    
                    // Mettre à jour le solde affiché
                    const balanceElement = document.querySelector('.display-6');
                    if (balanceElement && data.new_balance !== undefined) {
                        balanceElement.textContent = data.new_balance + ' Ar';
                    }
                    
                    // Réinitialiser le formulaire
                    amountInput.value = '';
                    
                    // Recharger la page après 2 secondes pour voir les nouvelles données
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                    
                } else {
                    showAlert(data.message, 'error');
                }
            } catch (error) {
                console.error('Erreur:', error);
                showAlert('Erreur de connexion. Veuillez réessayer.', 'error');
            } finally {
                // Réactiver le bouton
                button.disabled = false;
                button.innerHTML = originalText;
            }
        });
    }

    // ====== GESTION DES ALERTS PERSONNALISÉES ======
    function showAlert(message, type = 'info') {
        // Créer l'alert personnalisée
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'error' ? 'danger' : 'success'} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Ajouter l'alert en haut de la page
        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
            
            // Auto-supprimer après 5 secondes
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    const bsAlert = bootstrap.Alert.getOrCreateInstance(alertDiv);
                    bsAlert.close();
                }
            }, 5000);
        }
    }

    // ====== ANIMATION DES CARDS AU SCROLL ======
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, observerOptions);

    // Observer les cards pour l'animation
    document.querySelectorAll('.card-custom').forEach(card => {
        observer.observe(card);
    });

    // ====== GESTION DES FORMULAIRES AVEC CONFIRMATION ======
    const depositForm = document.querySelector('form[action="/depot"]');
    const withdrawalForm = document.querySelector('form[action="/retrait"]');

    if (depositForm) {
        depositForm.addEventListener('submit', function(e) {
            const amount = this.querySelector('input[name="amount"]').value;
            if (amount && !confirm(`Confirmez-vous le dépôt de ${amount} Ar ?`)) {
                e.preventDefault();
            } else {
                // Afficher loader
                const button = this.querySelector('button[type="submit"]');
                const originalText = button.innerHTML;
                button.disabled = true;
                button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Traitement en cours...';
            }
        });
    }

    if (withdrawalForm) {
        withdrawalForm.addEventListener('submit', function(e) {
            const amount = this.querySelector('input[name="amount"]').value;
            if (amount && !confirm(`Confirmez-vous le retrait de ${amount} Ar ?`)) {
                e.preventDefault();
            } else {
                // Afficher loader
                const button = this.querySelector('button[type="submit"]');
                const originalText = button.innerHTML;
                button.disabled = true;
                button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Traitement en cours...';
            }
        });
    }

    // ====== ANIMATION DES STATS ======
    function animateStats() {
        const stats = document.querySelectorAll('.floating h3');
        stats.forEach((stat, index) => {
            const originalText = stat.textContent;
            let current = 0;
            const target = parseInt(originalText.replace(/[^0-9]/g, ''));
            const duration = 2000;
            const increment = target / (duration / 16);
            
            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    current = target;
                    clearInterval(timer);
                }
                stat.textContent = Math.floor(current) + (originalText.includes('%') ? '%' : '');
            }, 16);
        });
    }

    // Lancer l'animation des stats si on est sur la page d'accueil
    if (document.querySelector('.hero')) {
        setTimeout(animateStats, 1000);
    }

    // ====== GESTION DES MESSAGES FLASH AUTO-DISPARITION ======
    const autoDismissAlerts = document.querySelectorAll('.alert');
    autoDismissAlerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                bsAlert.close();
            }
        }, 5000);
    });

    // ====== AMÉLIORATION DE L'EXPÉRIENCE UTILISATEUR ======
    
    // Validation en temps réel des montants
    const amountInputs = document.querySelectorAll('input[type="number"][name="amount"]');
    amountInputs.forEach(input => {
        input.addEventListener('input', function() {
            const value = parseFloat(this.value);
            const max = parseFloat(this.max);
            
            if (value > max) {
                this.value = max;
                showAlert(`Le montant maximum est de ${max} Ar`, 'error');
            }
            
            if (value < 0) {
                this.value = '';
            }
        });
    });

    // Effet de focus amélioré pour les inputs
    const formInputs = document.querySelectorAll('.form-control');
    formInputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            if (!this.value) {
                this.parentElement.classList.remove('focused');
            }
        });
    });

    // ====== ANIMATION DE PROGRESSION POUR LES INVESTISSEMENTS ======
    function updateInvestmentProgress() {
        const investments = document.querySelectorAll('.investment-progress');
        investments.forEach(progressBar => {
            const percentage = progressBar.getAttribute('data-progress');
            progressBar.style.width = percentage + '%';
        });
    }

    // Initialiser les progress bars
    updateInvestmentProgress();

    // ====== GESTION DES ERREURS RÉSEAU ======
    window.addEventListener('online', function() {
        showAlert('Connexion rétablie', 'success');
    });

    window.addEventListener('offline', function() {
        showAlert('Connexion perdue. Vérifiez votre connexion internet.', 'error');
    });

    // ====== COPIER LES RÉFÉRENCES DE TRANSACTION ======
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('copy-reference')) {
            const reference = e.target.getAttribute('data-reference');
            navigator.clipboard.writeText(reference).then(() => {
                showAlert('Référence copiée !', 'success');
            });
        }
    });

    console.log('🚀 Anamboary Invest - JavaScript initialisé');
});

// ====== FONCTIONS GLOBALES ======
function formatCurrency(amount) {
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'MGA'
    }).format(amount);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}