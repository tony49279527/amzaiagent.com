# confirm-session 与 n8n 配置说明（可选）

**后续优化方向**：若希望简化架构，可把分析流程从 n8n webhook 迁回后端代码（如 `discovery_service` 内直接调用 analyzer + 邮件），不再依赖 n8n。届时 confirm-session、N8N_* 等配置均可移除。

---

当前**不需要**改 n8n，站点会照常工作。

以后若要加固「确认支付会话」接口，按下面做即可。

## 1. 在 GitHub 里添加 Secret

仓库 **Settings → Secrets and variables → Actions** 中新增：

- `N8N_CONFIRM_SESSION_SECRET`：填一串只有你和 n8n 知道的随机字符串，例如用密码生成器生成 32 位。

## 2. 在 n8n 里给 confirm-session 请求加请求头

在 n8n 里找到「支付成功后调用 Amz AI Agent 后端」的那条流程，找到 **HTTP Request** 节点（请求地址里包含 `/api/payments/confirm-session`）：

1. 打开该节点。
2. 在 **Headers**（或「认证 / 请求头」）里新增一行：
   - **Name**: `X-Webhook-Secret`
   - **Value**: 填和 GitHub Secret `N8N_CONFIRM_SESSION_SECRET` **完全一致**的那串字符串。
3. 保存并发布流程。

这样后端只有在收到正确 `X-Webhook-Secret` 时才会接受 confirm-session 请求。

## 3. 可选：生产环境强制 Polar Webhook 校验

在 GitHub Actions 的 Secrets 里：

- 添加 `POLAR_WEBHOOK_SECRET`（Polar 后台里该 webhook 的签名密钥）。
- 添加 `ENV`，值填 `production`。

这样在生产环境下，Polar 的 webhook 必须带正确签名才会被接受。
