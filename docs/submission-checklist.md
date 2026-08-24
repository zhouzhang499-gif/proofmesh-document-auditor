# ProofMesh 参赛提交检查表

> 适用版本：0.1.0  
> 比赛截止：2026-08-31 15:59  
> 内部提交目标：2026-08-31 12:00  
> 当前状态：代码、评测、公开仓库与 GitHub Release 已完成；ModelScope 上传、Qoder 实机矩阵和录屏待完成。未勾选项目不得写成已完成。

这份清单用于最终发布门禁。执行人应在每个完成项后补充证据路径、公开链接或命令输出。平台页面、ZIP 结构和录屏都需要回读，不能只凭上传成功提示判断完成。

## A. Skill 元数据与轻量包

- [x] `SKILL.md` 位于 ZIP 根目录，且整个 ZIP 只有一个 `SKILL.md`。
  - 证据：`scripts/package-modelscope.ps1` 回读 ZIP，确认根目录 `SKILL.md` 数量为 1。
- [x] frontmatter 包含 `name: proofmesh-document-auditor`、`version: 0.1.0` 和准确的 `description`。
  - 证据：`dist/proofmesh-modelscope-v0.1.0.zip` 中的 `SKILL.md`。
- [x] ModelScope 专用 ZIP 小于 5MB。
  - 证据：`dist/proofmesh-modelscope-v0.1.0.zip`，当前发布候选小于 1MB；最终字节数以打包命令输出为准。
  - 最终证据：`proofmesh-modelscope-v0.1.0.zip` 小于 1MB；精确字节数以打包输出为准，避免归档内容自指。
- [x] ZIP 不含 `.venv`、`.build`、运行报告、缓存、凭证、个人绝对路径和大型模型权重。
  - 证据：ZIP 回读 70 个条目；禁入项计数为 0。
- [x] ZIP SHA256 已计算并写入发布记录。
  - 证据：打包脚本同时生成 `dist/proofmesh-modelscope-v0.1.0.zip.sha256`，避免把归档自身哈希写进归档。
- [x] 英文名称为 `proofmesh-document-auditor`，展示名称为“ProofMesh 文档一致性检查”。
- [x] 发布文件采用 `Apache-2.0`；ModelScope 页面仍需在上传时选择同一 License。
- [ ] Skill 设为公开，并添加 `AI PC`、`OpenVINO`、`文档一致性`、`本地隐私`、`交付质检` 标签。
- [ ] 所有者为实际参赛账号或组织，没有使用项目署名代替平台所有者。
- [x] 来源地址指向已经公开并能访问的源码仓库。
  - 公开 Skill 链接：【待填】
  - 公开仓库链接：https://github.com/zhouzhang499-gif/proofmesh-document-auditor

## B. 模型与安装

- [x] 最终轻量包不再依赖仓库内的大型模型权重；模型分发方式与 README 一致。
- [x] 模型来源、固定 revision、文件大小、SHA256 和许可证写入 `model-manifest.json` 或等价发布清单。
  - 当前独立模型包：`dist/proofmesh-openvino-model-v0.1.0.zip`
  - SHA256：`2df1ad03de1359859eb59ea168d770eaebd49634ed82e9a4f3e4d2b7e861a561`
- [x] 全新用户目录可以完成安装，不读取开发机的 `.venv`、`.build` 或下载缓存。
  - 安装命令：解压轻量包后执行 `scripts\install.ps1`。
  - 安装结果：锁定依赖、独立模型下载和四格式演示审计均成功。
- [x] 模型完整时正常加载；文件缺失、大小错误、SHA256 错误和归档越界均有自动测试。
- [x] 模型缓存完成后，在不可达下载地址下热运行成功。
  - 证据：`run_id` 为 `20260824T105022Z-cf169fdc`，状态 `complete`。
- [x] `model_info.json` 记录实际设备和 OpenVINO 版本。
- [x] 文章和页面只陈述已实测的 CPU 链路；GPU/NPU 未作宣传。
- [x] `THIRD_PARTY_NOTICES.md` 与最终依赖、模型和分发文件一致。
- [x] Apache-2.0 完整许可证文本随包分发。

## C. 功能与失败路径

- [x] XLSX、DOCX、PPTX 和带文本层 PDF 均通过端到端检查。
- [x] 演示包得到与 `ground_truth.json` 一致的结果。
  - 期望：2 个确定性问题、1 个待确认候选。
  - 实际：2 个确定性问题、1 个待确认候选。
- [x] 金额、百分比、日期以及同比/环比口径至少各有覆盖样例。
- [x] 每个确定性问题保留文件路径和原生 locator。
- [x] 待确认候选与确定性问题分别保存在 `review_candidates.json` 和 `issues.json`。
- [x] 输入文件处理前后 SHA256 相同；发现变化时停止生成结果。
- [x] 扫描 PDF 无文本层时标记 `needs_ocr`，运行状态为 `partial`。
- [x] Excel 公式缺少缓存值时标记 `parsed_with_warnings`，不把公式字符串当成计算结果。
- [x] 损坏文件标记 `error`，运行状态为 `partial`，不得显示“没有发现问题”。
- [x] 模型不可用时，报告说明近似候选未执行。
- [x] UNC、网络路径、符号链接/重解析点越界和输出目录位于输入目录内的请求均被拒绝。
- [x] 源文档中的指令性文字只作为数据，不改变扫描目录与行为约束。

## D. 自动测试与量化评测

- [x] 执行全部自动测试；复验摘要写入 `docs/verification-log.md`。

  ```powershell
  python -m pytest
  ```

  - 最新结果：25/25 通过。
  - 环境：Windows 11、Python 3.11.9、OpenVINO 2026.3.0；CPU 运行链已验证。
  - 复验记录：`docs/verification-log.md`

- [x] README、参赛文章和测试矩阵的写作扫描均为 0 finding；演示运行的 `style_findings.json` 已回读。
- [x] 40 个明确冲突、40 个明确一致、20 个困难样例均有标准答案。
- [x] 评测脚本可一键复现，并输出原始 JSON 与汇总表。
- [x] 评测报告包含 TP、FP、FN、TN、Precision、Recall、F1 和 Accuracy。
- [x] 报告定位字段完整率。
- [ ] 报告 RapidFuzz、OpenVINO 与组合方案的候选召回消融结果。
- [ ] 报告冷启动、热运行耗时与峰值内存，并说明文件数量及页数构成。
- [ ] 所有未达目标的数据和误差样例保留原值，不用定性口号替代。
  - 评测结果：100 条；TP=50、FP=0、FN=0、TN=50；Precision、Recall、F1、Accuracy 均为 100%。
  - 分类结果：明确样例 80/80，困难样例 20/20，正确率均为 100%。
  - 定位字段：800/800 完整，完整率 100%。
  - 评测结果文件：`evaluation/results/evaluation.json`、`evaluation/results/evaluation.md`
  - 数据集 SHA256：`7c8ef65a3e732eb416617563fcc711d96e1f2dd7ab3bb7ea7f0f27752ac69a8f`
  - 当前误差样例：无。该结论只适用于本次可复现事实对数据集。

## E. Qoder 实机验证

- [ ] 最终 Skill 放入 Qoder 用户级或项目级目录后可以被识别。
- [ ] [`qoder-test-matrix.md`](qoder-test-matrix.md) 的 6 条自动触发测试全部执行。
- [ ] 2 条 `/proofmesh-document-auditor` 手动触发测试全部执行。
- [ ] 2 条不应触发的请求没有调用 ProofMesh。
- [ ] 10 条测试都有截图、实际参数、退出状态、`run_id` 或“不适用”记录。
- [ ] 连续运行 10 次无服务失联。
- [ ] 关闭服务后再次审计能够自动恢复。
- [ ] Qoder 回复只含完成任务所需的摘要，没有粘贴完整敏感原文。
- [ ] 录制一条完整视频，画面包含用户请求、Skill 调用和本地 HTML 报告。
  - Qoder 版本：【待填】
  - 矩阵结果：【待填：通过数/10】
  - 证据目录：【待填】
  - 录屏文件或链接：【待填】

## F. README、文章与展示材料

- [x] README 中的安装、审计、状态和查看运行命令均在干净环境逐条执行。
- [x] README 明确支持格式、扫描 PDF、Excel 公式、CPU 设备和不提供业务裁决等边界。
- [ ] [`modelscope-article.md`](modelscope-article.md) 中所有“待填”已替换为实际证据，或在发布稿中保留为明确的未完成说明。
- [x] 文章包含场景、第一性原理、公开项目取舍、架构、本地隐私、OpenVINO、评测、Qoder 复现、限制和 Hybrid AI 思考。
- [ ] 文章添加“Intel AI PC”专题标签。
- [ ] Skill 页面添加“AI PC”自定义标签。
- [ ] 方形图标已经上传，缩略图下仍能识别。
- [x] 架构图与代码中的真实链路一致。
- [ ] 截图覆盖 Qoder 触发、输入格式、本地 OpenVINO、问题摘要、证据位置和输入哈希。
- [ ] 录屏没有展示 Token、认证键、个人路径中的敏感信息或客户资料。
- [x] 所有演示文件为项目脚本原创生成。
- [x] 图注说明实际版本、设备和结果，不把计划能力写成当前能力。
  - 研习社文章链接：【待填】
  - 图标文件：`assets/proofmesh-icon.png`
  - 架构图文件：`assets/architecture.svg`
  - 截图目录：【待填】

## G. 公开仓库与发布记录

- [x] 仓库为公开状态，默认分支 `main` 可直接访问。
- [x] `.gitignore` 排除模型缓存、运行报告、虚拟环境和本地凭证。
- [x] 当前 Git 历史不含 Token、认证键、个人绝对路径和敏感文档。
- [x] Release 版本为 `v0.1.0`，包含轻量包、SHA256、安装说明和已知限制。
- [x] `LICENSE`、`THIRD_PARTY_NOTICES.md`、README 与实际发布内容一致。
- [x] Release 文件与 ModelScope 待提交文件属于同一版本，并用 SHA256 核对。
- [x] 没有复制许可证不明项目的源码、提示词或模板文本。
  - Release 链接：https://github.com/zhouzhang499-gif/proofmesh-document-auditor/releases/tag/v0.1.0
  - 提交 commit：【待填】

## H. 发布后回读

- [ ] 从 ModelScope 公开页面下载 Skill ZIP，并在一个没有开发缓存的目录解压。
- [ ] 解压后检查 `SKILL.md` 位置、文件大小、SHA256 和模型获取方式。
- [ ] 根据公开 README 重新安装并运行最小演示。
- [ ] 回读 Skill 页面中的名称、所有者、License、标签、描述、来源地址和公开状态。
- [ ] 打开研习社文章，检查图片、代码块、表格、链接和专题标签。
- [ ] 打开录屏链接，确认无需登录或特殊权限即可观看。
- [ ] 在比赛提交页打开 Skill 与文章链接，确认没有草稿或权限错误。
- [ ] 保存最终页面截图和提交时间。
  - 最终复验 `run_id`：【待填】
  - 最终复验日志：【待填】
  - 提交时间：【待填】
  - 页面截图：【待填】

## 最终签署

| 角色 | 姓名/账号 | 时间 | 结论 |
|---|---|---|---|
| 功能复验 | 【待填】 | 【待填】 | 【通过/不通过】 |
| 文档与许可证复验 | 【待填】 | 【待填】 | 【通过/不通过】 |
| Qoder 与录屏复验 | 【待填】 | 【待填】 | 【通过/不通过】 |
| ModelScope 发布复验 | 【待填】 | 【待填】 | 【通过/不通过】 |

四项结论都为“通过”后再提交比赛。任何一项缺少可回读证据，都应保留未完成状态并继续修正。
