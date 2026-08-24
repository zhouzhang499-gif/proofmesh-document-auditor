# ProofMesh v0.1.0 复验记录

复验日期：2026-08-24

## 自动验证

- 通用 Agent Skill 结构校验：通过。
- 自动测试：25/25 通过。
- 量化评测：100 条事实对；TP=50、FP=0、FN=0、TN=50；Precision、Recall、F1、Accuracy 均为 100%。
- README、参赛文章和 Qoder 测试矩阵表达扫描：0 finding。
- 锁定依赖安全扫描：未报告已知漏洞。

## ModelScope 轻量包

- 文件：`proofmesh-modelscope-v0.1.0.zip`
- 大小：小于 1MB；精确字节数以发布资产为准。
- ZIP 条目：70 个。
- 根目录 `SKILL.md`：1 个。
- `.venv`、构建目录、运行报告、缓存、凭证、个人绝对路径和模型权重：0 个。
- ZIP 内 `SKILL.md` 具备 `name`、`version`、`description`；仓库中的通用版不含非标准顶层 `version`。

## 干净环境与模型分发

- 干净目录安装验证通过；依赖来自独立虚拟环境，并由 `requirements.lock` 锁定。
- 从独立模型归档安装后，9 个模型文件的大小和 SHA256 全部吻合。
- 从公开 GitHub Release 的默认地址重新下载成功，归档 SHA256 为 `2df1ad03de1359859eb59ea168d770eaebd49634ed82e9a4f3e4d2b7e861a561`。
- 把下载地址改成不可达地址后，已缓存模型仍可完成审计，证明热运行不依赖网络。

## 演示审计

- 输入：2 个 XLSX、1 个 DOCX、1 个 PPTX、1 个带文本层 PDF。
- 结果：状态 `complete`，2 个确定性问题，1 个待确认候选。
- 模型：OpenVINO 2026.3.0，设备 CPU。
- 输入文件处理前后 SHA256 全部相同。
- 离线热运行编号：`20260824T105022Z-cf169fdc`。

## 仍需平台侧完成

- ModelScope 公开 Skill 上传与页面回读。
- Qoder Skill 发现、10 次触发矩阵、截图和录屏。
- 研习社文章发布与 `Intel AI PC` 专题标签回读。
