
import os

CLEAN_TESTIMONIALS = """        <!-- Testimonials Section -->
        <section class="testimonials-section">
            <div class="container">
                <div class="section-header">
                    <h2 class="section-title">What Sellers Are Saying</h2>
                    <p class="section-subtitle">See how top sellers are scaling with Amz AI Agent</p>
                </div>
                <div class="testimonials-grid">
                    <!-- Testimonial 1 -->
                    <div class="testimonial-card">
                        <div class="testimonial-header">
                            <div class="testimonial-avatar" style="background: #e0f2fe; color: #0284c7;">AS</div>
                            <div class="testimonial-author">
                                <div class="author-name">Amazon Seller</div>
                                <div class="author-title">Home & Kitchen Category</div>
                            </div>
                        </div>
                        <div class="testimonial-rating">⭐⭐⭐⭐⭐</div>
                        <p class="testimonial-content">"The sentiment analysis helped us identify a critical packaging
                            issue we'd missed. <strong>Our return rate improved significantly</strong> within weeks of
                            implementing the suggested fixes."
                        </p>
                    </div>
                    <!-- Testimonial 2 -->
                    <div class="testimonial-card">
                        <div class="testimonial-header">
                            <div class="testimonial-avatar" style="background: #fce7f3; color: #db2777;">EA</div>
                            <div class="testimonial-author">
                                <div class="author-name">E-commerce Agency</div>
                                <div class="author-title">Multi-brand Management</div>
                            </div>
                        </div>
                        <div class="testimonial-rating">⭐⭐⭐⭐⭐</div>
                        <p class="testimonial-content">"We now use AI-driven analysis for all our clients. It reduced
                            our market research time from <strong>days to under an hour</strong>. A real productivity
                            boost for our team."
                        </p>
                    </div>
                    <!-- Testimonial 3 -->
                    <div class="testimonial-card">
                        <div class="testimonial-header">
                            <div class="testimonial-avatar" style="background: #dcfce7; color: #16a34a;">PS</div>
                            <div class="testimonial-author">
                                <div class="author-name">Private Label Seller</div>
                                <div class="author-title">Sports & Outdoors</div>
                            </div>
                        </div>
                        <div class="testimonial-rating">⭐⭐⭐⭐⭐</div>
                        <p class="testimonial-content">"The Voice of Customer insights helped us understand exactly
                            what buyers wanted. The report identified <strong>key differentiation opportunities</strong>
                            that we hadn't considered."
                        </p>
                    </div>
                </div>
            </div>
        </section>"""

file_path = "d:/project/amzaiagent.com/index.html"

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Locate the start and end of the testimonials section
    start_marker = '<!-- Testimonials Section -->'
    end_marker = '<!-- FAQ Section -->'
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)

    if start_idx != -1 and end_idx != -1:
        # Construct new content
        new_content = content[:start_idx] + CLEAN_TESTIMONIALS + '\n\n        ' + content[end_idx:]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Successfully replaced testimonials section.")
    else:
        print(f"Could not find markers. Start: {start_idx}, End: {end_idx}")

except Exception as e:
    print(f"Error: {e}")
