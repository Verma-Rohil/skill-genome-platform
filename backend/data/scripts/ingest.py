import zipfile
import csv
import io
import re
import os
import json
from collections import Counter
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import database config and models
# Add the backend root to system path to allow importing app modules
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.config import get_settings
from app.models.skill_category import SkillCategory
from app.models.skill import Skill
from app.models.job_posting import JobPosting
from app.models.job_skill import JobSkill

# --- Configuration ---
MAX_JOBS = 10000          # Size of real-data cohort for local processing speed
MIN_SKILL_FREQUENCY = 5   # Filter out extremely rare/noisy skills
TOP_SKILLS_LIMIT = 800    # Limit the canonical vocabulary size
ZIP_PATH = r"c:\Project_2\Dataset\archive (3).zip"

# Regular expression to match tech/data roles cleanly (avoiding partial matches like "retail" containing "ai")
TECH_PATTERN = re.compile(
    r'\b(data|engineer|engineering|analyst|analysts|developer|developers|scientist|scientists|'
    r'devops|cloud|software|machine\s+learning|ai|database|databases|programmer|programmers|'
    r'architect|architects|tech\s+lead|product\s+manager|product\s+owners?)\b', 
    re.IGNORECASE
)

# Simple rule-based classifier to group real-world skills into categories
def categorize_skill(skill_name):
    name = skill_name.lower()
    
    prog_langs = ['python', 'java', 'c++', 'c#', 'javascript', 'typescript', 'ruby', 'php', 'html', 'css', 'rust', 'golang', 'go-lang', 'scala', 'perl', 'kotlin', 'swift', 'objective-c', 'shell', 'bash']
    databases = ['sql', 'mysql', 'postgres', 'postgresql', 'oracle', 'mongodb', 'cassandra', 'redis', 'sqlite', 'database', 'bigquery', 'redshift', 'snowflake', 'nosql', 'mariadb', 'dynamodb', 'elasticsearch']
    libraries = ['pandas', 'numpy', 'scipy', 'scikit', 'sklearn', 'tensorflow', 'pytorch', 'keras', 'react', 'next.js', 'nextjs', 'angular', 'vue', 'django', 'flask', 'fastapi', 'spring', 'bootstrap', 'tailwind', 'jquery', 'express', 'node']
    devops = ['aws', 'gcp', 'azure', 'docker', 'kubernetes', 'k8s', 'jenkins', 'terraform', 'ci/cd', 'cicd', 'ansible', 'puppet', 'chef', 'openstack', 'linux', 'unix', 'git', 'github', 'gitlab', 'monitoring', 'prometheus', 'grafana', 'cloud', 'sysadmin']
    ml_methodology = ['agile', 'scrum', 'kanban', 'project management', 'machine learning', 'deep learning', 'nlp', 'computer vision', 'data analysis', 'statistical', 'feature engineering', 'mlflow', 'dvc', 'ab testing', 'a/b testing', 'statistics', 'probability']
    soft_skills = ['communication', 'leadership', 'teamwork', 'management', 'solving', 'organization', 'analytical', 'presentation', 'negotiation', 'mentoring', 'collaboration', 'writing', 'critical thinking']
    
    if any(lang in name for lang in prog_langs):
        return "Programming Languages"
    elif any(db in name for db in databases):
        return "Databases & Storage"
    elif any(lib in name for lib in libraries):
        return "Libraries & Frameworks"
    elif any(dops in name for dops in devops):
        return "Cloud & DevOps"
    elif any(mld in name for mld in ml_methodology):
        return "Methodology & MLOps"
    elif any(soft in name for soft in soft_skills):
        return "Business & Soft Skills"
    else:
        return "General Tech Skills"

def normalize_link(link: str) -> str:
    if not link:
        return ""
    # Standardize subdomain to www.linkedin.com and strip query parameters
    link_clean = re.sub(r'https?://[a-z]{2,3}\.linkedin\.com', 'https://www.linkedin.com', link.strip())
    link_clean = link_clean.split('?')[0]
    return link_clean

def run_ingestion():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    print("[Ingestion] Starting real-data ingestion pipeline...")
    
    if not os.path.exists(ZIP_PATH):
        print(f"[Ingestion] Error: Zip file not found at {ZIP_PATH}")
        return
        
    # Step 1: Scan and filter postings for tech roles
    print("[Ingestion] Step 1: Scanning job postings...")
    job_postings_meta = []
    job_links_set = set()
    
    with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
        with zip_ref.open("linkedin_job_postings.csv") as f:
            wrapper = io.TextIOWrapper(f, encoding='utf-8', errors='ignore')
            reader = csv.DictReader(wrapper)
            
            for row in reader:
                title = row.get("job_title", "")
                if TECH_PATTERN.search(title):
                    job_link = row.get("job_link")
                    norm_link = normalize_link(job_link)
                    if norm_link not in job_links_set:
                        job_links_set.add(norm_link)
                        # Store metadata
                        job_postings_meta.append({
                            "external_id": norm_link.split("-")[-1] if "-" in norm_link else "unknown",
                            "job_link": norm_link,
                            "title": title,
                            "company_name": row.get("company", ""),
                            "location": row.get("job_location", ""),
                            "work_type": row.get("job_type", "Onsite"),
                            "seniority_level": row.get("job_level", "Mid senior"),
                            "posted_date": row.get("first_seen", None)
                        })
                        if len(job_postings_meta) >= MAX_JOBS:
                            break
                            
    print(f"[Ingestion] Filtered {len(job_postings_meta)} relevant tech job postings.")
    
    # Step 2: Read skills and identify the top canonical skills taxonomy
    print("[Ingestion] Step 2: Reading skill co-occurrences and building dynamic taxonomy...")
    postings_skills = {}
    skills_counter = Counter()
    
    with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
        with zip_ref.open("job_skills.csv") as f:
            wrapper = io.TextIOWrapper(f, encoding='utf-8', errors='ignore')
            reader = csv.reader(wrapper)
            next(reader)  # Skip header
            
            for row in reader:
                if not row or len(row) < 2:
                    continue
                link, skills_str = row[0], row[1]
                norm_link = normalize_link(link)
                if norm_link in job_links_set:
                    # Clean and split skills
                    skills = [s.strip() for s in skills_str.split(",") if s.strip()]
                    postings_skills[norm_link] = skills
                    skills_counter.update(skills)
                    
    # Select canonical skills
    top_skills = [
        skill for skill, count in skills_counter.most_common(TOP_SKILLS_LIMIT)
        if count >= MIN_SKILL_FREQUENCY
    ]
    print(f"[Ingestion] Discovered {len(top_skills)} canonical skills meeting frequency threshold.")
    
    # Step 3: Insert categories and skills into MySQL
    print("[Ingestion] Step 3: Inserting categories and skills into MySQL...")
    categories_set = set(categorize_skill(s) for s in top_skills)
    category_map = {}
    
    for cat_name in categories_set:
        cat_obj = session.query(SkillCategory).filter_by(name=cat_name).first()
        if not cat_obj:
            cat_obj = SkillCategory(name=cat_name, description=f"Canonical skills categorized under {cat_name}")
            session.add(cat_obj)
            session.flush()
        category_map[cat_name] = cat_obj.id
        
    session.commit()
    
    skills_map = {}
    for skill_name in top_skills:
        skill_obj = session.query(Skill).filter_by(canonical_name=skill_name).first()
        if not skill_obj:
            cat_name = categorize_skill(skill_name)
            cat_id = category_map[cat_name]
            # Simple alias: lowercase and lower-hyphenated forms
            aliases = list(set([skill_name.lower(), skill_name.lower().replace(" ", "-"), skill_name.lower().replace(" ", "_")]))
            skill_obj = Skill(
                canonical_name=skill_name,
                category_id=cat_id,
                aliases=aliases,
                first_seen_at=None
            )
            session.add(skill_obj)
            session.flush()
        skills_map[skill_name] = skill_obj.id
        
    session.commit()
    print("[Ingestion] Category and Skill taxonomy persisted.")
    
    # Step 4: Ingest raw job descriptions (job_summary.csv)
    print("[Ingestion] Step 4: Loading job descriptions and preparing job records...")
    postings_desc = {}
    with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
        with zip_ref.open("job_summary.csv") as f:
            wrapper = io.TextIOWrapper(f, encoding='utf-8', errors='ignore')
            reader = csv.reader(wrapper)
            next(reader)  # Skip header
            
            for row in reader:
                if not row or len(row) < 2:
                    continue
                link, desc = row[0], row[1]
                norm_link = normalize_link(link)
                if norm_link in job_links_set:
                    postings_desc[norm_link] = desc
                    
    # Step 5: Save Job Postings and Job-Skill Mappings
    print("[Ingestion] Step 5: Saving job postings and mappings in bulk...")
    
    # Clear out any previous mock jobs/skills to prevent constraint violations
    # (Since this is a clean start on real data)
    session.query(JobSkill).delete()
    session.query(JobPosting).delete()
    session.commit()
    
    # Prepare bulk insertions
    db_postings = []
    
    for i, meta in enumerate(job_postings_meta):
        desc_text = postings_desc.get(meta["job_link"], "")
        
        # Clean posted_date
        parsed_date = None
        if meta["posted_date"]:
            try:
                # Format: 2024-01-15
                parsed_date = datetime.strptime(meta["posted_date"].split()[0], "%Y-%m-%d").date()
            except:
                pass
                
        jp = JobPosting(
            external_id=meta["external_id"],
            title=meta["title"],
            company_name=meta["company_name"],
            description=desc_text,
            location=meta["location"],
            work_type=meta["work_type"],
            seniority_level=meta["seniority_level"],
            posted_date=parsed_date,
            source="linkedin"
        )
        session.add(jp)
        db_postings.append((meta["job_link"], jp))
        
        # Flush periodically to keep memory footprint low
        if i % 1000 == 0 and i > 0:
            session.flush()
            
    session.flush()
    
    # Map job-skills
    for job_link, jp in db_postings:
        job_id = jp.id
        if not job_id:
            continue
            
        skills = postings_skills.get(job_link, [])
        seen_skills = set()
        for s in skills:
            skill_id = skills_map.get(s)
            if skill_id and skill_id not in seen_skills:
                seen_skills.add(skill_id)
                js = JobSkill(
                    job_id=job_id,
                    skill_id=skill_id,
                    is_required=True,
                    confidence=1.0
                )
                session.add(js)
                
    session.commit()
    
    print(f"[Ingestion] SUCCESSFULLY ingested {len(job_postings_meta)} job postings and associated skills.")
    session.close()

if __name__ == "__main__":
    run_ingestion()
