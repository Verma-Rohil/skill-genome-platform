# Software Engineering Lessons Learned

This document outlines key technical challenges, debugging discoveries, and design patterns established during the implementation of the **Skill Genome Platform**.

---

## 1. Domain Normalization in Data Ingestion Pipelines
*   **The Issue**: During initial ingestion of the LinkedIn jobs dataset, we encountered duplicate entries and missing join records. Analysis revealed that the `job_link` and `job_skills` tables contained internationalized subdomains (e.g. `ca.linkedin.com`, `uk.linkedin.com`) with variable query parameters.
*   **The Lesson**: Always strip query parameters and normalize subdomains to a uniform standard (e.g., `www.linkedin.com`) before building lookup indexes. Implementing a regex-based `normalize_link` helper resolved the duplicate issues and allowed us to correctly map **86,445 job-skill associations**.

---

## 2. Mocking SQLAlchemy ORM Queries in Pytest
*   **The Issue**: Unit tests crashed because a generic mock `db.query().all()` returned the same mock array regardless of whether a service requested `Skill`, `SkillEmbedding`, or `CareerArchetype`.
*   **The Lesson**: Simple mock fixtures do not scale for multi-model database operations. We designed a dynamic `MockQuery` class that acts as a query builder. It intercepts SQLAlchemy comparison operations (like `ArchetypeSkill.archetype_id == id` by checking the `.left.name` and `.right` properties of binary expressions) and filters mock datasets accordingly:
    ```python
    def filter(self, *args):
        for arg in args:
            left = getattr(arg, "left", None)
            right = getattr(arg, "right", None)
            if left is not None and right is not None:
                key = getattr(left, "key", None) or getattr(left, "name", None)
                val = getattr(right, "value", right)
                if key:
                    self.filters[key] = val
        return self
    ```
    This mock builder has zero external dependencies and guarantees robust, isolated API unit testing.

---

## 3. Pydantic v2 Environment Settings Validation
*   **The Issue**: Upgrading to Pydantic v2 broke settings parsing because the `.env` configuration file contained machine learning hyperparameters (e.g. `EMBEDDING_WINDOW`) that were not explicitly declared in the FastAPI `Settings` model. Pydantic raised validation errors for these undeclared keys.
*   **The Lesson**: In Pydantic v2, always set `extra="ignore"` in the `SettingsConfigDict` config container to allow the co-existence of machine learning and framework variables within a single `.env` file without breaking boot processes.

---

## 4. Graph Shock Propagation Directionality
*   **The Issue**: Early testing of the technology shock simulator showed that a shock to `PyTorch` was causing a massive surge in unrelated skills and no surge in `Python`. The transition weights were incorrectly mapped.
*   **The Lesson**: In directed networks, propagate shocks from source to target using conditional probabilities $P(\text{target} \vert \text{source}) = \text{confidence\_a\_b}$ (if `skill_a` is the source). Mapping transition arrays as $T[\text{source}][\text{target}] = P(\text{target} \vert \text{source})$ correctly aligned the propagation cascades.
