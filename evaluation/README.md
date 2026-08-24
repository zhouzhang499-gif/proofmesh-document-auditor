# ProofMesh 量化评测

`fact_pairs.jsonl` 包含 100 条可复现事实对：40 条明确冲突、40 条明确一致和 20 条困难样例。数据不依赖 Office 文件，但会经过项目实际的 `parse_fact` 规范化和 `find_issues` 确定性规则。

重新生成数据：

```powershell
python evaluation/build_dataset.py
```

运行评测：

```powershell
python scripts/run_evaluation.py
```

默认结果写入 `evaluation/results/evaluation.json` 和 `evaluation/results/evaluation.md`。也可以通过 `--dataset` 和 `--output-dir` 指定其他路径。

评测会报告：

- 冲突检测的 precision、recall 和 F1。
- 按明确冲突、明确一致、困难样例划分的预测统计。
- 规则 ID 命中情况与事实解析覆盖率。
- `relative_path`、`locator`、`evidence_id` 和 `document_hash` 的定位字段完整率。

`decimal_scale_equivalence` 和 `percentage_decimal_scale` 专门用于观察当前规则对 Decimal 字符串尺度的处理，因此基线不必然是 100%。
