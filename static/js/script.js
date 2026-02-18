// Carousel functionality
let currentSlide = 0;
let slides = [];
let indicators = [];
let totalSlides = 0;
let carouselTrack = null;
let carouselWrapper = null;
let autoSlideTimer = null;

function updateCarousel() {
    if (!carouselTrack) return; // safety
    const offset = -currentSlide * 100;
    carouselTrack.style.transform = `translateX(${offset}%)`;

    // Update indicators
    if (indicators && indicators.length) {
        indicators.forEach((indicator, index) => {
            if (index === currentSlide) {
                indicator.classList.add('active');
            } else {
                indicator.classList.remove('active');
            }
        });
    }
}

function nextSlide() {
    currentSlide = (currentSlide + 1) % totalSlides;
    updateCarousel();
}

function previousSlide() {
    currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
    updateCarousel();
}

function goToSlide(slideIndex) {
    currentSlide = slideIndex;
    updateCarousel();
}

// Auto slide carousel will be started after DOM is ready in initCarousel()

// Reset timer on manual interaction
document.addEventListener('click', (e) => {
    if (e.target.closest('.carousel-btn') || e.target.closest('.indicator')) {
        if (autoSlideTimer) {
            clearInterval(autoSlideTimer);
            autoSlideTimer = setInterval(nextSlide, 5000);
        }
    }
});

// Add to cart functionality
function addToCart(event, productId) {
    event.stopPropagation();
    
    // Send request to backend
    fetch('/api/cart/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ product_id: productId, quantity: 1 })
    })
    .then(response => response.json())
    .then(data => {
        showNotification('장바구니에 추가되었습니다!');
        // Animate button
        const btn = event.target;
        const originalText = btn.textContent;
        btn.textContent = '✓ 추가됨';
        btn.style.backgroundColor = '#28a745';
        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.backgroundColor = '';
        }, 2000);
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('오류가 발생했습니다.');
    });
}

// View product details
function viewProduct(productId) {
    console.log('Viewing product:', productId);
    // This can be expanded to open a modal or navigate to product page
}

// Show notification
function showNotification(message) {
    const notification = document.getElementById('notification');
    const notificationText = document.getElementById('notificationText');
    
    notificationText.textContent = message;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// Keyboard navigation for carousel
document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') {
        previousSlide();
        clearInterval(autoSlideTimer);
        autoSlideTimer = setInterval(nextSlide, 5000);
    } else if (e.key === 'ArrowRight') {
        nextSlide();
        clearInterval(autoSlideTimer);
        autoSlideTimer = setInterval(nextSlide, 5000);
    }
});

// Touch swipe support for mobile
let touchStartX = 0;
let touchEndX = 0;

// carouselWrapper will be set in initCarousel()

function handleSwipe() {
    const swipeThreshold = 50;
    const diff = touchStartX - touchEndX;

    if (Math.abs(diff) > swipeThreshold) {
        if (diff > 0) {
            // Swiped left - next slide
            nextSlide();
        } else {
            // Swiped right - previous slide
            previousSlide();
        }
        if (autoSlideTimer) {
            clearInterval(autoSlideTimer);
            autoSlideTimer = setInterval(nextSlide, 5000);
        }
    }
}

// Search functionality (initialized on DOMContentLoaded)
let searchInput = null;

// Toggle mobile menu (if needed)
function toggleMobileMenu() {
    const navContainer = document.querySelector('.nav-container');
    navContainer.classList.toggle('mobile-active');
}

// Initialize - ensure carousel is at first slide after DOM ready
function initCarousel() {
    slides = Array.from(document.querySelectorAll('.carousel-slide'));
    indicators = Array.from(document.querySelectorAll('.indicator'));
    totalSlides = slides.length || 1;
    carouselTrack = document.getElementById('carouselTrack');
    carouselWrapper = document.querySelector('.carousel-wrapper');

    if (carouselWrapper) {
        carouselWrapper.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        }, false);

        carouselWrapper.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            handleSwipe();
        }, false);
    }

    // start auto slide
    if (!autoSlideTimer) {
        autoSlideTimer = setInterval(nextSlide, 5000);
    }

    // initialize search input
    searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const searchTerm = searchInput.value;
                console.log('Searching for:', searchTerm);
            }
        });
    }

    // Add smooth scroll to anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            if (this.getAttribute('href') !== '#') {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });

    // initial render
    updateCarousel();
}

document.addEventListener('DOMContentLoaded', initCarousel);

// Prevent carousel auto-play when user is interacting
document.addEventListener('mouseover', (e) => {
    if (e.target.closest('.carousel-container')) {
        clearInterval(autoSlideTimer);
    }
});

document.addEventListener('mouseout', (e) => {
    if (e.target.closest('.carousel-container')) {
        autoSlideTimer = setInterval(nextSlide, 5000);
    }
});
// 상세보기 페이지로 이동
function viewProduct(productId) {
    window.location.href = `/product/${productId}`;
}

// 장바구니 추가 (구버전 호환성)
function addToCart(event, productId) {
    if (event) {
        event.stopPropagation();
    }
    fetch('/api/cart/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId, quantity: 1 })
    })
    .then(r => r.json())
    .then(d => alert(d.message))
    .catch(e => alert('추가 실패: ' + e.message));
}