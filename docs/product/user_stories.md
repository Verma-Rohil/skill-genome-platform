# User Stories
## Skill Genome Platform

---

## Job Seeker Stories

**US-01** | As a job seeker, I want to **input my current skills** and see which career archetypes I'm closest to, so I can understand my career positioning.
- **Acceptance:** API returns top-3 matching archetypes with match percentage
- **Endpoint:** `POST /api/careers/gap`

**US-02** | As a job seeker, I want to **see which skills I'm missing** for my target career, so I can prioritize my learning.
- **Acceptance:** Gap analysis returns ranked list of missing skills with importance scores
- **Endpoint:** `POST /api/careers/gap`

**US-03** | As a job seeker, I want to **get personalized skill recommendations**, so I know exactly what to learn next.
- **Acceptance:** Returns top-5 recommended skills with reasoning (trend, proximity, gap)
- **Endpoint:** `POST /api/recommendations`

---

## Explorer Stories

**US-04** | As an explorer, I want to **search for a skill and see related skills**, so I can understand the skill ecosystem.
- **Acceptance:** Returns top-10 similar skills with similarity scores
- **Endpoint:** `GET /api/skills/{id}/similar`

**US-05** | As an explorer, I want to **see a visual network of skill relationships**, so I can discover connections I didn't know about.
- **Acceptance:** Dashboard renders interactive D3.js/vis-network graph
- **Component:** `SkillNetwork.jsx`

**US-06** | As an explorer, I want to **extract skills from any job description**, so I can analyze a specific posting.
- **Acceptance:** Paste text → get structured skill list
- **Endpoint:** `POST /api/skills/extract`

---

## Trend Watcher Stories

**US-07** | As a trend watcher, I want to **see which skills are growing fastest**, so I can invest in future-proof skills.
- **Acceptance:** Returns top-10 emerging skills with growth rates
- **Endpoint:** `GET /api/trends/emerging`

**US-08** | As a trend watcher, I want to **see historical demand trends for any skill**, so I can understand its trajectory.
- **Acceptance:** Time-series data with monthly mention counts + forecast
- **Endpoint:** `GET /api/skills/{id}/trend`

**US-09** | As a trend watcher, I want to **see declining skills**, so I can avoid investing in fading technologies.
- **Acceptance:** Returns bottom-10 skills by growth rate
- **Endpoint:** `GET /api/trends/declining`

---

## Hiring Manager Stories

**US-10** | As a hiring manager, I want to **see the defining skills of each career archetype**, so I can write better job descriptions.
- **Acceptance:** Each archetype shows top-15 skills ranked by importance
- **Endpoint:** `GET /api/careers/archetypes/{id}`

---

## System Stories

**US-11** | As a developer, I want a **health check endpoint**, so monitoring tools can verify the service is running.
- **Endpoint:** `GET /api/health`

**US-12** | As a developer, I want **all API responses to be JSON with consistent schema**, so the frontend can parse them reliably.
- **Implementation:** Pydantic response models on all endpoints
