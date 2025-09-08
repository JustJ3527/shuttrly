/**
 * Step Validation Script
 * Le bouton Next reste toujours actif, mais affiche les erreurs de validation
 * et surligne les champs manquants si l'utilisateur tente de passer à l'étape suivante
 * sans avoir rempli tous les champs requis
 */

// Check if StepValidator is already defined to prevent redeclaration errors
if (typeof StepValidator === 'undefined') {
    class StepValidator {
        constructor() {
            this.init();
        }
        
        /**
         * Initialise la validation des étapes
         */
        init() {
            document.addEventListener('DOMContentLoaded', () => {
                this.setupStepValidation();
                this.startStepMonitoring();
            });
        }
        
        /**
         * Démarre la surveillance des changements d'étape
         */
        startStepMonitoring() {
            setInterval(() => {
                this.checkForStepChanges();
            }, 1000);
        }
        
        /**
         * Vérifie s'il y a eu des changements d'étape
         */
        checkForStepChanges() {
            const forms = document.querySelectorAll('#registration-form, #login-form, #test-form');
            forms.forEach(form => {
                if (form) {
                    const currentStep = this.getCurrentStep(form);
                    if (form.dataset.lastStep !== currentStep) {
                        form.dataset.lastStep = currentStep;
                        this.refreshValidationForForm(form);
                    }
                }
            });
        }
        
        /**
         * Rafraîchit la validation pour un formulaire
         */
        refreshValidationForForm(form) {
            const nextButton = form.querySelector('button[type="submit"]:not([name="previous"])');
            if (nextButton) {
                const requiredFields = this.getRequiredFieldsForCurrentStep(form);
                this.updateValidationStatus(form, requiredFields);
            }
        }
        
        /**
         * Configure la validation pour l'étape actuelle
         */
        setupStepValidation() {
            const registrationForm = document.getElementById('registration-form');
            if (registrationForm) {
                this.setupRegistrationValidation(registrationForm);
            }
            
            const loginForm = document.getElementById('login-form');
            if (loginForm) {
                this.setupLoginValidation(loginForm);
            }
            
            const testForm = document.getElementById('test-form');
            if (testForm) {
                this.setupTestFormValidation(testForm);
            }
        }
        
        /**
         * Configure la validation pour le formulaire de test
         */
        setupTestFormValidation(form) {
            const nextButton = form.querySelector('button[type="submit"]');
            if (!nextButton) return;
            
            const requiredFields = this.getRequiredFieldsForCurrentStep(form);
            this.addEventListenersToForm(form, nextButton, requiredFields);
            
            form.addEventListener('submit', (e) => {
                this.handleFormSubmission(e, form, nextButton, requiredFields);
            });
            
            this.updateValidationStatus(form, requiredFields);
            form.dataset.lastStep = this.getCurrentStep(form);
        }
        
        /**
         * Configure la validation pour le formulaire d'inscription
         */
        setupRegistrationValidation(form) {
            const nextButton = form.querySelector('button[type="submit"]:not([name="previous"])');
            if (!nextButton) return;
            
            const requiredFields = this.getRequiredFieldsForCurrentStep(form);
            this.addEventListenersToForm(form, nextButton, requiredFields);
            
            form.addEventListener('submit', (e) => {
                this.handleFormSubmission(e, form, nextButton, requiredFields);
            });
            
            this.updateValidationStatus(form, requiredFields);
            form.dataset.lastStep = this.getCurrentStep(form);
        }
        
        /**
         * Configure la validation pour le formulaire de connexion
         */
        setupLoginValidation(form) {
            const nextButton = form.querySelector('button[type="submit"]:not([name="previous"])');
            if (!nextButton) return;
            
            const requiredFields = this.getRequiredFieldsForCurrentStep(form);
            this.addEventListenersToForm(form, nextButton, requiredFields);
            
            form.addEventListener('submit', (e) => {
                this.handleFormSubmission(e, form, nextButton, requiredFields);
            });
            
            this.updateValidationStatus(form, requiredFields);
            form.dataset.lastStep = this.getCurrentStep(form);
        }
        
        /**
         * Ajoute les écouteurs d'événements à un formulaire
         */
        addEventListenersToForm(form, nextButton, requiredFields) {
            const allFields = form.querySelectorAll('input, select, textarea');
            allFields.forEach(field => {
                field.addEventListener('input', () => {
                    const currentRequiredFields = this.getRequiredFieldsForCurrentStep(form);
                    this.updateValidationStatus(form, currentRequiredFields);
                });
                field.addEventListener('change', () => {
                    const currentRequiredFields = this.getRequiredFieldsForCurrentStep(form);
                    this.updateValidationStatus(form, currentRequiredFields);
                });
                field.addEventListener('blur', () => {
                    const currentRequiredFields = this.getRequiredFieldsForCurrentStep(form);
                    this.updateValidationStatus(form, currentRequiredFields);
                });
            });
        }
        
        /**
         * Gère la soumission du formulaire
         */
        handleFormSubmission(e, form, nextButton, requiredFields) {
            const currentRequiredFields = this.getRequiredFieldsForCurrentStep(form);
            const isValid = this.areAllRequiredFieldsFilled(currentRequiredFields);
            
            if (!isValid) {
                e.preventDefault();
                this.highlightMissingFields(currentRequiredFields);
                this.scrollToFirstMissingField(currentRequiredFields);
            }
        }
        
        /**
         * Surligne les champs manquants
         */
        highlightMissingFields(requiredFields) {
            requiredFields.forEach(field => {
                if (!this.isFieldValid(field)) {
                    this.addFieldError(field);
                } else {
                    this.removeFieldError(field);
                }
            });
        }
        
        /**
         * Ajoute l'état d'erreur à un champ
         */
        addFieldError(field) {
            field.classList.add('field-error');
            field.classList.remove('field-valid');
        }
        
        /**
         * Supprime l'état d'erreur d'un champ
         */
        removeFieldError(field) {
            field.classList.remove('field-error');
            field.classList.remove('field-valid');
        }
        
        /**
         * Fait défiler vers le premier champ manquant
         */
        scrollToFirstMissingField(requiredFields) {
            const firstMissingField = requiredFields.find(field => !this.isFieldValid(field));
            if (firstMissingField) {
                firstMissingField.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center' 
                });
                
                setTimeout(() => {
                    firstMissingField.focus();
                }, 500);
            }
        }
        
        /**
         * Met à jour le statut de validation (sans désactiver le bouton)
         */
        updateValidationStatus(form, requiredFields) {
            const isValid = this.areAllRequiredFieldsFilled(requiredFields);
            
            // Mettre à jour l'apparence des champs selon leur validité
            requiredFields.forEach(field => {
                if (this.isFieldValid(field)) {
                    this.removeFieldError(field);
                    field.classList.add('field-valid');
                } else {
                    this.removeFieldError(field);
                }
            });
            
            return isValid;
        }
        
        /**
         * Récupère les champs requis pour l'étape actuelle
         */
        getRequiredFieldsForCurrentStep(form) {
            const currentStep = this.getCurrentStep(form);
            const requiredFields = [];
            
            switch (currentStep) {
                case '1': // Email
                    const emailField = form.querySelector('input[name="email"]');
                    if (emailField && emailField.hasAttribute('required')) {
                        requiredFields.push(emailField);
                    }
                    break;
                    
                case '2': // Code de vérification
                    const codeField = form.querySelector('input[name="verification_code"]');
                    if (codeField && codeField.hasAttribute('required')) {
                        requiredFields.push(codeField);
                    }
                    break;
                    
                case '3': // Informations personnelles
                    const firstNameField = form.querySelector('input[name="first_name"]');
                    const lastNameField = form.querySelector('input[name="last_name"]');
                    const dateField = form.querySelector('input[name="date_of_birth"]');
                    
                    if (firstNameField && firstNameField.hasAttribute('required')) {
                        requiredFields.push(firstNameField);
                    }
                    if (lastNameField && lastNameField.hasAttribute('required')) {
                        requiredFields.push(lastNameField);
                    }
                    if (dateField && dateField.hasAttribute('required')) {
                        requiredFields.push(dateField);
                    }
                    break;
                    
                case '4': // Username
                    const usernameField = form.querySelector('input[name="username"]');
                    if (usernameField && usernameField.hasAttribute('required')) {
                        requiredFields.push(usernameField);
                    }
                    break;
                    
                case '5': // Mot de passe
                    const password1Field = form.querySelector('input[name="password1"]');
                    const password2Field = form.querySelector('input[name="password2"]');
                    const newPassword1Field = form.querySelector('input[name="new_password1"]');
                    const newPassword2Field = form.querySelector('input[name="new_password2"]');
                    
                    // Check for regular password fields (register form)
                    if (password1Field && password1Field.hasAttribute('required')) {
                        requiredFields.push(password1Field);
                    }
                    if (password2Field && password2Field.hasAttribute('required')) {
                        requiredFields.push(password2Field);
                    }
                    
                    // Check for new password fields (password reset form)
                    if (newPassword1Field && newPassword1Field.hasAttribute('required')) {
                        requiredFields.push(newPassword1Field);
                    }
                    if (newPassword2Field && newPassword2Field.hasAttribute('required')) {
                        requiredFields.push(newPassword2Field);
                    }
                    break;
                    
                case '6': // Résumé (pas de validation nécessaire)
                    break;
                    
                case 'login': // Connexion - email et mot de passe
                    const loginEmailField = form.querySelector('input[name="email"]');
                    const loginPasswordField = form.querySelector('input[name="password"]');
                    
                    if (loginEmailField && loginEmailField.hasAttribute('required')) {
                        requiredFields.push(loginEmailField);
                    }
                    if (loginPasswordField && loginPasswordField.hasAttribute('required')) {
                        requiredFields.push(loginPasswordField);
                    }
                    break;
                    
                case 'choose_2fa': // Choix 2FA
                    const methodField = form.querySelector('input[name="twofa_method"]:checked');
                    if (methodField) {
                        const radioGroup = form.querySelectorAll('input[name="twofa_method"]');
                        requiredFields.push(...Array.from(radioGroup));
                    }
                    break;
                    
                case 'email_2fa': // Code 2FA email
                case 'totp_2fa': // Code 2FA TOTP
                    const twofaCodeField = form.querySelector('input[name="twofa_code"]');
                    if (twofaCodeField && twofaCodeField.hasAttribute('required')) {
                        requiredFields.push(twofaCodeField);
                    }
                    break;
            }
            
            return requiredFields;
        }
        
        /**
         * Obtient l'étape actuelle
         */
        getCurrentStep(form) {
            const stepInput = form.querySelector('input[name="step"]');
            return stepInput ? stepInput.value : '1';
        }
        
        /**
         * Vérifie si tous les champs requis sont remplis
         */
        areAllRequiredFieldsFilled(requiredFields) {
            return requiredFields.every(field => this.isFieldValid(field));
        }
        
        /**
         * Vérifie si un champ individuel est valide
         */
        isFieldValid(field) {
            if (!field) return false;
            
            const value = field.value.trim();
            let isValid = false;
            
            switch (field.type) {
                case 'checkbox':
                    isValid = field.checked;
                    break;
                case 'radio':
                    const name = field.name;
                    const radioGroup = document.querySelectorAll(`input[name="${name}"]`);
                    isValid = Array.from(radioGroup).some(radio => radio.checked);
                    break;
                case 'email':
                    isValid = value !== '' && this.isValidEmail(value);
                    break;
                case 'date':
                    isValid = value !== '';
                    break;
                default:
                    isValid = value !== '';
                    break;
            }
            
            return isValid;
        }
        
        /**
         * Valide le format email
         */
        isValidEmail(email) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return emailRegex.test(email);
        }
    }

    // Initialisation automatique
    new StepValidator();
}
