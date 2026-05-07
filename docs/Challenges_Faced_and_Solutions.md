# Challenges Faced and Solutions

---

## 1. Train-Serve Skew

**Challenge**

After running the Training Pipeline on the CIC-IDS2017 dataset, one of the most widely used NIDS benchmarks in the world, the LightGBM model achieved strong evaluation metrics. However, when the system was tested at inference, the model failed completely, predicting BENIGN on 100% of live flows including confirmed DDoS traffic.

**Solution**

After thorough research, fundamental flaws were identified in both the CIC-IDS2017 dataset and the CICFlowMeter tool used to generate it. A detailed research and outcomes report covering the root cause and the solution adopted is available here: [Research and Outcomes](./Research%20and%20Outcomes/Readme.md)

---

## 2. Using LycoSTand for Live Flow Extraction

**Challenge**

LycoSTand, the C-based tool used to generate the LycoS-IDS2017 dataset was the natural candidate for live flow extraction, as it would guarantee that training and inference features are computed using identical mathematics. However, LycoSTand was designed to process static PCAP files and was never intended for live packet sniffing.

**Planned Solution**

A pipeline architecture was designed to work around this limitation:

- Use `tcpdump` in WSL to capture live packets at the network interface and write them in chunks to a `pcap_buffer/` folder
- LycoSTand would process each PCAP chunk and save the resulting CSV to a `pcap_processed/` folder
- The CSV would then be forwarded to the inference API for prediction
- The entire flow would be orchestrated using subprocess management and multithreading for efficient, low-latency processing

Despite thorough planning and partial implementation, LycoSTand failed to run, what was initially assumed to be a temporary environment issue turned out to be a fundamental incompatibility, detailed in Challenge 3 below.

---

## 3. Unable to Run LycoSTand Despite Exhaustive Efforts

**Challenge**

LycoSTand relies on legacy Linux IPC mechanisms specifically System V semaphores and was originally built and validated on Ubuntu 18.04. Every attempt to run it on a modern system failed with semaphore initialization errors (`errno 1`), indicating a fundamental incompatibility with modern Linux kernel security and IPC handling.

The following approaches were attempted exhaustively over two days:

- **Windows terminal** - failed at the initial compilation stage
- **WSL (Windows Subsystem for Linux)** - failed with the same semaphore errors
- **Virtual machine (Ubuntu, multiple versions)** - an entire day was spent reinstalling Ubuntu multiple times across different distributions, adjusting kernel parameters, tuning shared memory settings, and escalating permissions. The tool compiled but consistently failed at runtime
- **Native Ubuntu dual-boot** - as a final attempt, a full dual-boot setup was configured from scratch for the first time, including manual disk partitioning and disabling Secure Boot. Despite this, the semaphore initialization errors persisted across every configuration attempted

After exhausting every known workaround - dependency reinstallation, kernel parameter tuning, shared memory inspection, permission escalation, and capability adjustments, the conclusion was that LycoSTand's design assumptions are fundamentally incompatible with modern Linux environments. This was later confirmed by the original research paper, which explicitly states that LycoSTand was built and validated specifically on Ubuntu 18.04.

**Solution**

This experience directly motivated the development of a new open-source Python-based flow extraction tool that reimplements LycoSTand's corrected mathematical formulations with real-time streaming capability. Once complete, it will connect directly to the inference API without requiring any changes to the rest of the pipeline.

---

## 4. Excessive Synthetic Data Generation

**Challenge**

A common challenge in NIDS datasets is severe class imbalance, the vast majority of flows are benign, while attack classes are significantly under represented. Without proper handling, a model trained on such data becomes biased toward predicting BENIGN on everything.

During Phase I (CIC-IDS2017), a hybrid sampling strategy was applied but without sufficient constraints. The benign class was downsampled to 4,00,000 samples, while all minority attack classes were upsampled to the same level, including attack types like Bots that originally had only 600–800 samples. This resulted in 2.8M rows of resampled data, the majority of which was synthetic. The excessive synthetic data likely contributed to the dilution of genuine attack patterns and may have been a secondary factor in the model's failure during live inference.

**Solution**

During Phase II (LycoS-IDS2017), the sampling strategy was redesigned with explicit constraints. Rather than upsampling all classes to an arbitrary fixed target, the natural ratio between attack classes was calculated and preserved ensuring the relative proportions between attack types remained realistic. This approach avoided the creation of excessive synthetic data while still giving the model sufficient representation of minority classes.

The result was a significant reduction in sampling time from 2 hours 9 minutes to 13 minutes, alongside improved data quality. The long-term goal is to reduce dependence on synthetic data entirely, upcoming versions will explore techniques that handle class imbalance without oversampling, such as cost-sensitive learning and class-weighted loss functions.