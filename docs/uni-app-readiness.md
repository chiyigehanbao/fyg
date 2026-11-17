# UNI App 多端适配评估

## 当前结论

现阶段不建议立刻把现有 React 前端整体替换成 UNI App。当前更稳的路线是：

1. 继续把 React + FastAPI 版本打磨成可演示、可私有化交付的 Web 产品。
2. 保持 FastAPI 后端作为唯一业务与模型入口，数据、报告、导出、模型调用都留在服务端。
3. 在前端继续收敛 API 类型、页面状态和业务规则，等 Web 流程稳定后再用 UNI App 重建客户端壳层。

这样可以避免同时改业务流和技术栈，降低小程序/APP 首版返工风险。

## 推荐目标形态

- 后端：继续使用 FastAPI，统一提供 HTTP API。
- 数据库：演示和单机交付可继续 SQLite；商业/多用户部署切 PostgreSQL。
- 模型：Web 私有化版可连接本机 Ollama；小程序和 APP 不直连 Ollama，而是访问后端，由后端连接本地、局域网或服务器模型。
- Web：保留现有 React 版本作为桌面与私有化交付入口。
- Web App：已补充 `manifest.webmanifest` 和移动端 meta，可作为移动浏览器或轻量壳层的基础入口，但仍不等同于小程序/原生 APP。
- UNI App：重建移动端和小程序端页面，复用后端接口与报告结构，不复用 React DOM 组件。

## 页面迁移映射

| 当前 React 路由 | UNI App 页面建议 | 迁移说明 |
| --- | --- | --- |
| `/` | `pages/index/index` | 保留产品说明与开始入口，移动端首屏要更短。 |
| `/start` | `pages/start/index` | 创建诊断表单可直接迁移交互逻辑。 |
| `/workspace` | `pages/workspace/index` | 诊断列表、复制、删除、备份入口需要适配触摸操作。 |
| `/settings` | `pages/settings/index` | 小程序端不展示本地端口细节，只展示后端连通、模型状态与备份能力。 |
| `/cases/:id/basic` | `pages/interview/index?stage=basic&id=` | 访谈页是第一优先级，需复用输入质量规则。 |
| `/cases/:id/advanced` | `pages/interview/index?stage=advanced&id=` | 与基础访谈共用页面。 |
| `/cases/:id/reports/basic` | `pages/report/index?stage=basic&id=` | 报告阅读与版本切换可迁移，下载能力按端封装。 |
| `/cases/:id/reports/final` | `pages/report/index?stage=final&id=` | 与基础报告共用页面。 |

## 当前阻力点

- 路由依赖 `react-router-dom`，UNI App 需要改为 `uni.navigateTo`、`uni.redirectTo` 和页面参数。
- API 层已经收敛到统一客户端；UNI App 需要把底层请求从浏览器 `fetch` 替换为 `uni.request`，同时保留同样的 TypeScript 数据类型。
- 报告导出和备份入口已集中到 `frontend/src/components/FileDownloadLink.tsx`，当前 Web 仍使用 `<a href>` 下载；H5、微信小程序、APP 需要在 UNI App 客户端替换为 `uni.downloadFile`、`uni.openDocument` 或分享/保存流程。
- 报告页已改为服务端导出 Word/PDF；UNI App 只需要按端封装下载、打开和分享动作。
- 浏览器滚动与延迟执行已集中到 `frontend/src/platform/browserEffects.ts`；迁移 UNI App 时替换这一层为 `uni.pageScrollTo`、定时器和平台选择器。
- Vite 代理只适合 Web 开发；UNI App 需要显式配置 API Base URL，区分本地、局域网、测试服和生产服。
- Web App manifest 只改善浏览器安装与壳层体验；微信小程序和 APP 仍需要用 UNI App 页面、文件 API、登录态和合法域名重新封装。

## 迁移前要先完成的准备

1. 建立共享 API 契约：把 `DiagnosisCase`、`Interview`、`DiagnosisReport` 等类型保持稳定。
2. 继续稳定跨端 API 客户端：Web 用 `fetch`，UNI App 用 `uni.request`，上层页面拿到相同返回结构。
3. 保持路由映射集中：Web 端路径已抽到 `frontend/src/routes.ts`，迁移 UNI App 时应把 `appPaths` 映射为 `uni.navigateTo` 页面路径。
4. 持续校准输入质量规则：Web 端规则已抽到 `frontend/src/domain/answerQuality.ts`，后端规则已抽到 `backend/app/services/answer_quality.py`；迁移 UNI App 时应复用同名规则并保持与后端测试样例一致。
5. 保持展示规则集中：工作台日期展示已抽到 `frontend/src/domain/dateFormat.ts`，迁移 UNI App 时应复用同样的空值、异常值和中文日期显示语义。
6. 保持平台行为隔离：Web 端浏览器效果已抽到 `frontend/src/platform/browserEffects.ts`，UNI App 端应提供同名适配层。
7. 继续完善移动端文件预览策略：服务端已提供 PDF，Web 下载动作已集中，UNI App 需要按平台处理下载、打开、分享和权限提示。
8. 配置环境矩阵：`local`、`lan`、`staging`、`production`，明确小程序合法域名与 APP 私有化后端地址。

## 首个 UNI App 里程碑

首版不要追求完整替换 Web。建议只做以下闭环：

1. 创建诊断。
2. 查看工作台列表。
3. 完成基础访谈。
4. 生成并阅读基础报告。
5. 从基础报告进入深度共创。
6. 生成最终方案。

暂缓项：报告历史版本高级管理、移动端备份文件打开/分享、浏览器打印、桌面端宽屏布局。

## 当前下一步

短期继续在现有 Web 端打磨成品度，同时把 API 层和业务规则整理到更容易被 UNI App 复用的位置。等报告生成、版本管理、备份、错误恢复和本地启动都稳定后，再创建 `apps/uni-client` 或独立仓库进行 UNI App 客户端重建。
