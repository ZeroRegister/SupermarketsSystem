# Shelfwise 论文插图素材

共 71 幅图。图号为素材编号，正式论文排版时再按章节编号。英文标签，与现有系统界面一致。

分类数量：{'diagram': 24, 'ui': 27, 'code': 14, 'test-result': 3, 'benchmark-plot': 3}

本目录仅收集插图，未修改论文正文。

## 使用方式

- `diagrams/`：24 幅可编辑 draw.io 图，同时提供 SVG 矢量图和高分辨率 PNG。
- `ui/`：从 localhost 上实际运行的系统截取；包括完整页面、表单、角色视图和响应式手机页面。
- `code/`：源码片段的排版截图，保留原文件名、原行号；HTML 和 sources 中的文本可复核。
- `evidence/`：本次真实测试结果截图，及仓库已有原始性能样本绘制的图。
- `index.html`：可按类型筛选的完整图册。
- `manifest.json`：来源、建议章节、尺寸、时间和 SHA-256。
- `review/`：缩略联系表，用于整体检查。

## 数据与范围

- 手机图是响应式 Web，不代表开发了原生 App。
- 截图使用已有演示数据；表单截图仅打开和填写草稿，不提交库存、账户或目录改动。
- 测试结果来自本次执行：后端 Testcontainers 集成测试 27 项，前端 Vitest 测试 3 项。浏览器检查详见 sources/ui-verification.json。
- 性能图来自 docs/evidence/cache-benchmark.json 的历史测试，原始记录日期为 2026-10-03 UTC；16 商品、并发 1、每模式 600 样本。没有把这些数据冒充本次测试。
- 类图、权限图、数据库关系依据当前源码。固定角色没有继承关系；Redis 是可选预警缓存。
- 代码图只做显示换行和语法着色，不改写源码。

## 全部素材

| 编号 | 建议章节 | 类型 | 图题与 PNG |
|---|---:|---|---|
| 01 | 1 | diagram | [Overall functional model](diagrams/01-functional-model.png) |
| 02 | 1 | diagram | [Catalogue management use cases](diagrams/02-uc-catalogue.png) |
| 03 | 1 | diagram | [Stock activity use cases](diagrams/03-uc-stock.png) |
| 04 | 1 | diagram | [Warning management use cases](diagrams/04-uc-warning.png) |
| 05 | 1 | diagram | [Inventory reporting use cases](diagrams/05-uc-report.png) |
| 06 | 1 | diagram | [Identity and administration use cases](diagrams/06-uc-access.png) |
| 07 | 2 | diagram | [Fixed role authorization model](diagrams/07-permission-model.png) |
| 08 | 3 | diagram | [Layered runtime architecture](diagrams/08-runtime-architecture.png) |
| 09 | 3 | diagram | [Frontend module structure](diagrams/09-frontend-structure.png) |
| 10 | 3 | diagram | [Backend module structure](diagrams/10-backend-structure.png) |
| 11 | 3 | diagram | [Overall relational schema](diagrams/11-er-overall.png) |
| 12 | 3 | diagram | [Product category and supplier relationships](diagrams/12-er-catalogue.png) |
| 13 | 3 | diagram | [Stock audit relationships](diagrams/13-er-movements.png) |
| 14 | 3 | diagram | [Warning episode and reviewer relationships](diagrams/14-er-warnings.png) |
| 15 | 3 | diagram | [Settings and cache revision tables](diagrams/15-er-support.png) |
| 16 | 3 | diagram | [Core domain UML class diagram](diagrams/16-uml-domain.png) |
| 17 | 3 | diagram | [Service and repository UML dependencies](diagrams/17-uml-service.png) |
| 18 | 4 | diagram | [Session authentication sequence](diagrams/18-seq-login.png) |
| 19 | 4 | diagram | [Audited stock movement sequence](diagrams/19-seq-stock.png) |
| 20 | 4 | diagram | [Warning page cache sequence](diagrams/20-seq-warning.png) |
| 21 | 4 | diagram | [Stock movement transaction workflow](diagrams/21-stock-flow.png) |
| 22 | 3 | diagram | [Stock warning episode lifecycle](diagrams/22-warning-state.png) |
| 23 | 3 | diagram | [Request authentication and authorization](diagrams/23-security-flow.png) |
| 24 | 4 | diagram | [Implemented local deployment topology](diagrams/24-deployment.png) |
| 25 | 4 | ui | [Desktop sign-in interface](ui/01-login-desktop.png) |
| 26 | 4 | ui | [Administrator dashboard](ui/02-dashboard.png) |
| 27 | 4 | ui | [Inventory search and stock status](ui/03-inventory.png) |
| 28 | 4 | ui | [Product catalogue](ui/04-catalogue.png) |
| 29 | 4 | ui | [Category management](ui/05-categories.png) |
| 30 | 4 | ui | [Supplier directory](ui/06-suppliers.png) |
| 31 | 4 | ui | [Attributed stock movement history](ui/07-history.png) |
| 32 | 4 | ui | [Open warning board](ui/08-warnings.png) |
| 33 | 4 | ui | [Inventory reporting](ui/09-reports.png) |
| 34 | 4 | ui | [Staff and role administration](ui/10-team.png) |
| 35 | 4 | ui | [Store settings](ui/11-settings.png) |
| 36 | 2 | ui | [Product search by text](ui/12-inventory-search.png) |
| 37 | 5 | ui | [Empty-search recovery state](ui/13-empty-search.png) |
| 38 | 4 | ui | [Product creation form](ui/14-add-product.png) |
| 39 | 4 | ui | [Existing product and threshold edit form](ui/15-edit-product.png) |
| 40 | 4 | ui | [Stock receipt form](ui/16-stock-receipt.png) |
| 41 | 4 | ui | [Stock dispatch form](ui/17-stock-dispatch.png) |
| 42 | 4 | ui | [Signed stock adjustment form](ui/18-stock-adjustment.png) |
| 43 | 4 | ui | [Absolute stocktake form](ui/19-stocktake.png) |
| 44 | 4 | ui | [Category creation form](ui/20-category-form.png) |
| 45 | 4 | ui | [Supplier creation form](ui/21-supplier-form.png) |
| 46 | 4 | ui | [Staff account creation form](ui/22-account-form.png) |
| 47 | 4 | ui | [Manager threshold-only edit form](ui/23-manager-thresholds.png) |
| 48 | 4 | ui | [Manager warning-review workspace](ui/24-manager-workspace.png) |
| 49 | 4 | ui | [Clerk stock-activity workspace](ui/25-clerk-workspace.png) |
| 50 | 4 | ui | [Responsive Web sign-in on a phone](ui/26-mobile-login.png) |
| 51 | 4 | ui | [Responsive Web inventory on a phone](ui/27-mobile-inventory.png) |
| 52 | 4 | code | [Pessimistic product row locking](code/01-code-product-lock.png) |
| 53 | 4 | code | [Atomic stock movement with audit and replay checks](code/02-code-stock-transaction.png) |
| 54 | 4 | code | [Stock filtering and deterministic pagination](code/03-code-product-filter.png) |
| 55 | 4 | code | [Revision-based warning cache and database fallback](code/04-code-warning-cache.png) |
| 56 | 4 | code | [Warning episode transitions and recovery](code/05-code-warning-lifecycle.png) |
| 57 | 4 | code | [Session security CSRF and endpoint authorization](code/06-code-security.png) |
| 58 | 4 | code | [Session authentication and session ID rotation](code/07-code-session-login.png) |
| 59 | 4 | code | [Typed frontend API and CSRF header interceptor](code/08-code-api-client.png) |
| 60 | 4 | code | [Authenticated route and role navigation guards](code/09-code-navigation.png) |
| 61 | 3 | code | [Stock history schema and idempotency constraint](code/10-code-schema.png) |
| 62 | 4 | code | [MySQL and Redis container configuration](code/11-code-deployment.png) |
| 63 | 5 | code | [Concurrent dispatch and identical-submission tests](code/12-code-concurrency-tests.png) |
| 64 | 5 | code | [Frontend zero and threshold equality tests](code/13-code-boundary-tests.png) |
| 65 | 4 | code | [Stock form request key and submission guard](code/14-code-stock-form.png) |
| 66 | 5 | test-result | [Backend integration tests · current run](evidence/01-backend-tests.png) |
| 67 | 5 | test-result | [Frontend threshold tests · current run](evidence/02-frontend-tests.png) |
| 68 | 5 | test-result | [Browser capture and role checks · current run](evidence/03-browser-verification.png) |
| 69 | 5 | benchmark-plot | [Local warning-query latency summary](evidence/04-latency-summary.png) |
| 70 | 5 | benchmark-plot | [Empirical warning-query latency distribution](evidence/05-latency-ecdf.png) |
| 71 | 5 | benchmark-plot | [Warning-query latency variability](evidence/06-latency-boxplot.png) |

## 再生成

脚本位于仓库 scripts/，打包副本位于 sources/reproduction/。使用 workspace dependency loader 给出的 Python 和 Node 可执行文件。先用 Python 的 pip 将 scripts/paper-figure-requirements.txt 安装到 .runtime/paper-figure-deps；本机 draw.io CLI 用于 SVG 和 PNG 导出。

顺序：运行 prepare-paper-diagrams.py；启动已有应用后运行 capture-paper-ui.mjs；运行现有后端与前端测试并保存日志到 sources；运行 prepare-paper-code.py 与 prepare-paper-plots.py；运行 render-paper-images.mjs；最后运行 review-paper-figures.py 更新图册和压缩包。后端 Testcontainers 使用当前 Colima socket：DOCKER_HOST=unix:///Users/fch/.colima/default/docker.sock。
