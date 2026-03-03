# 本轮 SEO 优化说明（提交到 dev）

## 已完成（代码内）

- **P0-2** sitemap：generate_sitemap.py 已排除 dashboard.html、logo_redesign_preview.html；本次已加入 BLOG_REDIRECT_FROM_IDS，重跑后 sitemap 不再包含被 301 的博客 URL。
- **P0-3** 博客重复内容：blog-post.html 内增加 BLOG_301_MAP，16 个重复 URL 访问时 301 到 7 篇保留文章；sitemap 已排除这 16 个 ID。
- **P0-4** 首页 H1：改为「AI-Powered Amazon Competitor Analysis Tool」，「Let Data Drive Your Decisions」移至下方副标题。
- **P1-5/6** 首页、create、discovery、pricing、cases、blog 的 Title 与 Meta Description 已按任务清单更新。
- **P1-7** discovery / blog / cases / pricing 的 H1 已更新（去掉 emoji，更贴关键词）。
- **P1-8** 首页 FAQPage JSON-LD 已加在 `</body>` 前。
- **P1-9** 博客 Article Schema：blog-post.html 已有 injectSchema() 动态注入，未改。
- **P1-10** create、discovery、pricing、cases、blog 已加 BreadcrumbList JSON-LD。
- **P1-11** 首页、create、discovery、pricing、cases、blog 已加 hreflang en + x-default。

## 需在 Cloudflare 完成（非代码）

- **P0-1** www SSL / 301：在 Cloudflare 为 `www` 添加 CNAME 到 `amzaiagent.com`，并在 Redirect Rules 中设置 `www.amzaiagent.com/*` → 301 → `https://amzaiagent.com/$1`。
- **P0-3 可选**：若希望 301 由服务器/边缘完成，可在 Cloudflare Redirect Rules 中按 BLOG_301_MAP 批量添加 blog-post.html 的 301 规则（当前为前端 JS 跳转）。

## 部署后建议

- 在 Google Search Console 重新提交 sitemap：`https://amzaiagent.com/sitemap.xml`。
