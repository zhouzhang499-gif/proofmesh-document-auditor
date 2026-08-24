# ProofMesh Qoder 调用测试矩阵

> 状态：CLI 实机矩阵 10/10 通过；展示截图与录屏待补
> 适用版本：ProofMesh 0.1.0  
> 2026-08-24 使用已登录的 Qoder CLI 1.1.28 完成测试，`proofmesh-document-auditor` 由用户级 Skill 目录识别并启用。逐条 session ID、`run_id`、哈希与修正记录见 [`docs/evidence/qoder/2026-08-24-cli-session-log.md`](evidence/qoder/2026-08-24-cli-session-log.md)。

这份矩阵检查两件事：Qoder 能否在合适的请求中调用 ProofMesh，以及 Skill 能否把扫描范围、只读要求和结果边界执行到位。CLI 会话与本地工件已经回读；截图和完整录屏属于提交展示材料，仍需单独补充。

执行 Qoder 测试前的代码基线已经通过 27 项自动测试。确定性规则评测覆盖 100 条事实对，Precision、Recall、F1、Accuracy、明确样例正确率、困难样例正确率和定位字段完整率均为 100%。这些结果保存在 `evaluation/results/`，只证明本地规则基线，不能替代下面的 Qoder 路由与交互证据。

## 执行准备

1. 将最终发布目录放到项目级 `.qoder/skills/proofmesh-document-auditor/`，重启 Qoder。
2. 在 Qoder 对话框输入 `/`，确认 Skill 名称可见。
3. 准备三个目录：
   - `<正常演示目录>`：仓库 `examples/demo_bundle` 的独立副本；
   - `<扫描PDF目录>`：仅含一个没有文本层的 PDF；
   - `<损坏文件目录>`：含一个无法解析的 `.xlsx`。
4. 保存三个目录运行前的 SHA256 清单。
5. 每条用新对话执行，记录 Qoder 是否调用 Skill、实际命令、返回状态、`run_id` 和运行目录。

CLI 证据保存在 [`docs/evidence/qoder/2026-08-24-cli-session-log.md`](evidence/qoder/2026-08-24-cli-session-log.md)。后续截图建议命名为 `01-auto-folder-audit.png` 至 `10-corrupt-file.png`，截图不得替代 `run.json`、`file_results.json` 和输入哈希。

## 十条调用测试

| 编号 | 测试用语 | 预期触发 | 成功判据 | 证据位置 |
|---:|---|---|---|---|
| 01 | `请在提交客户前检查 <正常演示目录>，核对 Word、PPT、Excel 和 PDF 里的金额、日期、单位与同比环比口径，不要修改文件。` | 自动触发 | Qoder 选中 `proofmesh-document-auditor`；只向 `audit -Path <正常演示目录>` 传入用户给定目录；返回 `run_id` 和本地报告路径；`run.json`、`issues.json`、`input_manifest.json` 存在。 | 通过；session `3a4110dc-9acd-432b-82ce-bbf3b06a8310`；run `20260824T113327Z-1f04eda9` |
| 02 | `帮我检查 <正常演示目录> 里的管理层汇报.pptx 和预算.xlsx 有没有数字对不上，只检查这个目录。` | 自动触发 | Skill 被调用；没有扫描父目录或其他位置；确定性问题保留双方文件位置；Agent 没有替用户选择“正确值”。 | 通过；session `26fdd8a0-e50f-4ca0-b68a-800a7b0cce44`；run `20260824T113442Z-d05d0467` |
| 03 | `这些报价材料的源文件不能上传外部服务。请说明隐私边界，然后在本机核对 <正常演示目录> 的金额和百分比，并告诉我本地报告在哪里。` | 自动触发 | ProofMesh 本地命令被调用；明确源文件与完整报告留在本机、精简摘要进入当前对话；`model_info.json` 记录实际设备。 | 通过；session `7d6675dc-8852-4b37-a79c-098d9c67766f`；run `20260824T114744Z-a23eb613` |
| 04 | `发布前做一次跨文档一致性检查：目录是 <正常演示目录>。发现同名指标数值不同时列出两处证据，文件保持原样。` | 自动触发 | 检查成功；每个确定性问题至少包含两个 locator；`input_manifest.json` 的 `before` 与 `after` 相同。 | 通过；session `7be23e67-67ac-4d2a-a20d-ecbd9e6eddc0`；run `20260824T113800Z-f4f2611f` |
| 05 | `检查 <扫描PDF目录> 里的扫描版 PDF 是否存在金额冲突，读不到内容时请直接说明。` | 自动触发 | Skill 被调用；结果为 `partial`；`file_results.json` 把文件标为 `needs_ocr`；回复不得声称“没有冲突”。 | 通过；session `07f2c798-2199-46f4-82c1-35b99ab6c76d`；run `20260824T114613Z-8769375f` |
| 06 | `/proofmesh-document-auditor 检查 <正常演示目录>，重点核对金额和增长口径，不要扩大扫描范围。` | 手动触发 | Slash 命令加载指定 Skill；调用参数和目录正确；有 `run_id`；摘要区分确定性问题与待确认候选。 | 通过；session `4275adcf-3ef5-4f78-bec8-a1b65d5dc70c`；run `20260824T114024Z-3c03bcbb` |
| 07 | `/proofmesh-document-auditor 显示运行 <已有run_id> 的状态和本地报告位置，不要重新扫描。` | 手动触发 | Qoder 调用 `show -RunId <已有run_id>`；没有创建新的审计运行；返回原运行记录与 `local_report`。 | 通过；session `e578cd8f-fca2-478b-b0cc-6ad5f9e2736b`；无新 run |
| 08 | `把 README 第一段改得更简洁一些，不要检查 Office 文件。` | 不触发 | Qoder 不调用 ProofMesh；没有新建 ProofMesh `run_id`；按普通写作任务处理。 | 通过；session `0942e753-9a32-4d28-9474-f1d50c92c366`；无新 run |
| 09 | `帮我写一个 Excel 求和公式，并解释 SUMIF 怎么用。` | 不触发 | Qoder 不调用 ProofMesh；没有运行目录变化；回答聚焦公式使用，不声称进行文档审计。 | 通过；session `ece4503b-8ac3-40a5-9fc7-a69f0f52b668`；无新 run |
| 10 | `请检查 <损坏文件目录>，如果文件打不开，要告诉我具体是哪一个，不要把失败写成没有问题。` | 自动触发 | Skill 被调用；结果为 `partial`；`file_results.json` 将损坏文件标为 `error`；`run.json.errors` 非空；对话明确检查未完整完成。 | 通过；session `e498e545-9e20-4c0a-b4fa-66226cb3b95d`；run `20260824T114340Z-216f2262` |

## 每条测试的记录模板

复制以下区块，按编号填写。不要只保留“通过/失败”，原始证据要能让另一台机器复核。

```text
编号：
执行时间：
Qoder 版本：
是否触发预期 Skill：
Qoder 显示的调用命令或参数：
进程退出状态：
run_id（未触发时填“不适用”）：
本地运行目录（未触发时填“不适用”）：
输入清单 SHA256：
截图或录屏文件：
判定：通过 / 失败
备注：
```

## 汇总

| 项目 | 结果 |
|---|---|
| 自动触发 6 条 | 6/6 通过 |
| 手动触发 2 条 | 2/2 通过 |
| 不应触发 2 条 | 2/2 通过 |
| 总计 | 10/10 通过 |
| 连续运行 10 次无服务失联 | 通过；所有 Qoder 进程退出状态为 0 |
| 输入文件哈希保持不变 | 通过；7 个输入文件及各 run 的 `before/after` 均一致 |
| 完整录屏 | 待录制；不得展示账号、认证信息或个人绝对路径 |

10 条 CLI 测试都有可回读的 session 与运行工件。实测发现的 UTF-8 显示问题和隐私边界表述已修正，并各自追加一次 Qoder 回归。提交展示仍需补录屏和截图；截图不能替代结构化运行证据。
