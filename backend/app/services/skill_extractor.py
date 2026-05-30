"""
Skill Extractor Service
========================
Extracts skills from raw job description text using a high-performance Trie-based dictionary matcher.

WHY TRIE-BASED MATCHING (instead of regex or nested loops):
- Nested loops: checking 800 skills × 1000 characters is O(S * N) — extremely slow.
- Naive regex: compiling 1000+ regex patterns scales poorly and suffers from catastrophic backtracking.
- Trie Matcher (similar to FlashText): operates in O(N) where N is the number of words in the text.
  It is independent of vocabulary size (S), making it production-grade and highly scalable.

WHY MULTI-WORD MATCHING:
- Skills like "Machine Learning" or "Natural Language Processing" span multiple words.
- A character-level or naive split-word matcher misses these or extracts partial words ("Learning").
- Our word-level Trie traverses multi-word sequences and resolves them to their canonical name.
"""

import re
import csv
import json
import os
from typing import List, Set, Dict, Tuple
from sqlalchemy.orm import Session
from app.models.skill import Skill

class TrieNode:
    def __init__(self):
        self.children: Dict[str, 'TrieNode'] = {}
        self.canonical_name: str = None  # Populated only at leaf nodes

class TrieMatcher:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, alias: str, canonical_name: str):
        """Inserts an alias into the Trie."""
        words = self._tokenize(alias)
        if not words:
            return
            
        current = self.root
        for word in words:
            if word not in current.children:
                current.children[word] = TrieNode()
            current = current.children[word]
        current.canonical_name = canonical_name

    def match(self, text: str) -> Set[str]:
        """
        Extracts all matching skills from the text in O(N) time.
        Returns a set of canonical skill names.
        """
        words = self._tokenize(text)
        extracted: Set[str] = set()
        n = len(words)
        
        i = 0
        while i < n:
            current = self.root
            match_canonical = None
            match_length = 0
            
            # Lookahead to find the longest matching phrase starting at index i
            j = i
            while j < n:
                word = words[j]
                if word in current.children:
                    current = current.children[word]
                    j += 1
                    if current.canonical_name:
                        match_canonical = current.canonical_name
                        match_length = j - i
                else:
                    break
            
            if match_canonical:
                extracted.add(match_canonical)
                i += match_length  # Consume matched words (prevents overlapping sub-matches)
            else:
                i += 1  # Move to next word
                
        return extracted

    def _tokenize(self, text: str) -> List[str]:
        """Cleans and tokenizes text into lowercase alphanumeric words."""
        # Convert to lowercase and replace punctuation with spaces
        text = text.lower()
        # Keep letters, numbers, and basic symbols like ++, .js, .net, - (e.g. c++, next.js, .net, next-gen)
        # We replace other punctuation to avoid joining words
        cleaned = re.sub(r"[^\w\+\#\.\-]", " ", text)
        words = cleaned.split()
        return [w.strip(".-") for w in words if w.strip(".-")]


class SkillExtractor:
    def __init__(self, db: Session = None, taxonomy_path: str = None):
        """
        Initializes the SkillExtractor by building the Trie matcher.
        Loads from database if session is provided, otherwise falls back to CSV path.
        """
        self.matcher = TrieMatcher()
        self.db = db
        
        # Determine fallback taxonomy path
        if not taxonomy_path:
            # Try to resolve relative to this file
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            taxonomy_path = os.path.join(base_dir, "data", "processed", "skills_taxonomy.csv")
            
        self.taxonomy_path = taxonomy_path
        self._load_skills()

    def _load_skills(self):
        """Loads canonical skills and aliases into the Trie."""
        loaded = False
        
        # Strategy 1: Load from Database (Production)
        if self.db:
            try:
                skills = self.db.query(Skill).all()
                if skills:
                    for skill in skills:
                        # Insert canonical name itself
                        self.matcher.insert(skill.canonical_name, skill.canonical_name)
                        # Insert aliases
                        if skill.aliases:
                            aliases = skill.aliases if isinstance(skill.aliases, list) else json.loads(skill.aliases)
                            for alias in aliases:
                                self.matcher.insert(alias, skill.canonical_name)
                    print(f"[SkillExtractor] Loaded {len(skills)} skills from Database.")
                    loaded = True
            except Exception as e:
                print(f"[SkillExtractor] Failed to load from Database: {e}. Falling back to CSV.")
        
        # Strategy 2: Load from CSV (Development/Testing fallback)
        if not loaded:
            if os.path.exists(self.taxonomy_path):
                try:
                    count = 0
                    with open(self.taxonomy_path, mode="r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            canonical_name = row["canonical_name"]
                            aliases_str = row["aliases"]
                            
                            # Insert canonical name
                            self.matcher.insert(canonical_name, canonical_name)
                            count += 1
                            
                            # Insert aliases
                            if aliases_str:
                                try:
                                    aliases = json.loads(aliases_str)
                                    for alias in aliases:
                                        self.matcher.insert(alias, canonical_name)
                                except json.JSONDecodeError:
                                    # Fallback simple split if JSON is malformed
                                    aliases = [a.strip() for a in aliases_str.split(",") if a.strip()]
                                    for alias in aliases:
                                        self.matcher.insert(alias, canonical_name)
                    print(f"[SkillExtractor] Loaded {count} skills from CSV: {self.taxonomy_path}")
                except Exception as e:
                    print(f"[SkillExtractor] Error reading CSV: {e}")
            else:
                print(f"[SkillExtractor] Warning: Taxonomy CSV not found at {self.taxonomy_path}")

    def extract(self, text: str) -> List[str]:
        """
        Extracts and normalizes skills found in the raw text.
        Returns a sorted list of canonical skill names.
        """
        if not text:
            return []
            
        extracted_set = self.matcher.match(text)
        return sorted(list(extracted_set))
