// order_v2.js - Supabase & N8N Integration (Debug Version)

console.log('--- order_v2.js LOADED ---');

document.addEventListener('DOMContentLoaded', async () => {
    console.log('--- DOMContentLoaded START ---');
    try {
        // 1. Get Params
        const params = new URLSearchParams(window.location.search);
        const orderId = params.get('order_id');

        if (!orderId) {
            console.warn('No Order ID found');
            alert('No Order ID found. usage: order.html?order_id=123');
            return;
        }

        console.log('Loading order:', orderId);

        // 2. Mock Data (Enhanced for Preview)
        const mockOrder = {
            order_id: orderId,
            user_email: 'test_pro@example.com',
            report_id: 'RPT-' + (orderId ? orderId.substring(0, 8) : '000'),
            asin: 'B09XWYQ8Q5', // Added Mock ASIN
            amount: '25.00',  // Remaining balance after deposit

            // Full Framework Outline (TOC)
            toc: [
                "I. Market & User Insights",
                "II. Competitor Analysis & Strategy",
                "III. Return Report Analysis",
                "IV. Listing Optimization Plan",
                "V. Product & Peripheral Improvement",
                "VI. Expansion Opportunities"
            ],

            // Rich Preview Content (IV. Listing Optimization Plan)
            preview_htm: `
                <h2>IV. Listing Optimization Plan</h2>
                
                <h3>4.1 Title Optimization (COSMO)</h3>
                <blockquote>
                <strong>English Version:</strong><br>
                ROSONG Collapsible Wagon Cart with Wheels Foldable - 12lbs Ultra-Lightweight Utility Grocery Wagon for Apartment & Shopping, Compact Heavy Duty Garden Cart with Detachable Wheels, 120L Capacity (Black)
                </blockquote>
                <p><strong>Logic:</strong><br>
                • <strong>Context:</strong> "Apartment", "Shopping".<br>
                • <strong>USP:</strong> "12lbs Ultra-Lightweight", "Detachable Wheels".</p>

                <h3>4.2 Bullet Points Optimization</h3>
                <ul>
                    <li>
                        <strong>[Ultra-Lightweight & Apartment Essential]</strong> Weighing only 12 lbs, this grocery wagon is significantly lighter than standard carts, making it effortless to lift into car trunks or carry up stairs. A game-changer for apartment dwellers hauling groceries from garage to fridge in one trip.
                    </li>
                    <li>
                        <strong>[Compact Fold for Easy Storage]</strong> Designed with an innovative collapsing mechanism, this folding wagon shrinks to a mini size (22''x9.8''x7.5''), fitting perfectly in closets, corners, or small car trunks without sacrificing space.
                    </li>
                    <li>
                        <strong>[Detachable Wheels for Cleanliness]</strong> Featuring unique quick-release wheels, you can easily remove them for cleaning muddy tires before storing the cart indoors. 360° rotating front wheels ensure smooth maneuvering.
                    </li>
                    <li>
                        <strong>[Sturdy Frame & Large Capacity]</strong> Despite its light weight, the steel frame supports 200 lbs. The 120L deep capacity holds camping gear and sports equipment securely.
                    </li>
                </ul>
                
                <h3>4.3 Search Terms & Backend Keywords</h3>
                <p>Based on competitor gap analysis, include these high-volume keywords in your backend search terms:</p>
                <div style="background: #f8fafc; padding: 15px; border-radius: 8px; border: 1px dashed #cbd5e1; margin-bottom: 20px;">
                    <code>foldable wagon heavy duty, collapsible cart for groceries, beach wagon big wheels, utility wagon with brakes, camping cart portable</code>
                </div>

                <h3>4.4 A+ Content Recommendations</h3>
                <p>To maximize conversion, your A+ content should focus on these visual narratives:</p>
                <ul>
                    <li><strong>Module 1 (Hero):</strong> Lifestyle shot showing the wagon being unloaded from a car trunk (emphasizing compactness).</li>
                    <li><strong>Module 2 (Features):</strong> Close-up grid of the quick-release wheels and the one-pull folding mechanism.</li>
                    <li><strong>Module 3 (Usage):</strong> Split screen showing "Apartment to Car" and "Campsite to Beach" versatility.</li>
                </ul>

                <p><em>(Scroll to read more...)</em></p>
                <br><br>
            `
        };

        // Check if this is the "Final Payment" step
        const statusParam = params.get('status');
        console.log('Status Param:', statusParam);

        if (statusParam === 'final_payment') {
            mockOrder.amount = '25.00'; // Remaining balance
            const titleEl = document.querySelector('.section-title');
            if (titleEl) titleEl.textContent = 'Unlock Full Report';

            const subTitleEl = document.querySelector('.section-subtitle');
            if (subTitleEl) subTitleEl.textContent = 'Pay the remaining balance to download your comprehensive analysis.';
        }

        console.log('Mock Order Prepared:', mockOrder);
        renderOrderPage(mockOrder);
        console.log('renderOrderPage called');

        // 3. Setup Payment Button Listener (Stripe)
        const btn = document.getElementById('payment-complete-btn');
        if (btn) {
            console.log('Payment Button Correcting...');
            // Update button text to show $25
            btn.textContent = `Pay $${mockOrder.amount} with Stripe (Sandbox)`;

            btn.addEventListener('click', () => handlePaymentComplete(orderId, mockOrder.amount));
        }

        // 4. Setup PayPal Button
        const paypalBtn = document.getElementById('paypal-btn');
        if (paypalBtn) {
            // Placeholder: Waiting for real Sandbox Link from user
            console.log('PayPal Button ready for Sandbox Link');
        }

    } catch (error) {
        console.error('CRITICAL ERROR in order_v2.js:', error);
    }
});

function renderOrderPage(order) {
    console.log('Rendering Order Page...');
    try {
        // Populate Metadata
        const idDisplay = document.getElementById('order-id-display');
        if (idDisplay) idDisplay.textContent = order.order_id;

        const emailDisplay = document.getElementById('user-email-display');
        if (emailDisplay) emailDisplay.textContent = order.user_email;

        // Render ASIN
        const asinDisplay = document.getElementById('report-asin');
        if (asinDisplay && order.asin) {
            asinDisplay.textContent = `ASIN: ${order.asin}`;
        }

        const reportTitle = document.getElementById('report-title');
        if (reportTitle) reportTitle.textContent = `Analysis # ${order.order_id}`;

        // Render Preview HTML (sanitized to prevent XSS)
        const container = document.getElementById('report-preview-content');
        if (container) {
            // Use DOMPurify to sanitize HTML content
            const sanitizedHTML = typeof DOMPurify !== 'undefined'
                ? DOMPurify.sanitize(order.preview_htm, { USE_PROFILES: { html: true } })
                : order.preview_htm.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
            container.innerHTML = sanitizedHTML;
        } else {
            console.error('Container #report-preview-content NOT FOUND');
        }

        // Render TOC
        const tocList = document.getElementById('preview-toc');
        if (tocList && order.toc) {
            tocList.innerHTML = '';
            order.toc.forEach(item => {
                const li = document.createElement('li');
                li.textContent = item;
                tocList.appendChild(li);
            });
            console.log('TOC Rendered with items:', order.toc.length);
        } else {
            console.error('TOC List #preview-toc NOT FOUND');
        }

        // Pricing UI update (Force update any price displays)
        const priceEls = document.querySelectorAll('.price-display .price, .price');
        priceEls.forEach(el => {
            if (el.textContent.includes('29.99') && order.amount === '25.00') {
                el.innerHTML = '$25.00 <span class="currency">USD</span>';
            }
        });

    } catch (e) {
        console.error('Error inside renderOrderPage:', e);
    }
}

async function handlePaymentComplete(orderId, amount) {
    const btn = document.getElementById('payment-complete-btn');
    btn.textContent = 'Creating Payment...';
    btn.disabled = true;

    // Get resume_url from URL params (passed from n8n preview email)
    const params = new URLSearchParams(window.location.search);
    const resumeUrl = params.get('resume_url');

    // Build success URL with resume_url for triggering n8n workflow
    let successUrl = window.location.origin + `/success.html?order_id=${orderId}&paid=true`;
    if (resumeUrl) {
        successUrl += `&resume_url=${encodeURIComponent(resumeUrl)}`;
    }

    // 2. Call backend proxy to get Stripe Link (webhook URL stays server-side)
    try {
        const response = await fetch('/api/proxy/create-checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                amount: '25.00',
                order_id: orderId,
                success_url: successUrl,
                cancel_url: window.location.href
            })
        });

        const data = await response.json();
        if (data.url) {
            window.location.href = data.url; // Redirect to Stripe
        } else {
            throw new Error('No payment URL returned');
        }
    } catch (err) {
        console.error(err);
        alert('Payment Error: ' + err.message);
        btn.disabled = false;
        btn.textContent = `Pay Remaining $${amount} (Sandbox)`;
    }
}

function scrollToOrder() {
    document.getElementById('order-card').scrollIntoView({ behavior: 'smooth' });
}
