# Data Source Strategy
## Skill Genome Platform

---

## 1. Primary Dataset

### 1.3M LinkedIn Jobs & Skills (2024) — Kaggle

| Attribute | Details |
|:---|:---|
| **Source** | Kaggle (public, free) |
| **Size** | ~1.3M job postings |
| **Key Columns** | `job_id`, `title`, `description`, `company`, `location`, `skills`, `posted_date` |
| **Skills Column** | Pre-extracted comma-separated skill list |
| **Why This Dataset** | Large volume, pre-extracted skills (validation data), temporal coverage, tech-focused |

### Why This Over Alternatives

| Alternative | Why Not |
|:---|:---|
| Indeed dataset | Smaller, less structured |
| Scraping live data | ToS violations, rate limiting, time-consuming |
| O*NET | Occupational taxonomy but no job-level skill co-occurrence |
| Synthetic data | No real-world signal — defeats the purpose |

---

## 2. Data Usage Plan

```
Raw CSV (Kaggle download)
    │
    ├── job_id, title, company, location, posted_date
    │   └── → job_postings table
    │
    ├── description (raw text)
    │   └── → Skill Extraction pipeline (Phase 1)
    │
    └── skills (pre-extracted list)
        └── → Validation: compare our NLP extraction against these
             → Also used directly for initial graph/embedding if NLP pipeline
                is still being tuned
```

### Dual-Use Strategy

1. **Pre-extracted `skills` column** — Use as ground truth for validating our NLP extraction pipeline
2. **Raw `description` column** — Feed into our own extraction pipeline to demonstrate NLP capability

This gives us the best of both worlds: reliable data for embeddings AND a showcase for NLP skills.

---

## 3. Data Volume Decisions

| Decision | Value | Why |
|:---|:---|:---|
| **Total postings to ingest** | ~100K–200K (subset) | Full 1.3M is unnecessary; 100K gives sufficient co-occurrence signal |
| **Time range** | Most recent 12–18 months | Ensures trends are current |
| **Skill vocabulary** | ~800–1500 canonical skills | Covers tech industry thoroughly |
| **Minimum skill frequency** | ≥ 50 mentions | Filters noise; ensures meaningful embeddings |

---

## 4. Secondary Data Sources (Future Enrichment)

| Source | What It Adds | Priority |
|:---|:---|:---|
| Stack Overflow Developer Survey | Salary correlation, technology preferences | Low (v2) |
| GitHub Trending | Open-source skill signal | Low (v2) |
| Google Trends | Consumer interest validation | Low (v2) |

---

## 5. Data Quality Considerations

| Issue | Mitigation |
|:---|:---|
| Duplicate postings | Deduplicate on (title, company, posted_date) |
| Missing skills | Use NLP extraction on description as fallback |
| Skill typos/variants | Normalization pipeline (Phase 2) handles this |
| Date gaps | Interpolate or exclude sparse periods |
| Bias toward large companies | Acknowledge in limitations; sample by company if needed |
