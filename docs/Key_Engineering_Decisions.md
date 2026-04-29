**Why LycoS-IDS2017 instead of CIC-IDS2017?**

The original CIC-IDS2017 dataset and CICFlowMeter tool have documented labeling errors totaling up to 75% for some attack classes (Lanvin et al., 2022). Training on this data caused a train-serve skew where the previous model predicted BENIGN on confirmed DDoS flows with 45,000,000 bytes/sec. Full root cause analysis in [`Research and Outcomes/RCA.md`](./Research%20and%20Outcomes/RCA.md).

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