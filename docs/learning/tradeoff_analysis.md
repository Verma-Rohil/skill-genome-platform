# ML & Architecture Tradeoff Analysis

This document details the key technology selection decisions made during the architecture design of the **Skill Genome Platform**, comparing candidates against chosen solutions.

---

## 1. Skill Extraction: Rule-Based Trie Matcher vs. Machine Learning NER (spaCy)

| Parameter | Trie Matcher (Chosen) | Named Entity Recognition (spaCy) |
| :--- | :--- | :--- |
| **Time Complexity** | $O(N)$ (where $N$ is text length; independent of vocabulary size) | $O(N \times V)$ (heavy transformer/tensor pass) |
| **Precision** | **100%** (matches only registered canonical skills or aliases) | **Variable** (prone to context errors, e.g. "I am aware of AWS" vs "I coded in AWS") |
| **Punctuation Support** | **High** (trivially preserves symbols like `C++`, `.js`, `C#`) | **Low** (tokenizers split symbols like `C++` into `C` and `+`, `+`) |
| **Resource Overhead** | Extremely lightweight (pure memory tree traversal) | Heavy (requires large pipelines, GPU/CPU cores) |

### Tradeoff Decision
We chose the **Trie-based dictionary matcher** (similar to the FlashText algorithm) as our primary extractor, layered with a cascading normalizer. In resume screening and workforce analytics, high precision is paramount — a false positive (extracting a skill not actually possessed or required) is more damaging than a minor recall miss. Trie matching ensures exact match fidelity and operates at microsecond speeds.

---

## 2. Skill Representation: Word2Vec vs. Sentence-BERT (S-BERT)

| Parameter | Word2Vec (Local Training) | Sentence-BERT (Pre-trained) |
| :--- | :--- | :--- |
| **Semantic Extraction** | Learns only from local co-occurrence context | Captures universal semantic properties |
| **Out-Of-Vocabulary (OOV)** | Fails completely (Opaque to unseen tokens) | Encodes on-the-fly via character/sub-word tokenizers |
| **Training Requirement** | Requires massive datasets ($>10^5$ posts) to generalize | Pre-trained on billions of general sentences |
| **Dimension Size** | Configurable (usually 100–300) | Fixed by model configuration (384 for MiniLM) |

### Tradeoff Decision
While local Word2Vec embeddings reflect specific co-occurrences in our dataset, they cannot represent out-of-vocabulary terms entered by users on-the-fly and suffer from data sparsity. We chose **S-BERT (`all-MiniLM-L6-v2`)** to leverage rich semantic relationships (e.g., mapping `TensorFlow` and `PyTorch` closely even if they rarely co-occur in the same job posting).

---

## 3. Forward Analysis: Prophet Trend Forecasting vs. Skill Synergy Disruption Simulator

| Parameter | Time-Series Forecasting (Prophet) | Shock Propagation Simulator (Chosen) |
| :--- | :--- | :--- |
| **Data Requirements** | Multi-year sequential time-series data | Static co-occurrence network |
| **Scientific Defense** | **Low** (extrapolating trends from static 2024 data is an ML anti-pattern) | **High** (models structural dependencies via conditional probability transitions) |
| **Product Value** | Static chart | Interactive "What-If" planning dashboard |
| **Math Foundation** | Additive regression curves | 2-hop decayed transition shock propagation ($P(B \vert A)$) |

### Tradeoff Decision
Extrapolating a time-series model from static, non-temporal Kaggle job data to predict future skill demand violates statistical modeling principles. We pivoted to a **Workforce Disruption Simulator** modeling the skill ecosystem as a network of co-occurrences. This allows interactive workforce simulation and calculates archetype vulnerability with high mathematical defense.
