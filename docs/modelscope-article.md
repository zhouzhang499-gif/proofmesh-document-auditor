# ProofMesh：把跨文档数字冲突留在本机查清楚

> 文章状态：参赛发布稿草案  
> 项目版本：0.1.0  
> 最后核对：2026-08-24  
> 尚待补充：公开 Skill 链接、Qoder 展示截图与录屏、性能与断网结果

咨询方案、项目预算、管理层汇报和合同摘要往往不是一个文件。它们由不同的人维护，也会在不同时间修改。单独打开每份材料时，1260 万元和 126 万元都像一个正常数字；等到汇报开始，跨文件的不一致才暴露出来。

ProofMesh 是一个面向交付前检查的本地 Skill。它读取用户指定目录中的 XLSX、DOCX、PPTX 和带文本层的 PDF，提取金额、百分比、日期以及同比、环比口径，把可以确认的问题连回文件位置。当前版本不会修改源文件，也不会替用户决定哪个值正确。

![ProofMesh 项目图标](../assets/proofmesh-icon.png)

本项目参加 [ModelScope Production AI Skills 大赛](https://www.modelscope.cn/events/289/summary)。目前与赛事要求的对应情况如下。

| 赛事关注点 | ProofMesh 的做法 | 当前证据状态 |
|---|---|---|
| 真实生产力场景 | 检查项目交付文件夹中的跨格式事实漂移 | 四格式原创演示包、27 项自动测试和 100 条事实对评测已完成 |
| 本地 AI 与 OpenVINO | 本地中文嵌入模型为近似指标候选打分 | CPU 链路已验证；GPU/NPU 未验证 |
| 生产力 Agent 集成 | 以 Qoder 为首要宿主，支持自动与手动触发 | Qoder CLI 十条实机矩阵 10/10 通过；展示截图与录屏待补 |
| 可复现与可商用基础 | 只读审计、结构化工件、Apache-2.0、第三方声明 | 公开发布包与公开页面待复验 |

## 场景从哪里来

传统校对擅长查错别字，表格校验擅长查单个工作簿。项目交付的麻烦在文件之间：预算表改过了，方案正文没有同步；汇报稿保留了旧日期；一个文件写同比，另一个文件沿用了环比。

这类错误有三个共同点：

- 事实散落在不同格式里；
- 错误通常需要两处证据才能说明；
- 文件可能包含报价、客户信息和经营数据，不适合把全文交给不受控的在线服务。

ProofMesh 目前把目标收得很窄：发现、定位、解释。自动改写和业务裁决都不在 0.1.0 的范围内。这个边界让结果更容易复查，也降低了误操作对正式交付物的影响。

## 从第一性原理倒推实现

交付审计的结果需要回答三个问题：哪里不一致，依据是什么，接下来该确认什么。模型生成一段流畅摘要并不能替代证据。

因此，ProofMesh 把一组带来源位置的事实记录作为中间产物，Markdown 只承担阅读和展示。记录中保留原文件相对路径、文档哈希、定位符、原始值、归一化值和抽取方式。不同格式使用各自能复核的位置：Excel 使用 `工作表!单元格`，PowerPoint 使用幻灯片和形状，Word 使用段落或表格位置，数字 PDF 使用页码及坐标。

确定性检查放在主链上。金额、百分比、日期、单位和增长口径经过归一化后，由版本化规则判断冲突。名称相似但含义尚未确认的指标只进入复核候选，不能被写成确定问题。

这一安排也决定了 AI 的位置。RapidFuzz 负责找出字面接近的名称，本地 OpenVINO 嵌入模型给候选打语义分。它们帮助扩大召回范围，不承担最终裁决。

## 公开项目给了哪些启发

调研没有从“能接多少模型”出发，而是围绕证据、复现、许可和本地运行筛选公开资源。

| 公开项目 | 值得采用的部分 | ProofMesh 中的落点 |
|---|---|---|
| [OpenVINO local-ai-skill-authoring](https://github.com/openvino-dev-samples/local-ai-skill-authoring) | 单一入口、短客户端与常驻服务分离、命名管道、本地模型管理 | `run.ps1 → client.py → server.py` 的调用链 |
| [Docling](https://github.com/docling-project/docling) | 统一文档模型、来源信息和版面位置 | 统一事实记录，但保留各格式的原生 locator |
| [Unstructured](https://github.com/Unstructured-IO/unstructured) | `partition → typed elements → metadata` 的处理思路 | 把解析、事实抽取和规则检查分层 |
| [Great Expectations](https://github.com/great-expectations/great_expectations) | 版本化规则和人可读验证结果 | YAML 规则、结构化问题和本地报告 |
| [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz) | 快速、可解释的字符串相似度 | 只做近似名称候选召回 |
| [OpenLineage](https://github.com/OpenLineage/OpenLineage) | 运行状态与输入输出追踪 | 每次检查保存运行记录、模型信息、规则哈希和输入哈希 |
| [Vale](https://github.com/errata-ai/vale) 与 [Proselint](https://github.com/amperser/proselint) | 配置化写作规则和结构化 finding | README、报告与 Agent 摘要共用本地写作检查 |

项目没有把这些仓库拼成一套重型依赖。Office 文件使用 `openpyxl`、`python-docx` 和 `python-pptx` 保留原生位置；数字 PDF 使用 `pdfplumber`。公开项目提供的是设计参照，具体规则、数据结构和报告链路由 ProofMesh 独立实现。详细的写作研究与许可证处理记录在 [`docs/human-writing-research.md`](human-writing-research.md) 和 [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md)。

## 架构：Agent 负责意图，本地服务负责证据

```text
Qoder / 其他生产力 Agent
          |
          | 调用 scripts/run.ps1
          v
   短生命周期 client.py
          |
          | Windows Named Pipe + 当前用户认证键
          v
      常驻 server.py
          |
          +-- DOCX / PPTX / XLSX / 数字 PDF 解析
          +-- 事实归一与确定性规则
          +-- RapidFuzz 候选召回
          +-- OpenVINO 本地语义打分（当前验证设备：CPU）
          +-- 本地运行记录与 JSON / Markdown / HTML 报告
```

客户端只负责传递命令并接收结构化结果。服务首次调用时启动，后续调用复用同一条本地链路。每次运行保存在 `%LOCALAPPDATA%\ProofMesh\runs\<run_id>`；测试环境可以通过 `PROOFMESH_HOME` 改到临时目录。

主要工件包括：

- `issues.json`：确定性规则确认的问题；
- `review_candidates.json`：仍需人工确认的近似指标；
- `file_results.json`：每个文件的解析状态和失败原因；
- `input_manifest.json`：输入文件处理前后的 SHA256；
- `model_info.json` 与 `matching_info.json`：模型、设备、阈值、规则及清单信息；
- `report.md`、`report.html`：本地完整报告；
- `agent_summary.json`：返回 Agent 的精简结果。

![ProofMesh 本地文档一致性审计架构](../assets/architecture.svg)

## OpenVINO 在主链里做什么

当前语义模型为 `bge-small-zh-v1.5` 的 OpenVINO 版本，使用 `TextEmbeddingPipeline` 在 CPU 上生成归一化嵌入。模型文件加载前会根据 `model-manifest.json` 检查文件大小和 SHA256。校验失败、模型缺失或加载异常时，运行状态会标为 `partial`，报告说明“近似指标候选未执行”。确定性规则仍可继续处理已经成功解析的事实。

这条链路区分了两种结果：

- 同一规范化指标出现不同值，可以进入 `issues.json`；
- “项目实施费用”和“项目执行费用”看起来相近，只能进入 `review_candidates.json`。

当前公开材料只记录了 CPU 实测。GPU 与 NPU 尚无可复核结果，本文不把它们写成已经支持的设备。

模型与轻量 Skill 分开发布。当前独立模型包为 `proofmesh-openvino-model-v0.1.0.zip`，SHA256 为 `2df1ad03de1359859eb59ea168d770eaebd49634ed82e9a4f3e4d2b7e861a561`。下载器按发布清单限制归档字节数，并拒绝越界路径、符号链接、未声明文件、重复文件和超量解压。加入图标、评测数据和发布文档后的 ModelScope 轻量包仍小于 1MB；最终归档哈希由打包脚本写入同名 `.sha256` 文件，避免把归档自身哈希写进归档。

【待填：`model_info.json` 或 Qoder 运行中的 CPU 设备截图】

## 隐私边界

ProofMesh 的解析、规则匹配、语义打分和报告生成都在本机完成。源文件不会被写回；处理前后哈希不一致时，本次结果会停止生成。默认返回 Agent 的是问题数量、简短标题和本地报告路径，完整证据留在运行目录。

本地运行不等于宿主完全离线。Qoder 如何处理用户输入仍取决于宿主自身的服务与隐私条款。因此，Skill 把工具返回值压缩到完成任务所需的范围，避免把整份文档原文放进对话上下文。文档中的指令性文字也只作为待检查数据，不会改变 Skill 的扫描范围或执行规则。

还有几条明确限制：首版拒绝 UNC 和网络路径；遇到符号链接或 Windows 重解析点会中止；`PROOFMESH_HOME` 不能位于待检查目录内部；服务使用按当前用户和运行目录派生的命名管道及本地认证键。

## 在 Qoder 中复现

Qoder 官方文档支持用户级和项目级 Skill。项目级目录为 `.qoder/skills/{skill-name}/SKILL.md`，用户级目录为 `~/.qoder/skills/{skill-name}/SKILL.md`；重启 Qoder 后可以通过自然语言自动触发，也可以输入 `/skill-name` 手动调用。参见 [Qoder Skills 文档](https://docs.qoder.com/extensions/skills)。

以下步骤已在 Qoder CLI 1.1.28 的登录账号中逐条执行。最终结果为自动触发 6/6、手动触发 2/2、负向路由 2/2，总计 10/10 通过。完整 session ID、`run_id`、输入哈希和回归记录见 [`docs/evidence/qoder/2026-08-24-cli-session-log.md`](evidence/qoder/2026-08-24-cli-session-log.md)。

1. 将最终发布目录放到 `.qoder/skills/proofmesh-document-auditor/`，确认该目录下直接包含 `SKILL.md`、`scripts/`、`src/`、`rules/` 和运行依赖说明。
2. 在 Windows PowerShell 中安装运行环境：

   ```powershell
   .\scripts\install.ps1
   ```

3. 重启 Qoder，在对话框输入 `/`，确认 `proofmesh-document-auditor` 已被识别。
4. 准备演示目录后输入：

   > 请在提交客户前检查这个项目文件夹，核对金额、日期、单位和同比环比口径，不要修改原文件：`<演示目录绝对路径>`

5. 手动触发时输入：

   ```text
   /proofmesh-document-auditor 检查 <演示目录绝对路径>，不要扩大扫描范围。
   ```

6. 对照 [`docs/qoder-test-matrix.md`](qoder-test-matrix.md) 保存十条对话、运行编号、退出状态和本地工件。

不经过 Qoder时，可以在项目目录直接运行：

```powershell
.\scripts\run.ps1 audit -Path .\examples\demo_bundle
.\scripts\run.ps1 status
.\scripts\run.ps1 show -RunId <run_id>
```

【待填：Qoder 自动触发截图】  
【待填：Qoder 手动触发截图】  
【待填：完整录屏链接】

## 当前演示与完整评测

仓库中的原创演示包包含 2 个 XLSX、1 个 DOCX、1 个 PPTX 和 1 个带文本层 PDF。`ground_truth.json` 记录了 2 个确定性问题和 1 个待确认候选。现有自动测试覆盖四种格式解析、证据位置、输入哈希不变、OpenVINO CPU 加载、损坏文件、扫描型 PDF、Excel 公式无缓存值和报告写作规则。

2026-08-24 的最新本机复验使用 Windows 11、Python 3.11.9 和 OpenVINO 2026.3.0，27 项自动测试全部通过。同一环境的演示审计处理了 5 个支持文件，得到 2 个确定性问题和 1 个待确认候选；运行记录中的设备为 CPU，输入文件处理前后哈希一致。Qoder CLI 随后完成十条路由与交互测试，所有进程退出状态均为 0。

量化评测包含 100 条可复现事实对：40 条明确冲突、40 条明确一致和 20 条困难样例。每条样例都经过项目实际的 `parse_fact` 归一化和 `find_issues` 确定性规则。最新结果为 TP=50、FP=0、FN=0、TN=50，Precision、Recall、F1 与 Accuracy 均为 100%；明确样例与困难样例的正确率都是 100%，定位字段完整率为 100%。数据集 SHA256 为 `7c8ef65a3e732eb416617563fcc711d96e1f2dd7ab3bb7ea7f0f27752ac69a8f`。

这组数据用于验证事实解析与确定性规则，不能外推为任意真实文档都能达到 100%。事实对评测本身不覆盖 Qoder 路由、扫描 PDF OCR、语义候选 Top-3 召回、冷启动和热运行性能；Qoder 路由由独立十条矩阵验证，扫描 PDF 当前仍明确标记为 `needs_ocr`。完整结果与逐样例记录保存在 [`evaluation/results/evaluation.md`](../evaluation/results/evaluation.md) 和 [`evaluation/results/evaluation.json`](../evaluation/results/evaluation.json)。

| 指标 | 结果 | 证据 |
|---|---:|---|
| 自动测试 | 27/27；Windows 11、Python 3.11.9、OpenVINO 2026.3.0 | 【待填：正式测试日志或 CI 链接】 |
| 确定性问题 Precision | 100% | `evaluation/results/evaluation.json` |
| 确定性问题 Recall | 100% | `evaluation/results/evaluation.json` |
| 确定性问题 F1 | 100% | `evaluation/results/evaluation.json` |
| Accuracy | 100% | `evaluation/results/evaluation.json` |
| 明确样例正确率 | 100%（80/80） | `evaluation/results/evaluation.json` |
| 困难样例正确率 | 100%（20/20） | `evaluation/results/evaluation.json` |
| 定位字段完整率 | 100%（800/800） | `evaluation/results/evaluation.json` |
| 模糊候选 Top-3 Recall | 未单独评测 | 当前数据集只评估确定性事实对 |
| 冷启动耗时 | 【待填】 | 【待填：设备与运行日志】 |
| 热运行耗时 | 【待填】 | 【待填：设备与运行日志】 |
| Qoder 调用 | 10/10 | `docs/evidence/qoder/2026-08-24-cli-session-log.md` |
| 断网热运行 | 【待填】 | 【待填：网络状态与运行记录】 |

评测发布时还会写明 Windows、Python、OpenVINO 版本、CPU 型号、文件数量和页数构成。未达到目标的数据保留原值，不用“整体表现良好”代替误差分析。

## 已知限制

- 扫描 PDF 没有 OCR 主链；没有文本层时，文件状态为 `needs_ocr`，整次运行为 `partial`。
- Excel 公式不会在 ProofMesh 内重新计算。公式缺少缓存值时，相关数值不参与核对，并在报告中提示。
- 当前只承诺常见文本框、表格和数字 PDF；复杂图表、SmartArt、旧版 `.doc/.ppt/.xls` 以及加密文件没有进入支持范围。
- 语义候选仍需人工判断。相似分数不能证明两个指标业务含义相同。
- 当前设备验证只有 CPU。GPU/NPU、完整性能基准和 OCR 都需后续实测。
- ProofMesh 是交付前辅助工具，不提供法律、财务或投标合规结论。

## 对 Hybrid AI 的理解

混合 AI 不必把同一任务平均分给云端和本地。更实用的分工是按风险拆开：Agent 理解用户意图、确认目录并组织结果；本地 Skill 读取敏感文件、执行可复现检查并保存证据。对话里只返回完成协作所需的信息，原文和完整报告留在设备上。

这套边界仍有改进空间。用户以后如果主动要求解释某条冲突，Agent 可以在得到明确同意后读取一小段证据；企业版也可以接入本地规则包和人工确认流程。无论如何，确定性结论、模型候选和人工判断应继续分开记录。

## 发布信息

- ModelScope Skill：【待填：公开 Skill 链接】
- 源码仓库：[zhouzhang499-gif/proofmesh-document-auditor](https://github.com/zhouzhang499-gif/proofmesh-document-auditor)
- GitHub Release：[ProofMesh v0.1.0](https://github.com/zhouzhang499-gif/proofmesh-document-auditor/releases/tag/v0.1.0)
- 演示录屏：【待填：公开录屏链接】
- License：Apache-2.0
- 自定义标签：`AI PC`、`OpenVINO`、`文档一致性`、`本地隐私`、`交付质检`
- 当前轻量包：小于 1MB；最终字节数与 SHA256 以 `dist` 中同名 `.sha256` 文件为准
- 独立模型包 SHA256：`2df1ad03de1359859eb59ea168d770eaebd49634ed82e9a4f3e4d2b7e861a561`

GitHub 源码、Release 资产和默认模型下载地址已经回读，轻量包也已在没有开发缓存的新目录完成安装与演示审计。Qoder CLI 十条矩阵已完成；ModelScope 页面、Qoder 展示截图和录屏仍按 [`docs/submission-checklist.md`](submission-checklist.md) 保留为待办，取得平台证据后再替换相应“待填”项。
