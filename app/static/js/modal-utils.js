/**
 * Modal Utilities
 * Reusable modal system for confirmations, alerts, and info messages
 */

class ModalManager {
    constructor() {
        this.activeModal = null;
        this.setupKeyboardListeners();
    }

    /**
     * Show a confirmation modal with Confirm/Cancel buttons
     * @param {Object} options - Modal configuration
     * @param {string} options.title - Modal title
     * @param {string} options.message - Main message
     * @param {string} options.warning - Optional warning message (shown in red)
     * @param {string} options.confirmText - Text for confirm button (default: "Confirm")
     * @param {string} options.cancelText - Text for cancel button (default: "Cancel")
     * @param {Function} options.onConfirm - Callback when confirmed
     * @param {Function} options.onCancel - Optional callback when cancelled
     */
    showConfirm(options) {
        const {
            title = 'Confirm Action',
            message,
            warning = '',
            confirmText = 'Confirm',
            cancelText = 'Cancel',
            onConfirm,
            onCancel
        } = options;

        const modalId = 'genericModal_' + Date.now();
        const modal = this.createModal({
            id: modalId,
            title,
            message,
            warning,
            buttons: [
                {
                    text: cancelText,
                    className: 'btn btn-secondary',
                    onClick: () => {
                        this.closeModal(modalId);
                        if (onCancel) onCancel();
                    }
                },
                {
                    text: confirmText,
                    className: 'btn btn-danger',
                    onClick: () => {
                        this.closeModal(modalId);
                        if (onConfirm) onConfirm();
                    }
                }
            ]
        });

        this.showModal(modal);
    }

    /**
     * Show an alert modal with OK button
     * @param {Object} options - Modal configuration
     * @param {string} options.title - Modal title
     * @param {string} options.message - Main message
     * @param {string} options.type - Type of alert: 'info', 'success', 'error', 'warning' (default: 'info')
     * @param {Function} options.onClose - Optional callback when closed
     */
    showAlert(options) {
        const {
            title = 'Notice',
            message,
            type = 'info',
            onClose
        } = options;

        const modalId = 'alertModal_' + Date.now();
        const modal = this.createModal({
            id: modalId,
            title,
            message,
            type,
            buttons: [
                {
                    text: 'OK',
                    className: 'btn btn-primary',
                    onClick: () => {
                        this.closeModal(modalId);
                        if (onClose) onClose();
                    }
                }
            ]
        });

        this.showModal(modal);
    }

    /**
     * Show a modal with a form (for confirmations that need form submission)
     * @param {Object} options - Modal configuration
     * @param {string} options.title - Modal title
     * @param {string} options.message - Main message
     * @param {string} options.warning - Optional warning message
     * @param {string} options.formAction - Form action URL
     * @param {string} options.formMethod - Form method (default: POST)
     * @param {Object} options.formData - Additional form data to include
     * @param {string} options.submitText - Text for submit button (default: "Confirm")
     * @param {string} options.cancelText - Text for cancel button (default: "Cancel")
     */
    showFormConfirm(options) {
        const {
            title = 'Confirm Action',
            message,
            warning = '',
            formAction,
            formMethod = 'POST',
            formData = {},
            submitText = 'Confirm',
            cancelText = 'Cancel'
        } = options;

        const modalId = 'formModal_' + Date.now();
        const modal = this.createFormModal({
            id: modalId,
            title,
            message,
            warning,
            formAction,
            formMethod,
            formData,
            submitText,
            cancelText
        });

        this.showModal(modal);
    }

    /**
     * Create a modal element
     */
    createModal({ id, title, message, warning = '', type = 'info', buttons }) {
        const modal = document.createElement('div');
        modal.id = id;
        modal.className = 'modal';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        modal.setAttribute('aria-labelledby', `${id}-title`);

        const typeClass = type !== 'info' ? `modal-${type}` : '';

        modal.innerHTML = `
            <div class="modal-content ${typeClass}">
                <span class="close" aria-label="Close modal">&times;</span>
                <h2 id="${id}-title">${title}</h2>
                <p class="modal-message">${message}</p>
                ${warning ? `<p class="warning">${warning}</p>` : ''}
                <div class="modal-actions">
                    ${buttons.map((btn, idx) => `
                        <button
                            class="${btn.className}"
                            data-action="${idx}"
                            ${idx === buttons.length - 1 ? 'autofocus' : ''}
                        >
                            ${btn.text}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;

        // Add event listeners
        const closeBtn = modal.querySelector('.close');
        closeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.closeModal(id);
        });

        buttons.forEach((btn, idx) => {
            const buttonEl = modal.querySelector(`[data-action="${idx}"]`);
            buttonEl.addEventListener('click', (e) => {
                e.preventDefault();
                btn.onClick();
            });
        });

        // Click outside to close
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeModal(id);
            }
        });

        return modal;
    }

    /**
     * Create a modal with a form
     */
    createFormModal({ id, title, message, warning, formAction, formMethod, formData, submitText, cancelText }) {
        const modal = document.createElement('div');
        modal.id = id;
        modal.className = 'modal';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');

        // Get CSRF token
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';

        // Create hidden fields for form data
        const hiddenFields = Object.entries(formData).map(([key, value]) =>
            `<input type="hidden" name="${key}" value="${value}">`
        ).join('');

        modal.innerHTML = `
            <div class="modal-content">
                <span class="close" aria-label="Close modal">&times;</span>
                <h2>${title}</h2>
                <p class="modal-message">${message}</p>
                ${warning ? `<p class="warning">${warning}</p>` : ''}
                <div class="modal-actions">
                    <button class="btn btn-secondary cancel-btn">${cancelText}</button>
                    <form method="${formMethod}" action="${formAction}" style="display: inline;">
                        <input type="hidden" name="csrf_token" value="${csrfToken}">
                        ${hiddenFields}
                        <button type="submit" class="btn btn-danger">${submitText}</button>
                    </form>
                </div>
            </div>
        `;

        // Add event listeners
        const closeBtn = modal.querySelector('.close');
        closeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.closeModal(id);
        });

        const cancelBtn = modal.querySelector('.cancel-btn');
        cancelBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.closeModal(id);
        });

        // Click outside to close
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeModal(id);
            }
        });

        return modal;
    }

    /**
     * Show a modal
     */
    showModal(modal) {
        document.body.appendChild(modal);
        this.activeModal = modal;

        // Trigger reflow and show modal
        setTimeout(() => {
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden';

            // Focus on the autofocus button
            const autofocusBtn = modal.querySelector('[autofocus]');
            if (autofocusBtn) {
                autofocusBtn.focus();
            }
        }, 10);
    }

    /**
     * Close a modal
     */
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;

        modal.style.display = 'none';
        document.body.style.overflow = 'auto';

        // Remove from DOM after animation
        setTimeout(() => {
            if (modal.parentNode) {
                modal.parentNode.removeChild(modal);
            }
            if (this.activeModal === modal) {
                this.activeModal = null;
            }
        }, 300);
    }

    /**
     * Setup keyboard listeners for ESC key
     */
    setupKeyboardListeners() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.activeModal) {
                const modalId = this.activeModal.id;
                this.closeModal(modalId);
            }
        });
    }
}

// Create global instance
window.modalManager = new ModalManager();

// Convenience functions for backward compatibility
window.showConfirmModal = (options) => window.modalManager.showConfirm(options);
window.showAlertModal = (options) => window.modalManager.showAlert(options);
window.showFormConfirmModal = (options) => window.modalManager.showFormConfirm(options);
