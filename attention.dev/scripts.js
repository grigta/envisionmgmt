/**
 * ATTENTION.DEV - JavaScript
 * Modern Web Agency Landing Page
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize all modules
    initNavigation();
    initMobileMenu();
    initScrollAnimations();
    initFAQ();
    initCounters();
    initSmoothScroll();
    initFormValidation();
});

/**
 * Navigation - Scroll effects and active states
 */
function initNavigation() {
    const nav = document.getElementById('nav');
    let lastScroll = 0;

    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;

        // Add scrolled class for background change
        if (currentScroll > 50) {
            nav.classList.add('scrolled');
        } else {
            nav.classList.remove('scrolled');
        }

        lastScroll = currentScroll;
    }, { passive: true });

    // Active link highlighting
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-link');

    const observerOptions = {
        rootMargin: '-20% 0px -80% 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const id = entry.target.getAttribute('id');
                navLinks.forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === `#${id}`) {
                        link.classList.add('active');
                    }
                });
            }
        });
    }, observerOptions);

    sections.forEach(section => observer.observe(section));
}

/**
 * Mobile Menu Toggle
 */
function initMobileMenu() {
    const burger = document.getElementById('navBurger');
    const mobileMenu = document.getElementById('mobileMenu');
    const mobileLinks = document.querySelectorAll('.mobile-link, .mobile-cta');

    if (!burger || !mobileMenu) return;

    burger.addEventListener('click', () => {
        burger.classList.toggle('active');
        mobileMenu.classList.toggle('active');
        document.body.classList.toggle('menu-open');
    });

    // Close menu on link click
    mobileLinks.forEach(link => {
        link.addEventListener('click', () => {
            burger.classList.remove('active');
            mobileMenu.classList.remove('active');
            document.body.classList.remove('menu-open');
        });
    });

    // Close menu on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && mobileMenu.classList.contains('active')) {
            burger.classList.remove('active');
            mobileMenu.classList.remove('active');
            document.body.classList.remove('menu-open');
        }
    });
}

/**
 * Scroll Animations using Intersection Observer
 */
function initScrollAnimations() {
    const animatedElements = document.querySelectorAll('.animate-on-scroll');

    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReducedMotion) {
        animatedElements.forEach(el => el.classList.add('visible'));
        return;
    }

    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    animatedElements.forEach(el => observer.observe(el));
}

/**
 * FAQ Accordion
 */
function initFAQ() {
    const faqItems = document.querySelectorAll('.faq-item');

    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');

        question.addEventListener('click', () => {
            const isActive = item.classList.contains('active');

            // Close all other items
            faqItems.forEach(otherItem => {
                if (otherItem !== item) {
                    otherItem.classList.remove('active');
                }
            });

            // Toggle current item
            item.classList.toggle('active', !isActive);
        });

        // Keyboard accessibility
        question.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                question.click();
            }
        });
    });
}

/**
 * Animated Counters
 */
function initCounters() {
    const counters = document.querySelectorAll('.stat-number[data-count]');

    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const observerOptions = {
        threshold: 0.5
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counter = entry.target;
                const target = parseInt(counter.getAttribute('data-count'), 10);

                if (prefersReducedMotion) {
                    counter.textContent = target;
                } else {
                    animateCounter(counter, target);
                }

                observer.unobserve(counter);
            }
        });
    }, observerOptions);

    counters.forEach(counter => observer.observe(counter));
}

function animateCounter(element, target) {
    const duration = 2000;
    const startTime = performance.now();
    const startValue = 0;

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Easing function (ease-out)
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const currentValue = Math.floor(startValue + (target - startValue) * easeOut);

        element.textContent = currentValue;

        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            element.textContent = target;
        }
    }

    requestAnimationFrame(update);
}

/**
 * Smooth Scroll for Anchor Links
 */
function initSmoothScroll() {
    const links = document.querySelectorAll('a[href^="#"]');

    links.forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');

            if (href === '#') return;

            const target = document.querySelector(href);

            if (target) {
                e.preventDefault();

                const navHeight = document.getElementById('nav').offsetHeight;
                const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - navHeight - 20;

                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });

                // Update URL without jumping
                history.pushState(null, null, href);
            }
        });
    });
}

/**
 * Form Validation and Submission
 */
function initFormValidation() {
    const form = document.getElementById('contactForm');

    if (!form) return;

    const successMsg = document.getElementById('form-success');
    const errorMsg = document.getElementById('form-error');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;

        // Basic validation
        const name = form.querySelector('#name').value.trim();
        const phone = form.querySelector('#phone').value.trim();
        const message = form.querySelector('#message').value.trim();

        if (!name || !phone || !message) {
            showNotification('Пожалуйста, заполните все обязательные поля', 'error');
            return;
        }

        // Hide previous messages
        if (successMsg) successMsg.style.display = 'none';
        if (errorMsg) errorMsg.style.display = 'none';

        // Show loading state
        submitBtn.disabled = true;
        submitBtn.textContent = 'Отправка...';

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: new FormData(form)
            });

            const data = await response.json();

            if (data.success) {
                // Success
                showNotification('Заявка успешно отправлена! Мы свяжемся с вами в ближайшее время.', 'success');
                if (successMsg) successMsg.style.display = 'block';
                form.reset();
            } else {
                throw new Error('Form submission failed');
            }
        } catch (error) {
            showNotification('Произошла ошибка. Пожалуйста, попробуйте позже.', 'error');
            if (errorMsg) errorMsg.style.display = 'block';
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    });
}

/**
 * Show Notification
 */
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existing = document.querySelector('.notification');
    if (existing) existing.remove();

    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button class="notification-close" aria-label="Закрыть">&times;</button>
    `;

    // Styles
    Object.assign(notification.style, {
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        maxWidth: '400px',
        padding: '16px 20px',
        background: type === 'success' ? '#10B981' : type === 'error' ? '#EF4444' : '#3B82F6',
        color: 'white',
        borderRadius: '12px',
        boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.2)',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        zIndex: '9999',
        animation: 'slideIn 0.3s ease',
        fontWeight: '500'
    });

    const closeBtn = notification.querySelector('.notification-close');
    Object.assign(closeBtn.style, {
        background: 'none',
        border: 'none',
        color: 'white',
        fontSize: '24px',
        cursor: 'pointer',
        padding: '0',
        lineHeight: '1'
    });

    document.body.appendChild(notification);

    // Close button handler
    closeBtn.addEventListener('click', () => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    });

    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);

    // Add keyframes if not exists
    if (!document.getElementById('notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
    }
}

/**
 * Parallax Effect for Hero Elements (subtle)
 */
function initParallax() {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    const heroCards = document.querySelectorAll('.hero-card');
    const floatElements = document.querySelectorAll('.float-element');

    window.addEventListener('mousemove', (e) => {
        const x = (e.clientX - window.innerWidth / 2) / window.innerWidth;
        const y = (e.clientY - window.innerHeight / 2) / window.innerHeight;

        heroCards.forEach((card, i) => {
            const factor = (i + 1) * 10;
            card.style.transform = `translate(${x * factor}px, ${y * factor}px)`;
        });

        floatElements.forEach((el, i) => {
            const factor = (i + 1) * 5;
            el.style.transform = `translate(${x * factor}px, ${y * factor}px)`;
        });
    });
}

// Initialize parallax if on desktop
if (window.innerWidth > 1024) {
    initParallax();
}
