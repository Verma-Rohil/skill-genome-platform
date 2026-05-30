"""
Unit Tests — Skill Extractor Service
=====================================
Tests the TrieMatcher and SkillExtractor for exact string and alias matching,
multi-word lookahead, punctuation resilience, and case insensitivity.
"""

import pytest
import os
import tempfile
import json
import csv
from app.services.skill_extractor import TrieMatcher, SkillExtractor

@pytest.fixture
def temp_taxonomy():
    """Creates a temporary taxonomy CSV file for test isolation."""
    skills_data = [
        {"canonical_name": "Python", "category": "Languages", "aliases": ["python", "py"]},
        {"canonical_name": "Machine Learning", "category": "ML", "aliases": ["machine learning", "ml", "statistical learning"]},
        {"canonical_name": "Next.js", "category": "Frontend", "aliases": ["nextjs", "next.js"]},
        {"canonical_name": "C++", "category": "Languages", "aliases": ["cpp", "c++"]},
        {"canonical_name": "Natural Language Processing", "category": "ML", "aliases": ["nlp", "text mining"]}
    ]
    
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["canonical_name", "category", "aliases"])
        for s in skills_data:
            writer.writerow([s["canonical_name"], s["category"], json.dumps(s["aliases"])])
        temp_path = f.name
        
    yield temp_path
    
    # Cleanup after test
    if os.path.exists(temp_path):
        os.remove(temp_path)


def test_trie_matcher_basic():
    """Tests basic word insertions and matching in TrieMatcher."""
    matcher = TrieMatcher()
    matcher.insert("python", "Python")
    matcher.insert("py", "Python")
    matcher.insert("machine learning", "Machine Learning")
    matcher.insert("ml", "Machine Learning")
    
    # Text matching
    assert matcher.match("I code in Python and love ML.") == {"Python", "Machine Learning"}
    assert matcher.match("Python is great, py is short.") == {"Python"}  # "py" gets resolved to "Python"
    assert matcher.match("No skills in this text.") == set()


def test_trie_matcher_multi_word():
    """Tests that TrieMatcher performs longest-match lookahead correctly."""
    matcher = TrieMatcher()
    matcher.insert("learning", "Learning")
    matcher.insert("machine learning", "Machine Learning")
    
    # "machine learning" should match as one skill, not split or match "learning" separately
    assert matcher.match("I love machine learning.") == {"Machine Learning"}
    
    # If separated, it matches "learning" alone
    assert matcher.match("Active learning is a technique.") == {"Learning"}


def test_trie_matcher_punctuation_resilience():
    """Tests that TrieMatcher is resilient to case and standard punctuation."""
    matcher = TrieMatcher()
    matcher.insert("next.js", "Next.js")
    matcher.insert("c++", "C++")
    matcher.insert("react", "React")
    
    # Case insensitivity
    assert matcher.match("I write REACT.") == {"React"}
    
    # Punctuation isolation
    assert matcher.match("My favorite is next.js, followed by c++!") == {"Next.js", "C++"}
    assert matcher.match("Using next-js (not next.js)") == {"Next.js"}  # next-js tokenizes to next js or matches if normalized


def test_skill_extractor_csv_load(temp_taxonomy):
    """Tests that SkillExtractor loads correctly from a CSV file."""
    extractor = SkillExtractor(taxonomy_path=temp_taxonomy)
    
    text = "We need someone skilled in py and Next.js, with solid NLP knowledge."
    skills = extractor.extract(text)
    
    # Expected: ["Machine Learning" isn't in text, "C++" isn't, but Python (from 'py'), Next.js, and Natural Language Processing (from 'nlp') are]
    assert "Python" in skills
    assert "Next.js" in skills
    assert "Natural Language Processing" in skills
    assert len(skills) == 3
    
    # Result should be sorted alphabetically
    assert skills == sorted(skills)


def test_skill_extractor_empty_edge_cases(temp_taxonomy):
    """Tests that SkillExtractor handles edge cases (empty strings, None) gracefully."""
    extractor = SkillExtractor(taxonomy_path=temp_taxonomy)
    assert extractor.extract("") == []
    assert extractor.extract(None) == []
