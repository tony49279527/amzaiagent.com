// order.js - Supabase & N8N Integration

document.addEventListener('DOMContentLoaded', async () => {
    // 1. Get Params
    const params = new URLSearchParams(window.location.search);
    const orderId = params.get('order_id');

    if (!orderId) {
        alert('No Order ID found. usage: order.html?order_id=123');
        return;
    }


    // 2. Mock Data (No Supabase in Static Mode)
    // In a real app, we would fetch(orderId) here.
    // For this static demo, we mock the order details so the page renders.

    // 2. Mock Data (Enhanced for Preview)
    // Structure derived from real reports
    const mockOrder = {
        order_id: orderId,
        user_email: 'test_pro@example.com',
        report_id: 'RPT-' + orderId.substring(0, 8),
        amount: '29.99',

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
            
            <p><em>(Scroll to read more...)</em></p>
            <br><br><br><br>
        `
    };

    // Check if this is the "Final Payment" step (paying the remainder)
    const statusParam = params.get('status');
    if (statusParam === 'final_payment') {
        mockOrder.amount = '25.00'; // Remaining balance
        document.querySelector('.section-title').textContent = 'Unlock Full Report';
        document.querySelector('.section-subtitle').textContent = 'Pay the remaining balance to download your comprehensive analysis.';
    }

    renderOrderPage(mockOrder);

    // 3. Setup Payment Button Listener
    const btn = document.getElementById('payment-complete-btn');
    if (btn) {
        // Update button text for clarity
        if (statusParam === 'final_payment') {
            btn.textContent = `Pay Remaining $${mockOrder.amount}`;
        } else {
            btn.textContent = `Pay Full Amount $${mockOrder.amount}`;
        }

        btn.addEventListener('click', () => handlePaymentComplete(orderId, mockOrder.amount));
    }
});

function renderOrderPage(order) {
    // Populate Metadata
    document.getElementById('order-id-display').textContent = order.order_id;
    const emailDisplay = document.getElementById('user-email-display');
    if (emailDisplay) emailDisplay.textContent = order.user_email;

    document.getElementById('report-title').textContent = `Analysis # ${order.order_id}`;

    // Render Preview HTML
    const container = document.getElementById('report-preview-content');
    if (container) container.innerHTML = order.preview_htm;

    // Render TOC
    const tocList = document.getElementById('preview-toc');
    if (tocList && order.toc) {
        tocList.innerHTML = '';
        order.toc.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item;
            tocList.appendChild(li);
        });
    }

    // Pricing UI update (if elements exist)
    const priceEl = document.querySelector('.price-display'); // Assuming class exists or we allow default
    // Since original HTML might be hardcoded, we might strictly rely on the button text update above for now.
}

async function handlePaymentComplete(orderId, amount) {
    const btn = document.getElementById('payment-complete-btn');

    // === TEST MODE START ===
    const confirmed = confirm(`🚧 TEST MODE ACTIVATED 🚧\n\nSimulate paying the balance of $${amount}?\n\n(Click 'OK' to finish order)`);

    if (!confirmed) return;
    // === TEST MODE END ===

    btn.disabled = true;
    btn.textContent = 'Verifying...';

    // Simulate Network Delay
    setTimeout(() => {
        // Redirect to Success
        window.location.href = `success.html?order_id=${orderId}&paid=true`;
    }, 1500);
}

function scrollToOrder() {
    document.getElementById('order-card').scrollIntoView({ behavior: 'smooth' });
}
