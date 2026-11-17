# AI 共创官

从真实业务痛点出发的 AI 赋能诊断与共创平台。

当前生成能力默认使用本机 Ollama，推荐模型为 `qwen3.5:9b`。用户回答和报告生成请求不会发送到外部模型服务。

产品采用两阶段流程：

1. 基础诊断：用户描述场景与问题，完成基础访谈后生成在线《AI 机会诊断报告》。
2. 深度共创：系统结合已有回答动态追问流程、数据、系统、验收与治理要求，生成《专属 AI 落地方案》。
3. 报告交付：在线报告支持版本保留，并可下载为可编辑的 Word 文件或 PDF 文件。

## 本地启动

推荐从项目根目录一键启动 API 和 Web：

```powershell
.\scripts\start-local.ps1
```

脚本会启动：

- 后端 API：`http://127.0.0.1:8000`
- 前端 Web：`http://127.0.0.1:5173`
- 健康检查：`http://127.0.0.1:8000/api/health`
- 运行状态：`http://127.0.0.1:8000/api/system/status`

日志写入 `.local/logs`。保持脚本窗口开启即可使用，按 `Ctrl+C` 会停止本地 API 和 Web。
如只想检查当前服务是否已启动：

```powershell
.\scripts\start-local.ps1 -CheckOnly
```

`-CheckOnly` 会同时检查 API 是否加载了当前代码需要的能力标记，例如模型状态错误码和 PDF 导出；如果 8000 端口上仍是旧后端进程，会提示重启。

也可以分别启动：

```powershell
cd backend
./start.bat
```

```powershell
cd frontend
npm install
npm run dev
```

前端默认使用相对路径 `/api`，开发时由 Vite 代理到 `http://127.0.0.1:8000`，也可以通过 `VITE_API_PROXY_TARGET` 覆盖代理目标。
如果要让打包后的 Web 直接访问局域网、测试服或生产后端，可在前端构建时设置 `VITE_API_BASE_URL`，例如 `http://192.168.1.10:8000`。
对应后端也需要允许这个前端来源访问 API，可在 `backend/.env` 中设置：

```dotenv
CORS_ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173,http://192.168.1.10:5173
```

小程序或 APP 版本仍建议通过 HTTPS 后端域名访问；不要让客户端直连本机 Ollama。

如果要做本机私有化交付或单进程预览，可以先构建前端，再只启动 FastAPI。后端检测到 `frontend/dist/index.html` 后，会托管构建产物，并对非 `/api` 路径回退到 React：

```powershell
cd frontend
npm run build
cd ..\backend
.\start.bat
```

此时可直接访问 `http://127.0.0.1:8000`，刷新 `/workspace`、`/cases/:id/basic` 等前端路由也会回到应用。`FRONTEND_DIST_DIR` 可在 `backend/.env` 中覆盖。

## 本地验收

每轮改动后建议执行一次：

```powershell
.\scripts\verify-local.ps1
```

脚本会依次运行后端测试、前端 lint 和生产构建；如果当前机器只想验证后端，可加 `-SkipFrontend`。
如果还要确认当前 `8000/5173` 上正在运行的服务已经加载最新能力，可运行：

```powershell
.\scripts\verify-local.ps1 -CheckRunning
```

如需同时验证当前 `DATABASE_URL` 的真实连接、表结构和数据计数，可运行：

```powershell
.\scripts\verify-local.ps1 -SkipFrontend -CheckDatabase
```

如需强制验证本机 Ollama 和当前模型能真实完成一次结构化推理，可运行：

```powershell
.\scripts\verify-local.ps1 -SkipFrontend -CheckModel
```

## 本地模型

确保 Ollama 已启动并安装模型：

```powershell
ollama pull qwen3.5:9b
```

默认配置无需 `.env`。如需切换模型或地址，可在 `backend/.env` 中设置：

```dotenv
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3.5:9b
OLLAMA_KEEP_ALIVE=15m
```

## PostgreSQL

默认会使用 `backend/data/app.db`，方便直接体验。要接入你本机 PostgreSQL：

```dotenv
DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5432/ai_cocreator
```

首次启动后端时会自动创建当前版本所需的数据表。正式商用前建议再补 Alembic 迁移、账号体系和租户隔离。

## 主要页面

- `/`：产品首页
- `/start`：创建诊断
- `/workspace`：诊断工作台
- `/settings`：运行状态与本地备份
- `/cases/:id/basic`：基础访谈
- `/cases/:id/reports/basic`：初步报告
- `/cases/:id/advanced`：深度共创
- `/cases/:id/reports/final`：最终方案
- 未匹配路径：显示应用内 404，引导返回首页或工作台

报告页提供 Word 和 PDF 下载入口，移动端或小程序客户端也可以复用同一组服务端导出接口。

设置页提供本地 JSON 备份下载，会导出案例、访谈、报告与历史版本，适合升级、迁移 PostgreSQL 或交付客户环境前留存快照。删除单条诊断前，删除确认弹窗也提供该诊断的独立 JSON 备份下载。

恢复整库备份或删除前下载的单次诊断备份，都使用同一个脚本。建议先演练，确认即将写入的数据量和目标库状态：

```powershell
cd backend
python .\scripts\restore_backup.py --input D:\path\to\ai-cocreator-backup-or-case-export.json
```

确认无误后再写入。默认按案例、访谈阶段、报告阶段和历史版本做幂等导入，重复执行不会复制同一条业务数据：

```powershell
python .\scripts\restore_backup.py --input D:\path\to\ai-cocreator-backup-or-case-export.json --apply
```

需要覆盖恢复时，先加 `--replace` 演练替换范围。输出中的 `replacement_scope` 表示整库（`all`）或指定诊断（`cases`），`replacement_case_ids` 列出指定诊断 ID，`to_delete` 列出将删除的各类数据数量；演练不会创建业务表或修改业务数据：

```powershell
python .\scripts\restore_backup.py --input D:\path\to\ai-cocreator-backup-or-case-export.json --replace
```

确认范围后加 `--apply --replace` 执行。整库备份会替换全部诊断数据；单次诊断备份只替换该诊断及其访谈、报告和历史版本，其他诊断保持不变：

```powershell
python .\scripts\restore_backup.py --input D:\path\to\ai-cocreator-backup-or-case-export.json --apply --replace
```

脚本在连接目标库前校验必需数据段、记录唯一性、关联关系、阶段、版本、日期和 JSON 内容类型。缺段或损坏的文件会拒绝导入；删除和写入在同一事务内完成，写入失败时回滚。恢复前应暂停对目标库的业务写入，并保留当前备份。
