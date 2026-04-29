<div align="center">

# ActiveFlow NIDS

### ML-based End-to-End Real-Time Network Intrusion Detection System

![Python](https://img.shields.io/badge/Python-3.10-blue?style=flat-square&logo=python)
![XGBoost](https://img.shields.io/badge/Model-XGBoost-orange?style=flat-square)
![F1 Score](https://img.shields.io/badge/F1%20Score-0.9999-brightgreen?style=flat-square)
![FPR](https://img.shields.io/badge/False%20Positive%20Rate-0.000069-brightgreen?style=flat-square)
![MLflow](https://img.shields.io/badge/Tracking-MLflow%20%2B%20DagsHub-blue?style=flat-square)
![License](https://img.shields.io/badge/License-Apache%202.0-blue?style=flat-square)
![Status](https://img.shields.io/badge/Status-v2.0.0%20Active-success?style=flat-square)

A production-grade, end-to-end pipeline that ingests live network flows, classifies them into 7 attack categories in real time using a trained XGBoost model, and visualizes threats on a live Streamlit dashboard - including geolocation mapping, attack trend charts, and a live alert panel.

---
 
> [!IMPORTANT]
> **Please read before exploring the project.**
>
> 1. **Simulation-based environment:** Due to fundamental incompatibilities between existing flow extraction tools (CICFlowMeter, PyFlowMeter) and production-grade mathematical correctness, live packet sniffing is currently not supported. ActiveFlow operates in a simulated real-time environment by replaying pre-processed LycoS-IDS2017 flows. A new, corrected Python-based flow extraction tool is under active development and will be integrated into the inference pipeline once complete. See [`docs/RCA.md`](docs/RCA.md) for full details.
>
> 2. **Active development:** v2.0.0 is a stable release but is not yet production-deployment ready. ActiveFlow is under continuous development - new features, optimizations, and architectural improvements are planned for every upcoming version with the long-term goal of building a production-grade NIDS.
>
> 3. **Documentation:** This README presents a high-level overview of the architecture, challenges, and limitations. For detailed technical documentation, design decisions, and the full root cause analysis, refer to the **[`docs` folder](./docs)** *(recommended)*.
 
---

<!-- DEMO PLACEHOLDER -->
> 📸 **Demo Screenshot / GIF** — *Add dashboard screenshot or GIF here*
>
> `docs/assets/dashboard.png`

---

</div>

## What It Does

- **Ingests network flows** from a simulation engine replaying LycoS-IDS2017 PCAP-derived CSV files at ~1000 flows/sec, or directly from a live network sniffer
- **Classifies each flow** into one of 7 categories — Benign, DoS, DDoS, PortScan, Brute Force, Web Attack, Bots — in under 1ms per prediction via an async FastAPI inference server
- **Streams predictions** to a real-time Streamlit dashboard with threat counts, network health score, attack trend charts, system health trend, live alert panel, and IP geolocation map
- **Trained on LycoS-IDS2017** — a peer-reviewed, corrected dataset that fixes documented labeling errors, duplicate flows, and miscalculated TCP features present in the original CIC-IDS2017 benchmark
- **Tracks experiments** with MLflow and DagsHub — full training run history, hyperparameter logs, and model metrics are versioned and reproducible

---

## Architecture

```
PCAP File / Live Network Interface
            ↓
  simulation_engine.py          ← replays LycoS flows at 1000/sec
  (or traffic_engine.py)        ← live PyFlowMeter sniffer
            ↓  POST /predict (per flow, async)
  inference_api.py              ← FastAPI inference server
            ↓
  preprocessor.pkl              ← sklearn Pipeline
  (ColumnNameCleaner →          ← custom transformers
   FeatureDropper →
   InfinityToNanConverter →
   SimpleImputer →
   RobustScaler)
            ↓
  model.pkl                     ← trained XGBoost classifier
            ↓
  traffic_buffer (deque)        ← last 100 flows, thread-safe
  stats dict                    ← live packet + prediction counts
            ↓  GET /metrics
  dashboard.py                  ← Streamlit live dashboard
  (auto-refreshes every 1 sec)
```

---

## Model Performance

Trained on **1.6M real network flows** across 7 attack classes. The v2 migration to LycoS-IDS2017 eliminated the train-serve skew that caused the v1 model to predict BENIGN on confirmed DDoS and PortScan flows.

| Metric | v1 — CIC-IDS2017 | v2 — LycoS-IDS2017 |
|--------|:----------------:|:------------------:|
| F1 Score (Test) | 0.9402 | **0.9999** |
| Precision | 0.9029 | **0.9999** |
| Recall | 0.9990 | **0.9999** |
| False Positive Rate | — | **0.000069** |
| Train/Test Gap | 0.0596 | **~0.0000** |
| Training Time | 3h 10m | **49 min** |
| Best Model | LightGBM | **XGBoost** |

> **On FPR:** A False Positive Rate of 0.000069 means the system raises a false alarm on approximately 1 in 14,000 benign flows — the operationally critical metric for any production IDS.

### Per-Class Detection

| Attack Class | Recall |
|---|:---:|
| Benign | 0.9999 |
| DDoS | 1.0000 |
| PortScan | 0.9999 |
| DoS Hulk | 0.9999 |
| Brute Force | 1.0000 |
| Web Attack | 1.0000 |
| Bots | 1.0000 |

---

## Tech Stack

| Layer | Tools |
|---|---|
| ML Pipeline | scikit-learn, XGBoost, LightGBM, imbalanced-learn |
| Sampling | RandomUnderSampler + SMOTETomek (hybrid) |
| Experiment Tracking | MLflow, DagsHub |
| Inference API | FastAPI, Uvicorn |
| Dashboard | Streamlit, Altair, Plotly, Folium |
| Data Versioning | DVC |
| Dataset | LycoS-IDS2017 (corrected CIC-IDS2017) |
| Language | Python 3.10 |

---

## Project Structure

```
ActiveFlow-NIDS/
├── inference_api.py            # FastAPI server — real-time predictions
├── simulation_engine.py        # Replays LycoS flows to the inference API
├── traffic_engine.py           # Live network sniffer (PyFlowMeter-based)
├── dashboard.py                # Streamlit live dashboard
│
├── IDS_Pipeline/
│   ├── components/
│   │   ├── data_ingestion.py       # MD5 integrity check, zip extraction, train/test split
│   │   ├── data_validation.py      # Schema validation, Evidently drift detection
│   │   ├── data_transformation.py  # Custom sklearn transformers + hybrid sampling
│   │   └── model_trainer.py        # Hyperparameter tuning, MLflow tracking
│   ├── utils/
│   │   └── ml_utils/model/
│   │       └── estimator.py        # NetworkModel — preprocessor + model wrapper
│   └── constant/
│       └── training_pipeline.py    # All constants, label mappings, config
│
├── final_model/
│   ├── preprocessor.pkl            # Trained sklearn pipeline
│   └── model.pkl                   # Trained XGBoost classifier
│
├── pcap_processed_csv/             # LycoS-IDS2017 CSV files
├── top_features_schema.yaml        # 28 selected features with dtypes
├── scrapped_code/                  # LycoSTand source (reference for future tool)
│
├── docs/
│   └── RCA.md                      # Root cause analysis — train-serve skew
│
├── EDA/
│   └── EDA.ipynb                   # Exploratory data analysis notebook
│
└── Artifacts/                      # Pipeline run artifacts (gitignored)
```

---

## How to Run

### Prerequisites

```bash
pip install -r requirements.txt
```

> Requires Python 3.10+. For live sniffing, root/admin privileges are needed for packet capture.

### Step 1 — Start the Inference API

```bash
python inference_api.py
```

Server starts at `http://0.0.0.0:8000`. Visit `http://127.0.0.1:8000` to verify — should return `{"status": "IDS Server is live and watching."}`.

### Step 2 — Start the Simulation Engine

```bash
# In a new terminal
python simulation_engine.py
```

This replays LycoS-IDS2017 Friday flows to the inference API at ~1000 flows/sec. Ensure your CSV is present at `pcap_processed_csv/Friday-WorkingHours.pcap_lycos.csv`.

### Step 3 — Open the Dashboard

```bash
# In a new terminal
streamlit run dashboard.py
```

Visit `http://localhost:8501` — the dashboard auto-refreshes every second.

### API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Health check |
| `/predict` | POST | Classify a single network flow |
| `/metrics` | GET | Live traffic buffer + prediction counts |

---

## Key Engineering Decisions

**Why LycoS-IDS2017 instead of CIC-IDS2017?**

The original CIC-IDS2017 dataset and CICFlowMeter tool have documented labeling errors totaling up to 75% for some attack classes (Lanvin et al., 2022). Training on this data caused a train-serve skew where the v1 model predicted BENIGN on confirmed DDoS flows with 45,000,000 bytes/sec. Full root cause analysis in [`docs/RCA.md`](docs/RCA.md).

**Why custom sklearn transformers?**

`ColumnNameCleaner`, `FeatureDropper`, and `InfinityToNanConverter` are implemented as `BaseEstimator`/`TransformerMixin` subclasses so they serialize correctly with pickle — ensuring mathematically identical preprocessing at training time and inference time. Without explicit imports of these classes, pickle cannot deserialize the preprocessor object.

**Why hybrid sampling (RandomUnderSampler + SMOTETomek)?**

Pure SMOTETomek oversample based on majority class size — computationally expensive when the majority class contains millions of samples. RandomUnderSampler first reduces the majority class to a manageable size, then SMOTETomek balances minority classes. This reduced training time from 2h 9m to 13 minutes for the sampling stage alone.

**Why RobustScaler over StandardScaler?**

Network traffic features contain extreme outliers — DDoS flows can have `bytes/s` values orders of magnitude above normal traffic. RobustScaler uses IQR (Q1-Q3) instead of mean/std, making it resistant to these outliers without clipping them. StandardScaler would have its statistics dominated by attack traffic extremes.

**Why deque over list for the traffic buffer?**

`deque(maxlen=100)` provides O(1) append with automatic size management — no manual `pop(0)` needed. A plain list `pop(0)` is O(n) and not safe under concurrent requests. The `deque` is also directly JSON-serializable via `list(traffic_buffer)`.

**Why model loaded outside the route function?**

Loading `preprocessor.pkl` and `model.pkl` inside `/predict` would deserialize ~50MB of objects on every single packet — at 1000 packets/sec this would consume all available memory within seconds. Loading once at startup and reusing the `NetworkModel` instance keeps inference latency under 1ms.

---

## Known Limitations

| Limitation | Status |
|---|---|
| Simulation-based only — no live sniffer in v2.0.0 | Planned v2.1.0 |
| Same PCAPs for train and test — known evaluation bias in IDS benchmarking | Documented in RCA |
| No model explainability (SHAP values) | Planned v2.0.1 |
| LycoSTand incompatible with modern Linux kernels (errno 1 semaphore init failure) | See RCA.md |
| No unit tests | Planned v2.0.1 |
| No Docker containerization | Planned v2.1.0 |
| `global` state in inference API — not safe for multi-worker deployment | Planned Redis migration v2.1.0 |

---

## Roadmap

```
v2.0.0  ✅  Stable simulation-based pipeline — LycoS dataset, XGBoost, live dashboard
v2.0.1  🔄  SHAP explainability + TabNet neural network + unit tests
v2.1.0  📋  Custom Python flow extractor (PyLycoFlow) — LycoSTand math in Python
v2.2.0  📋  Minimum latency optimization — ONNX export, batched inference
v2.3.0  📋  Online learning + concept drift detection (River + Evidently)
v2.4.0  📋  Adversarial robustness testing (IBM ART)
v2.5.0  📋  Cross-dataset formal evaluation (UNSW-NB15)
```

---

## Root Cause Analysis

During live deployment, v1 predicted BENIGN on 100% of flows — including confirmed DDoS traffic with 45M bytes/sec. The root cause was a **train-serve skew** between CICFlowMeter (Java, used for training data) and PyFlowMeter (Python, used for inference) — two tools that compute the same feature names using different underlying mathematics.

Further research revealed the original CIC-IDS2017 dataset has documented labeling errors of up to 75% for some attack classes. The architecture was migrated to LycoS-IDS2017, a peer-reviewed corrected dataset, eliminating the skew and reducing the train/test gap from 0.0596 to ~0.0000.

Full analysis with academic citations: [`docs/RCA.md`](docs/RCA.md)

---

## References

1. Lanvin et al. — *Errors in the CICIDS2017 dataset and the significant differences in detection performances it makes* (2022)
2. Engelen et al. — *Troubleshooting an Intrusion Detection Dataset: the CICIDS2017 Case Study* (2021)
3. Lui et al. — *Error Prevalence in NIDS datasets: A Case Study on CIC-IDS-2017 and CSE-CIC-IDS-2018* (2022)
4. D'hooge et al. — *Discovering non-metadata contaminant features in intrusion detection datasets* (2021)
5. [LycoS-IDS2017 Official Repository](https://lycos-ids.univ-lemans.fr/)
6. [LycoSTand: A New Feature Extraction Tool — SciTePress](https://www.scitepress.org/Papers/2022/107740/pdf/index.html)
7. [Network Intrusion Analysis at Scale — InfoSec Writeups](https://infosecwriteups.com/network-intrusion-analysis-at-scale-733169fc29ff)
8. [CIC-IDS2017 Original Dataset — University of New Brunswick](https://www.unb.ca/cic/)
9. [Anatomy of a Flawed Dataset — HAL Science](https://hal.science/hal-03775466v1/document)
10. [Evaluation of CIC-IDS2017 — IEEE](https://ieeexplore.ieee.org/document/9474286)
11. [Dataset Reliability Analysis — IEEE](https://ieeexplore.ieee.org/abstract/document/9947235)

---

## License

Licensed under the [Apache License 2.0](LICENSE).

---

<div align="center">

Built with obsession by [Priyanshuc26](https://github.com/Priyanshuc26)

*"Sometimes the wall is where the real work begins."*

</div>