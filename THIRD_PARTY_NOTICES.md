# Third-party notices

ProofMesh currently depends on these runtime libraries:

- openpyxl — MIT License
- defusedxml — Python Software Foundation License
- python-docx — MIT License
- python-pptx — MIT License
- pdfplumber — MIT License
- RapidFuzz — MIT License
- NumPy — BSD-3-Clause License
- OpenVINO — Apache-2.0 License
- OpenVINO Tokenizers — Apache-2.0 License
- OpenVINO GenAI — Apache-2.0 License
- Pydantic — MIT License
- PyYAML — MIT License
- Jinja2 — BSD-3-Clause License

The optional model-build environment also uses Transformers and Hugging Face Hub. They are not needed after the OpenVINO model assets have been built.

The separately distributed `bge-small-zh-v1.5` OpenVINO assets originate from BAAI's MIT-licensed model. The ONNX distribution used for reproducible conversion is `Qdrant/bge-small-zh-v1.5` at commit `46fbe35fd4374a00fee7de77dfddaeb6dd6a2c59`. The upstream BAAI revision is `7999e1d3359715c523056ef9478215996d62a620`. Generated file hashes are recorded in `models/bge-small-zh-v1.5-openvino/model-manifest.json`; the release archive hash is recorded in `models/model-distribution.json`.

The writing research document cites public projects for design study. No prompt text or source code from repositories without a declared license is copied into ProofMesh.
