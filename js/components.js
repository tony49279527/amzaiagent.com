/**
 * components.js - Unified UI Components for Amz AI Agent
 * Handles Navbar and Footer injection across all pages.
 */

document.addEventListener('DOMContentLoaded', () => {
    renderNavbar();
    renderFooter();
    initMobileMenu();
});

function renderNavbar() {
    const navPlaceholder = document.getElementById('navbar-placeholder');
    if (!navPlaceholder) return;

    // Get current page filename for active link highlighting
    const currentPath = window.location.pathname.split('/').pop() || 'index.html';

    // Check if we are in "Order" flow (simplified nav)
    // Actually, per audit, we want CONSISTENT nav, so we use the full nav everywhere
    // unless explicitly overridden by a data attribute like data-nav="simple"

    const isSimpleNav = navPlaceholder.getAttribute('data-nav') === 'simple';

    const navHTML = `
    <nav class="navbar">
        <div class="nav-container">
            <!-- Mobile Menu Button -->
            <button class="mobile-menu-btn" aria-label="Toggle Menu">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" class="menu-icon-open">
                    <path d="M3 12H21M3 6H21M3 18H21" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
                </svg>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" class="menu-icon-close" style="display:none;">
                    <path d="M6 18L18 6M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
                </svg>
            </button>

            <a href="index.html" class="logo">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="2" y="2" width="20" height="20" rx="6" fill="#2563eb" />
                    <path d="M12 5L6 19H9L10.5 15H13.5L15 19H18L12 5ZM11.25 12.5L12 10L12.75 12.5H11.25Z"
                        fill="white" />
                </svg>
                <span class="logo-text">Amz AI Agent</span>
            </a>

            <div class="nav-links">
                <a href="index.html" class="${currentPath === 'index.html' ? 'active' : ''}">Home</a>
                <a href="create.html" class="${currentPath === 'create.html' ? 'active' : ''}">Competitor Analysis</a>
                <a href="discovery.html" class="${currentPath === 'discovery.html' ? 'active' : ''}">Product Discovery</a>
                <a href="cases.html" class="${currentPath === 'cases.html' ? 'active' : ''}">Cases</a>
                <a href="blog.html" class="${currentPath === 'blog.html' ? 'active' : ''}">Blog</a>
                <a href="pricing.html" class="${currentPath === 'pricing.html' ? 'active' : ''}">Pricing</a>
            </div>
            
            <div class="nav-actions">
                <a href="create.html" class="btn btn-primary" style="border-radius: 0.375rem;">Start Analysis</a>
            </div>
        </div>
    </nav>
    `;

    navPlaceholder.innerHTML = navHTML;
}

function renderFooter() {
    const footerPlaceholder = document.getElementById('footer-placeholder');
    if (!footerPlaceholder) return;

    const currentYear = new Date().getFullYear();

    const footerHTML = `
    <footer class="footer">
        <div class="container">
            <div class="footer-top">
                <h3 class="footer-logo">Amz AI Agent</h3>
                <p class="footer-tagline">AI Amazon Competitor Review Analysis Platform</p>
            </div>
            <!-- Middle: 3 Link Columns -->
            <div class="footer-columns">
                <div class="footer-col">
                    <h4>Product</h4>
                    <a href="create.html">Competitor Analysis</a>
                    <a href="reports.html">Analysis Reports</a>
                    <a href="pricing.html">Pricing</a>
                </div>
                <div class="footer-col">
                    <h4>Resources</h4>
                    <a href="blog.html">Blog</a>
                    <a href="cases.html">Case Studies</a>
                    <a href="faq.html">FAQ</a>
                </div>
                <div class="footer-col">
                    <h4>Company</h4>
                    <a href="about.html">About Us</a>
                    <a href="privacy.html">Privacy Policy</a>
                    <a href="terms.html">Terms of Service</a>
                </div>
            </div>
            <div class="footer-bottom">
                <p class="footer-copyright">&copy; ${currentYear} Amz AI Agent. All rights reserved.</p>
            </div>
        </div>
    </footer>
    `;

    footerPlaceholder.innerHTML = footerHTML;
}

function initMobileMenu() {
    // Wait for renderNavbar to complete (synchonous, but safe to delegate)
    setTimeout(() => {
        const menuBtn = document.querySelector('.mobile-menu-btn');
        const navLinks = document.querySelector('.nav-links');
        const iconOpen = document.querySelector('.menu-icon-open');
        const iconClose = document.querySelector('.menu-icon-close');

        if (menuBtn && navLinks) {
            menuBtn.addEventListener('click', () => {
                navLinks.classList.toggle('active');

                // Toggle Icons
                const isActive = navLinks.classList.contains('active');
                if (isActive) {
                    iconOpen.style.display = 'none';
                    iconClose.style.display = 'block';
                } else {
                    iconOpen.style.display = 'block';
                    iconClose.style.display = 'none';
                }
            });
        }
    }, 0);
}
