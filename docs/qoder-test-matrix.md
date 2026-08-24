# ProofMesh Qoder 调用测试矩阵

> 状态：待实机执行  
> 适用版本：ProofMesh 0.1.0  
> 已确认 Qoder CLI 版本为 1.1.28，`proofmesh-document-auditor` 已在用户级 Skill 目录被识别并启用。当前 Qoder 账号未登录，因此 10 次 Agent 调用尚未执行；Windows、CPU、Python 与 OpenVINO 版本仍以正式录屏环境为准。

这份矩阵检查两件事：Qoder 能否在合适的请求中调用 ProofMesh，以及 Skill 能否把扫描范围、只读要求和结果边界执行到位。表中的“预期”不是实测结论；每条完成后必须补上截图、`run_id` 和本地工件。

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

建议证据命名为 `docs/evidence/qoder/01-auto-folder-audit.png` 至 `10-corrupt-file.png`。该目录和文件尚未创建，正式提交时应以实际截图或录屏替换下表中的占位符。

## 十条调用测试

| 编号 | 测试用语 | 预期触发 | 成功判据 | 证据位置 |
|---:|---|---|---|---|
| 01 | `请在提交客户前检查 <正常演示目录>，核对 Word、PPT、Excel 和 PDF 里的金额、日期、单位与同比环比口径，不要修改文件。` | 自动触发 | Qoder 选中 `proofmesh-document-auditor`；只向 `audit -Path <正常演示目录>` 传入用户给定目录；返回 `run_id` 和本地报告路径；`run.json`、`issues.json`、`input_manifest.json` 存在。 | 对话截图：【待填：`docs/evidence/qoder/01-auto-folder-audit.png`】；运行证据：`%LOCALAPPDATA%\ProofMesh\runs\<run_id>\` |
| 02 | `帮我检查 <正常演示目录> 里的管理层汇报.pptx 和预算.xlsx 有没有数字对不上，只检查这个目录。` | 自动触发 | Skill 被调用；没有扫描父目录或其他位置；确定性问题保留双方文件位置；Agent 没有替用户选择“正确值”。 | 对话截图：【待填：`docs/evidence/qoder/02-ppt-xlsx.png`】；`issues.json`、`report.html` |
| 03 | `这些报价材料不能上传外部服务。请在本机核对 <正常演示目录> 的金额和百分比，并告诉我本地报告在哪里。` | 自动触发 | ProofMesh 本地命令被调用；Agent 返回精简摘要和 `local_report`；对话回复不粘贴完整文档原文；`model_info.json` 记录实际设备。 | 对话截图：【待填：`docs/evidence/qoder/03-local-private.png`】；`agent_summary.json`、`model_info.json` |
| 04 | `发布前做一次跨文档一致性检查：目录是 <正常演示目录>。发现同名指标数值不同时列出两处证据，文件保持原样。` | 自动触发 | 检查成功；每个确定性问题至少包含两个 locator；`input_manifest.json` 的 `before` 与 `after` 相同。 | 对话截图：【待填：`docs/evidence/qoder/04-evidence-hash.png`】；`issues.json`、`input_manifest.json` |
| 05 | `检查 <扫描PDF目录> 里的扫描版 PDF 是否存在金额冲突，读不到内容时请直接说明。` | 自动触发 | Skill 被调用；结果为 `partial`；`file_results.json` 把文件标为 `needs_ocr`；回复不得声称“没有冲突”。 | 对话截图：【待填：`docs/evidence/qoder/05-scanned-pdf.png`】；`run.json`、`file_results.json`、`report.md` |
| 06 | `/proofmesh-document-auditor 检查 <正常演示目录>，重点核对金额和增长口径，不要扩大扫描范围。` | 手动触发 | Slash 命令加载指定 Skill；调用参数和目录正确；有 `run_id`；摘要区分确定性问题与待确认候选。 | 对话截图：【待填：`docs/evidence/qoder/06-manual-audit.png`】；`agent_summary.json`、`review_candidates.json` |
| 07 | `/proofmesh-document-auditor 显示运行 <已有run_id> 的状态和本地报告位置，不要重新扫描。` | 手动触发 | Qoder 调用 `show -RunId <已有run_id>`；没有创建新的审计运行；返回原运行记录与 `local_report`。 | 对话截图：【待填：`docs/evidence/qoder/07-manual-show.png`】；执行前后 runs 目录清单、对应 `run.json` |
| 08 | `把 README 第一段改得更简洁一些，不要检查 Office 文件。` | 不触发 | Qoder 不调用 ProofMesh；没有新建 ProofMesh `run_id`；按普通写作任务处理。 | 对话截图：【待填：`docs/evidence/qoder/08-negative-readme.png`】；执行前后 runs 目录清单 |
| 09 | `帮我写一个 Excel 求和公式，并解释 SUMIF 怎么用。` | 不触发 | Qoder 不调用 ProofMesh；没有运行目录变化；回答聚焦公式使用，不声称进行文档审计。 | 对话截图：【待填：`docs/evidence/qoder/09-negative-formula.png`】；执行前后 runs 目录清单 |
| 10 | `请检查 <损坏文件目录>，如果文件打不开，要告诉我具体是哪一个，不要把失败写成没有问题。` | 自动触发 | Skill 被调用；结果为 `partial`；`file_results.json` 将损坏文件标为 `error`；`run.json.errors` 非空；对话明确检查未完整完成。 | 对话截图：【待填：`docs/evidence/qoder/10-corrupt-file.png`】；`run.json`、`file_results.json`、`report.md` |

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
| 自动触发 6 条 | 【待填：通过数/6】 |
| 手动触发 2 条 | 【待填：通过数/2】 |
| 不应触发 2 条 | 【待填：通过数/2】 |
| 总计 | 【待填：通过数/10】 |
| 连续运行 10 次无服务失联 | 【待填】 |
| 输入文件哈希保持不变 | 【待填】 |
| 完整录屏 | 【待填：文件名或链接】 |

完成条件为 10 条测试都有可回读证据，并且失败项已经修复或在参赛文章中披露。截图数量不能替代 `run.json`、`file_results.json` 和输入哈希。
