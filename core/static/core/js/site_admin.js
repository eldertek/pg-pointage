document.addEventListener('DOMContentLoaded', function() {
    // Validation des emails en temps réel
    const emailInput = document.querySelector('.email-list-input');
    if (emailInput) {
        emailInput.addEventListener('input', function() {
            const emails = this.value.split('\n');
            const invalidEmails = [];
            
            emails.forEach((email, index) => {
                email = email.trim();
                if (email && !isValidEmail(email)) {
                    invalidEmails.push(`Ligne ${index + 1}: ${email}`);
                }
            });
            
            // Mise à jour du message d'erreur
            let errorDiv = this.nextElementSibling;
            if (!errorDiv || !errorDiv.classList.contains('email-validation-error')) {
                errorDiv = document.createElement('div');
                errorDiv.classList.add('email-validation-error');
                this.parentNode.insertBefore(errorDiv, this.nextSibling);
            }
            
            if (invalidEmails.length > 0) {
                errorDiv.innerHTML = `<strong>Emails invalides :</strong><br>${invalidEmails.join('<br>')}`;
                errorDiv.style.color = 'var(--danger)';
            } else {
                errorDiv.innerHTML = '';
            }
        });
    }
    
    // Fonction de validation d'email
    function isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }
    
    // Prévisualisation du QR code
    const qrInput = document.querySelector('input[name="qr_code_value"]');
    if (qrInput) {
        qrInput.addEventListener('input', function() {
            const value = this.value.trim();
            let previewDiv = this.nextElementSibling;
            
            if (!previewDiv || !previewDiv.classList.contains('qr-preview')) {
                previewDiv = document.createElement('div');
                previewDiv.classList.add('qr-preview');
                this.parentNode.insertBefore(previewDiv, this.nextSibling);
            }
            
            if (value) {
                const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(value)}`;
                previewDiv.innerHTML = `
                    <div class="qr-preview-container">
                        <img src="${qrUrl}" alt="QR Code Preview">
                        <div class="qr-preview-value">${value}</div>
                    </div>
                `;
            } else {
                previewDiv.innerHTML = '';
            }
        });
        
        // Déclencher l'événement pour les QR codes existants
        qrInput.dispatchEvent(new Event('input'));
    }
    
    // Confirmation pour la régénération des QR codes
    const regenerateForm = document.querySelector('form#changelist-form');
    if (regenerateForm) {
        regenerateForm.addEventListener('submit', function(e) {
            const action = document.querySelector('select[name="action"]').value;
            if (action === 'regenerate_qr_codes') {
                if (!confirm('Attention : La régénération des codes QR va modifier les codes existants. Êtes-vous sûr de vouloir continuer ?')) {
                    e.preventDefault();
                }
            }
        });
    }
}); 