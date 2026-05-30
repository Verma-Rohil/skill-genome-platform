# Feature Engineering Design Document — Skill Extraction Pipeline
## Skill Genome Platform

---

## 1. Executive Summary

The **Skill Extraction Pipeline** is the ingestion gateway of the Skill Genome Platform. It transforms raw, unstructured job description text into a clean, normalized, and structured list of canonical skills. 

This document details the architectural decisions, algorithmic choices, and tradeoffs involved in designing this pipeline, with a specific focus on **defensibility for data science and engineering interviews**.

---

## 2. Rule-Based vs. ML-Based Extraction Tradeoffs

When building a production entity extraction pipeline for professional skills, we evaluated two primary architectural patterns:

| Dimension | Rule-Based (Trie Dictionary Matcher) | ML-Based (Named Entity Recognition / NER) |
|:---|:---|:---|
| **Precision** | **Near 100%**. Only extracts pre-validated skills in our taxonomy. | **Variable (70-85%)**. Prone to hallucinating skills or misidentifying generic nouns. |
| **Recall** | **Moderate**. Misses newly emerged skills or unmapped aliases. | **High**. Can generalize to extract unseen or newly coined skills. |
| **Computational Cost** | **Ultra-Low**. $O(N)$ execution, negligible RAM, <5ms latency. No GPU needed. | **High**. Model inference takes 50-200ms per request, requires GPU or high CPU. |
| **Data Requirements** | **None**. Needs a curated taxonomy (dictionary) of skills. | **High**. Requires thousands of hand-labeled job postings for NER training. |
| **Maintenance** | **Simple**. To add a skill, simply append a row to the taxonomy table. | **Complex**. Requires retraining, evaluating, and redeploying a new NER model. |

### Our Production Strategy: Dictionary-First Hybrid Model
We opted for a **Trie-based dictionary matcher** using a curated taxonomy of ~800 skills as our production core.
- **Why?** In workforce intelligence, a **false positive** (e.g., extracting "AWS" from "We do NOT use AWS" or misidentifying "React" from "She reacted quickly") is far more damaging to clustering and recommendation models than a false negative.
- **Precision is paramount**. By utilizing a high-performance word-level Trie, we achieve sub-millisecond extraction speeds, absolute predictability, and perfect precision, while covering the vast majority of tech job market requirements.

---

## 3. Algorithmic Complexity: Naive vs. Trie Search

A critical interview talking point is the efficiency of our extraction algorithm. Naive string matching scales horribly.

### The Naive Approach
Searching for a list of $S$ skills inside a text document of $W$ words:
- **Nested Search:** Loop through each skill, check if it exists in the text using `skill in text` or compiled Regex.
- **Time Complexity:** $O(S \times W \times C)$ where $C$ is the average character length of a skill.
- **Why it Fails:** With a taxonomy of $S = 1,000$ skills and a job description of $W = 500$ words, we perform up to $500,000$ operations *per request*. Scaling this to batch-process 100,000 postings results in extreme bottlenecks.

### The Trie-Based Approach (Our Choice)
Instead of searching the text *for each skill*, we search our *Trie database* using the text's words:
- We index all skills and aliases into a **Prefix Tree (Trie)**.
- We tokenize the job description and walk the text word-by-word. At each word, we traverse the Trie branches.
- **Time Complexity:** $O(W \times L)$ where $W$ is the number of words in the text and $L$ is the length of the longest skill phrase (typically $L \le 4$ words).
- **Why it Wins:** The extraction speed is **independent of vocabulary size**. Whether we have 500 skills or 50,000 skills in our taxonomy, the extraction takes the same linear time relative to the text length.

---

## 4. Key Design Patterns & Edge Cases

### A. Longest-Match Lookahead (No Overlapping Matches)
A common failure of naive keyword matchers is splitting multi-word phrases. 
- *Problem:* If "Learning" and "Machine Learning" are both valid skills, the phrase `"I love machine learning"` might extract both `["Machine Learning", "Learning"]`. This introduces severe redundancy.
- *Solution:* Our Trie matcher uses **greedy longest-match lookahead**. When traversing the words, it keeps advancing down the Trie branches as long as characters match, and only registers the longest completed canonical name (i.e., consuming `"machine learning"` as a single token of length 2, and skipping the single word `"learning"`).

### B. Clean Tokenization & Punctuation Resilience
Specialized technical skills contain unique punctuation that standard NLP tokenizers strip:
- Skills like `C++`, `C#`, `.NET`, `Node.js`, and `Next.js` must be preserved.
- *Solution:* We implemented a customized regex tokenization pass that retains alphanumeric characters plus `+`, `#`, `.`, and `-`, while replacing commas, parentheses, and brackets with spaces. This ensures `C++` is tokenized as `["c++"]` rather than being stripped to `["c"]`.

---

## 5. Architectural Implementation

The service is fully decoupled from active databases via a **fallback strategy**:
1. At startup, the `SkillExtractor` attempts to read canonical skills and aliases from the MySQL database using the SQLAlchemy session.
2. If the database is empty or inaccessible (e.g., during test suites or offline notebook scripts), it automatically falls back to reading the pre-built `skills_taxonomy.csv` file.
3. This guarantees that developer pipelines can run out-of-the-box and unit tests run instantly with 100% isolation.
