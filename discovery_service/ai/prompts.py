"""
Prompt templates for Product Discovery analysis
"""

def get_source_finder_prompt(category: str, keywords: str, marketplace: str, web_sources: list = None) -> str:
    """
    Prompt to find relevant web sources for product research
    

Format your response as a JSON array:
[
  {{"url": "https://...", "reason": "...", "type": "reddit|youtube|blog"}},
  ...
]

Only return the JSON array, no other text."""

def get_free_tier_prompt(
    category: str,
    keywords: str,
    marketplace: str,
    web_sources: list,
    amazon_products: list
) -> str:
    """
    FREE Tier Prompt: Market Entry Assessment
    """
    sources_text = _format_sources(web_sources)
    products_text = _format_products(amazon_products)

    return f"""You are a Lead Market Analyst.
Your task is to write a **High-Value Market Opportunity Report** (Standard Version).
The goal is to provide **Actionable, Money-Making Insights** that serve as an irresistible "Lead Magnet".

**CRITICAL REQUIREMENTS:**
1. **Value Density**: Do not write fluff. Every sentence must offer specific value.
2. **Data**: You MUST cite specific review examples (at least 5 key quotes).
3. **Structure**: Professional Business English (US).
4. **Tables**: Include at least 4 tables, including a Profitability Simulator.
5. **WORD COUNT: 2000-3000 words minimum. If shorter, REWRITE.**

=== INPUT DATA ===
Category: {category}
Keywords: {keywords}
Marketplace: {marketplace}

=== RESEARCH DATA ===
{sources_text}

=== PRODUCT DATA ===
{products_text}

---

# Commercial Opportunity Report (Standard Edition)

## 1. Market Scorecard

| Dimension | Score (1-10) | Deep Dive Analysis |
|---|---|---|
| Demand Heat | [X] | [Analyze search trends, review velocity, discussion volume...] |
| Competition | [X] | [Analyze brand monopoly, entry barriers, price war risks...] |
| Profitability | [X] | [Analyze margin structure at different price points...] |
| **Verdict** | **[GO / NO-GO]** | [300-word core decision logic: Why enter/avoid? Is it a Blue Ocean or Red Ocean?] |

## 2. High-Value Opportunity Matrix
*Core Value Section: Direct paths to revenue*

| Unmet Need | Product Solution | Premium Potential | Difficulty |
|---|---|---|---|
| [Pain Point 1] | [Specific Solution] | High/Med/Low | High/Med/Low |
| [Pain Point 2] | [Specific Solution] | High/Med/Low | High/Med/Low |
| [Pain Point 3] | [Specific Solution] | High/Med/Low | High/Med/Low |

## 3. Deep Pain Point Analysis (Top 5)
*MUST cite real user reviews as evidence*

| Rank | Core Pain Point | % Share | User Voice (Evidence) | Root Cause Analysis |
|---|---|---|---|---|
| 1 | [Name] | [X]% | "[Review Quote]" | [Technical/Design root cause] |
| 2 | [Name] | [X]% | "[Review Quote]" | [Technical/Design root cause] |
| 3 | [Name] | [X]% | "[Review Quote]" | [Technical/Design root cause] |

## 4. Profitability Simulator
*Estimated based on suggested entry price $[Price]*

| Cost Item | Estimate ($) | % of Price | Notes |
|---|---|---|---|
| Target Retail Price | $[X] | 100% | Mid-High End Positioning |
| COGS (Landed) | $[X] | [X]% | Manufacturing + Packaging |
| Freight (Sea) | $[X] | [X]% | Est. Sea Shipping |
| Referral Fee | $[X] | 15% | Standard Category Fee |
| FBA Fee | $[X] | [X]% | Based on size tier |
| **Gross Margin** | **$[X]** | **[X]%** | **[Health Check]** |

## 5. Monday Morning Checklist
*Actionable steps to start immediately*
1. **Supply Chain**: Find factories capable of [Specific Tech/Material].
2. **Design**: Avoid [Bad Design] and adopt [Suggested Style].
3. **Operations**: Focus keywords on [Keyword 1], [Keyword 2].

---
**[Upgrade to Pro for Manufacturer Contacts, 3-Year P&L Forecast, and Full Launch Timeline]**
"""

def get_pro_tier_prompt(
    category: str,
    keywords: str,
    marketplace: str,
    web_sources: list,
    amazon_products: list,
    custom_focus: str = None
) -> str:
    """
    PRO Tier Prompt: Deep Discovery Analysis
    """
    sources_text = _format_sources(web_sources)
    products_text = _format_products(amazon_products)
    
    return f"""You are a Lead Market Analyst. Your task is to write an EXTREMELY DETAILED Category Opportunity Report.

**CRITICAL OUTPUT REQUIREMENTS:**
1. **MINIMUM 5000 WORDS** - If your output is shorter, you have FAILED.
2. **CITE EVERY REVIEW** - You MUST quote and analyze EVERY review provided below.
3. **USE TABLES** - Each section MUST contain at least one detailed table.
4. **SPECIFIC PERCENTAGES** - Calculate and show percentages from the review data.
5. **LANGUAGE: SIMPLIFIED CHINESE**

---

**TARGET MARKET:**
Category: {category}
Keywords: {keywords}
Marketplace: {marketplace}

**WEB RESEARCH DATA:**
{sources_text}

**AMAZON PRODUCT & REVIEW DATA (YOU MUST CITE ALL OF THESE):**
{products_text}

---

# 全品类深度分析报告: {keywords}

## 一、市场吸引力综合评估 (500+ words)

### 1.1 市场评分卡
| 维度 | 评分(1-10) | 详细分析 (至少3句话解释) |
|---|---|---|
| 需求强度 | [X] | [从评论数量、评论增速分析] |
| 竞争壁垒 | [X] | [分析品牌集中度、价格战风险] |
| 利润潜力 | [X] | [分析价格区间、成本结构] |
| 进入难度 | [X] | [分析资金、供应链、合规要求] |

**综合判断**: [ENTER / WAIT / AVOID] + 500字详细理由

### 1.2 价格生态系统深度分析
- 列出提供数据中每个产品的价格
- 计算: 最低价、最高价、平均价、中位数
- 识别价格带: 
  - **引流款区间 ($X-$Y)**: 特征描述 + 竞争程度
  - **主流款区间 ($X-$Y)**: 特征描述 + 竞争程度 (红海?)
  - **高端款区间 ($X+)**: 特征描述 + 蓝海机会?
- **建议切入价位**: [具体价格] + 200字理由

---

## 二、用户群体深度画像 (600+ words)

### 2.1 核心用户画像表
| 画像编号 | 用户类型 | 年龄 | 特征 | 购买动机 | 价格敏感度 | 占比估计 |
|---|---|---|---|---|---|---|
| A | [名称] | [X-Y岁] | [3个特征] | [核心动机] | 高/中/低 | X% |
| B | [名称] | [X-Y岁] | [3个特征] | [核心动机] | 高/中/低 | X% |
| C | [名称] | [X-Y岁] | [3个特征] | [核心动机] | 高/中/低 | X% |

### 2.2 场景化需求分析表
| 优先级 | 使用场景 | 详细描述 | 转化驱动因素 | 评论证据 |
|---|---|---|---|---|
| 1 | [场景名] | [100字描述] | [3个因素] | "[引用评论原文]" |
| 2 | ... | ... | ... | ... |

### 2.3 用户痛点深度挖掘 (MUST CITE REVIEWS)
**从评论中提取的Top 5痛点:**

| 排名 | 痛点 | 占比 | 评论证据 (原文引用) | 根因分析 |
|---|---|---|---|---|
| 1 | [痛点] | X% | "[Review quote 1]", "[Review quote 2]" | [100字分析] |
| 2 | ... | | | |

---

## 三、产品与技术趋势 (400+ words)

### 3.1 材质/设计演进表
| 阶段 | 主流材质 | 核心功能 | 代表品牌 | 状态 |
|---|---|---|---|---|
| 过去(淘汰中) | [X] | [X] | [X] | 🔻 下降 |
| 当前(主流) | [X] | [X] | [X] | ➡️ 稳定 |
| 未来(崛起中) | [X] | [X] | [X] | 🔺 上升 |

### 3.2 爆款基因解码
分析提供数据中评分最高的产品，提取共性:
- **必备功能**: [列出]
- **加分功能**: [列出]
- **设计语言**: [描述]
- **定价区间**: [范围]

---

## 四、竞争格局详解 (600+ words)

### 4.1 品牌垄断度分析
- **头部品牌**: [从数据中识别]
- **市场格局**: 垄断 / 寡头 / 分散?
- **新卖家切入可能性**: 高/中/低 + 理由

### 4.2 竞品逐一深度解剖
**对提供数据中的每一个产品进行分析:**

#### 产品 A: [Title]
- **ASIN**: [X]
- **价格**: [X]
- **评分**: [X]/5 ([X] reviews)
- **核心优势** (从评论提取):
  1. "[引用好评原文]" → 说明优势
  2. ...
- **核心劣势** (从差评提取):
  1. "[引用差评原文]" → 说明问题根因
  2. ...
- **市场定位**: [描述]

#### 产品 B: [Title]
[重复上述结构]

#### 产品 C: [Title]
[重复上述结构]

### 4.3 竞争对比矩阵
| 维度 | 产品A | 产品B | 产品C | 市场机会 |
|---|---|---|---|---|
| 价格 | | | | |
| 评分 | | | | |
| 核心功能 | | | | |
| 主要缺陷 | | | | |

---

## 五、蓝海机会与差异化 (500+ words)

### 5.1 未被满足的需求 (从差评中提取)
| 排名 | 未满足需求 | 证据(差评原文) | 解决难度 | 差异化价值 |
|---|---|---|---|---|
| 1 | [需求] | "[引用]" | 高/中/低 | 高/中/低 |

### 5.2 差异化策略矩阵
| 策略类型 | 具体方案 | 实施成本 | 预期效果 | 优先级 |
|---|---|---|---|---|
| 功能创新 | [具体描述] | [估算] | [描述] | 高/中/低 |
| 设计创新 | ... | | | |
| 定位创新 | ... | | | |
| 服务创新 | ... | | | |

---

## 六、进入策略与执行计划 (500+ words)

### 6.1 理想产品规格定义
| 维度 | 规格要求 | 理由 |
|---|---|---|
| 材质 | [X] | [为什么] |
| 容量 | [X] | [为什么] |
| 核心功能 | [列表] | [为什么] |
| 包装设计 | [X] | [为什么] |
| 目标成本 | $[X] | [为什么] |
| 目标售价 | $[X] | [为什么] |
| 目标毛利 | X% | [为什么] |

### 6.2 风险雷达
| 风险类型 | 具体风险 | 概率 | 影响 | 缓解措施 |
|---|---|---|---|---|
| 市场风险 | [X] | 高/中/低 | 高/中/低 | [措施] |
| 供应链风险 | ... | | | |
| 合规风险 | ... | | | |
| 竞争风险 | ... | | | |

### 6.3 30-60-90天执行计划
**第1-30天 (筹备期):**
- [ ] [具体任务1]
- [ ] [具体任务2]
- ...

**第31-60天 (启动期):**
- [ ] ...

**第61-90天 (验证期):**
- [ ] ...

---

## 七、数据附录

### 7.1 原始评论数据汇总
[列出所有提供的评论，按正面/负面分类]

### 7.2 价格数据汇总
[列出所有产品价格]

---

**OUTPUT VALIDATION CHECKLIST (AI must self-check before output):**
- [ ] Total word count >= 5000?
- [ ] Every review from input data cited at least once?
- [ ] At least 10 tables included?
- [ ] Specific percentages calculated from data?
- [ ] All products analyzed individually?

If any checkbox is NO, REWRITE until all are YES.
"""

def _format_sources(web_sources: list) -> str:
    if not web_sources:
        return "No external web sources gathered."
        
    formatted = []
    for i, source in enumerate(web_sources):
        # Handle dictionary vs object (Web sources are dicts, YouTube are objects)
        if isinstance(source, dict):
            title = source.get('title', 'Unknown Source')
            url = source.get('url', 'N/A')
            content = source.get('body', '') or source.get('content', '')
            sType = "web"
        else:
            title = getattr(source, 'title', 'Unknown Source')
            url = getattr(source, 'url', 'N/A')
            content = getattr(source, 'captions', '') or getattr(source, 'content', '')
            sType = getattr(source, 'source_type', 'unknown')
            
        formatted.append(
            f"### Source {i+1}: {title}\n"
            f"Type: {sType}\n"
            f"URL: {url}\n"
            f"Content:\n{content[:2000]}..."
        )
    return "\n\n".join(formatted)

def _format_products(amazon_products: list) -> str:
    if not amazon_products:
        return "No reference products provided."
        
    return "\n\n".join([
        f"### Product {i+1}: {product.title}\n"
        f"ASIN: {product.asin}\n"
        f"Price: {product.price}\n"
        f"Rating: {product.rating} ({product.review_count} reviews)\n"
        f"Features:\n" + "\n".join([f"- {f}" for f in (product.features or [])]) + "\n"
        f"Sample Reviews:\n" + "\n".join([
            f"- [{r.get('rating')}★] {r.get('title')}: {r.get('text', '')[:200]}..."
            for r in (product.reviews or [])[:5]
        ])
        for i, product in enumerate(amazon_products)
    ])

def get_quick_summary_prompt(full_report: str) -> str:
    """Generate a quick 2-paragraph summary of the full report"""
    return f"""Summarize the following product discovery report in exactly 2 concise paragraphs (max 150 words total). Focus on:
1. The main opportunity/finding
2. The key recommendation (GO/NO-GO)

Report:
{full_report[:3000]}

Summary:"""
