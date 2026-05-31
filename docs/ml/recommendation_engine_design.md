# Recommendation Engine Design Document — Multi-Signal Scoring Layer
## Skill Genome Platform

---

## 1. Introduction

The **Personalized Recommendation Engine** is the core product feature of the Skill Genome Platform. It answers the user's primary query: *"Given my current skills, what should I learn next to transition to my target career?"*

Rather than relying on simple popularity or single-factor similarity, our recommendation engine uses a **multi-signal score blending algorithm** that balances semantic adjacency, statistical market demand co-occurrences, and target career gaps.

---

## 2. Multi-Signal Scoring Architecture

To recommend a candidate skill $s$ to a user with a current skill set $U$ and a target career archetype $C_{\text{target}}$ represented by centroid $\mathbf{\mu}_{\text{target}}$, the engine computes three normalized sub-scores:

```
                  ┌──────────────────────────────┐
                  │ User Profile & Target Career │
                  └──────────────┬───────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
┌──────────────────┐   ┌──────────────────┐    ┌──────────────────┐
│  Semantic Score  │   │  Synergy Score   │    │    Gap Score     │
│    (S_embed)     │   │   (S_synergy)    │    │     (S_gap)      │
│ Vector proximity │   │ Co-occurrence    │    │ Centroid urgency │
│   to current     │   │   market lift    │    │    in target     │
└────────┬─────────┘   └────────┬─────────┘    └────────┬─────────┘
         │                      │                       │
         └───────────────┬──────┴───────────────────────┘
                         │ Weights: [0.4, 0.3, 0.3]
                         ▼
             ┌───────────────────────┐
             │ Recommendation Score  │
             │         R(s)          │
             └───────────────────────┘
```

### Signal 1: Semantic Adjacency ($S_{\text{embed}}$)
*   **Concept:** Measures how "easy" it is for the user to learn the skill based on its semantic proximity to their *existing* skill set. Learning adjacent skills (e.g. learning PyTorch when you already know Python) has a lower cognitive hurdle than jumping to completely unrelated fields.
*   **Formula:** The similarity of candidate skill $s$ is the maximum cosine similarity to any skill in the user's current profile $U$:
    
    $$S_{\text{embed}}(s) = \max_{u \in U} \text{CosineSimilarity}(\mathbf{v}_s, \mathbf{v}_u)$$

### Signal 2: Co-occurrence Synergy ($S_{\text{synergy}}$)
*   **Concept:** Measures how frequently the candidate skill co-occurs with the user's current skills in actual job listings. This captures market bundling practices.
*   **Formula:** The average normalized Lift score between the candidate skill $s$ and all of the user's current skills $U$:
    
    $$S_{\text{synergy}}(s) = \frac{1}{|U|} \sum_{u \in U} \text{MinMaxNormalizedLift}(s, u)$$

### Signal 3: Centroid Gap Priority ($S_{\text{gap}}$)
*   **Concept:** Measures how crucial the candidate skill is to the user's *target* career archetype. A skill that is central to the target centroid but missing from the user's profile is a critical gap.
*   **Formula:** Extracted directly from the archetype feature weights:
    
    $$S_{\text{gap}}(s) = \text{SCIS}(s, C_{\text{target}})$$

---

## 3. Score Blending & Weighting

The unified **Recommendation Score $R(s)$** is computed as a weighted linear combination of the three sub-scores:

$$R(s) = w_1 \cdot S_{\text{embed}}(s) + w_2 \cdot S_{\text{synergy}}(s) + w_3 \cdot S_{\text{gap}}(s)$$

*   **Production Weights:** $w_1 = 0.40$ (Semantic Proximity), $w_2 = 0.30$ (Co-occurrence Synergy), $w_3 = 0.30$ (Target Gap Priority).
*   **Score Normalization:** Prior to blending, all three sub-scores are normalized using Min-Max scaling to the range $[0, 1]$ across all candidate skills to ensure equal scaling:
    
    $$S_{\text{normalized}} = \frac{S - S_{\min}}{S_{\max} - S_{\min}}$$

---

## 4. Cold Start Mitigation

A common failure mode in recommender system design is the **Cold Start Problem** (e.g. what if a new user enters zero skills or only one skill?):

*   **Zero Skills Entered:** If $U = \emptyset$, the semantic proximity and co-occurrence synergy calculations are undefined. In this scenario, the engine automatically falls back to **Popularity-Based Centroid Seeding**, recommending the top-ranked skills in the target archetype $C_{\text{target}}$ sorted by their centroid importance scores.
*   **Niche Skills Entered:** If a user enters highly unique skills that have zero co-occurrence counts in our `skill_cooccurrences` table, $S_{\text{synergy}}$ defaults to $0$, and the engine relies entirely on the semantic S-BERT similarity ($S_{\text{embed}}$) to suggest relevant adjacent terms.

---

## 5. Recommendation Explainability (API Metadata)

For modern product interfaces, "black-box" recommendations are ineffective. The API response for each recommended skill includes structured metadata explaining *why* it was suggested:

```json
{
  "skill_name": "Docker",
  "recommended_score": 0.87,
  "reasons": [
    {
      "type": "gap",
      "text": "Critical gap: Required in 84% of ML Engineer roles."
    },
    {
      "type": "synergy",
      "text": "High synergy with your skill: Python (3.1x co-occurrence lift)."
    },
    {
      "type": "similarity",
      "text": "Semantically related to your skill: Kubernetes (89% similarity)."
    }
  ]
}
```
This metadata is parsed by the React frontend to render detailed tooltips on the **Career Intel** dashboard page.
