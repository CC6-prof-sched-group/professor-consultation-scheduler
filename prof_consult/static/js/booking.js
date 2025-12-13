// Real-time Availability Checker
document.addEventListener('DOMContentLoaded', function() {
    const professorSelect = document.getElementById('professor');
    const dateInput = document.getElementById('date');
    const timeInput = document.getElementById('time');
    const durationInput = document.getElementById('duration');
    const submitButton = document.querySelector('button[type="submit"]');
    const availabilityIndicator = document.getElementById('availabilityIndicator');
    
    // Debounce function to avoid too many API calls
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Check availability function
    async function checkAvailability() {
        const professorId = professorSelect?.value;
        const date = dateInput?.value;
        const time = timeInput?.value;
        const duration = durationInput?.value || 30;
        
        // Don't check if required fields are empty
        if (!professorId || !date || !time) {
            hideAvailabilityIndicator();
            return;
        }
        
        // Show loading state
        showLoadingIndicator();
        
        try {
            const formData = new FormData();
            formData.append('professor_id', professorId);
            formData.append('date', date);
            formData.append('time', time);
            formData.append('duration', duration);
            
            // Get CSRF token
            const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            const response = await fetch('/api/check-availability/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                },
                body: formData
            });
            
            const data = await response.json();
            
            if (data.available) {
                showAvailableIndicator(data.message);
                enableSubmitButton();
            } else {
                showUnavailableIndicator(data.message);
                disableSubmitButton();
            }
        } catch (error) {
            console.error('Error checking availability:', error);
            showErrorIndicator('Unable to check availability. Please try again.');
            disableSubmitButton();
        }
    }
    
    // Debounced version of checkAvailability
    const debouncedCheck = debounce(checkAvailability, 500);
    
    // Add event listeners
    if (professorSelect) {
        professorSelect.addEventListener('change', debouncedCheck);
    }
    
    if (dateInput) {
        dateInput.addEventListener('change', debouncedCheck);
    }
    
    if (timeInput) {
        timeInput.addEventListener('change', debouncedCheck);
    }
    
    if (durationInput) {
        durationInput.addEventListener('change', debouncedCheck);
    }
    
    // UI update functions
    function showLoadingIndicator() {
        if (!availabilityIndicator) return;
        
        availabilityIndicator.className = 'alert alert-info d-flex align-items-center mt-3';
        availabilityIndicator.innerHTML = `
            <div class="spinner-border spinner-border-sm me-2" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <span>Checking availability...</span>
        `;
        availabilityIndicator.style.display = 'block';
    }
    
    function showAvailableIndicator(message) {
        if (!availabilityIndicator) return;
        
        availabilityIndicator.className = 'alert alert-success d-flex align-items-center mt-3';
        availabilityIndicator.innerHTML = `
            <i class="bi bi-check-circle-fill me-2"></i>
            <span>${message}</span>
        `;
        availabilityIndicator.style.display = 'block';
    }
    
    function showUnavailableIndicator(message) {
        if (!availabilityIndicator) return;
        
        availabilityIndicator.className = 'alert alert-danger d-flex align-items-center mt-3';
        availabilityIndicator.innerHTML = `
            <i class="bi bi-x-circle-fill me-2"></i>
            <span>${message}</span>
        `;
        availabilityIndicator.style.display = 'block';
    }
    
    function showErrorIndicator(message) {
        if (!availabilityIndicator) return;
        
        availabilityIndicator.className = 'alert alert-warning d-flex align-items-center mt-3';
        availabilityIndicator.innerHTML = `
            <i class="bi bi-exclamation-triangle-fill me-2"></i>
            <span>${message}</span>
        `;
        availabilityIndicator.style.display = 'block';
    }
    
    function hideAvailabilityIndicator() {
        if (!availabilityIndicator) return;
        availabilityIndicator.style.display = 'none';
    }
    
    function enableSubmitButton() {
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.classList.remove('disabled');
        }
    }
    
    function disableSubmitButton() {
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.classList.add('disabled');
        }
    }
    
    // Set minimum date to today
    if (dateInput) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.setAttribute('min', today);
    }
    
    // Prevent form submission if not available
    const bookingForm = document.getElementById('bookingForm');
    if (bookingForm) {
        bookingForm.addEventListener('submit', function(e) {
            if (submitButton && submitButton.disabled) {
                e.preventDefault();
                alert('Please select an available time slot before submitting.');
                return false;
            }
        });
    }
});