"""
Skill Genome Platform — Synthetic Data Generator
==================================================
Generates a highly realistic dataset of canonical skills (taxonomy) and job postings.
This bootstrap dataset allows developers to run and test the complete ML and API
pipeline without downloading the multi-gigabyte Kaggle dataset.

Skills are grouped into categories, and job descriptions are generated dynamically
using career-archetype templates to ensure realistic co-occurrence patterns
(e.g., React & TypeScript in Frontend, PyTorch & MLOps in ML Engineering).
"""

import csv
import json
import random
import os
from datetime import datetime, timedelta

# --- Configuration ---
NUM_JOBS = 200
SEED = 42
random.seed(SEED)

SKILLS_DATA = [
    # --- Data Science & Machine Learning ---
    {"name": "Python", "category": "Programming Languages", "aliases": ["python", "py"]},
    {"name": "R", "category": "Programming Languages", "aliases": ["r-lang", "r programming"]},
    {"name": "Julia", "category": "Programming Languages", "aliases": ["julia-lang"]},
    {"name": "SQL", "category": "Databases & Storage", "aliases": ["sql", "structured query language"]},
    {"name": "Machine Learning", "category": "Methodology & MLOps", "aliases": ["ml", "machine-learning", "statistical learning"]},
    {"name": "Deep Learning", "category": "Methodology & MLOps", "aliases": ["dl", "deep-learning", "neural networks"]},
    {"name": "Natural Language Processing", "category": "Methodology & MLOps", "aliases": ["nlp", "text-mining", "large language models"]},
    {"name": "Computer Vision", "category": "Methodology & MLOps", "aliases": ["cv", "image-processing"]},
    {"name": "PyTorch", "category": "Libraries & Frameworks", "aliases": ["pytorch", "torch"]},
    {"name": "TensorFlow", "category": "Libraries & Frameworks", "aliases": ["tensorflow", "tf"]},
    {"name": "Scikit-Learn", "category": "Libraries & Frameworks", "aliases": ["scikit-learn", "sklearn"]},
    {"name": "Pandas", "category": "Libraries & Frameworks", "aliases": ["pandas"]},
    {"name": "NumPy", "category": "Libraries & Frameworks", "aliases": ["numpy"]},
    {"name": "MLflow", "category": "Methodology & MLOps", "aliases": ["mlflow", "ml-flow"]},
    {"name": "DVC", "category": "Methodology & MLOps", "aliases": ["dvc", "data-version-control"]},
    {"name": "Feature Engineering", "category": "Methodology & MLOps", "aliases": ["feature-engineering", "feature selection"]},
    {"name": "Statistics", "category": "Methodology & MLOps", "aliases": ["stats", "probability", "statistical analysis"]},

    # --- Software Engineering & Web Development ---
    {"name": "JavaScript", "category": "Programming Languages", "aliases": ["javascript", "js"]},
    {"name": "TypeScript", "category": "Programming Languages", "aliases": ["typescript", "ts"]},
    {"name": "Java", "category": "Programming Languages", "aliases": ["java"]},
    {"name": "C++", "category": "Programming Languages", "aliases": ["c plus plus", "cpp"]},
    {"name": "Go", "category": "Programming Languages", "aliases": ["golang", "go-lang"]},
    {"name": "Rust", "category": "Programming Languages", "aliases": ["rust-lang"]},
    {"name": "HTML", "category": "Programming Languages", "aliases": ["html5", "html"]},
    {"name": "CSS", "category": "Programming Languages", "aliases": ["css3", "css"]},
    {"name": "React", "category": "Libraries & Frameworks", "aliases": ["react", "react.js", "reactjs"]},
    {"name": "Next.js", "category": "Libraries & Frameworks", "aliases": ["nextjs", "next.js"]},
    {"name": "Node.js", "category": "Libraries & Frameworks", "aliases": ["nodejs", "node"]},
    {"name": "FastAPI", "category": "Libraries & Frameworks", "aliases": ["fastapi"]},
    {"name": "Flask", "category": "Libraries & Frameworks", "aliases": ["flask"]},
    {"name": "Django", "category": "Libraries & Frameworks", "aliases": ["django"]},
    {"name": "Redux", "category": "Libraries & Frameworks", "aliases": ["redux", "redux-toolkit"]},
    {"name": "TailwindCSS", "category": "Libraries & Frameworks", "aliases": ["tailwind", "tailwindcss"]},
    {"name": "GraphQL", "category": "Libraries & Frameworks", "aliases": ["graphql"]},
    {"name": "REST API", "category": "Methodology & MLOps", "aliases": ["rest", "rest-api", "web services"]},

    # --- Cloud & DevOps ---
    {"name": "Docker", "category": "Cloud & DevOps", "aliases": ["docker", "containers"]},
    {"name": "Kubernetes", "category": "Cloud & DevOps", "aliases": ["k8s", "kubernetes"]},
    {"name": "AWS", "category": "Cloud & DevOps", "aliases": ["aws", "amazon web services"]},
    {"name": "GCP", "category": "Cloud & DevOps", "aliases": ["gcp", "google cloud platform", "google cloud"]},
    {"name": "Azure", "category": "Cloud & DevOps", "aliases": ["azure", "microsoft azure"]},
    {"name": "Terraform", "category": "Cloud & DevOps", "aliases": ["terraform", "iac"]},
    {"name": "CI/CD", "category": "Cloud & DevOps", "aliases": ["cicd", "continuous integration", "github actions", "jenkins"]},
    {"name": "Linux", "category": "Cloud & DevOps", "aliases": ["linux", "bash", "unix"]},
    {"name": "Git", "category": "Cloud & DevOps", "aliases": ["git", "github", "gitlab"]},
    {"name": "Prometheus", "category": "Cloud & DevOps", "aliases": ["prometheus", "monitoring"]},
    {"name": "Grafana", "category": "Cloud & DevOps", "aliases": ["grafana"]},

    # --- Databases ---
    {"name": "PostgreSQL", "category": "Databases & Storage", "aliases": ["postgres", "postgresql"]},
    {"name": "MySQL", "category": "Databases & Storage", "aliases": ["mysql"]},
    {"name": "MongoDB", "category": "Databases & Storage", "aliases": ["mongodb", "mongo"]},
    {"name": "Redis", "category": "Databases & Storage", "aliases": ["redis"]},
    {"name": "Cassandra", "category": "Databases & Storage", "aliases": ["cassandra"]},
    {"name": "Snowflake", "category": "Databases & Storage", "aliases": ["snowflake"]},

    # --- Product & Design ---
    {"name": "Product Strategy", "category": "Product & Design", "aliases": ["product-strategy", "product vision"]},
    {"name": "User Research", "category": "Product & Design", "aliases": ["user-research", "ux-research"]},
    {"name": "Agile", "category": "Product & Design", "aliases": ["agile", "scrum", "kanban"]},
    {"name": "Roadmapping", "category": "Product & Design", "aliases": ["roadmapping", "roadmap planning"]},
    {"name": "Figma", "category": "Product & Design", "aliases": ["figma"]},
    {"name": "UI/UX", "category": "Product & Design", "aliases": ["ui-ux", "user interface", "user experience"]},

    # --- Business & Soft Skills ---
    {"name": "Communication", "category": "Business & Soft Skills", "aliases": ["communication", "writing", "presentation"]},
    {"name": "Leadership", "category": "Business & Soft Skills", "aliases": ["leadership", "mentoring", "team management"]},
    {"name": "Problem Solving", "category": "Business & Soft Skills", "aliases": ["problem-solving", "analytical skills"]},
    {"name": "Data Visualization", "category": "Business & Soft Skills", "aliases": ["data-viz", "tableau", "powerbi", "recharts"]},
]

ARCHETYPES = {
    "ML Engineer": {
        "skills": ["Python", "PyTorch", "TensorFlow", "Docker", "Kubernetes", "MLflow", "CI/CD", "Git", "Linux", "SQL", "Machine Learning", "Deep Learning"],
        "companies": ["OpenAI", "Google", "Meta", "Tesla", "NVIDIA", "Anthropic", "Hugging Face"],
        "templates": [
            "We are seeking an experienced ML Engineer to join our AI team. In this role, you will design, train, and deploy large-scale deep learning models. You'll write clean code in {skill_0} using frameworks like {skill_1} and {skill_2}. MLOps is central to our pipeline, and you will use {skill_3} and {skill_4} for containerization and orchestration, alongside {skill_5} for experiment tracking. Strong familiarity with {skill_6} and {skill_7} is required.",
            "Our Core AI Infrastructure team is looking for a Machine Learning Engineer. You will work on productionizing NLP and computer vision systems. The role demands deep expertise in {skill_0} and structural software engineering. You will build scalable systems using {skill_1}, deploy using {skill_3} and {skill_4}, and manage infrastructure through {skill_6}. Standard workflows include active {skill_7} and querying structured datasets via {skill_9}."
        ]
    },
    "Data Scientist": {
        "skills": ["Python", "SQL", "Pandas", "NumPy", "Scikit-Learn", "Statistics", "Machine Learning", "Communication", "Data Visualization"],
        "companies": ["Netflix", "Airbnb", "Uber", "Spotify", "Stripe", "Lyft"],
        "templates": [
            "Join our Data Science team to drive decisions across our consumer products. You will formulate hypotheses, design A/B tests, and build predictive models. Excellent coding skills in {skill_0} and {skill_1} are required. You will leverage {skill_2} and {skill_3} for feature engineering, train classifiers using {skill_4}, and apply rigorous {skill_5} principles. Strong {skill_7} skills are essential to present insights to stakeholders, using tools for {skill_8}.",
            "We are hiring a Senior Data Scientist to analyze complex user behavioral datasets. This role requires a balance of statistical expertise and hands-on engineering. You will query massive tables with {skill_1}, write preprocessing pipelines in {skill_0} with {skill_2}, and construct models using {skill_4} and {skill_6}. You will interpret findings using advanced {skill_5} and communicate strategies via high-impact {skill_8}."
        ]
    },
    "Frontend Engineer": {
        "skills": ["JavaScript", "TypeScript", "React", "Next.js", "HTML", "CSS", "TailwindCSS", "Redux", "Git", "REST API", "UI/UX", "Figma"],
        "companies": ["Vercel", "Stripe", "Shopify", "Canva", "Linear", "Slack"],
        "templates": [
            "We are looking for a creative Frontend Engineer who loves building stunning user experiences. You will own client-side applications written in {skill_1} utilizing {skill_2} and {skill_3}. You will translate mockups from {skill_11} into responsive {skill_4} and {skill_5} layouts, styled with {skill_6}. Integrating with {skill_9} is a core duty, and managing codebase version control is handled via {skill_8}.",
            "Our Product Experience team has an opening for a Frontend Developer. You will build interactive components using {skill_2} and manage state with {skill_7}. High proficiency in {skill_1} and web core technologies like {skill_4}/{skill_5} is a must. You will collaborate closely with designers on {skill_10} patterns, leveraging {skill_11} files, and pull data from dynamic {skill_9} systems."
        ]
    },
    "Backend Engineer": {
        "skills": ["Python", "FastAPI", "PostgreSQL", "MySQL", "Redis", "Docker", "REST API", "Git", "AWS", "Linux"],
        "companies": ["Dropbox", "Stripe", "GitHub", "Zoom", "Reddit", "DoorDash"],
        "templates": [
            "We are seeking a Backend Engineer to scale our transactional systems. You will build high-performance services in {skill_0} using {skill_1}. Persistence is managed using relational databases like {skill_2} and caching is handled with {skill_4}. You will package applications using {skill_5}, expose them via standardized {skill_6}, and deploy across {skill_8} infrastructure. Collaborative development is run via {skill_7}.",
            "Our Core Platform team is looking for a Backend Systems Developer. You will write robust, low-latency APIs. You should have strong experience building {skill_6} endpoints in {skill_0} (using {skill_1} or Django). The infrastructure is powered by {skill_2} and cached with {skill_4}. The system runs on {skill_9} nodes containerized using {skill_5}, with source control on {skill_7}."
        ]
    },
    "DevOps/SRE": {
        "skills": ["Docker", "Kubernetes", "AWS", "GCP", "Terraform", "CI/CD", "Linux", "Git", "Prometheus", "Grafana"],
        "companies": ["HashiCorp", "Datadog", "Cloudflare", "PagerDuty", "AWS", "Sentry"],
        "templates": [
            "We are hiring a DevOps Engineer to automate and scale our cloud infrastructure. You will manage robust deployments on {skill_2} and {skill_3}. You will define Infrastructure as Code using {skill_4} and orchestrate clusters using {skill_1}. Continuous delivery is powered by automated {skill_5}. You will monitor ecosystem health with {skill_8} and {skill_9}, ensuring stability on our production {skill_6} environment.",
            "Our Site Reliability Engineering team is looking for an engineer to champion automation. You will containerize applications with {skill_0}, manage container systems on {skill_1}, and automate platform builds using {skill_4} on {skill_2} networks. Core tasks involve configuring continuous delivery pipelines via {skill_5}, managing repositories in {skill_7}, and building dashboard visualizations in {skill_9}."
        ]
    },
    "Product Manager": {
        "skills": ["Product Strategy", "User Research", "Agile", "Roadmapping", "Communication", "Leadership", "Data Visualization"],
        "companies": ["Google", "Atlassian", "Asana", "Intercom", "Notion", "Figma"],
        "templates": [
            "We are seeking a Product Manager to lead a cross-functional squad. You will define the {skill_0} and manage the active {skill_3}. In this role, you will conduct continuous {skill_1} to understand pain points, collaborate with engineers in an {skill_2} framework, and coordinate rollouts. Effective {skill_4} and cross-squad {skill_5} are mandatory to align stakeholders.",
            "Join us as a Product Manager for our Growth team. You will drive feature adoption. You will define product metrics and analyze behavior utilizing {skill_6}. The day-to-day includes aligning developers via {skill_2} processes, drafting high-fidelity {skill_3} plans, and communicating product updates to customers. This role demands exceptional {skill_5} and {skill_4} skills."
        ]
    }
}

LOCATIONS = ["San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX", "Boston, MA", "Remote", "Chicago, IL"]
WORK_TYPES = ["Remote", "Hybrid", "On-site"]
SENIORITIES = ["Entry-level", "Mid-level", "Senior-level", "Lead"]

def generate_data():
    # Ensure directories exist
    os.makedirs("backend/data/processed", exist_ok=True)
    os.makedirs("backend/data/raw", exist_ok=True)

    # 1. Write skills taxonomy CSV
    taxonomy_file = "backend/data/processed/skills_taxonomy.csv"
    with open(taxonomy_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["canonical_name", "category", "aliases"])
        for skill in SKILLS_DATA:
            writer.writerow([skill["name"], skill["category"], json.dumps(skill["aliases"])])
    print(f"[OK] Generated skills taxonomy CSV: {taxonomy_file}")

    # 2. Generate job postings
    jobs = []
    base_date = datetime.now() - timedelta(days=90)
    
    for i in range(NUM_JOBS):
        role_type = random.choice(list(ARCHETYPES.keys()))
        archetype = ARCHETYPES[role_type]
        
        # Pick skills to weave into the template
        role_skills = archetype["skills"]
        # Make sure we select enough skills to satisfy the template placeholders
        picked_skills = random.sample(role_skills, len(role_skills))
        
        template = random.choice(archetype["templates"])
        # Format the description with random but relevant skills
        format_dict = {f"skill_{idx}": val for idx, val in enumerate(picked_skills)}
        description = template.format(**format_dict)
        
        # Add random noise text to simulate messy descriptions
        description += "\n\nRequirements:\n"
        for s in picked_skills[:random.randint(4, 8)]:
            description += f"- Experience with {s} or equivalent technologies\n"
        description += "\nBenefits:\n- Competitive salary & equity\n- Health, dental, and vision insurance\n- Flexible work schedule"

        company = random.choice(archetype["companies"])
        title = f"{random.choice(['Senior ', 'Lead ', 'Staff ', ''])}{role_type}"
        posted_date = (base_date + timedelta(days=random.randint(0, 90))).strftime("%Y-%m-%d")
        
        jobs.append({
            "external_id": f"lk-{1000000 + i}",
            "title": title,
            "company_name": company,
            "description": description,
            "location": random.choice(LOCATIONS),
            "work_type": random.choice(WORK_TYPES),
            "seniority_level": random.choice(SENIORITIES),
            "posted_date": posted_date,
            "source": "linkedin"
        })
    
    jobs_file = "backend/data/processed/sample_jobs.csv"
    with open(jobs_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["external_id", "title", "company_name", "description", "location", "work_type", "seniority_level", "posted_date", "source"])
        for job in jobs:
            writer.writerow([
                job["external_id"],
                job["title"],
                job["company_name"],
                job["description"],
                job["location"],
                job["work_type"],
                job["seniority_level"],
                job["posted_date"],
                job["source"]
            ])
    print(f"[OK] Generated synthetic jobs CSV ({NUM_JOBS} records): {jobs_file}")

if __name__ == "__main__":
    generate_data()
