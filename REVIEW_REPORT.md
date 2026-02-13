# Amz AI Agent 网站完整审查报告

**审查日期**: 2026-01-31  
**审查范围**: 支付集成、Free/Pro 功能区分、前端页面、后端 API、邮件与流程

---

## 一、总体评价

网站整体架构清晰，Polar 支付和 Free/Pro 区分已基本实现，但存在若干**关键 Bug**、**安全风险**和**配置不一致**问题，需要优先修复。

---

## 二、支付集成 (Polar / Stripe)

### 2.1 已实现功能

| 项目 | 状态 | 说明 |
|------|------|------|
| Polar 静态链接 | ✅ | create.html、discovery.html、discovery_report.html 均有「Pay with Polar.sh」链接 |
| Stripe 代理 | ✅ | `/api/proxy/create-checkout` 代理到 n8n webhook |
| Polar Webhook | ✅ | `/api/webhooks/polar` 处理 checkout.updated |
| 支付验证 | ✅ | `/api/payments/verify-session` 验证 session |
| Polar SDK Checkout | ✅ | `payment_service.py` 支持 `create_checkout_session` |

### 2.2 发现的问题

#### 🔴 严重：create.html Stripe 支付按钮 `orderId` 未定义

**文件**: [script_v2.js](script_v2.js) 第 579-588 行

```javascript
// payDepositBtn 点击时使用了 orderId，但从未定义
body: JSON.stringify({
    amount: '4.99',
    order_id: orderId,  // ❌ orderId 未定义！会导致 ReferenceError
    success_url: ...
})
```

**影响**: 点击「Pay $4.99 Deposit with Stripe」会抛出 `ReferenceError: orderId is not defined`，支付流程无法完成。

**修复建议**: 在 fetch 前添加：
```javascript
const payload = preparePayload(true);
const orderId = payload.order_id;
```

---

#### 🔴 严重：Stripe 按钮逻辑顺序错误

**文件**: [script_v2.js](script_v2.js) 第 572-576 行

当前逻辑：
1. 先弹出 `alert('Payment successful! (Sandbox mode)')` 
2. 再执行 fetch 获取支付链接

**问题**: 用户会先看到「支付成功」提示，然后才发起请求。且 `orderId` 未定义会导致 fetch 直接报错，用户永远不会被重定向到 Stripe。

**修复建议**: 删除 sandbox alert，先 fetch 获取 URL，再 `window.location.href = paymentUrl` 跳转。

---

#### 🟡 中：Polar 静态链接未传递订单信息

**文件**: [create.html](create.html) 第 359-366 行

```html
<a href="https://buy.polar.sh/polar_cl_3udFF79S8v3TpXhKL6CWnHCGLfiHqc3urNBGs0Ae4qk" ...>
```

**问题**: 链接为固定产品页，未携带 `order_id`、`email` 等参数。用户支付完成后，后端无法将支付与具体订单关联（除非通过 Polar metadata 或 webhook 中的 customer_email 推断）。

**现状**: `payPolarDepositBtn` 已通过 `localStorage.setItem('pending_analysis_payload', ...)` 存储数据，`processing.html` 的 `triggerPendingAnalysis` 会读取并调用 `/api/discovery/start-task`。但这是 **Discovery 流程**，**create.html 的 Competitor Analysis** 流程走的是 n8n，两者不同。

**建议**: 确认 Polar 产品是否支持 metadata，或在 webhook 中通过 email 匹配订单。

---

#### 🟡 中：discovery_report.html 报告 API 不存在

**文件**: [discovery_report.html](discovery_report.html) 第 733 行

```javascript
const response = await fetch(`https://amz-ai-replica-znaw4q4ldq-uc.a.run.app/api/discovery-report/${reportId}`);
```

**问题**: 
1. `discovery_service/main.py` 中**没有** `/api/discovery-report/{id}` 端点
2. 使用硬编码 URL，与 deploy 的 Cloud Run 服务名可能不一致
3. 报告存储在 `reports_store` 内存字典，重启即丢失

**影响**: 报告预览页无法加载真实报告内容，始终显示「Loading report content...」。

**修复建议**: 
- 在 main.py 添加 `GET /api/discovery-report/{report_id}`，从 `reports_store` 或 Supabase 读取
- 使用相对路径 `/api/discovery-report/${reportId}` 或通过环境变量配置 base URL

---

## 三、Free vs Pro 功能区分

### 3.1 已实现功能

| 功能 | Free | Pro | 实现位置 |
|------|------|-----|----------|
| 报告语言 | 仅英文 | 多语言可选 | create.html select |
| LLM 模型 | 固定 | 可选 6 种 | create.html, config.py |
| 参考网站/YouTube 数量 | 固定 | 可调 | create.html |
| 文件上传 (退货报告/人群画像) | 锁定 | 解锁 | create.html, script_v2.js |
| 自定义提示词 | 仅 Prompt A | A/B/C + 自定义 | create.html, script_v2.js |
| Discovery 分析焦点 | 仅 Market Entry | 多选 | discovery.html |
| 后端模型 | Claude 3.5 Sonnet | Claude Sonnet 4.5 等 | analyzer.py, config.py |
| 邮件内容 | 完整报告 | 预览 + 支付链接 | email_service.py |

### 3.2 发现的问题

#### 🔴 严重：Pro 解锁仅在前端，可被绕过

**文件**: [script_v2.js](script_v2.js) 第 315-319 行

```javascript
// TODO: Pro unlock state is currently client-side only. For production,
// validate Pro status via a backend API (e.g. check payment record in
// Supabase) before enabling premium features. Users can currently bypass
// this via browser DevTools.
```

**问题**: 用户可在控制台执行 `window.unlockProFeatures()` 或直接移除 `disabled` 属性，无需支付即可使用 Pro 功能。

**修复建议**: 
- 后端在接收分析请求时校验 `user_tier` 与支付记录
- Discovery 服务已通过 `request.user_tier` 区分，但 create.html 的 n8n 流程需在 n8n 或代理层增加校验

---

#### 🟡 中：Discovery 的 `unlockProFeatures` 无支付校验

**文件**: [discovery.html](discovery.html) 第 648-689 行

```javascript
function unlockProFeatures() {
    // WARNING: This is client-side only. A user could call unlockProFeatures()
    // from the console to bypass payment.
    paymentModal.style.display = 'none';
    isProMode = true;
    // ... 解锁所有 Pro 选项
}
```

点击「Unlock Premium Features」overlay 会直接解锁，无需支付。设计上可能是「先配置再支付」，但若用户不支付就提交，后端需拒绝 Pro 请求。

---

## 四、双产品线架构差异

网站有两条产品线，后端不一致：

| 产品线 | 入口 | Free 后端 | Pro 后端 |
|--------|------|-----------|----------|
| **Competitor Analysis** | create.html | n8n webhook 直连 | /api/proxy/pro-analysis |
| **Product Discovery** | discovery.html | /api/discovery/start-task | /api/discovery/start-task (user_tier=pro) |

**create.html** 的 Free 流程直接请求：
```javascript
endpointUrl = 'https://tony4927.app.n8n.cloud/webhook/c6b3034f-250a-433f-9017-c14c3f8c7f9f';
```

**问题**: n8n webhook URL 暴露在前端，且与 Discovery 的 FastAPI 后端分离，两套逻辑需分别维护和校验。

---

## 五、配置与环境变量

### 5.1 deploy.yml 缺失变量

**文件**: [.github/workflows/deploy.yml](.github/workflows/deploy.yml)

当前仅配置：
- SMTP_USER, SMTP_PASSWORD, SMTP_PORT, SMTP_SERVER
- N8N_CHECKOUT_WEBHOOK_URL
- OPENROUTER_API_KEY

**缺失**（main.py 使用）:
- `N8N_PRO_ANALYSIS_URL` → `/api/proxy/pro-analysis` 会返回 503
- `N8N_SEND_REPORT_URL` → `/api/proxy/send-full-report` 会返回 503
- `POLAR_ACCESS_TOKEN`, `POLAR_ORGANIZATION_ID`, `POLAR_PRODUCT_ID`, `POLAR_WEBHOOK_SECRET`
- `CORS_ALLOWED_ORIGINS`
- `N8N_ALLOWED_HOSTS`（resume-workflow 的 SSRF 校验需要）
- `GOOGLE_SEARCH_API_KEY`, `GOOGLE_CX`（analyzer 搜索依赖）
- `SCRAPINGBEE_API_KEY`（爬虫依赖）

### 5.2 URL 不一致

- config.py: `POLAR_CHECKOUT_SUCCESS_URL` 使用 `amz-ai-replica-550177383294.us-central1.run.app`
- discovery_report.html: 使用 `amz-ai-replica-znaw4q4ldq-uc.a.run.app`
- 实际部署的 Cloud Run URL 需与上述之一一致

---

## 六、其他问题

### 6.1 报告存储易失

```python
reports_store = {}  # TODO: Replace with Supabase — lost on container restart
paid_reports = set()
verified_sessions = set()
```

容器重启后，报告和支付状态丢失，Pro 用户可能无法获取已购报告。

### 6.2 discovery_report 支付为模拟

**文件**: [discovery_report.html](discovery_report.html) 第 679-711 行

```javascript
function processPayment() {
    // Simulate Stripe payment
    setTimeout(() => {
        // 直接解锁，无真实支付
        document.querySelectorAll('.report-section.locked').forEach(...);
    }, 2000);
}
```

余额支付 ($25) 仅为前端模拟，未调用真实 Stripe/Polar API。

### 6.3 安全：敏感信息暴露

- deploy.yml 中 SMTP 密码、OpenRouter API Key 等以明文写入（应使用 GitHub Secrets 引用）
- 当前 `env_vars` 已直接写值，需改为 `${{ secrets.XXX }}`

### 6.4 主 ASIN 支持多选与校验不一致

- create.html 文案：「Enter 1-5 ASINs of the same product」
- `validateAsins()` 使用 `asinRegex.test(mainAsinValue)` 只校验单个 ASIN
- 若用户输入多个 ASIN（逗号/换行分隔），校验逻辑需支持拆分后逐个校验

---

## 七、修复优先级建议

| 优先级 | 问题 | 文件 | 预估工作量 |
|--------|------|------|------------|
| P0 | orderId 未定义导致 Stripe 支付失败 | script_v2.js | 5 分钟 |
| P0 | 删除错误的 sandbox alert，调整支付流程顺序 | script_v2.js | 5 分钟 |
| P1 | 添加 `/api/discovery-report/{id}` 端点 | discovery_service/main.py | 30 分钟 |
| P1 | discovery_report 使用相对路径或配置 base URL | discovery_report.html | 5 分钟 |
| P1 | 补全 deploy 环境变量 | .github/workflows/deploy.yml | 15 分钟 |
| P2 | 后端校验 Pro 支付状态 | main.py / n8n | 1-2 小时 |
| P2 | 报告持久化到 Supabase | main.py, analyzer | 2-4 小时 |
| P2 | discovery_report 真实支付集成 | discovery_report.html | 1-2 小时 |
| P3 | 主 ASIN 多选校验 | script_v2.js | 20 分钟 |

---

## 八、总结

- **支付**: Polar 链接可用，Stripe 代理存在 `orderId` 未定义和逻辑顺序错误，需立即修复。
- **Free/Pro**: 前端区分完整，后端 Discovery 已按 tier 区分，但 create 的 n8n 流程和前端 Pro 解锁缺少支付校验。
- **架构**: Competitor Analysis 与 Product Discovery 使用不同后端，需统一配置与校验策略。
- **配置**: 环境变量和 URL 不一致，影响部署与报告加载。

建议优先修复 P0 问题，确保 Stripe 支付流程可正常完成。
