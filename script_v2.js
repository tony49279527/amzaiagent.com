

const initApp = () => {
    // === MOBILE MENU TOGGLE ===
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');
    const navActions = document.querySelector('.nav-actions');

    if (mobileMenuBtn && navLinks) {
        mobileMenuBtn.addEventListener('click', () => {
            const isOpen = navLinks.classList.toggle('active');
            if (navActions) navActions.classList.toggle('active', isOpen);

            // Toggle icons
            const openIcon = mobileMenuBtn.querySelector('.menu-icon-open');
            const closeIcon = mobileMenuBtn.querySelector('.menu-icon-close');
            if (openIcon && closeIcon) {
                openIcon.style.display = isOpen ? 'none' : 'block';
                closeIcon.style.display = isOpen ? 'block' : 'none';
            }
        });
    }

    // === FILE UPLOAD HANDLING ===
    const fileInputs = document.querySelectorAll('input[type="file"]');

    fileInputs.forEach(input => {
        const inputId = input.id;
        const listEl = document.getElementById(`${inputId}-list`);
        const areaEl = document.getElementById(`${inputId}-area`);
        const clearBtn = areaEl ? areaEl.querySelector('.file-clear-btn') : null;

        // Store files in a Map to allow deletion
        let filesMap = new Map();
        input.filesMap = filesMap; // Expose map to input element for access during submit

        if (!listEl) return;

        // Handle file selection
        input.addEventListener('change', () => {
            const newFiles = Array.from(input.files);

            // Filter and Validate Files
            const validFiles = [];
            let invalidFound = false;

            newFiles.forEach(file => {
                const name = file.name.toLowerCase();
                if (name.endsWith('.csv') || name.endsWith('.txt')) {
                    validFiles.push(file);
                } else {
                    invalidFound = true;
                }
            });

            if (invalidFound) {
                alert("⚠️ Format Not Supported\n\nPlease only upload files in .csv or .txt format.");
            }

            validFiles.forEach(file => {
                // Use unique key to allow re-upload of same filename
                const key = `${file.name}-${file.size}-${Date.now()}-${Math.random()}`;
                filesMap.set(key, file);
            });
            renderFileList();
            // Reset input to allow re-selecting same file
            input.value = '';
        });

        // Handle clear all
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                filesMap.clear();
                renderFileList();
            });
        }

        function renderFileList() {
            listEl.innerHTML = '';

            if (filesMap.size === 0) {
                if (clearBtn) clearBtn.hidden = true;
                return;
            }

            if (clearBtn) clearBtn.hidden = false;

            filesMap.forEach((file, key) => {
                const li = document.createElement('li');

                const fileInfo = document.createElement('div');
                fileInfo.className = 'file-info';

                const fileName = document.createElement('span');
                fileName.textContent = file.name;

                const fileSize = document.createElement('span');
                fileSize.className = 'file-size';
                fileSize.textContent = formatFileSize(file.size);

                fileInfo.appendChild(fileName);
                fileInfo.appendChild(fileSize);

                const deleteBtn = document.createElement('button');
                deleteBtn.type = 'button';
                deleteBtn.className = 'file-delete';
                deleteBtn.innerHTML = '×';
                deleteBtn.title = 'Delete';
                deleteBtn.addEventListener('click', () => {
                    filesMap.delete(key);
                    renderFileList();
                });

                li.appendChild(fileInfo);
                li.appendChild(deleteBtn);
                listEl.appendChild(li);
            });
        }

        function formatFileSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        }
    });

    // === PROMPT CHIPS ===
    const promptChips = document.querySelectorAll('.prompt-chip');
    const customPrompt = document.getElementById('custom-prompt');

    const promptTemplates = {
        'A': `1. Market & Customer Insights	
1.1 Target Customer Segments  
Identify the primary customer segments based on review patterns, usage scenarios,
and persona data (if available). Describe key characteristics, expectations,
and purchasing motivations.

1.2 Core Use Cases & Scenarios  
List and prioritize the main usage scenarios from broad to specific.
Explain how customers actually use the product in real-world workflows.

1.3 Customer Pain Points & Expectations  
Summarize the most critical customer pain points revealed through reviews
and external references. Highlight unmet expectations and recurring frustrations.

Present key pain points, their impact, and current market solutions in a table."
2. Competitive Landscape Analysis	"2.1 Main Product – Strengths & Weaknesses  
Analyze the main product’s strengths and weaknesses based on review frequency,
sentiment patterns, and feature feedback.

- List major positive themes with supporting evidence
- List major negative themes with representative review examples
- Indicate the relative importance of each issue

2.2 Key Competitor Analysis  
For each major competitor ASIN:
- Summarize positioning and core value proposition
- Identify key strengths and weaknesses based on reviews
- Highlight where competitors outperform or underperform the main product

2.3 Category-Level Comparison  
Compare the main product against competitors at the category level
(e.g., performance tiers, material quality, durability, ease of use).
Use tables to clearly visualize differences.

2.4 Competitive Summary & Strategic Implications  
Provide a structured comparison summary.
Clearly outline immediate operational or positioning improvements
the main product can implement to gain competitive advantage."
3. Return & Post-Purchase Issue Analysis (If Available)	"3.1 Primary Return Reasons  
List return reasons from highest to lowest frequency.
Include estimated proportions if possible.

3.2 Root Cause Analysis  
Analyze underlying causes behind returns and dissatisfaction.
Distinguish between product issues, expectation mismatch, and usage errors.

3.3 Actionable Solutions  
Map each major return reason to concrete corrective actions
(product, listing, packaging, or education-related)."
4. Listing & Conversion Optimization Strategy	"4.1 Title Optimization  
Propose an optimized English title aligned with customer intent
and competitive differentiation.
Explain the optimization logic.

4.2 Bullet Points (About This Item) Optimization  
Rewrite the bullet points to clearly communicate value, reduce objections,
and address key pain points.
Include guidance on supporting visuals for each bullet point.

4.3 Image & Visual Content Optimization  
Provide recommendations for image improvements, comparison charts,
usage visuals, and infographic concepts.

4.4 A+ Content & Video Strategy  
Suggest a modular A+ content and video structure focused on
education, differentiation, and trust-building."
5. Product, Packaging & Experience Improvements	"5.1 Product-Level Improvements  
Recommend improvements related to specifications, materials,
performance consistency, or quality control.

5.2 Packaging & Presentation  
Suggest packaging upgrades that improve perceived value,
reduce damage, or clarify usage.

5.3 Instructions & Customer Education  
Outline a clear, easy-to-follow instruction structure.
Highlight common mistakes and best practices to reduce misuse and returns.

5.4 Customer Q&A Expansion  
Generate a practical Q&A section addressing the most common
pre-purchase and post-purchase concerns."
6. Expansion Opportunities & Adjacent Use Cases	"6.1 Related Use Cases & Scenarios  
List high-potential adjacent use cases ranked by relevance.
Provide example keywords for each use case.

6.2 Related Products & Bundling Opportunities  
Identify complementary or adjacent products that align with
customer workflows and buying behavior.

6.3 Workflow Integration  
Describe end-to-end usage workflows involving the main product
and related products.
Present workflows in a structured table format, including:
- User goal
- Steps
- Pain points addressed
- Supporting products`,
        'B': 'Please conduct a comprehensive analysis of the above product, focusing on return reasons, product quality issues, packaging issues, and other return-related data.',
        'C': 'Please conduct a full version analysis of the above product, including: market positioning, target audience, pros and cons, competitive advantages, usage scenario expansion, marketing strategy suggestions, and improvement suggestions.',
    };

    // === PROMPT CHIPS (Auto-resize handled above) ===
    promptChips.forEach(chip => {
        chip.addEventListener('click', () => {
            // ... existing logic ...
            promptChips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');

            const promptKey = chip.dataset.prompt;
            if (customPrompt && promptTemplates[promptKey]) {
                customPrompt.value = promptTemplates[promptKey];
                autoResizeTextarea(customPrompt);
            }
        });
    });

    // === AUTO-EXPAND TEXTAREA ===
    if (customPrompt) {
        autoResizeTextarea(customPrompt);
        customPrompt.addEventListener('input', () => {
            autoResizeTextarea(customPrompt);
        });
    }

    function autoResizeTextarea(element) {
        element.style.height = 'auto';
        element.style.height = element.scrollHeight + 'px';
    }

    // (Old Modal Logic Removed to Fix Redeclaration)


    // === HOMEPAGE HERO SEARCH ===
    const heroForm = document.getElementById('hero-search-form');
    if (heroForm) {
        heroForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const asinInput = document.getElementById('hero-asin-input');
            const asin = asinInput.value.trim();

            // Validation Logic
            if (!asin) {
                // Try to find existing error msg
                let errorMsg = document.getElementById('hero-error-msg');

                // If not found, creating it dynamically to guarantee feedback
                if (!errorMsg) {
                    errorMsg = document.createElement('div');
                    errorMsg.id = 'hero-error-msg';
                    errorMsg.style.cssText = 'color: #f87171; font-size: 0.95rem; margin-top: 0.75rem; font-weight: 500; background: rgba(0,0,0,0.5); padding: 0.25rem 0.75rem; border-radius: 4px; display: inline-block;';
                    errorMsg.innerHTML = '⚠️ Please enter a valid ASIN (e.g. B08CVS825S)';
                    // Insert after form
                    heroForm.parentNode.insertBefore(errorMsg, heroForm.nextSibling);
                }

                // Show Error
                errorMsg.style.display = 'inline-block';

                // Shake animation
                asinInput.style.border = '1px solid #f87171';
                setTimeout(() => asinInput.style.border = '1px solid rgba(255,255,255,0.2)', 2000);
                setTimeout(() => errorMsg.style.display = 'none', 3000);

                asinInput.focus();
                return; // Stop execution
            }

            // Redirect if valid
            window.location.href = `create.html?asin=${encodeURIComponent(asin)}`;
        });
    }

    // === FAQ ACCORDION (for other pages) ===
    const faqItems = document.querySelectorAll('.faq-item');
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        if (question) {
            question.addEventListener('click', () => {
                item.classList.toggle('active');
            });
        }
    });

    // === PRO FEATURE INTERACTION ===
    let isProIntent = false;

    const proLockedSection = document.querySelector('.pro-locked');
    const badgePro = document.querySelector('.badge-pro');
    const unlockOverlay = document.getElementById('pro-unlock-overlay');

    if (unlockOverlay && proLockedSection) {
        unlockOverlay.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();

            // Direct Unlock (No annoying confirm dialog needed if they clicked the button)
            isProIntent = true;

            // Visual Unlock
            proLockedSection.classList.remove('pro-locked');
            proLockedSection.style.opacity = '1';
            proLockedSection.style.pointerEvents = 'auto';

            // Hide Overlay
            unlockOverlay.style.display = 'none';

            // Enable ALL inputs and buttons within the section
            const disabledElements = proLockedSection.querySelectorAll('[disabled]');
            disabledElements.forEach(el => el.removeAttribute('disabled'));

            // Remove .disabled class from file upload labels and update text
            const disabledLabels = proLockedSection.querySelectorAll('label.file-upload-btn.disabled');
            disabledLabels.forEach(lbl => {
                lbl.classList.remove('disabled');
                if (lbl.textContent.includes('Pro Only')) {
                    lbl.textContent = 'Choose File';
                }
            });

            // Aggressively hide lock icons
            const locks = proLockedSection.querySelectorAll('.lock-icon');
            locks.forEach(icon => icon.style.display = 'none');

            // Update Badge
            if (badgePro) {
                badgePro.style.background = '#10b981';
                badgePro.textContent = 'PRO ENABLED';
            }
        });
    }

    // === GLOBAL SCROLL REVEAL ===
    const observerOptions = {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px"
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
                observer.unobserve(entry.target); // Only animate once
            }
        });
    }, observerOptions);

    document.querySelectorAll('.fade-up').forEach(el => {
        observer.observe(el);
    });



    // === MODAL HANDLING ===
    const modal = document.getElementById('modal'); // Free Modal
    const paymentModal = document.getElementById('payment-modal'); // Pro Deposit Modal
    const modalClose = document.getElementById('modal-close');
    const paymentModalClose = document.getElementById('payment-modal-close');

    const analysisForm = document.getElementById('analysis-form');
    const modalForm = document.getElementById('modal-form');
    const payDepositBtn = document.getElementById('pay-deposit-btn');

    // === FORM VALIDATION HELPER ===
    function validateAsins() {
        const mainAsin = document.getElementById('main-asin');
        const compAsin = document.getElementById('comp-asin');
        let isMainValid = true;
        let isCompValid = true;

        // ASIN format regex: B followed by 9 alphanumeric characters
        const asinRegex = /^B[A-Z0-9]{9}$/i;

        // Reset Validity
        mainAsin.setCustomValidity("");
        compAsin.setCustomValidity("");

        // Check Main ASIN - not empty AND valid format
        const mainAsinValue = mainAsin.value.trim().toUpperCase();
        if (!mainAsinValue) {
            isMainValid = false;
            mainAsin.setCustomValidity("Please enter the Core Product ASIN.");
        } else if (!asinRegex.test(mainAsinValue)) {
            isMainValid = false;
            mainAsin.setCustomValidity("Invalid ASIN format. Must start with 'B' followed by 9 alphanumeric characters (e.g. B08CVS825S).");
        }

        if (!isMainValid) {
            mainAsin.style.borderColor = '#ef4444';
            mainAsin.style.boxShadow = '0 0 0 3px rgba(239, 68, 68, 0.2)';
            // Shake animation
            mainAsin.animate([
                { transform: 'translate(0)' },
                { transform: 'translate(-5px)' },
                { transform: 'translate(5px)' },
                { transform: 'translate(0)' }
            ], { duration: 300, iterations: 1 });
        } else {
            mainAsin.style.borderColor = '';
            mainAsin.style.boxShadow = '';
        }

        // Check Comp ASIN - not empty AND all ASINs valid format
        const compAsinValue = compAsin.value.trim();
        if (!compAsinValue) {
            isCompValid = false;
            compAsin.setCustomValidity("Please enter at least one Competitor ASIN.");
        } else {
            // Split by comma, newline, or space and validate each ASIN
            const compAsins = compAsinValue.split(/[\n,\s]+/).map(s => s.trim().toUpperCase()).filter(s => s);
            const invalidAsins = compAsins.filter(asin => !asinRegex.test(asin));
            if (invalidAsins.length > 0) {
                isCompValid = false;
                compAsin.setCustomValidity(`Invalid ASIN format: ${invalidAsins.join(', ')}. Each ASIN must start with 'B' followed by 9 alphanumeric characters.`);
            }
        }

        if (!isCompValid) {
            compAsin.style.borderColor = '#ef4444';
            compAsin.style.boxShadow = '0 0 0 3px rgba(239, 68, 68, 0.2)';
            // Shake animation
            compAsin.animate([
                { transform: 'translate(0)' },
                { transform: 'translate(-5px)' },
                { transform: 'translate(5px)' },
                { transform: 'translate(0)' }
            ], { duration: 300, iterations: 1 });
        } else {
            compAsin.style.borderColor = '';
            compAsin.style.boxShadow = '';
        }

        // Trigger Messages (Native Bubble but with English Text)
        if (!isMainValid) {
            mainAsin.reportValidity();
            return false;
        }

        if (!isCompValid) {
            compAsin.reportValidity();
            return false;
        }

        return true;
    }

    // Main Form Submit -> Choose Path
    if (analysisForm) {
        analysisForm.addEventListener('submit', (e) => {
            e.preventDefault();

            if (!validateAsins()) {
                return;
            }

            if (isProIntent) {
                paymentModal.classList.add('active');
            } else {
                modal.classList.add('active');
            }
        });
    }

    // Close Handlers
    [modalClose, paymentModalClose].forEach(btn => {
        if (btn) btn.addEventListener('click', () => {
            modal.classList.remove('active');
            paymentModal.classList.remove('active');
        });
    });

    // === SWITCH TO PRO (Upsell Link) ===
    const switchToProLink = document.getElementById('switch-to-pro-link');
    if (switchToProLink) {
        switchToProLink.addEventListener('click', (e) => {
            e.preventDefault();
            // Switch Modals
            modal.classList.remove('active');

            // Confirm Upgrade Logic? Or just direct to Payment?
            // User wants to upgrade -> Show them Payment immediately as confirmation of intent
            isProIntent = true;
            paymentModal.classList.add('active');
        });
    }

    // Path A: Free Submission
    if (modalForm) {
        modalForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await handleSubmission(false);
        });
    }

    if (payDepositBtn) {
        payDepositBtn.addEventListener('click', async () => {
            if (!validateAsins()) return;

            // Save original text
            const originalText = payDepositBtn.textContent;

            // Add Spinner
            payDepositBtn.innerHTML = `
                    <svg class="spinner" viewBox="0 0 50 50" style="width: 20px; height: 20px; animation: spin 1s linear infinite; vertical-align: middle; margin-right: 8px; display: inline-block;">
                        <circle cx="25" cy="25" r="20" fill="none" stroke="currentColor" stroke-width="5"></circle>
                    </svg>
                    Creating Payment...
                `;
            payDepositBtn.disabled = true;

            // 1. Get User Email from the new Input from the new Input
            const emailInput = document.getElementById('pro-email-input');
            let userEmail = emailInput ? emailInput.value.trim() : '';

            // Validation
            if (!userEmail || !userEmail.includes('@')) {
                alert("Please enter a valid email address to receive your report.");
                emailInput.focus();

                // Reset Button
                payDepositBtn.textContent = 'Pay $4.99 with Stripe (Sandbox)';
                payDepositBtn.disabled = false;
                return;
            }

            // Sync to hidden field for consistency
            const emailField = document.getElementById('user-email');
            if (emailField) emailField.value = userEmail;

            // === SAVE PAYLOAD TO LOCALSTORAGE (For Post-Payment Trigger) ===
            // Generate a short, friendly Order ID (e.g. ORD-839210) matching the display style
            const orderId = 'ORD-' + Math.floor(100000 + Math.random() * 900000);
            const proPayload = {
                order_id: orderId,
                user_email: userEmail,
                user_name: (userEmail.split('@')[0]) || 'Valued User',
                industry: 'General',
                main_asins: [document.getElementById('main-asin').value.trim()],
                competitor_asins: document.getElementById('comp-asin').value.trim().split(/[\n,]+/).map(s => s.trim()).filter(s => s),
                productSite: document.getElementById('marketplace').value,
                language: 'en',
                llm_model: document.getElementById('llm-model').value,
                custom_prompt: document.getElementById('custom-prompt').value.trim(),
                reference_site_count: document.getElementById('website-count') ? document.getElementById('website-count').value : 5,
                reference_youtube_count: document.getElementById('youtube-count') ? document.getElementById('youtube-count').value : 5,
                version: 'v1_pro_verified',
                payment_status: 'deposit_paid', // Will be sent after payment
                amount_paid: 4.99
            };
            localStorage.setItem('pending_pro_payload', JSON.stringify(proPayload));

            // 2. Call backend proxy to get Stripe Link (webhook URL stays server-side)
            try {
                const response = await fetch('/api/proxy/create-checkout', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        amount: '4.99',
                        order_id: orderId,
                        success_url: window.location.origin + `/processing.html?pro=true&orderId=${orderId}&email=${encodeURIComponent(userEmail)}`,
                        cancel_url: window.location.href
                    })
                });

                if (!response.ok) {
                    const errData = await response.json().catch(() => ({}));
                    throw new Error(errData.detail || 'Payment service error');
                }

                const data = await response.json();
                console.log('Checkout response:', data);

                // Handle both object {url:...} and array [{url:...}] formats
                const paymentUrl = data.url || (Array.isArray(data) && data[0] && data[0].url);

                if (paymentUrl) {
                    window.location.href = paymentUrl; // Redirect to Stripe
                } else {
                    throw new Error('No payment URL returned');
                }
            } catch (err) {
                console.error(err);
                alert('Payment Error: ' + err.message);
                payDepositBtn.disabled = false;
                payDepositBtn.textContent = 'Try Again';
            }
        });
    }

    async function handleSubmission(isPro) {
        if (!validateAsins()) return;

        const submitBtn = isPro ? payDepositBtn : modalForm.querySelector('.submit-btn');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Generating...';

        const payload = {
            // == 0. Order ID (Critical for tracking) ==
            order_id: 'ORD-' + Date.now(),

            // == 1. Critical Fields for n8n ==
            // User Info
            user_name: (document.getElementById('user-email').value.split('@')[0]) || 'Valued User',
            user_email: document.getElementById('user-email').value.trim() || 'guest@example.com',
            industry: 'General',

            // Product Data (Arrays required)
            main_asins: [document.getElementById('main-asin').value.trim()],
            competitor_asins: document.getElementById('comp-asin').value.trim().split(/[\n,]+/).map(s => s.trim()).filter(s => s),

            // Config
            productSite: document.getElementById('marketplace').value,
            language: 'en', // Strict English

            // AI Config
            llm_model: isPro ? document.getElementById('llm-model').value : 'gpt-4o-mini', // Default model
            custom_prompt: isPro ? document.getElementById('custom-prompt').value.trim() : '',

            // Scraping Limits
            reference_website_count: 5,
            reference_youtube_count: 5,

            // == 2. Meta Data (Passed for auditing) ==
            version: 'v1_pro_verified',
            payment_status: isPro ? 'deposit_paid' : 'free',
            amount_paid: isPro ? 4.99 : 0
        };

        try {
            // Pro URL: routed through backend proxy (webhook URL stays server-side)
            let endpointUrl = '/api/proxy/pro-analysis';

            if (!isPro) {
                // === FREE TIER: USE LOCAL BACKEND FOR REAL-TIME TRACKING ===
                const backendPayload = {
                    category: "General", // TODO: Add category input to form if needed
                    keywords: payload.main_asins[0] + " " + (document.getElementById('comp-asin').value.trim().replace(/\n/g, ' ')), // simple concat for keywords
                    marketplace: payload.productSite,
                    user_email: payload.user_email,
                    user_tier: "free",
                    reference_asins: [payload.main_asins[0], ...payload.competitor_asins]
                };

                const res = await fetch('/api/discovery/start-task', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(backendPayload)
                });

                if (!res.ok) throw new Error("Backend start-task failed: " + res.statusText);

                const data = await res.json();
                const taskId = data.report_id;

                // Redirect to new Transparent Processing Page
                const email = encodeURIComponent(payload.user_email);
                window.location.href = `processing.html?taskId=${taskId}&email=${email}&pro=false`;
                return;
            }

            // === PRO TIER: Submit via backend proxy ===
            const response = await fetch(endpointUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                let data = {};
                try {
                    data = await response.json();
                } catch (e) {
                    console.log('Response was not JSON');
                }

                // Redirect standard flow
                const email = encodeURIComponent(payload.user_email);
                window.location.href = `processing.html?email=${email}&pro=${isPro}`;

            } else {
                const errText = await response.text();
                throw new Error(`Server responded with ${response.status}: ${errText}`);
            }
        } catch (error) {
            console.error(error);
            alert('Submission Error: ' + error.message);
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }

    // === CREATE PAGE PRE-FILL & INIT ===
    const mainAsinInput = document.getElementById('main-asin');
    if (mainAsinInput) {
        const urlParams = new URLSearchParams(window.location.search);
        const prefillAsin = urlParams.get('asin');
        if (prefillAsin) {
            mainAsinInput.value = prefillAsin;
        }

        const customPrompt = document.getElementById('custom-prompt');
        if (customPrompt && promptTemplates['A']) {
            customPrompt.value = promptTemplates['A'];
            customPrompt.defaultValue = promptTemplates['A']; // Capture default for restoration
            autoResizeTextarea(customPrompt);
        }
    }
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}
