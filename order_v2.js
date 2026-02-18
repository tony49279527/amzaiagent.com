// order_v2.js - Supabase Integration (Live Data)

console.log('--- order_v2.js LOADED (Live Mode) ---');

document.addEventListener('DOMContentLoaded', async () => {
    try {
        // 1. Get Params
        const params = new URLSearchParams(window.location.search);
        const orderId = params.get('order_id');

        if (!orderId) {
            document.querySelector('.order-page-wrapper').innerHTML =
                '<div style="text-align:center; padding: 4rem;"><h3>Error: No Order ID provided</h3><p>Please return to the home page.</p></div>';
            return;
        }

        console.log('Fetching order:', orderId);

        // 2. Fetch Data from Backend
        let orderData = null;
        try {
            const res = await fetch(`/api/report?report_id=${encodeURIComponent(orderId)}`);
            if (res.ok) {
                orderData = await res.json();
            } else {
                console.warn('Report not found or error:', res.status);
            }
        } catch (e) {
            console.error('Fetch error:', e);
        }

        // 3. Fallback or Render
        if (!orderData) {
            console.warn('Using fallback display for invalid/missing ID');
            // Show loading or error state in UI
            document.getElementById('report-title').textContent = 'Order Not Found';
            document.getElementById('report-asin').textContent = 'ID: ' + orderId;
            return;
        }

        // 4. Transform DB Data to UI Format
        // Note: AnalysisReports table structure varies. Adapt as needed.
        const orderModel = {
            order_id: orderData.id,
            user_email: orderData.user_email || 'User',
            status: orderData.status,
            asin: orderData.asin,
            // Calculate amount based on payment status or fixed price
            amount: '25.00',

            // Content
            toc: parseTOC(orderData.result_json),
            preview_htm: generatePreview(orderData.result_json)
        };

        // Check for 'paid' status in URL or DB to toggle view
        const isPaid = orderData.payment_status === 'paid' || params.get('paid') === 'true';
        if (isPaid) {
            document.getElementById('state-unpaid').style.display = 'none';
            document.getElementById('state-paid').style.display = 'block';
            document.getElementById('paid-order-id').textContent = orderId;
        }

        renderOrderPage(orderModel);

        // 5. Setup Payment Button (Stripe/Backend Proxy)
        const btn = document.getElementById('payment-complete-btn');
        if (btn) {
            btn.addEventListener('click', () => handlePaymentComplete(orderId, '25.00'));
        }

    } catch (error) {
        console.error('CRITICAL ERROR in order_v2.js:', error);
    }
});

function parseTOC(jsonStr) {
    // Try to parse the result JSON from the DB
    try {
        if (!jsonStr) return ["Analysis Pending..."];
        const data = (typeof jsonStr === 'object') ? jsonStr : JSON.parse(jsonStr);
        // Assuming data structure has sections or similar
        // Adjust this logic based on actual LLM output structure
        return [
            "I. Market & User Insights",
            "II. Competitor Analysis",
            "III. Listing Optimization",
            "IV. Strategic Recommendations"
        ];
    } catch (e) {
        return ["Overview", "Analysis", "Strategy"];
    }
}

function generatePreview(jsonStr) {
    if (!jsonStr) return '<p>Analysis data is being generated...</p>';

    // For now, return a generic preview or extract specific summary if available
    // In future, parse the actual JSON to snippet
    return `
        <h2>Analysis Preview</h2>
        <p>Your comprehensive report for this ASIN is ready.</p>
        <p>It contains deep insights into market trends, competitor weaknesses, and actionable listing improvements.</p>
        <div class="blur-hint">Unlock to see full details</div>
    `;
}

function renderOrderPage(order) {
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
    if (reportTitle) reportTitle.textContent = `Analysis Report`;

    // Render Preview HTML
    const container = document.getElementById('report-preview-content');
    if (container) {
        container.innerHTML = order.preview_htm;
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
    }
}

async function handlePaymentComplete(orderId, amount) {
    const btn = document.getElementById('payment-complete-btn');
    const originalText = btn.textContent;
    btn.textContent = 'Processing...';
    btn.disabled = true;

    try {
        const response = await fetch('/api/proxy/create-checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                amount: amount,
                order_id: orderId,
                success_url: window.location.origin + `/success.html?order_id=${orderId}&paid=true`,
                cancel_url: window.location.href
            })
        });

        const data = await response.json();
        if (data.url) {
            window.location.href = data.url;
        } else {
            throw new Error('No payment URL returned');
        }
    } catch (err) {
        alert('Payment Error: ' + err.message);
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

function scrollToOrder() {
    document.getElementById('order-card').scrollIntoView({ behavior: 'smooth' });
}
