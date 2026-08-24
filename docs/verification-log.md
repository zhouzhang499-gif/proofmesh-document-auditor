# ProofMesh v0.1.0 复验记录

复验日期：2026-08-24

## 自动验证

- 通用 Agent Skill 结构校验：通过。
- 自动测试：27/27 通过。
- 量化评测：100 条事实对；TP=50、FP=0、FN=0、TN=50；Precision、Recall、F1、Accuracy 均为 100%。
- README、参赛文章和 Qoder 测试矩阵表达扫描：0 finding。
- 锁定依赖安全扫描：未报告已知漏洞。

## ModelScope 轻量包

- 文件：`proofmesh-modelscope-v0.1.0.zip`
- 大小：小于 1MB；精确字节数与 SHA256 以发布资产和同名 `.sha256` 文件为准。
- ZIP 条目：73 个。
- 根目录 `SKILL.md`：1 个。
- `.venv`、构建目录、运行报告、缓存、凭证、个人绝对路径和模型权重：0 个。
- ZIP 内 `SKILL.md` 具备 `name`、`version`、`description`；仓库中的通用版不含非标准顶层 `version`。

## 干净环境与模型分发

- 干净目录安装验证通过；依赖来自独立虚拟环境，并由 `requirements.lock` 锁定。
- 从独立模型归档安装后，9 个模型文件的大小和 SHA256 全部吻合；下载字节数、解压总量、条目数和文件白名单均受限。
- 从公开 GitHub Release 的默认地址重新下载成功，归档 SHA256 为 `2df1ad03de1359859eb59ea168d770eaebd49634ed82e9a4f3e4d2b7e861a561`。
- 把下载地址改成不可达地址后，已缓存模型仍可完成审计，证明热运行不依赖网络。

## 演示审计

- 输入：2 个 XLSX、1 个 DOCX、1 个 PPTX、1 个带文本层 PDF。
- 结果：状态 `complete`，2 个确定性问题，1 个待确认候选。
- 模型：OpenVINO 2026.3.0，设备 CPU。
- 输入文件处理前后 SHA256 全部相同。
- 离线热运行编号：`20260824T105022Z-cf169fdc`。

## Qoder CLI 实机矩阵

- Qoder CLI 1.1.28 已登录，`proofmesh-document-auditor` 已识别并启用。
- 自动触发 6/6、手动触发 2/2、负向路由 2/2，总计 10/10 通过；所有进程退出状态为 0。
- 7 个测试输入文件的 SHA256 在执行前后不变；7 个审计运行的 `input_manifest.json` 均满足 `before == after`。
- 扫描 PDF 返回 `partial` 与 `needs_ocr`；损坏 XLSX 返回 `partial`、文件状态 `error`，并在 `run.json.errors` 中留下错误。
- 实测发现的 Windows 控制台乱码已通过固定 UTF-8 I/O 修正；隐私说明已明确区分本地源文件、完整报告与进入 Agent 对话的精简摘要。两项均已追加 Qoder 回归。
- 服务关闭后由本地客户端自动重启，并在 Qoder session 中完成新审计；恢复运行编号为 `20260824T115246Z-aece63b7`。
- Skill 已明确 locator 不是源文档页面截图；查询同一运行的回归 session 准确说明报告内容且没有重新扫描。
- 逐条证据：`docs/evidence/qoder/2026-08-24-cli-session-log.md`。

## 仍需平台侧完成

- ModelScope 公开 Skill 上传与页面回读。
- Qoder 展示截图与完整录屏；CLI session 和结构化运行工件已完成。
- 研习社文章发布与 `Intel AI PC` 专题标签回读。
