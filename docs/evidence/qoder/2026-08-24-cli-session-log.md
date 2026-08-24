# Qoder CLI 实测记录（2026-08-24）

## 环境

- Qoder CLI：1.1.28
- 账号：已登录（记录中不保存邮箱或认证信息）
- Skill：`proofmesh-document-auditor`，用户级目录已识别并启用
- 运行方式：每条请求使用独立的 `qoder -p` 会话，退出状态均为 0
- 测试输入：`%TEMP%\ProofMesh-Qoder-20260824\`
- ProofMesh 工件：`%LOCALAPPDATA%\ProofMesh\runs\<run_id>\`

Qoder 的会话正文由本机 CLI 保存，可通过下面的 session ID 回读。仓库不复制完整对话，避免把用户目录和本地运行路径固化进公开包。

## 十条测试

| 编号 | 触发结果 | Qoder session ID | ProofMesh run_id | 结果 | 核验要点 |
|---:|---|---|---|---|---|
| 01 | 自动触发 | `3a4110dc-9acd-432b-82ce-bbf3b06a8310` | `20260824T113327Z-1f04eda9` | 通过 | 5/5 文件；2 个确定性问题；1 个候选；返回本地报告 |
| 02 | 自动触发 | `26fdd8a0-e50f-4ca0-b68a-800a7b0cce44` | `20260824T113442Z-d05d0467` | 通过 | 只扫描指定目录；保留 PPTX 与 XLSX locator；不代选正确值 |
| 03 | 自动触发 | `7d6675dc-8852-4b37-a79c-098d9c67766f` | `20260824T114744Z-a23eb613` | 通过 | 明确源文件不上传、精简摘要进入当前对话；CPU 模型记录完整 |
| 04 | 自动触发 | `7be23e67-67ac-4d2a-a20d-ecbd9e6eddc0` | `20260824T113800Z-f4f2611f` | 通过 | 两个问题分别含 5 条和 4 条证据；处理前后哈希一致 |
| 05 | 自动触发 | `07f2c798-2199-46f4-82c1-35b99ab6c76d` | `20260824T114613Z-8769375f` | 通过 | 状态 `partial`；`scan.pdf` 为 `needs_ocr`；没有误称“未发现冲突” |
| 06 | 手动触发 | `4275adcf-3ef5-4f78-bec8-a1b65d5dc70c` | `20260824T114024Z-3c03bcbb` | 通过 | CLI 显示 Skill activated；确定性问题和候选分开表达 |
| 07 | 手动触发 | `e578cd8f-fca2-478b-b0cc-6ad5f9e2736b` | 不适用 | 通过 | 查询 06 的运行；runs 数量保持 7，没有重新扫描 |
| 08 | 不触发 | `0942e753-9a32-4d28-9474-f1d50c92c366` | 不适用 | 通过 | 在隔离副本中完成 README 精简；runs 数量不变 |
| 09 | 不触发 | `ece4503b-8ac3-40a5-9fc7-a69f0f52b668` | 不适用 | 通过 | 只回答 SUM/SUMIF；runs 数量不变 |
| 10 | 自动触发 | `e498e545-9e20-4c0a-b4fa-66226cb3b95d` | `20260824T114340Z-216f2262` | 通过 | 状态 `partial`；`损坏.xlsx` 为 `error`；`run.json.errors` 有 1 条 |

## 输入哈希

以下 SHA256 在测试前后相同；每次审计的 `input_manifest.json` 也已逐项核对 `before == after`。

| 文件 | SHA256 |
|---|---|
| `normal/方案.docx` | `700747d383ecb993c19c4dd30800e1c9069189d1d5ea4e8c56d7fd28f0fdf804` |
| `normal/管理层汇报.pptx` | `00d635b7d447a386955c2d8ba249702681aaf8a8500202cbe4cea55d776cc1a7` |
| `normal/管理层汇报数据.xlsx` | `6ef0b076cb3a680fbfc5da59ded3ac17e61cec09fff69933196a2e49faa43566` |
| `normal/预算.xlsx` | `2fd40ff08dcb231087576a5ac8f77ba89eb61a4d323947cff30e8848ad09513b` |
| `normal/contract-summary.pdf` | `c567e8b6456f704e2414c366414329a9b736d2fd39202635e7ccc27f4672b3d8` |
| `scanned-pdf/scan.pdf` | `e84a4ac93e96b86a65845a533407d54f372bf26ede36beec71ca911d0cd8cf56` |
| `corrupt-xlsx/损坏.xlsx` | `b308d5e0287ce68d9b87b0ce137d235e68e4ea310d502ccd850cd6dd00b2533e` |

## 实测后修正与回归

首次扫描 PDF 测试中，Qoder 正确判断 `needs_ocr`，但把工具返回的中文 `message` 显示成乱码。`scripts/run.ps1` 随后固定为 UTF-8 控制台与 Python I/O；05 的最终 session 已确认乱码消失。

首次隐私场景使用了过宽的“全部在本机处理”说法。Skill 已改为清楚区分源文件、本地完整报告和进入 Agent 对话的精简摘要；03 的最终 session 已回归通过。

服务恢复测试关闭 PID 56064，本地客户端随即启动 PID 52840；Qoder session `859ea1c3-5f15-4d50-bb3c-d2eafe37690d` 完成审计并生成 run `20260824T115246Z-aece63b7`。

该恢复测试的首次回复把 locator 误写成“原文截图”。Skill 已明确报告只含提取值、文件位置和 locator，不含源文档页面截图；session `cc40c768-6d75-4a01-8123-10497ab9c80f` 查询同一 run 后准确说明了报告内容，且没有创建新运行。

## 尚需展示侧补充

CLI 会话和 ProofMesh 结构化工件已经齐全。参赛演示仍需录制一条不暴露账号、认证信息和个人绝对路径的视频，并截取自动触发、手动触发及本地 HTML 报告画面。
