# Embedding Design Document — Semantic Representation Layer
## Skill Genome Platform

---

## 1. Mathematical Concept & Core Definition

### 1.1 The Semantic Vector Space
In the Skill Genome Platform, we model the professional skill ecosystem as a dense vector space. Every canonical skill $s_i$ is mapped to a high-dimensional dense vector $\mathbf{v}_i \in \mathbb{R}^D$ where $D = 384$. 

The spatial proximity of two vectors $\mathbf{v}_i$ and $\mathbf{v}_j$ represents their **semantic and functional similarity** within the industry.

### 1.2 Similarity Metric: Cosine Similarity
To measure the relationship between two skills, we utilize **Cosine Similarity**, which measures the cosine of the angle between two non-zero vectors in an inner product space.

$$\text{Cosine Similarity}(\mathbf{v}_i, \mathbf{v}_j) = \frac{\mathbf{v}_i \cdot \mathbf{v}_j}{\|\mathbf{v}_i\| \|\mathbf{v}_j\|} = \frac{\sum_{k=1}^D v_{i,k} v_{j,k}}{\sqrt{\sum_{k=1}^D v_{i,k}^2} \sqrt{\sum_{k=1}^D v_{j,k}^2}}$$

*   **Range:** $[-1, 1]$, but in practice, normalized S-BERT vectors reside in $[0, 1]$ for technical terms.
*   **Why Cosine over Euclidean Distance?** Cosine similarity focuses on **direction rather than magnitude**. In NLP and embedding spaces, the direction of the vector captures the semantic meaning (the context of surrounding text), while the magnitude can be biased by frequency or token length.

---

## 2. Model Selection: Sentence-BERT vs. Word2Vec

As a Principal Data Scientist, choosing the right embedding representation involves evaluating fundamental structural tradeoffs:

| Dimension | Word2Vec (Distributional Hypothesis) | Sentence-BERT (Transformer Embeddings) |
|:---|:---|:---|
| **Underlying Concept** | Learns vector space solely from *co-occurrence* within job postings. | Encodes general semantic meaning using a *pre-trained Transformer* model. |
| **Data Requirements** | Needs millions of job descriptions to converge on meaningful weights. | **None**. Works instantly out-of-the-box using pre-trained weights. |
| **Zero-Shot Synonyms** | **Poor**. Cannot link terms that never co-occur in the same training jobs. | **Excellent**. Understands synonyms (`py` $\approx$ `Python`) based on deep English pre-training. |
| **Domain Specificity** | High. Strictly models our local market's co-occurrences. | General. Can be slightly biased by non-tech definitions. |
| **Computational Footprint** | Extremely low. Standard lookup dictionary. | Low. Small model inference on CPU (~50ms/request) or cached. |

### Our Choice: Sentence-BERT (`all-MiniLM-L6-v2`)
We chose **S-BERT** (`all-MiniLM-L6-v2`) as our production embedding model:
1.  **Vocabulary Sparsity:** With only $\sim 1,000$ canonical skills, training Word2Vec from scratch fails to learn strong semantic associations because the vocabulary is too sparse to capture latent dimensions.
2.  **Out-of-the-box Accuracy:** S-BERT immediately understands that `"FastAPI"` is related to `"Flask"` and `"Django"`, and `"PyTorch"` to `"TensorFlow"`, without needing millions of job postings to prove they co-occur.
3.  **MiniLM Efficiency:** The `all-MiniLM-L6-v2` model is a distilled Transformer:
    *   **Dimension size:** 384 (compact, memory-friendly).
    *   **Disk footprint:** ~80 MB.
    *   **Performance:** Highly competitive semantic search scores with extremely fast execution on standard CPU nodes.

---

## 3. The Hybrid Model: Semantic + Co-occurrence Proximity

An advanced, interview-grade feature of our system design is the **Hybrid Proximity Engine**. 

While S-BERT is excellent at general semantics, it can miss strict professional alignment (e.g., S-BERT might find "Java" and "JavaScript" close due to textual overlap, even though they represent separate backend vs. frontend career paths).

To solve this, we compute a **Hybrid Proximity Score (HPS)** that merges semantic vector similarity with statistical co-occurrence metrics:

$$\text{HPS}(s_i, s_j) = \alpha \cdot \text{CosineSimilarity}(\mathbf{v}_i, \mathbf{v}_j) + (1 - \alpha) \cdot \text{MinMaxNormalizedPMI}(s_i, s_j)$$

*   $\alpha = 0.70$ (Semantic weight) and $1 - \alpha = 0.30$ (Co-occurrence network weight).
*   **PMI (Pointwise Mutual Information):** Extracted from our `skill_cooccurrences` table:
    
    $$\text{PMI}(s_i, s_j) = \log\left(\frac{P(s_i \cap s_j)}{P(s_i) P(s_j)}\right)$$

This hybrid approach ensures that our recommendations are mathematically grounded in **both semantic meaning and actual job market demand patterns**.

---

## 4. Vector Storage, Indexing, and Search Complexity

### 4.1 In-Memory Startup Caching
To achieve extremely low latency ($<1\text{ms}$ search time), we load the entire SQL `skill_embeddings` table into an in-memory NumPy matrix at application startup:

*   **Embedding Matrix:** $\mathbf{M} \in \mathbb{R}^{S \times D}$, where $S \approx 1,000$ and $D = 384$.
*   **Memory Footprint:** $1,000 \times 384 \times 4 \text{ bytes} \approx 1.53 \text{ MB}$. (Fits easily into standard container RAM).

### 4.2 Search Complexity
When finding the top $K$ most similar skills for a query embedding $\mathbf{q} \in \mathbb{R}^{1 \times D}$:
1.  **Vectorized Dot Product:** We run a matrix-vector dot product in NumPy:
    
    $$\mathbf{s} = \frac{\mathbf{q} \mathbf{M}^T}{\|\mathbf{q}\| \|\mathbf{M}\|}$$
    
    *   **Time Complexity:** $O(S \times D)$ using NumPy BLAS operations.
    *   **Performance:** Completes in $<0.5\text{ms}$.
2.  **Top-K Sort:** We use `np.argpartition` to find the indices of the largest $K$ elements in $O(S \log K)$ time.

By utilizing in-memory matrix arithmetic, we avoid complex database scanning and avoid external indexing tools (like FAISS or HNSW indices), which are unnecessary at this scale.
