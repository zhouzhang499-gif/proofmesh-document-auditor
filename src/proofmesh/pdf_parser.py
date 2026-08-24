from __future__ import annotations

import hashlib
from pathlib import Path

import pdfplumber

from .contracts import EvidenceAtom, FactObservation
from .text_extraction import extract_facts_from_text
from .xlsx_parser import load_rules, sha256_file


def parse_pdf(path: Path, root: Path, rules_path: Path) -> tuple[list[EvidenceAtom], list[FactObservation]]:
    rules = load_rules(rules_path)
    document_hash = sha256_file(path)
    relative_path = path.relative_to(root).as_posix()
    evidence: list[EvidenceAtom] = []
    observations: list[FactObservation] = []

    with pdfplumber.open(path) as document:
        for page_index, page in enumerate(document.pages, start=1):
            words = page.extract_words() or []
            for line_number, line_words in enumerate(_group_lines(words), start=1):
                text = " ".join(word["text"] for word in line_words).strip()
                if not text:
                    continue
                bbox = [
                    min(float(word["x0"]) for word in line_words),
                    min(float(word["top"]) for word in line_words),
                    max(float(word["x1"]) for word in line_words),
                    max(float(word["bottom"]) for word in line_words),
                ]
                bbox_text = ",".join(f"{value:.1f}" for value in bbox)
                locator = f"page:{page_index}/line:{line_number}/bbox:[{bbox_text}]"
                evidence_id = hashlib.sha256(f"{document_hash}|{locator}".encode("utf-8")).hexdigest()[:20]
                evidence.append(
                    EvidenceAtom(
                        evidence_id=evidence_id,
                        document_hash=document_hash,
                        relative_path=relative_path,
                        media_type="application/pdf",
                        locator=locator,
                        raw_text=text,
                        extractor="pdfplumber",
                    )
                )
                observations.extend(
                    extract_facts_from_text(
                        text=text,
                        base_locator=locator,
                        document_hash=document_hash,
                        relative_path=relative_path,
                        evidence_id=evidence_id,
                        rules=rules,
                    )
                )
    return evidence, observations


def _group_lines(words: list[dict]) -> list[list[dict]]:
    lines: list[list[dict]] = []
    for word in sorted(words, key=lambda item: (round(float(item["top"]), 1), float(item["x0"]))):
        if not lines or abs(float(lines[-1][0]["top"]) - float(word["top"])) > 3:
            lines.append([word])
        else:
            lines[-1].append(word)
    return lines

