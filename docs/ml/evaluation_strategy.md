# Evaluation Strategy Document — Model Validation Framework
## Skill Genome Platform

---

## 1. Overview of Unsupervised Evaluation

A common trap in Machine Learning interviews is the question: *"How do you evaluate an unsupervised model (like embeddings or clustering) without labels?"* 

In the Skill Genome Platform, we address this by designing a **multi-layered, scientifically rigorous validation framework**. We combine statistical metrics, nearest-neighbor sanity thresholds, and an advanced **offline recommendation back-testing pipeline**.

---

## 2. Layer 1: NLP Skill Extraction Validation

To measure our TrieMatcher extraction accuracy before pushing it to API routes, we hand-label a gold-standard validation set of 100 job descriptions:

*   **Metric:** Precision and Recall.
    
    $$\text{Precision} = \frac{\text{True Positives (TP)}}{\text{TP} + \text{False Positives (FP)}}$$
    
    $$\text{Recall} = \frac{\text{True Positives (TP)}}{\text{TP} + \text{False Negatives (FN)}}$$

*   **Production Targets:**
    *   **Precision $> 0.90$:** We prioritize precision (avoiding extracting incorrect words as skills) over recall.
    *   **Recall $> 0.80$:** Capturing the vast majority of relevant technical skills.

---

## 3. Layer 2: Embedding Quality Validation

Since S-BERT is unsupervised, we evaluate embedding quality through spatial coherence tests:

*   **Nearest-Neighbor Domain Coherence:**
    For a test set of 20 diverse technical skills (e.g., Python, Docker, Figma, Agile), we extract their Top-5 nearest spatial neighbors based on Cosine Similarity.
    *   **Target:** $\ge 80\%$ average domain coherence (e.g., Python's neighbors must all be data/software libraries like Pandas, NumPy, or R, rather than unrelated UI/design tools).
*   **Analogy Validation Tests:**
    We evaluate semantic vectors using vector arithmetic checks:
    
    $$\mathbf{v}_{\text{PyTorch}} - \mathbf{v}_{\text{Python}} + \mathbf{v}_{\text{JavaScript}} \approx \mathbf{v}_{\text{React}}$$

---

## 4. Layer 3: Career Archetype Clustering Validation

We evaluate our KMeans and HDBSCAN clustering quality using three standard cluster validation metrics:

### 4.1 Silhouette Coefficient
Measures how similar a job posting is to its own cluster compared to other clusters.
*   **Formula:** $s(i) = \frac{b(i) - a(i)}{\max(a(i), b(i))}$ (Intra-cluster compact vs. Inter-cluster separation).
*   **Target:** Global Silhouette Score $\ge 0.35$.

### 4.2 Davies-Bouldin Index (DBI)
Measures the average similarity between each cluster and its most similar one. Lower scores mean better separation.
*   **Formula:** Let $R_{i,j}$ be the similarity between cluster $i$ and $j$. DBI is the average of the maximum $R_{i,j}$ for each cluster.
*   **Target:** DBI $< 1.5$.

### 4.3 Human Coherence Review
We extract the top 15 skills for each centroid (highest Centroid Importance Scores). 
*   **Acceptance:** The skills must paint a coherent, distinct professional profile (e.g., a cluster containing "React", "TypeScript", and "HTML" is valid; a cluster mixing "Kubernetes" and "Figma" is flagged for recalculation).

---

## 5. Layer 4: Recommender Engine Offline Back-Testing

The **crowning jewel of our ML validation** is our **Offline Skill Holdout Back-Test**. This mimics how production recommendation engines are evaluated at scale (e.g., Netflix, Spotify).

```
                      ┌────────────────────────────────┐
                      │   Validation Job Posting      │
                      │  Skills: [A, B, C, D, E, F]    │
                      └───────────────┬────────────────┘
                                      │
                      ┌───────────────▼────────────────┐
                      │    Random Split (80/20)        │
                      └───────┬────────────────┬───────┘
                              │                │
             Input (80%)      │                │ Hidden Ground Truth (20%)
             [A, B, C, D]     │                │ [E, F]
                      ┌───────▼────────┐       │
                      │  Recommendation│       │
                      │     Engine     │       │
                      └───────┬────────┘       │
                              │                │
            Top-5 Recs        │                │
            [E, G, H, I, J]   │                │
                      ┌───────▼────────┐       │
                      │ Compare & Rate ◀───────┘
                      │   Recall@K     │
                      │   MAP@K        │
                      └────────────────┘
```

### 5.1 The Holdout Process
1.  We select 1,000 job postings from our processed database.
2.  For each job, we randomly **hide 20% of its actual skills** (the ground truth target $Y$).
3.  We feed the remaining 80% of skills into our `Recommender` as the user's "current profile" $U$.
4.  We ask the recommender to generate the Top $K$ recommendations ($K=5$).
5.  We measure if the hidden ground truth skills $Y$ appear in our recommendations.

### 5.2 Evaluation Metrics
*   **Recall@K:** Measures the proportion of hidden skills successfully captured in the Top $K$ recommendations:
    
    $$\text{Recall@K} = \frac{|Y \cap \text{Top-K Recs}|}{|Y|}$$
    
    *   *Target:* Recall@5 $\ge 60\%$.
*   **Mean Average Precision (MAP@K):** Evaluates if the recommender ranks the hidden skills at the very top of the list, which is critical for user interfaces:
    
    $$\text{MAP@K} = \frac{1}{N} \sum_{i=1}^N \text{AP@K}_i$$
    
    $$\text{AP@K} = \frac{1}{|Y|} \sum_{p=1}^K \text{Precision@p} \cdot \mathbb{I}(p\text{th recommendation } \in Y)$$
    
    *   *Target:* MAP@5 $\ge 0.50$.
