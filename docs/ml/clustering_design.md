# Clustering Design Document — Career Archetype Discovery
## Skill Genome Platform

---

## 1. Mathematical Concept & Core Definition

### 1.1 Representing Job Postings in Vector Space
To group job postings into distinct **Career Archetypes**, we must first represent each unstructured job posting as a dense numerical vector. 

Given a job posting $J$ containing a set of extracted and normalized canonical skills $S_J = \{s_1, s_2, \dots, s_M\}$, and their corresponding S-BERT dense embeddings $\{\mathbf{v}_1, \mathbf{v}_2, \dots, \mathbf{v}_M\} \subset \mathbb{R}^D$:

$$\mathbf{v}_J = \frac{1}{M} \sum_{i=1}^M \mathbf{v}_i$$

*   **Job Vector ($\mathbf{v}_J \in \mathbb{R}^D$):** The average skill embedding represents the centroid of the skills required by the role, mapping the job posting into our 384-dimensional skill vector space.

### 1.2 Career Archetype Discovery
A **Career Archetype** represents a dense region in the job-skills vector space. By clustering these job posting vectors, we discover natural professional roles (e.g., "ML Engineer", "Data Scientist", "Frontend Engineer") without manual cataloging.

---

## 2. Algorithm Selection: KMeans vs. HDBSCAN

We implemented a dual-algorithm approach to compare their performance in production. This comparison represents **essential talking points in senior data science interviews**:

| Dimension | KMeans (Centroid-Based Baseline) | HDBSCAN (Density-Based Advanced Model) |
|:---|:---|:---|
| **Cluster Shape** | Assumes spherical, equally-sized clusters. | Can find clusters of arbitrary shape and varying density. |
| **Noise Handling** | **Poor**. Forces every single job posting into a cluster, even outliers. | **Excellent**. Identifies outliers and labels them as "noise" (Cluster -1). |
| **Parameters** | Requires pre-specifying $k$ (number of clusters). | Automatic cluster selection based on minimum cluster size. |
| **Execution Speed** | Fast. $O(I \cdot k \cdot N \cdot D)$ time complexity. | Moderately slow. $O(N^2)$ or $O(N \log N)$ space/time. |
| **Use Case in Platform** | **Core Baseline**. Centennial coordinates make it easy to map career gaps. | **Niche Exploration**. Identifies rare, evolving, or interdisciplinary roles. |

### Our Production Clustering Strategy
We utilize **KMeans** as our production centroid-based engine because the resulting centroids represent clear "idealized" vector profiles. This is crucial for **Skill Gap Analysis**, which measures Euclidean distance and cosine distance between a user's skills and the centroid vector. 

However, we log **HDBSCAN** metrics to demonstrate system design flexibility and handling of market outliers during technical interviews.

---

## 3. Selecting Hyperparameters ($k$ Analysis)

To determine the optimal number of career archetypes ($k$) in KMeans, we utilize two mathematical validation techniques:

### 3.1 Within-Cluster Sum of Squares (Inertia / Elbow Method)
We calculate the inertia (SSE) for a range of $k \in [3, 15]$:

$$\text{SSE} = \sum_{j=1}^k \sum_{\mathbf{v}_J \in C_j} \|\mathbf{v}_J - \mathbf{\mu}_j\|^2$$

Where $\mathbf{\mu}_j$ is the centroid of cluster $C_j$. The optimal $k$ is selected at the "elbow" point where the rate of SSE decrease flattens out, balancing model complexity with cluster compactness.

### 3.2 Silhouette Coefficient
To measure how well-separated the discovered archetypes are, we calculate the Silhouette Score for each posting:

$$s(i) = \frac{b(i) - a(i)}{\max(a(i), b(i))}$$

*   $a(i)$: Mean intra-cluster distance between posting $i$ and all other postings in the same cluster.
*   $b(i)$: Mean nearest-cluster distance between posting $i$ and the next closest cluster.
*   **Target:** Global Silhouette Score $\ge 0.35$ with balanced cluster size distributions.

---

## 4. Centroid-Based Archetype Labeling

Once job postings are clustered, we label each archetype dynamically by inspecting the feature importance of skills in each cluster.

Instead of simple frequency counting (which biases common skills like "Python" or "Git"), we calculate a **Skill Centroid Importance Score (SCIS)**:

$$\text{SCIS}(s_g, C_j) = \text{Frequency}(s_g, C_j) \times \text{CosineSimilarity}(\mathbf{v}_g, \mathbf{\mu}_j)$$

*   $\mathbf{v}_g$: S-BERT embedding of canonical skill $s_g$.
*   $\mathbf{\mu}_j$: Centroid vector of archetype cluster $C_j$.
*   **Result:** A skill is highly important to an archetype if it appears frequently in that cluster's job postings AND its semantic embedding is highly aligned with the cluster's mathematical center. This gives us pristine, noise-free profile labels (e.g., matching `"PyTorch"` highly to `"ML Engineer"`, but `"React"` to `"Frontend Engineer"`).
