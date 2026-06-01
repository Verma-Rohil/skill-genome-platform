# Technical Interview Preparation Guide — Skill Genome Platform

This guide contains 30+ technical questions and answers designed to prepare you for senior data science, ML engineering, and full-stack software development interviews, based on the engineering decisions in this repository.

---

## 🧬 Section 1: NLP & Skill Extraction

### Q1: Why did you choose a Trie prefix tree for skill extraction over regular expressions or simple string loops?
> **Answer**: Nesting string checks for $S$ skills against text of length $N$ runs in $O(S \times N)$ time, which scales poorly. Compiling hundreds of regular expressions is also slow and prone to catastrophic backtracking. A Trie matcher (like FlashText) tokenizes the text and traverses the prefix tree in $O(N)$ linear time, completely independent of the size of the vocabulary ($S$).

### Q2: What is "greedy longest-match lookahead" and why is it important in skill extraction?
> **Answer**: If we match word-by-word, a description containing "Machine Learning" might trigger false positives for both "Machine" and "Learning". Greedy lookahead ensures that the parser continues traversing down the Trie to match the longest possible phrase ("Machine Learning") and consumes those tokens, preventing overlapping sub-matches.

### Q3: How does your tokenizer preserve symbols in technical skills like `C++`, `C#`, and `.js`?
> **Answer**: Standard tokenizers split on all non-alphanumeric characters, turning `C++` into `C` and `+`. In our Trie tokenizer (`_tokenize` in `skill_extractor.py`), we use regex patterns that specifically retain `+`, `#`, `.`, and `-` when they appear inside word boundaries, ensuring exact entity matching.

### Q4: How do you handle casing differences and pluralizations in Trie matching?
> **Answer**: We normalize all text input to lowercase and strip leading/trailing punctuation during tokenization. Pluralizations are mapped as registered aliases in the taxonomy database (e.g. `["Kubernetes clusters", "Kubernetes cluster"]` pointing to the canonical `Kubernetes`).

### Q5: What are the primary limits of a dictionary-based Trie matcher compared to a transformer-based NER model?
> **Answer**: Dictionary matching has 100% precision but cannot extract unseen skills (low recall for new entities). A transformer-based NER model can generalize to unseen terms based on syntactic context, but at the cost of high compute requirements and frequent false positives (e.g., extracting "Great" in "Great developer" as a skill).

---

## 📡 Section 2: Embeddings & Similarity Search

### Q6: Why did you choose Sentence-BERT (S-BERT) instead of Word2Vec for representing skill vectors?
> **Answer**: Word2Vec learns representations based only on local context co-occurrences in our dataset, failing on out-of-vocabulary (OOV) terms. S-BERT (`all-MiniLM-L6-v2`) is pre-trained on billions of sentences, allowing us to generate high-quality dense vectors for any arbitrary skill string entered by the user.

### Q7: Explain the mathematical formula for Cosine Similarity. Why is it used for embeddings?
> **Answer**: Cosine similarity measures the angle between two vectors:
> $$\text{Cosine Similarity}(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2}$$
> It is preferred for text/embeddings because it measures directional alignment rather than magnitude, ensuring long and short descriptions of the same concept remain close in vector space.

### Q8: How did you optimize cosine similarity lookups to execute in microseconds instead of milliseconds?
> **Answer**: Generating embeddings on-the-fly takes milliseconds. We pre-compute S-BERT vectors for all canonical skills and store them in MySQL. At app startup, we load these vectors into memory and normalize them ($\|\mathbf{u}\|_2 = 1$). Cosine similarity then simplifies to a simple matrix dot product:
> $$\text{Similarity} = \mathbf{X} \cdot \mathbf{q}$$
> This executes in microseconds via NumPy BLAS operations.

### Q9: How does the system handle Out-Of-Vocabulary (OOV) terms entered by users?
> **Answer**: If a searched skill is not in our database taxonomy, the `SimilarityEngine` falls back to the `EmbeddingEngine` to run local S-BERT inference on-the-fly, generating a 384-dimensional vector and comparing it against the pre-computed canonical matrix.

### Q10: What is the dimension of the `all-MiniLM-L6-v2` embedding? What are the tradeoffs of using a larger model like `all-mpnet-base-v2`?
> **Answer**: The dimension is 384. A larger model like `all-mpnet-base-v2` has 768 dimensions and slightly higher semantic accuracy, but increases inference latency, memory footprint, and database storage requirements.

---

## 💼 Section 3: Career Clustering & Archetypes

### Q11: How do you represent a job posting in vector space to feed into K-Means clustering?
> **Answer**: For a job posting requiring $k$ skills, we retrieve the S-BERT embedding for each skill and perform average pooling:
> $$\mathbf{v}_{\text{job}} = \frac{1}{k} \sum_{i=1}^k \mathbf{v}_{\text{skill}_i}$$
> This average vector represents the centroid of the job's skill requirements.

### Q12: Why did you choose K-Means for discovering career archetypes over hierarchical models like HDBSCAN?
> **Answer**: K-Means enforces spherical clusters and maps every job posting to a cluster, which is ideal for creating partition-based career paths (e.g. Frontend vs Backend). HDBSCAN is density-based and labels outliers as noise, which, while great for detecting anomalies, is less practical for cataloging all jobs in the market.

### Q13: How do you automatically generate names and descriptions for your career archetypes?
> **Answer**: In `clustering_engine.py`, we identify all job postings belonging to a cluster and calculate the frequency of each skill. The top 3 most frequent skills are joined to name the cluster (e.g. "Python, SQL, AWS"), and the top 5 are woven into the archetype's description.

### Q14: How do you determine the optimal number of clusters ($K$) for job postings?
> **Answer**: We use the **Elbow Method** (plotting the sum of squared distances to centroids against $K$) and the **Silhouette Coefficient**. We also run human sanity checks to ensure that the resulting archetypes represent realistic industry profiles.

### Q15: What are the limits of average-pooling skill vectors to represent a job posting?
> **Answer**: Average pooling assumes all skills are of equal importance and loses context. For example, a job requiring "Python" (core) and "Word" (minor) averages them equally. In production, TF-IDF or attention-based weighting can be layered to weight core skills higher.

---

## 🤝 Section 4: Synergy Networks & Disruption Simulator

### Q16: Define Support, Confidence, Lift, and PMI in the context of skill co-occurrences.
> **Answer**:
> - **Support**: $P(A \cap B)$ — Proportion of postings containing both skills.
> - **Confidence**: $P(B \vert A)$ — If a job requires $A$, probability it also requires $B$.
> - **Lift**: $P(A \cap B) / (P(A)P(B))$ — Ratio of observed co-occurrence to random chance. Lift $> 1$ indicates positive synergy.
> - **PMI**: $\log_2(\text{Lift})$ — Pointwise Mutual Information, showing semantic relatedness.

### Q17: Why is PMI (Pointwise Mutual Information) highly valuable in association mining?
> **Answer**: PMI normalizes for high-frequency skills. For example, "Communication" appears in almost all jobs, so it has high support with many skills. PMI penalizes these general associations and highlights niche, strong bonds (e.g., "React" and "Redux").

### Q18: Explain how your Workforce Disruption Simulator propagates shocks across the skill network.
> **Answer**: We model the market as a graph where nodes are skills and edge weights are conditional probabilities $P(\text{target} \vert \text{source})$. When a skill is shocked with value $s^{(0)}$, the shock propagates up to 2 hops:
> - **Hop 1**: $s_j^{(1)} = \max \left( s_j^{(0)}, \sum_{i} s_i^{(0)} \cdot P(j \vert i) \right)$
> - **Hop 2**: $s_j^{(2)} = \max \left( s_j^{(1)}, \gamma \sum_{k} s_k^{(1)} \cdot P(j \vert k) \right)$ (where $\gamma$ is a decay factor, e.g. 0.5).

### Q19: How do you calculate the vulnerability of a career archetype to technology shocks?
> **Answer**: The vulnerability is the weighted average of the propagated shocks of its required skills, weighted by their importance within the archetype:
> $$\text{Disruption}_c = \frac{\sum_j \text{Importance}_{c, j} \cdot s_j^{(2)}}{\sum_j \text{Importance}_{c, j}}$$

### Q20: Why did you pivot from time-series demand forecasting (Prophet) to a shock simulator?
> **Answer**: Extrapolating demand trends from static 2024 data is mathematically undefensible. A shock propagation model treats the market as a structural dependency network, enabling interactive "What-If" scenario planning that models how shifts propagate.

---

## 🔌 Section 5: Web App & API Architecture

### Q21: Explain the FastAPI dependency injection pattern using `Depends(get_db)`.
> **Answer**: `Depends(get_db)` injects a MySQL database session generator into endpoints. FastAPI opens a connection at the start of the HTTP request, injects it, and guarantees it closes via a `finally` block when the request finishes, preventing connection leaks.

### Q22: What is the Repository Pattern? How is it implemented in your codebase?
> **Answer**: The Repository Pattern decouples business logic from database operations. In our project, SQLAlchemy models define schemas, `database.py` manages connections, services handle calculations and SQL queries, and routers manage HTTP requests.

### Q23: Why do we configure CORS (Cross-Origin Resource Sharing) middleware in FastAPI?
> **Answer**: Browsers restrict cross-origin HTTP requests for security. Since our React frontend runs on `http://localhost:5173` and the backend on `http://localhost:8000`, we configure CORS middleware to allow the Vite server to query our endpoints.

### Q24: What is the benefit of using Pydantic's `from_attributes = True`?
> **Answer**: In Pydantic v2, `from_attributes = True` (formerly `orm_mode = True`) allows the schema to read data directly from ORM models (lazy-loaded attributes) instead of requiring a raw dictionary, simplifying serialization.

### Q25: How do database indexes optimize your API queries?
> **Answer**: We indexed the `skills` and `job_postings` tables. Searching for matching skills or archetypes query indexes instead of scanning millions of rows, keeping search times constant.

---

## 🛠️ Section 6: MLOps & Deployment

### Q26: What is a multi-stage Docker build? What are its benefits for ML applications?
> **Answer**: Multi-stage builds compile packages in a temporary image and copy only the final assets to the runtime container. This excludes compiler libraries (like GCC) and build tools from the final image, reducing image sizes from gigabytes to megabytes.

### Q27: Why did you bake S-BERT weights into the Docker image during build time?
> **Answer**: S-BERT downloads model weights on startup, causing high latencies (~10-30s) and failing in offline environments. Baking weights into the image cache during the build stage ensures instant startup and offline capability.

### Q28: How does MLflow track your career clustering experiments?
> **Answer**: In our training scripts, MLflow logs hyperparameters (e.g. cluster count $K$) and metrics (e.g. Silhouette scores) to the tracking server. This logs experiment histories to compare model quality across versions.

### Q29: How do volumes in `docker-compose.yml` ensure database persistence?
> **Answer**: Containers are ephemeral. Mounting a local host directory or named docker volume to `/var/lib/mysql` inside the container ensures that MySQL data persists even if the container is stopped or rebuilt.

### Q30: What is the role of your GitHub Actions CI pipeline?
> **Answer**: The pipeline automates checks on push. It sets up python, installs dependencies, runs `flake8` to check code quality, and runs `pytest` to ensure all tests pass before code is merged.
