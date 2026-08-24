from __future__ import annotations

from proofmesh.text_extraction import extract_facts_from_text


def test_chinese_comma_separates_adjacent_fact_labels() -> None:
    facts = extract_facts_from_text(
        text="项目预算126万元，项目成本50万元",
        base_locator="paragraph:1",
        document_hash="a" * 64,
        relative_path="方案.docx",
        evidence_id="evidence",
        rules={"aliases": {}, "money_labels": ["预算", "成本"], "date_labels": []},
    )

    assert [item.canonical_label for item in facts] == ["项目预算", "项目成本"]
