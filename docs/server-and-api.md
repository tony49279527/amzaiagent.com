# server.py 与 api/ 目录说明

**线上环境**：生产使用 **discovery_service**（FastAPI），通过 Cloud Run 部署，提供静态页、API（含 `/api/contact`、支付、Discovery 等）。

**本地/旧方案**：根目录的 `server.py` 和 `api/` 是另一套实现：

- `server.py`：Python 标准库 `http.server`，提供静态文件 + `/api/analysis`、`/api/contact`、`/api/report`。
- `api/analysis.py`、`api/contact.py`：被 `server.py` 调用，走 Supabase / SMTP。

若你只跑 Cloud Run（`uvicorn discovery_service.main:app`），**不需要**运行 `server.py`。  
若本地想用「提交分析 / 联系表单」且不跑 discovery_service，可单独运行 `python server.py`（需配置 `.env` 等）。

以后若完全迁移到 discovery_service，可将 `server.py` 与 `api/` 归档或删除，避免两套逻辑并存。
