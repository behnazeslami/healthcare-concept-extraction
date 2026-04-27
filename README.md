# 🏥 Healthcare Concept Extraction - Agentic AI

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A **true agentic AI system** for extracting and classifying clinical concepts from unstructured medical notes using local LLMs (Llama 3.1, Mistral) with autonomous decision-making, multi-step reasoning, UMLS enrichment, and self-correction capabilities.

## 🎥 Demo

<video controls preload="metadata" width="100%">
  <source src="./concept_extraction_agentic_ai_demo.mp4" type="video/mp4" />
</video>

https://github.com/user-attachments/assets/bcd36dd7-64b4-4d67-b927-0230615d50ac

If the embedded video does not render on your platform, use this direct link:
[Watch or download the demo](concept_extraction_agentic_ai_demo.mp4)

## 🎯 Key Features

### ✅ True Agentic AI
- **Autonomous Decision-Making**: Agent selects tools based on confidence and goals
- **ReACT Reasoning Loop**: Multi-step reasoning with full transparency
- **Self-Correction**: Detects and fixes hallucinations automatically
- **Learning from Memory**: Few-shot learning from similar past cases
- **Goal-Directed**: Optimize for accuracy, speed, or coverage

### 🔬 Clinical Intelligence
- **LLM-Powered Extraction**: Llama 3.1-8B running locally (no API calls)
- **UMLS Enrichment**: CUI codes, SNOMED CT codes, preferred terminology
- **Concept Categorization**: Diagnoses, symptoms, medications, procedures, findings
- **Phenotyping**: Hierarchical concept expansion
- **Context-Aware**: Maintains full clinical context during extraction

### 🎨 Modern UI
- **Interactive Dashboard**: Real-time concept extraction visualization
- **5-Tab Interface**: Summary, Concepts, UMLS, Reasoning, Raw JSON
- **Visual Analytics**: Confidence bars, KPI cards, concept pills with status
- **Export Options**: Download JSON, copy results, shareable records

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- 8GB+ VRAM (for Llama 3.1-8B model)
- 20GB disk space (for model weights)

### Installation

```bash
# 1. Clone repository
git clone https://github.com/yourusername/healthcare-concept-extraction.git
cd healthcare_concept_agent

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set UMLS API Key (optional, for concept validation)
export UMLS_API_KEY="your_api_key_here"
```

### Running the System

```bash
# Terminal 1: Start the API server (port 8002)
python server.py

# Terminal 2: Start the UI server (port 8001)
python -m http.server 8001 --directory .
```

Then open: **http://127.0.0.1:8001/index.html**

## 📡 API Usage

### Endpoint: `/reason`

**Request:**
```json
{
  "clinical_text": "58-year-old male with severe asthma exacerbation presenting with acute respiratory distress...",
  "main_note": "Brief summary of the clinical case",
  "record_id": "CASE_001",
  "goal": "BALANCED"
}
```

**Response:**
```json
{
  "status": "success",
  "record_id": "CASE_001",
  "extracted_concepts": ["asthma", "respiratory distress", "hypoxemia", ...],
  "confidence": 0.84,
  "reasoning_chain": [
    {
      "step_number": 1,
      "thought": "Extracting medical concepts from clinical text",
      "action": "RUN concept_extractor",
      "observation": "Extracted 23 concepts",
      "confidence": 0.66
    },
    ...
  ],
  "umls_enrichment": {
    "asthma": {
      "cui": "C0004096",
      "snomed_ct": "195967001",
      "preferred_name": "Asthma",
      "found": true
    },
    ...
  },
  "script_runtime": 27.34
}
```

### Python Client Example

```python
import requests

url = "http://127.0.0.1:8002/reason"
payload = {
    "clinical_text": "Patient presents with chest pain and shortness of breath...",
    "main_note": "Acute chest pain, rule out MI",
    "record_id": "CASE_001",
    "goal": "BALANCED"
}

response = requests.post(url, json=payload)
result = response.json()

print(f"Concepts: {result['extracted_concepts']}")
print(f"Confidence: {result['confidence']:.2%}")
print(f"Runtime: {result['script_runtime']:.2f}s")
```

## 🧠 Architecture

```
┌─────────────────────────────────────┐
│    Web UI (index.html)              │
│  - Interactive dashboard            │
│  - 5 visualization tabs             │
└────────────┬────────────────────────┘
             │
             │ HTTP POST
             ↓
┌─────────────────────────────────────┐
│  FastAPI Server (server.py)         │
│  - REST endpoint /reason            │
│  - Request validation               │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│  HealthcareAgenticAI (agent.py)     │
│  - ReACT reasoning loop             │
│  - Autonomous tool selection        │
└────────────┬────────────────────────┘
             │
      ┌──────┴──────┬─────────┬──────────┬─────────┐
      ↓             ↓         ↓          ↓         ↓
   Concept      UMLS        Phenotyping Self-   Memory
   Extractor    Validator   Tool      Correction Tool
   (LLM)        (REST API)  (DB)      (LLM)    (JSON)
```

## 🔄 Reasoning Loop Example

**Input:** Clinical text about asthma exacerbation

**Step 1: Extract** 🔍
- Uses Llama 3.1 to identify ~20 medical concepts
- Initial confidence: 0.66

**Step 2: Validate** ✓
- Validates concepts against UMLS database
- Retrieves CUI codes and SNOMED CT codes
- Confidence boost: +0.18 → 0.84

**Step 3: Analyze** 📊
- Categorizes concepts by type:
  - 2 Diagnoses, 3 Symptoms, 2 Medications, 1 Procedure, 2 Findings

**Step 4+: Optional**
- Phenotyping expansion (if coverage goal)
- Self-correction (if errors detected)
- Memory learning (if similar cases found)

**Result:** 20-23 validated, enriched medical concepts with 84%+ confidence

## 🛠️ Configuration

Edit `config.py` to customize:

```python
# Model selection
MODEL_SIZE = "8B"  # 8B or 13B

# Confidence thresholds
CONFIDENCE_THRESHOLD_HIGH = 0.9
CONFIDENCE_THRESHOLD_MEDIUM = 0.7

# UMLS validation
UMLS_API_KEY = os.getenv("UMLS_API_KEY")
UMLS_RATE_LIMIT = 0.05  # seconds between API calls

# Reasoning
MAX_REASONING_STEPS = 6
DEFAULT_GOAL = "BALANCED"
```

## 📊 Performance

| Metric | Value |
|--------|-------|
| Extraction Time | ~5-7 seconds |
| UMLS Validation | ~18-22 seconds |
| Total Runtime | ~25-30 seconds |
| Accuracy | 84-92% (depends on goal) |
| Concepts Extracted | 15-30 per case |
| Confidence Range | 0.66-0.95 |

## 📁 Project Structure

```
concept_extraction_agentic_ai/
├── agent.py                 # Core ReACT reasoning engine
├── server.py                # FastAPI REST server
├── index.html               # Interactive web UI
├── config.py                # Configuration settings
├── models.py                # Data models & schemas
├── requirements.txt         # Python dependencies
├── tools/
│   ├── __init__.py
│   ├── concept_extractor.py # LLM-based extraction
│   ├── umls_validator.py    # UMLS REST API integration
│   ├── phenotyping_tool.py  # Hierarchical expansion
│   ├── self_correction.py   # Error detection & fixing
│   ├── memory_tool.py       # Few-shot learning memory
│   └── umls_enricher.py     # SNOMED CT enrichment
├── examples/
│   ├── clinical_case_1.json
│   └── clinical_case_2.json
└── README.md
```

## 🔐 UMLS Integration

To use UMLS enrichment:

1. Get API key: https://www.nlm.nih.gov/research/umls/
2. Set environment variable:
   ```bash
   export UMLS_API_KEY="your_api_key"
   ```
3. System will automatically validate concepts and retrieve:
   - CUI (Concept Unique Identifier)
   - SNOMED CT codes
   - Preferred terminology names

## 🎯 Goals

Set extraction goals to optimize behavior:

- **`MAXIMIZE_ACCURACY`**: Validate extensively, self-correct, expand aggressively
- **`MAXIMIZE_SPEED`**: Extract once, minimal validation, early stopping
- **`MAXIMIZE_COVERAGE`**: Expand concepts, memory learning, phenotyping
- **`BALANCED`** *(default)*: Validate once, optional expansion, smart stopping

## 🧪 Testing

Run via web UI:
1. Open http://127.0.0.1:8001/index.html
2. Paste clinical text in payload
3. Click "Run Analysis"
4. View results in reasoning tab

## 🐛 Troubleshooting

**Issue**: CUDA Out of Memory
- Solution: Reduce `max_new_tokens` in config, or use 4-bit quantization

**Issue**: UMLS API timeout
- Solution: Check UMLS_API_KEY, increase rate limit threshold

**Issue**: LLM model not loading
- Solution: Ensure model path is correct in config, check available disk space

## 📚 Resources

- [ReACT Paper](https://arxiv.org/abs/2210.03629) - Reasoning + Acting in LLMs
- [UMLS Overview](https://www.nlm.nih.gov/research/umls/)
- [SNOMED CT Browser](https://browser.ihtsdotools.org/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)

### 📖 Related Publications

**[A Hybrid Language Framework for Ontology-Based Clinical Concept Extraction](https://www.researchgate.net/profile/Behnaz-Eslami/publication/401258282_A_Hybrid_Language_Framework_for_Ontology-Based_Clinical_Concept_Extraction/links/69b1c7b7e4cc384db521d422/A-Hybrid-Language-Framework-for-Ontology-Based-Clinical-Concept-Extraction.pdf)**

Eslami B, Dligach D, Azarvash N, de la Pena P, Strickland B, Tootooni S. *Journal of Healthcare Informatics Research*, 2026 Feb 26:1-8.

## 📄 License

MIT License - See LICENSE file

## 👨‍💻 Author

Behnaz Eslami

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

---

**Built with ❤️ for clinical NLP research**
