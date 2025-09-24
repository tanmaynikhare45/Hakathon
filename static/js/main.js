// Civic Eye - Main JavaScript File

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize components
    initializeLocationServices();
    initializeFileUpload();
    initializeFormValidation();
    initializeModals();
    initializeNotifications();
    // Smooth scrolling disabled to avoid elastic scroll feel
    
    // Initialize mobile menu if exists
    initializeMobileMenu();
    
    console.log('Civic Eye app initialized successfully');
}

// Location Services
function initializeLocationServices() {
    const getLocationBtn = document.getElementById('getLocationBtn');
    
    if (getLocationBtn) {
        getLocationBtn.addEventListener('click', function() {
            getCurrentLocation();
        });
    }
}

function getCurrentLocation() {
    const btn = document.getElementById('getLocationBtn');
    const latInput = document.getElementById('latitude');
    const lngInput = document.getElementById('longitude');
    
    if (!navigator.geolocation) {
        showNotification('Geolocation is not supported by this browser.', 'error');
        return;
    }
    
    // Update button state
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Getting location...';
    btn.disabled = true;
    btn.classList.remove('success', 'error');
    
    const options = {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 600000 // 10 minutes
    };
    
    navigator.geolocation.getCurrentPosition(
        function(position) {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            
            latInput.value = lat.toFixed(6);
            lngInput.value = lng.toFixed(6);
            
            btn.innerHTML = '<i class="fas fa-check"></i> Location detected';
            btn.classList.add('success');
            btn.disabled = false;
            
            // Initialize map if available
            if (typeof initializeMap === 'function') {
                initializeMap(lat, lng);
            }
            
            showNotification('Location detected successfully!', 'success');
        },
        function(error) {
            let errorMessage = 'Unable to get location. ';
            switch(error.code) {
                case error.PERMISSION_DENIED:
                    errorMessage += 'Location access denied by user.';
                    break;
                case error.POSITION_UNAVAILABLE:
                    errorMessage += 'Location information unavailable.';
                    break;
                case error.TIMEOUT:
                    errorMessage += 'Location request timeout.';
                    break;
                default:
                    errorMessage += 'An unknown error occurred.';
                    break;
            }
            
            btn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Location failed';
            btn.classList.add('error');
            btn.disabled = false;
            
            showNotification(errorMessage, 'error');
            console.error('Geolocation error:', error);
        },
        options
    );
}

// File Upload Handling
function initializeFileUpload() {
    const fileInput = document.getElementById('image');
    const uploadArea = document.querySelector('.file-upload-area');
    const preview = document.getElementById('imagePreview');
    
    if (!fileInput || !uploadArea) return;
    
    // Click to upload
    uploadArea.addEventListener('click', function() {
        fileInput.click();
    });
    
    // Drag and drop
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.style.backgroundColor = '#f0f8ff';
        uploadArea.style.borderColor = '#0072ff';
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.style.backgroundColor = '#f8f9fa';
        uploadArea.style.borderColor = '#ddd';
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.style.backgroundColor = '#f8f9fa';
        uploadArea.style.borderColor = '#ddd';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelection(files[0]);
        }
    });
    
    // File input change
    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });
}

function handleFileSelection(file) {
    const preview = document.getElementById('imagePreview');
    const maxSize = 16 * 1024 * 1024; // 16MB
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
    
    // Validate file type
    if (!allowedTypes.includes(file.type)) {
        showNotification('Please select a valid image file (PNG, JPEG, GIF, WEBP)', 'error');
        return;
    }
    
    // Validate file size
    if (file.size > maxSize) {
        showNotification('File size must be less than 16MB', 'error');
        return;
    }
    
    // Show preview
    const reader = new FileReader();
    reader.onload = function(e) {
        const sizeInMB = (file.size / 1024 / 1024).toFixed(2);
        preview.innerHTML = `
            <div class="preview-item">
                <img src="${e.target.result}" alt="Preview">
                <p><strong>${file.name}</strong> (${sizeInMB} MB)</p>
                <button type="button" class="btn btn-small btn-secondary" onclick="removeFilePreview()">
                    <i class="fas fa-times"></i> Remove
                </button>
            </div>
        `;
        preview.style.display = 'block';
    };
    reader.readAsDataURL(file);
}

function removeFilePreview() {
    const fileInput = document.getElementById('image');
    const preview = document.getElementById('imagePreview');
    
    fileInput.value = '';
    preview.style.display = 'none';
    preview.innerHTML = '';
}

// Form Validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(form)) {
                e.preventDefault();
            }
        });
        
        // Real-time validation
        const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(input);
            });
            
            input.addEventListener('input', function() {
                clearFieldError(input);
            });
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('input[required], textarea[required], select[required]');
    
    requiredFields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });
    
    // Special validation for report form
    if (form.classList.contains('report-form')) {
        const description = form.querySelector('#description');
        const imageInput = form.querySelector('#image');
        
        if (!description.value.trim() && !imageInput.files.length) {
            showFieldError(description, 'Please provide either a description or upload an image');
            isValid = false;
        }
    }
    
    // Special validation for password confirmation
    const password = form.querySelector('input[name="password"]');
    const confirmPassword = form.querySelector('input[name="confirm_password"]');
    
    if (password && confirmPassword && password.value !== confirmPassword.value) {
        showFieldError(confirmPassword, 'Passwords do not match');
        isValid = false;
    }
    
    return isValid;
}

function validateField(field) {
    const value = field.value.trim();
    
    // Required field check
    if (field.hasAttribute('required') && !value) {
        showFieldError(field, 'This field is required');
        return false;
    }
    
    // Email validation
    if (field.type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            showFieldError(field, 'Please enter a valid email address');
            return false;
        }
    }
    
    // Password strength
    if (field.type === 'password' && field.name === 'password' && value) {
        if (value.length < 8) {
            showFieldError(field, 'Password must be at least 8 characters long');
            return false;
        }
    }
    
    // Phone number validation
    if (field.type === 'tel' && value) {
        const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
        if (!phoneRegex.test(value.replace(/[\s\-\(\)]/g, ''))) {
            showFieldError(field, 'Please enter a valid phone number');
            return false;
        }
    }
    
    clearFieldError(field);
    return true;
}

function showFieldError(field, message) {
    clearFieldError(field);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.textContent = message;
    errorDiv.style.color = '#dc3545';
    errorDiv.style.fontSize = '0.9rem';
    errorDiv.style.marginTop = '5px';
    
    field.style.borderColor = '#dc3545';
    field.parentNode.appendChild(errorDiv);
}

function clearFieldError(field) {
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
    field.style.borderColor = '';
}

// Modal Handling
function initializeModals() {
    const modals = document.querySelectorAll('.modal');
    
    modals.forEach(modal => {
        const closeBtn = modal.querySelector('.modal-close');
        
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                closeModal(modal.id);
            });
        }
        
        // Close modal when clicking outside
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeModal(modal.id);
            }
        });
    });
    
    // ESC key to close modals
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal[style*="block"]');
            if (openModal) {
                closeModal(openModal.id);
            }
        }
    });
}

function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Notification System
function initializeNotifications() {
    // Create notification container if it doesn't exist
    if (!document.getElementById('notification-container')) {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
        `;
        document.body.appendChild(container);
    }
}

function showNotification(message, type = 'info', duration = 5000) {
    const container = document.getElementById('notification-container');
    const notification = document.createElement('div');
    const id = Date.now().toString();
    
    const colors = {
        success: '#28a745',
        error: '#dc3545',
        warning: '#ffc107',
        info: '#17a2b8'
    };
    
    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };
    
    notification.className = 'notification';
    notification.id = `notification-${id}`;
    notification.style.cssText = `
        background: ${colors[type] || colors.info};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: slideInRight 0.3s ease;
        display: flex;
        align-items: center;
        gap: 10px;
        cursor: pointer;
        transition: all 0.3s ease;
    `;
    
    notification.innerHTML = `
        <i class="${icons[type] || icons.info}"></i>
        <span style="flex: 1;">${message}</span>
        <i class="fas fa-times" style="cursor: pointer; opacity: 0.7;"></i>
    `;
    
    // Add click to dismiss
    notification.addEventListener('click', function() {
        removeNotification(id);
    });
    
    container.appendChild(notification);
    
    // Auto-remove after duration
    if (duration > 0) {
        setTimeout(() => removeNotification(id), duration);
    }
}

function removeNotification(id) {
    const notification = document.getElementById(`notification-${id}`);
    if (notification) {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }
}

// Add CSS animations for notifications
const notificationStyles = document.createElement('style');
notificationStyles.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    .notification:hover {
        transform: translateX(-5px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.2);
    }
`;
document.head.appendChild(notificationStyles);

// Smooth Scrolling
function addSmoothScrolling() {
    const links = document.querySelectorAll('a[href^="#"]');
    
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetSection = document.querySelector(targetId);
            
            if (targetSection) {
                targetSection.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Mobile Menu
function initializeMobileMenu() {
    const menuToggle = document.querySelector('.menu-toggle');
    const mainNav = document.querySelector('.main-nav');
    
    if (menuToggle && mainNav) {
        menuToggle.addEventListener('click', function() {
            mainNav.classList.toggle('active');
            this.classList.toggle('active');
        });
    }
}

// Utility Functions
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

function formatDate(dateString) {
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// API Helper Functions
function makeApiCall(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    const mergedOptions = { ...defaultOptions, ...options };
    
    return fetch(url, mergedOptions)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error('API call failed:', error);
            showNotification('An error occurred. Please try again.', 'error');
            throw error;
        });
}

// Loading States
function showLoading(element) {
    if (element) {
        element.classList.add('loading');
        element.disabled = true;
    }
}

function hideLoading(element) {
    if (element) {
        element.classList.remove('loading');
        element.disabled = false;
    }
}

// Form Submission with Loading
function submitFormWithLoading(form, callback) {
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    showLoading(submitBtn);
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    
    // Simulate form submission
    if (callback && typeof callback === 'function') {
        callback()
            .then(() => {
                hideLoading(submitBtn);
                submitBtn.innerHTML = originalText;
            })
            .catch((error) => {
                hideLoading(submitBtn);
                submitBtn.innerHTML = originalText;
                console.error('Form submission error:', error);
            });
    }
}

// Initialize tooltips (if needed)
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function(e) {
            showTooltip(e.target, e.target.getAttribute('data-tooltip'));
        });
        
        element.addEventListener('mouseleave', function() {
            hideTooltip();
        });
    });
}

function showTooltip(element, text) {
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = text;
    tooltip.style.cssText = `
        position: absolute;
        background: #333;
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 0.9rem;
        z-index: 1000;
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.3s ease;
    `;
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
    
    setTimeout(() => {
        tooltip.style.opacity = '1';
    }, 10);
}

function hideTooltip() {
    const tooltip = document.querySelector('.tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// Export functions for global use
window.CivicEye = {
    showNotification,
    getCurrentLocation,
    showModal,
    closeModal,
    validateForm,
    makeApiCall,
    formatDate,
    formatFileSize
};

console.log('Civic Eye JavaScript loaded successfully');
