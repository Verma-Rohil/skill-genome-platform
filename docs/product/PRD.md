# Product Requirements Document (PRD)
## Skill Genome & Career Intelligence Platform

**Version:** 1.0  
**Author:** [Your Name]  
**Date:** 2026-05-30  
**Status:** Approved

---

## 1. Executive Summary

The Skill Genome Platform is a career intelligence system that models the professional skill ecosystem as a living, evolving entity. Unlike traditional job analytics tools that answer "which skills are in demand?", this platform answers deeper questions:

- How do skills relate to each other?
- Which skill combinations define career archetypes?
- What should a professional learn next based on their current skill set?
- How do market shifts in one skill propagate to other skills and career archetypes?

The platform processes 100K+ job postings, extracts and normalizes skills using NLP, generates skill embeddings using Sentence-BERT, discovers career archetypes via clustering, and delivers personalized recommendations through a React dashboard backed by FastAPI.

---

## 2. Problem Statement

### Current State
- Job seekers rely on gut feeling or anecdotal advice to decide which skills to learn
- Hiring managers struggle to define precise skill requirements for evolving roles
- Career planning resources are static, outdated, and generic
- No system models the *relationships* between skills — they're treated as isolated keywords

### Desired State
- A data-driven platform that reveals hidden patterns in the skill ecosystem
- Personalized, evidence-based career recommendations
- Real-time trend tracking of skill demand
- Visual exploration of skill relationships and career pathways

### Impact
- Professionals make informed upskilling decisions
- Organizations understand skill landscape for workforce planning
- Educators align curricula with actual market demand

---

## 3. Target Users

| User Persona | Need | Key Feature |
|:---|:---|:---|
| **Job Seeker** | "What should I learn next?" | Skill gap analysis + recommendations |
| **Career Changer** | "What careers match my skills?" | Career archetype matching |
| **Hiring Manager** | "What skills define an ML Engineer?" | Archetype skill profiles |
| **Educator** | "What skills are in high synergy or vulnerable to shifts?" | Synergy & Disruption dashboard |
| **Data Enthusiast** | "How do skills relate?" | Skill explorer + network visualization |

---

## 4. Product Goals

| # | Goal | Metric |
|:--|:---|:---|
| G1 | Extract skills accurately from job descriptions | Precision > 0.85, Recall > 0.75 |
| G2 | Normalize skills to canonical forms | < 5% duplicate skill entities |
| G3 | Generate meaningful skill embeddings | Nearest-neighbor sanity: Python → Pandas ✅ |
| G4 | Discover interpretable career archetypes | Silhouette score > 0.3, human-labeled names |
| G5 | Provide relevant skill recommendations | Top-5 recommendation accuracy > 70% (user survey proxy) |
| G6 | Model skill synergies & simulate market shifts | Propagation sensitivity validates against controlled shocks |
| G7 | Expose all intelligence via API | 100% endpoints documented, <500ms latency |
| G8 | Deliver an interactive dashboard | 4 pages, responsive, <3s initial load |

---

## 5. Scope

### In Scope (v1.0)
- Skill extraction from job descriptions (dictionary + NER)
- Skill normalization pipeline
- Skill embedding generation (Sentence-BERT)
- Career archetype discovery (KMeans + HDBSCAN)
- Skill gap analysis
- Skill synergy mapping & Workforce Disruption Simulator (Conditional Probability matrix)
- Personalized skill recommendations
- REST API (FastAPI)
- React dashboard with network visualization
- MLflow experiment tracking
- Docker containerization

### Out of Scope (v1.0)
- User authentication / login
- Resume parsing (PDF upload)
- Real-time job scraping (using Kaggle datasets instead)
- Multi-language support
- Mobile application
- Salary prediction

---

## 6. Success Criteria

| Criterion | Measurement | Target |
|:---|:---|:---|
| **Technical Quality** | All automated tests pass | 100% pass rate |
| **ML Quality** | Embedding nearest-neighbor accuracy | > 80% meaningful neighbors |
| **Pipeline Completeness** | End-to-end: raw text → recommendation | Fully functional |
| **Documentation** | All 30 documents complete | 100% coverage |
| **Interview Readiness** | Can explain any component in < 5 min | Self-assessed |
| **Portfolio Impact** | Live demo accessible | Deployed or Docker runnable |

---

## 7. Assumptions

1. Kaggle LinkedIn/Indeed job posting datasets provide sufficient volume and quality
2. MySQL 8.x is available on the development machine
3. ~800 canonical skills cover the majority of tech industry demand
4. Jaccard similarity and Pointwise Mutual Information (PMI) capture robust semantic synergies
5. Sentence-BERT combined with co-occurrence metrics produces highly expressive semantic representations

---

## 8. Constraints

1. **Data:** No live scraping — dependent on static Kaggle datasets
2. **Compute:** Training runs on local machine (no GPU required for Word2Vec/KMeans)
3. **Scale:** Designed for thousands of skills, not millions
4. **Time:** 25-30 working days from start to completion

---

## 9. Risks

| Risk | Likelihood | Impact | Mitigation |
|:---|:--:|:--:|:---|
| Poor extraction accuracy | Medium | High | Start with curated dictionary; iterate on NER |
| Embeddings not meaningful | Low | High | Validate with known relationships; try S-BERT as fallback |
| Clusters not interpretable | Medium | Medium | Try multiple k values; manual labeling; HDBSCAN comparison |
| Scope creep (too many features) | High | High | Strict phase gates; each phase independently shippable |
| MySQL performance on large data | Low | Low | Proper indexing; load embeddings into memory |

---

## 10. Revision History

| Version | Date | Author | Changes |
|:---|:---|:---|:---|
| 1.0 | 2026-05-30 | [Your Name] | Initial PRD |
