# SEO 自检清单

## 一、发现过的问题（必改项）

以下为实际影响分享与收录的缺失，已在本轮修复中补齐；新页或改版时请避免再犯。

| 项目 | 说明 |
|------|------|
| **twitter:description 为空** | 分享到 Twitter 无描述，需与 og:description 或 meta description 一致 |
| **og:url 缺失** | report / discovery_report 等页需有 og:url，与 canonical 一致 |
| **og:image 缺失** | about 等页需有 og:image（可统一用 logo 或首图） |
| **流程页无 OG/Twitter** | processing / success / failed / 404 / order 需有完整 OG + Twitter，避免被分享时错用默认信息 |
| **无 canonical** | 每页应有 canonical；404 可指向首页 |
| **blog 模板无 OG/Twitter** | blog-post.html 等动态模板需有 fallback 或按文章注入的 og/twitter |
| **blog 文章样式路径错误** | 从 /blog/ 子目录引用根样式应为 `/styles.css?v=5`，勿用 `//styles.css` 或相对路径导致错链 |
| **绝对 URL 被加前缀** | 生成器里勿把 `href="https://"` 统一替换成 `href="/https://"`，需保护绝对 URL |

## 二、优化项（建议做）

| 项目 | 说明 |
|------|------|
| **og:site_name** | 全站统一 `Amz AI Agent`，利于品牌与分享展示 |
| **hreflang** | 单语站也建议有 en + x-default，多语/多地区时必做 |
| **字体 preload** | 关键页（index / create / discovery / about / blog / pricing）加 preconnect + preload，利于 LCP |
| **styles.css 版本号** | 统一用 `?v=5`（或发版时递增），便于缓存与发布一致 |
| **结构化数据** | 首页 Organization + SoftwareApplication；列表/详情页 WebPage + BreadcrumbList；文章 Article |

## 三、新页/新模板检查项

- [ ] `<title>` + `<meta name="description">`
- [ ] `<link rel="canonical" href="...">`
- [ ] `og:site_name`、`og:title`、`og:description`、`og:url`、`og:type`、`og:image`
- [ ] `twitter:card`、`twitter:title`、`twitter:description`、`twitter:image`
- [ ] 若在子目录（如 /blog/），CSS/JS 用根路径如 `/styles.css?v=5`、`/script_v2.js`
- [ ] 需要时加 hreflang（en、x-default）

## 四、生成脚本注意点

- **generate_blog_ssg.py**：替换相对路径时不要动 `https://`、`http://`、`data:` 等绝对 URL；输出样式为 `/styles.css?v=5`。
- 日后若新增 SSG/静态生成脚本，同样只对相对路径加前缀，保护绝对 URL。
