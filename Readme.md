<div align="center">

# ActiveFlow NIDS

### ML-based End-to-End Real-Time Network Intrusion Detection System

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
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
> 1. **Simulation-based environment:** Due to fundamental incompatibilities between existing flow extraction tools (CICFlowMeter, PyFlowMeter) and production-grade mathematical correctness, live packet sniffing is currently not supported. ActiveFlow operates in a simulated real-time environment by replaying pre-processed LycoS-IDS2017 flows. A new, corrected Python-based flow extraction tool is under active development and will be integrated into the inference pipeline once complete. See [`docs/Research and Outcomes/RCA.md`](./docs/Research%20and%20Outcomes/RCA.md) for full details.
>
> 2. **Active development:** v2.0.0 is a stable release but is not yet production-deployment ready. ActiveFlow is under continuous development - new features, optimizations, and architectural improvements are planned for every upcoming version with the long-term goal of building a production-grade NIDS.
>
> 3. **Documentation:** This README presents a high-level overview of the architecture, challenges, and limitations. For detailed technical documentation, design decisions, and the full root cause analysis, refer to the **[`docs`](./docs) folder** *(recommended)*.
 
---

<!-- DEMO PLACEHOLDER -->
> 📸 **Demo Screenshot / GIF** — *Add dashboard screenshot or GIF here*
>
> `docs/assets/dashboard.png`

---

</div>

## What It Does

- **Ingests network flows** from a simulation engine replaying LycoS-IDS2017 PCAP-derived CSV files at ~1000 flows/sec, or directly from a live network sniffer
- **Classifies each flow** into one of 7 categories - Benign, DoS, DDoS, PortScan, Brute Force, Web Attack, Bots - in under 1ms per prediction via an async FastAPI inference server
- **Streams predictions** to a real-time Streamlit dashboard with threat counts, network health score, attack trend charts, system health trend, live alert panel, and IP geolocation map
- **Trained on LycoS-IDS2017** - a peer-reviewed, corrected dataset that fixes documented labeling errors, duplicate flows, and miscalculated TCP features present in the original CIC-IDS2017 benchmark
- **Tracks experiments** with MLflow and DagsHub - full training run history, hyperparameter logs, and model metrics are versioned and reproducible

---
<br>

## Architecture
<br>

![Inference Pipeline](./docs/assets/Inference_Pipeline-Architecture%20(1).png)

For Detailed Architecture of Inference Pipeline and Training Pipeline, please refer to [`docs/Architecture`](./docs/Architecture/)
---

## Model Performance

Trained on **1.8M real network flows** across 7 attack classes. The migration to LycoS-IDS2017 eliminated the train-serve skew that caused the previous model(Trained on CIC-IDS2017 Dataset) to predict BENIGN on confirmed DDoS and PortScan flows.

| Metric | CIC-IDS2017 (Previous) | LycoS-IDS2017 (Current) |
|--------|:----------------:|:------------------:|
| F1 Score (Test) | 0.9402 | **0.9999** |
| Precision | 0.9029 | **0.9999** |
| Recall | 0.9990 | **0.9999** |
| False Positive Rate | — | **0.000069** |
| Train/Test Gap | 0.0596 | **~0.0000** |
| Training Time | 3h 10m | **49 min** |
| Best Model | LightGBM | **XGBoost** |

> **On FPR:** A False Positive Rate of 0.000069 means the system raises a false alarm on approximately 1 in 14,000 benign flows — the operationally critical metric for any production IDS.

**For Detailed Information of how model was trained using Training Pipeline and how it behaved on different Datasets please refer to:** <br>
[`Log File of Training Pipeline when trained on CIC-IDS2017 Dataset`](./logs/04_11_2026_06_31_44.log)<br>
[`Log File of Training Pipeline when trained on LycoS-IDS2017 Dataset`](./logs/04_16_2026_19_33_32.log)

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
| Some Important Libs. | Evidently, GeoIP2 |
| Experiment Tracking | MLflow, DagsHub |
| Inference API | FastAPI, Uvicorn |
| Dashboard | Streamlit, Altair, Plotly |
| Data Versioning | DVC |
| Dataset | LycoS-IDS2017 (corrected CIC-IDS2017), previously Original CIC-IDS2017 |
| Language | Python 3.12 |

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

Visit `http://localhost:8501` - the dashboard auto-refreshes every second.

### API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Health check |
| `/predict` | POST | Classify a single network flow |
| `/metrics` | GET | Live traffic buffer + prediction counts |

---

## Documentations
Main Readme contains a higher level overview to keep it clean and easily readable. Detailed documentations can be accessed in **[`/docs`](./docs) folder**

### Challenges Faced and Solutions

During Making of ActiveFlow I faced severe challenges that took lot of time and research to find a proper solution. All the challenges faced an whatsolutions were found are listed in [`Challenges Faced and Solutions`](./docs/Challenges_Faced_and_Solutions.md) file


### Key Engineering Decisions

[`Key Engineering Decisions`](./docs/Key_Engineering_Decisions.md) file contains The important descisions that were taken to improve the performance, stability and robustness of system.


### Known Limitations

Currenty ActiveFlow contains limitations due to some flaws of toolsets or other reasons. All the current and global limitations are listed in [`Limitations`](./docs/Limitations.md) file


### Upcoming Updates

ActiveFlow is an ambitious project and intended to be a production grade NIDS. To continously improve and remove current limitations lot of major and minor updates are alreaddy planned and same will be worked on. You see what updates can come on the way in [`Future Updates`](./docs/Future_Updates.md) file


## Root Cause Analysis

During live deployment, v1 predicted BENIGN on 100% of flows including confirmed DDoS traffic with 45M bytes/sec. The root cause was a **train-serve skew** between CICFlowMeter (Java, used for training data) and PyFlowMeter (Python, used for inference) two tools that compute the same feature names using different underlying mathematics.

Further research revealed the original CIC-IDS2017 dataset has documented labeling errors of up to 75% for some attack classes. The architecture was migrated to LycoS-IDS2017, a peer-reviewed corrected dataset, eliminating the skew and reducing the train/test gap from 0.0596 to ~0.0000.

Full analysis with academic citations: [`docs/Research and Outcomes/RCA.md`](./docs/Research%20and%20Outcomes/RCA.md)

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