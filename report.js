const initReport = async () => {
    // 获取 DOM 容器
    const contentContainer = document.getElementById('markdown-render');
    const tocContainer = document.getElementById('toc');
    const reportTitle = document.querySelector('.report-title');
    const reportDate = document.querySelector('.report-date');
    const breadcrumbTitle = document.getElementById('breadcrumb-title');

    // 初始化返回按钮（智能返回逻辑）
    initBackButton();

    // 从 URL 获取报告 ID
    const urlParams = new URLSearchParams(window.location.search);
    const reportId = urlParams.get('id');

    // 如果没有 ID，使用示例内容
    if (!reportId) {
        await loadSampleMarkdown();
        return;
    }

    try {

        // 1. Load Index (priority: LocalStorage > Window > Fetch)
        let reports = [];

        // Try LocalStorage first
        const localReports = JSON.parse(localStorage.getItem('my_reports') || '[]');
        if (localReports.length > 0) {
            reports = localReports;
        }

        // Fallback to window global or static fetch if not found in local (or for hybrid)
        // Check if our ID exists in local first
        let report = reports.find(r => r.id === reportId);

        if (!report) {
            // Offline Mode: Check static reportsData from reports.js
            if (window.reportsData) {
                report = window.reportsData.find(r => r.id === reportId);
            }

            // Fallback: Fetch index.json (for server environment)
            if (!report) {
                const indexResponse = await fetch(`data/reports/index.json?v=${new Date().getTime()}`);
                if (indexResponse.ok) {
                    const staticReports = await indexResponse.json();
                    report = staticReports.find(r => r.id === reportId);
                }
            }
        }

        if (!report) {
            showError('Report not found');
            return;
        }

        // 2. Update Metadata
        if (reportTitle) reportTitle.textContent = report.title;
        if (reportDate) reportDate.textContent = `Generated on ${report.created_at}`;
        document.title = `${report.title} - Amz AI Agent`;

        // 2.1 Update Breadcrumb
        updateBreadcrumbTitle(report.title);

        // 3. Load Markdown Content
        // Use pre-bundled content if available (local file mode), else fetch
        let markdownContent = report.content;

        if (!markdownContent) {
            const mdResponse = await fetch(report.markdown_path);
            if (!mdResponse.ok) throw new Error('Unable to load report content');
            markdownContent = await mdResponse.text();
        }

        // 4. 渲染 markdown
        await renderMarkdown(markdownContent);

    } catch (error) {
        console.error('Failed to load report:', error);
        showError('Bummer! Failed to load report. Please refresh and try again.');
    }

    /**
     * 显示错误信息
     */
    function showError(message) {
        contentContainer.innerHTML = `
            <div class="error-state" style="text-align: center; padding: 4rem; color: #dc2626;">
                <p style="font-size: 1.25rem; margin-bottom: 1rem;">⚠️ ${message}</p>
                <a href="cases.html" style="color: #2563eb; text-decoration: underline;">Back to Case List</a>
            </div>
        `;
    }

    /**
     * 加载示例 markdown（当没有 ID 参数时使用）
     */
    async function loadSampleMarkdown() {
        const sampleMarkdown = `
# 1. Market Overview & Competitor Background

## 1.1 Core Product Information
**Anker Soundcore Liberty 4** is a flagship true wireless noise-canceling earbud from Anker, featuring Hi-Res Audio, Heart Rate Monitoring, and personalized noise cancellation.

| Dimension | Parameter |
| :--- | :--- |
| **ASIN** | B0B9M5T6X8 |
| **Current Price** | $129.99 |
| **Rating** | 4.3 (12,450 ratings) |
| **Release Date** | 2022-09-28 |

> **AI Analysis Insight**: This product has the highest rating and review count in its price range, indicating high market acceptance.

## 1.2 Market Positioning Analysis
Positioned in the mid-to-high-end market, direct competitors include **AirPods Pro 2**, **Sony WF-1000XM5**, and **Samsung Galaxy Buds2 Pro**.

- Higher Value for Money ($129 vs $249)
- Unique Heart Rate Monitoring feature
- Excellent App customization experience

# 2. Deep User Review Mining

## 2.1 Positive Sentiment Analysis
Based on AI analysis of **5,000+** positive reviews, user satisfaction centers on:

### 2.1.1 Sound Quality Performance
> "The sound quality is absolutely amazing, especially the LDAC support. Bass is punchy but not muddy."

Key Findings:
- **Keywords**: Crisp, Punchy Bass, LDAC, EQ settings
- **Share**: 45% of positive reviews mentioned sound quality

### 2.1.2 Comfort
Users widely report comfort provided by CloudComfort ear tips, suitable for long wear.

> "I can wear these for 4+ hours without any discomfort."

# 3. Marketing Strategy Recommendations

## 3.1 Keyword Optimization (SEO)
Recommend adding the following long-tail keywords to the Listing:

1. \`wireless earbuds with heart rate monitor\`
2. \`LDAC noise cancelling headphones\`
3. \`best workout earbuds 2024\`

## 3.2 Off-Site Promotion Opportunities
- **YouTube Reviews**: Focus on fitness influencers
- **TikTok Shorts**: Showcase cool interactive features

# 4. Improvement Recommendations Summary

1. **Firmware Upgrade** - Prioritize fixing multipoint connection instability
2. **Packaging Optimization** - Enhance packaging texture
3. **Noise Cancellation Algorithm** - Optimize for wind noise scenarios

> **Conclusion**: This is a highly competitive product with significant value-for-money advantages.
`;

        await renderMarkdown(sampleMarkdown);
    }

    /**
     * 渲染 Markdown 内容
     */
    async function renderMarkdown(markdownContent) {
        if (!window.marked) {
            showError('Markdown renderer failed to load');
            return;
        }

        // 配置 marked（启用 GitHub Flavored Markdown, 禁止原生 HTML）
        const renderer = new marked.Renderer();
        marked.use({
            gfm: true,
            breaks: true,
            renderer: renderer
        });

        // 渲染 Markdown 到页面
        contentContainer.innerHTML = marked.parse(markdownContent);

        // 移除加载状态（如果存在）
        const loadingState = contentContainer.querySelector('.loading-state');
        if (loadingState) {
            loadingState.remove();
        }

        // 生成目录 (TOC)
        generateTOC();

        // 启动滚动监听
        setupScrollSpy();

        // 初始化时高亮第一个目录项
        const firstLink = tocContainer.querySelector('a');
        if (firstLink) {
            firstLink.classList.add('active');
        }
    }

    /**
     * 生成 slug（用于 heading ID）
     */
    function slugify(text) {
        return text
            .toLowerCase()
            .trim()
            .replace(/[\s]+/g, '-')
            .replace(/[^\w\u4e00-\u9fa5-]/g, '')
            .replace(/--+/g, '-')
            .replace(/^-+|-+$/g, '');
    }

    /**
     * 生成目录函数
     */
    function generateTOC() {
        const headers = contentContainer.querySelectorAll('h1, h2, h3, h4');
        const ul = document.createElement('ul');
        const usedIds = new Set();

        headers.forEach((header, index) => {
            // 生成唯一的 slug ID
            let baseSlug = slugify(header.textContent);
            let slug = baseSlug || `heading-${index}`;

            let counter = 1;
            let uniqueSlug = slug;
            while (usedIds.has(uniqueSlug)) {
                uniqueSlug = `${slug}-${counter}`;
                counter++;
            }
            usedIds.add(uniqueSlug);
            header.id = uniqueSlug;

            // 创建目录项
            const li = document.createElement('li');
            const a = document.createElement('a');
            a.href = `#${header.id}`;
            a.textContent = header.textContent;
            a.className = `toc-${header.tagName.toLowerCase()}`;

            // 点击平滑滚动
            a.addEventListener('click', (e) => {
                e.preventDefault();
                header.scrollIntoView({ behavior: 'smooth', block: 'start' });
                updateActiveLink(a);
            });

            li.appendChild(a);
            ul.appendChild(li);
        });

        tocContainer.innerHTML = '';
        tocContainer.appendChild(ul);
    }

    /**
     * 滚动监听 (ScrollSpy)
     */
    function setupScrollSpy() {
        const headers = contentContainer.querySelectorAll('h1, h2, h3, h4');

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const id = entry.target.id;
                    const activeLink = tocContainer.querySelector(`a[href="#${id}"]`);
                    if (activeLink) {
                        updateActiveLink(activeLink);
                    }
                }
            });
        }, {
            rootMargin: '-100px 0px -60% 0px',
            threshold: 0.1
        });

        headers.forEach(header => observer.observe(header));
    }

    /**
     * 更新当前激活的目录链接
     */
    function updateActiveLink(activeLink) {
        const links = tocContainer.querySelectorAll('a');
        links.forEach(link => link.classList.remove('active'));
        activeLink.classList.add('active');
        activeLink.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    /**
     * 初始化返回按钮 - 智能返回逻辑
     * 如果从 cases 页面进入，使用 history.back()
     * 否则直接跳转到 cases.html
     */
    function initBackButton() {
        const backBtn = document.getElementById('back-to-cases');
        if (!backBtn) return;

        backBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const referrer = document.referrer || '';
            // 如果是从 cases 页面来的，返回上一页
            if (referrer.includes('cases')) {
                history.back();
            } else {
                // 否则直接跳转到 cases.html
                window.location.href = 'cases.html';
            }
        });
    }

    /**
     * 更新面包屑标题
     */
    function updateBreadcrumbTitle(title) {
        const breadcrumbTitle = document.getElementById('breadcrumb-title');
        if (breadcrumbTitle && title) {
            breadcrumbTitle.textContent = title;
            breadcrumbTitle.title = title; // 完整标题作为 tooltip
        }
    }
};

// Execute immediately (script is loaded dynamically after DOMContentLoaded)
initReport();
