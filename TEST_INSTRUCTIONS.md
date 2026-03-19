# Competitor Analysis 测试说明

## 测试数据
- **邮箱**: leetony4927@gmail.com
- **主品 ASIN**: B07BGV23GK, B0DP1X5RD7, B0CRHJ2FP9
- **竞品 ASIN**: B0DJ4Z4RDL, B0BM6YWTS1, B095NX3BFY, B0C1RSH46Z
- **站点**: 美国站 (US)

## 方式一：浏览器手动测试（推荐）

1. 打开 https://amzaiagent.com/create.html
2. 在 **Core Product ASIN** 输入框填入：
   ```
   B07BGV23GK
   B0DP1X5RD7
   B0CRHJ2FP9
   ```
3. 在 **Competitor ASINs** 输入框填入：
   ```
   B0DJ4Z4RDL
   B0BM6YWTS1
   B095NX3BFY
   B0C1RSH46Z
   ```
4. **Marketplace** 选择 US
5. 点击 **Start Free Analysis** 提交
6. 跳转到 processing 页后，等待约 10–20 分钟
7. 检查 leetony4927@gmail.com 收件箱，查看报告邮件

## 方式二：本地脚本测试（需配置 n8n）

本地需配置 `discovery_service/.env` 中的 `N8N_FREE_ANALYSIS_URL`。

```bash
# 启动服务
cd d:\project\amzaiagent.com
python -m uvicorn discovery_service.main:app --host 127.0.0.1 --port 8000

# 另开终端执行测试
python test_analysis.py
```

## 说明
- Competitor Analysis 流程依赖 n8n 工作流，生产环境已配置
- 生产站点的 Cloudflare 会拦截脚本请求，因此需通过浏览器提交
