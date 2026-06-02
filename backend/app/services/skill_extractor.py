import re
import csv
import json
import os
from typing import List, Set, Dict
from sqlalchemy.orm import Session
from app.models.skill import Skill


class PhraseMatcher:
    def __init__(self):
        # We just store a simple flat dictionary of: normalized_phrase -> canonical_name
        self.lookup: Dict[str, str] = {}

    def insert(self, alias: str, canonical_name: str):
        """Inserts an alias into the matcher."""
        words = self._tokenize(alias)
        if words:
            phrase = " ".join(words)
            self.lookup[phrase] = canonical_name

    def match(self, text: str) -> Set[str]:
        """Extracts all matching skills from the text."""
        words = self._tokenize(text)
        extracted: Set[str] = set()
        n = len(words)
        
        i = 0
        while i < n:
            match_canonical = None
            match_length = 0
            
            # Check phrases starting at index i of lengths from max down to 1
            # To handle greedy longest match (e.g. "machine learning" over "learning")
            for length in range(n - i, 0, -1):
                phrase = " ".join(words[i:i+length])
                if phrase in self.lookup:
                    match_canonical = self.lookup[phrase]
                    match_length = length
                    break
            
            if match_canonical:
                extracted.add(match_canonical)
                i += match_length
            else:
                i += 1
                
        return extracted

    def _tokenize(self, text: str) -> List[str]:
        """Cleans and tokenizes text into lowercase alphanumeric words."""
        text = text.lower()
        cleaned = re.sub(r"[^\w\+\#\.\-]", " ", text)
        words = cleaned.split()
        return [w.strip(".-") for w in words if w.strip(".-")]


class SkillExtractor:
    def __init__(self, db: Session = None, taxonomy_path: str = None):
        """Initializes the SkillExtractor by building the matcher."""
        self.matcher = PhraseMatcher()
        self.db = db
        
        if not taxonomy_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            taxonomy_path = os.path.join(base_dir, "data", "processed", "skills_taxonomy.csv")
            
        self.taxonomy_path = taxonomy_path
        self._load_skills()

    def _load_skills(self):
        """Loads canonical skills and aliases into the matcher."""
        loaded = False
        
        if self.db:
            try:
                skills = self.db.query(Skill).all()
                if skills:
                    for skill in skills:
                        self.matcher.insert(skill.canonical_name, skill.canonical_name)
                        if skill.aliases:
                            aliases = skill.aliases if isinstance(skill.aliases, list) else json.loads(skill.aliases)
                            for alias in aliases:
                                self.matcher.insert(alias, skill.canonical_name)
                    print(f"Loaded {len(skills)} skills from database.")
                    loaded = True
            except Exception as e:
                print(f"Failed to load from database: {e}. Falling back to CSV.")
        
        if not loaded:
            if os.path.exists(self.taxonomy_path):
                try:
                    count = 0
                    with open(self.taxonomy_path, mode="r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            canonical_name = row["canonical_name"]
                            aliases_str = row["aliases"]
                            
                            self.matcher.insert(canonical_name, canonical_name)
                            count += 1
                            
                            if aliases_str:
                                try:
                                    aliases = json.loads(aliases_str)
                                    for alias in aliases:
                                        self.matcher.insert(alias, canonical_name)
                                except json.JSONDecodeError:
                                    aliases = [a.strip() for a in aliases_str.split(",") if a.strip()]
                                    for alias in aliases:
                                        self.matcher.insert(alias, canonical_name)
                    print(f"Loaded {count} skills from CSV: {self.taxonomy_path}")
                except Exception as e:
                    print(f"Error reading CSV: {e}")
            else:
                print(f"Warning: Taxonomy CSV not found at {self.taxonomy_path}")

    def extract(self, text: str) -> List[str]:
        """Extracts and normalizes skills found in the raw text."""
        if not text:
            return []
            
        extracted_set = self.matcher.match(text)
        return sorted(list(extracted_set))
