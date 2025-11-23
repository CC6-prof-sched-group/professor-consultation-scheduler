// Main JavaScript for Professor Consultation Scheduler

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    initAnimations();
    initNavbar();
    initCards();
    initForms();
    initTooltips();
    initSearchFilters();
    initNotifications();
});

// Smooth scroll animations
function initAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);

    document.querySelectorAll('.card, .feature-card, .stat-card').forEach(el => {
        el.classList.add('animate-on-scroll');
        observer.observe(el);
    });
}

// Navbar scroll effect
function initNavbar() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;

    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('navbar-scrolled');
        } else {
            navbar.classList.remove('navbar-scrolled');
        }
    });

    // Active link highlighting
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}

// Interactive cards
function initCards() {
    // Make cards clickable
    document.querySelectorAll('.card-clickable').forEach(card => {
        card.addEventListener('click', function(e) {
            if (e.target.tagName === 'A' || e.target.tagName === 'BUTTON') return;
            
            const link = this.querySelector('a.btn, a.card-link');
            if (link) {
                link.click();
            }
        });

        // Add ripple effect
        card.addEventListener('mousedown', function(e) {
            const ripple = document.createElement('span');
            ripple.classList.add('ripple');
            this.appendChild(ripple);

            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';

            setTimeout(() => ripple.remove(), 600);
        });
    });

    // Stat card counter animation
    animateCounters();
}

// Animate counters
function animateCounters() {
    const counters = document.querySelectorAll('.stat-number, .card h2');
    
    counters.forEach(counter => {
        const target = parseInt(counter.textContent);
        if (isNaN(target)) return;

        let current = 0;
        const increment = target / 50;
        const duration = 1000;
        const stepTime = duration / 50;

        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                counter.textContent = target;
                clearInterval(timer);
            } else {
                counter.textContent = Math.floor(current);
            }
        }, stepTime);
    });
}

// Form enhancements
function initForms() {
    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Input animations
    document.querySelectorAll('.form-control, .form-select').forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('input-focused');
        });

        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('input-focused');
        });
    });

    // Date input minimum date (today)
    const dateInputs = document.querySelectorAll('input[type="date"]');
    const today = new Date().toISOString().split('T')[0];
    dateInputs.forEach(input => {
        if (!input.hasAttribute('min')) {
            input.setAttribute('min', today);
        }
    });

    // Professor selection auto-update
    const professorSelect = document.getElementById('professor');
    if (professorSelect) {
        professorSelect.addEventListener('change', function() {
            // Could fetch available time slots here via AJAX
            console.log('Professor selected:', this.value);
        });
    }
}

// Initialize Bootstrap tooltips
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Search and filter functionality
function initSearchFilters() {
    // Real-time search for professors
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const searchTerm = this.value.toLowerCase();
            
            searchTimeout = setTimeout(() => {
                filterProfessors(searchTerm);
            }, 300);
        });
    }

    // Department filter
    const deptFilter = document.querySelector('select[name="department"]');
    if (deptFilter) {
        deptFilter.addEventListener('change', function() {
            const dept = this.value.toLowerCase();
            filterByDepartment(dept);
        });
    }

    // Status filter for consultations
    const statusTabs = document.querySelectorAll('[data-status-filter]');
    statusTabs.forEach(tab => {
        tab.addEventListener('click', function(e) {
            e.preventDefault();
            const status = this.dataset.statusFilter;
            filterConsultations(status);
        });
    });
}

function filterProfessors(searchTerm) {
    const professorCards = document.querySelectorAll('.professor-card');
    let visibleCount = 0;

    professorCards.forEach(card => {
        const name = card.querySelector('h5')?.textContent.toLowerCase() || '';
        const dept = card.querySelector('.text-muted')?.textContent.toLowerCase() || '';
        
        if (name.includes(searchTerm) || dept.includes(searchTerm)) {
            card.style.display = '';
            card.classList.add('fade-in');
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });

    // Show no results message
    showNoResultsMessage('professors', visibleCount === 0);
}

function filterByDepartment(dept) {
    const professorCards = document.querySelectorAll('.professor-card');
    
    professorCards.forEach(card => {
        const cardDept = card.querySelector('.text-muted')?.textContent.toLowerCase() || '';
        
        if (dept === '' || cardDept.includes(dept)) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}

function filterConsultations(status) {
    const consultationCards = document.querySelectorAll('.consultation-card');
    
    consultationCards.forEach(card => {
        const cardStatus = card.dataset.status?.toLowerCase() || '';
        
        if (status === 'all' || cardStatus === status) {
            card.style.display = '';
            card.classList.add('fade-in');
        } else {
            card.style.display = 'none';
        }
    });
}

function showNoResultsMessage(context, show) {
    let message = document.querySelector('.no-results-message');
    
    if (show && !message) {
        message = document.createElement('div');
        message.className = 'no-results-message alert alert-info text-center fade-in';
        message.innerHTML = '<i class="bi bi-search"></i> No results found. Try adjusting your search.';
        document.querySelector('.row').appendChild(message);
    } else if (!show && message) {
        message.remove();
    }
}

// Notification handling
function initNotifications() {
    // Auto-dismiss alerts
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Mark notification as read on click
    document.querySelectorAll('.notification-item').forEach(item => {
        item.addEventListener('click', function() {
            this.classList.add('read');
            this.style.opacity = '0.6';
        });
    });
}

// Utility: Show loading spinner
function showLoading(element) {
    const spinner = document.createElement('div');
    spinner.className = 'spinner-border spinner-border-sm me-2';
    spinner.setAttribute('role', 'status');
    element.prepend(spinner);
    element.disabled = true;
}

function hideLoading(element) {
    const spinner = element.querySelector('.spinner-border');
    if (spinner) spinner.remove();
    element.disabled = false;
}

// Utility: Confirm action
function confirmAction(message) {
    return confirm(message);
}

// Add to consultation buttons
document.querySelectorAll('.btn-cancel-consultation').forEach(btn => {
    btn.addEventListener('click', function(e) {
        if (!confirmAction('Are you sure you want to cancel this consultation?')) {
            e.preventDefault();
        }
    });
});

// Smooth scroll to section
function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// Scroll to Top Button
function initScrollToTop() {
    const scrollBtn = document.getElementById('scrollTopBtn');
    if (!scrollBtn) return;

    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            scrollBtn.classList.add('show');
        } else {
            scrollBtn.classList.remove('show');
        }
    });

    scrollBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// Initialize scroll to top on load
initScrollToTop();

// Export for global use
window.consultationScheduler = {
    showLoading,
    hideLoading,
    confirmAction,
    scrollToSection
};
