# ProofMesh 易读写作研究

调研日期：2026-08-24

## 我们要解决的问题

审计报告常见两种失败。一种只输出技术字段，用户需要自己拼出发生了什么；另一种写得很顺，却充满套话、漂亮结论和不必要的总结。ProofMesh 需要把证据说清楚，同时保留审计工具应有的克制。

## 参考项目

| 项目 | 固定参考 | 采用的做法 | 许可证处理 |
|---|---|---|---|
| [blader/humanizer](https://github.com/blader/humanizer/tree/e2e92e7b4b8229253ed5c8e81dc65463fdeddda5) | `e2e92e7b4b8229253ed5c8e81dc65463fdeddda5` | 事实保真、按文体调整、清理聊天机器人残留和虚高判断 | MIT；只借鉴规则思想 |
| [shir-danishyar/humanize](https://github.com/shir-danishyar/humanize/tree/454179265115bea6c2eeb96e6b4191fa8873c4b1) | `454179265115bea6c2eeb96e6b4191fa8873c4b1` | 生成前约束、生成后 lint、CI 检查 | MIT；独立实现中文检查器 |
| [chujianyun/skills](https://github.com/chujianyun/skills/blob/d5966dd5428b5662b526ca259ffb8201fa7dd364/skills/content/remove-ai-flavor/SKILL.md) | `d5966dd5428b5662b526ca259ffb8201fa7dd364` | 区分轻改和深改，关注资料味与内容空心 | 未声明许可证；不复制文本或代码 |
| [fy-agent/humanize-chinese-writing](https://github.com/fy-agent/humanize-chinese-writing/tree/e284777b055717e029478623f6be6c1940ebfd2c) | `e284777b055717e029478623f6be6c1940ebfd2c` | 用语境失配解释 AI 味，优先保留事实和作者位置 | 未声明许可证；只做研究引用 |
| [Vale](https://github.com/vale-cli/vale/tree/d0e65f4187c304b174f9bcb2854f02ebb455708f) | `d0e65f4187c304b174f9bcb2854f02ebb455708f` | 配置化规则、理解 Markdown 结构、适合 CI | MIT；首版不引入二进制 |
| [Proselint](https://github.com/amperser/proselint/tree/dbed789caae662d06c7c8a5a13dd31f1acd36f5c) | `dbed789caae662d06c7c8a5a13dd31f1acd36f5c` | 带规则、位置、span 和建议的结构化 finding | BSD-3-Clause；独立设计数据结构 |

## 筛选结果

ProofMesh 不做自动“洗稿”，也不承诺通过任何 AI 检测器。报告生成器使用固定模板和本地规则，写完后再做一次确定性检查。

证据字段属于只读数据。写作处理不能改动：

- 金额、百分比和日期；
- 文件名、工作表、幻灯片、单元格和坐标；
- 规则编号、文件哈希和模型版本；
- 引用的原始证据。

正文采用项目交付说明的语气。每个问题按“发生了什么、证据在哪里、用户需要确认什么”展开。技术字段放在附录。

## 验收方法

1. README 和报告运行 style guard，不出现 error 级 finding。
2. 报告生成前后逐项比对锁定字段。
3. 正文能在不看 JSON 的情况下说明冲突。
4. 写作检查结果保存为 `style_findings.json`。
5. 没有命中规则只表示已知模板句未出现，不表示文本一定由人类创作。

