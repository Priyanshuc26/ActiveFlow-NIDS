| Limitation | Status |
|---|---|
| Simulation-based only — no live sniffer in v2.0.0 | Planned v2.1.0 |
| Same PCAPs for train and test — known evaluation bias in IDS benchmarking | Documented in RCA |
| No model explainability (SHAP values) | Planned v2.0.1 |
| LycoSTand incompatible with modern Linux kernels (errno 1 semaphore init failure) | See RCA.md |
| No unit tests | Planned v2.0.1 |
| No Docker containerization | Planned v2.1.0 |
| `global` state in inference API — not safe for multi-worker deployment | Planned Redis migration v2.1.0 |