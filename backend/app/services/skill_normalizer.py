"""
Skill Normalization Service
============================
Resolves raw, messy extracted skill strings into standardized canonical forms.

WHY NORMALIZATION IS CRITICAL:
- Job postings write the same skill in dozens of formats (e.g. "python3", "Py", "PYTHON").
- Duplicate entities dilute clustering centers, causing career archetypes to dissolve.
- Normalization ensures a single source of truth (canonical form) for all downstream models.

CASCADING ARCHITECTURE (Three-Tier Matcher):
- Tier 1: Direct/Alias Match — Fast exact database checks against names and registered aliases.
- Tier 2: Levenshtein Fuzzy Match — Accounts for spelling errors and minor spacing changes (threshold >= 0.85).
- Tier 3: Semantic Embeddings (S-BERT) — Translates terms using semantic meanings (threshold >= 0.90).
"""

import json
from typing import Optional, Dict, List, Tuple
import numpy as np
from sqlalchemy.orm import Session
from app.models.skill import Skill
from app.models.skill_embedding import SkillEmbedding

try:
    from rapidfuzz import process, fuzz
except ImportError:
    # Fallback to simple matching if rapidfuzz is not yet fully loaded
    process = None
    fuzz = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


class SkillNormalizer:
    def __init__(self, db: Session, similarity_threshold: float = 0.85, semantic_threshold: float = 0.90):
        self.db = db
        self.similarity_threshold = similarity_threshold
        self.semantic_threshold = semantic_threshold
        
        # In-memory caches to prevent repeated DB lookups
        self.canonical_skills: List[Skill] = []
        self.name_to_canonical: Dict[str, str] = {}  # Resolves lowercase term -> canonical name
        self.all_lookup_terms: List[str] = []       # List of all canonical names + aliases for fuzzy search
        self.term_to_canonical: Dict[str, str] = {}  # Map of lookup term -> canonical name
        
        # Load embedding model lazily
        self._embedding_model = None
        self.skill_embeddings_matrix: Optional[np.ndarray] = None
        self.embedding_skill_ids: List[int] = []
        self.id_to_canonical: Dict[int, str] = {}
        
        self.load_taxonomy()

    def load_taxonomy(self):
        """Loads canonical skills and aliases from database into local lookup caches."""
        try:
            self.canonical_skills = self.db.query(Skill).all()
            
            name_to_canonical = {}
            all_lookup_terms = []
            term_to_canonical = {}
            id_to_canonical = {}
            
            for skill in self.canonical_skills:
                canon_name = skill.canonical_name
                canon_name_lower = canon_name.lower()
                id_to_canonical[skill.id] = canon_name
                
                # Canonical name itself is a lookup term
                name_to_canonical[canon_name_lower] = canon_name
                term_to_canonical[canon_name_lower] = canon_name
                all_lookup_terms.append(canon_name_lower)
                
                # Process aliases
                if skill.aliases:
                    aliases = skill.aliases if isinstance(skill.aliases, list) else json.loads(skill.aliases)
                    for alias in aliases:
                        alias_lower = alias.lower()
                        term_to_canonical[alias_lower] = canon_name
                        all_lookup_terms.append(alias_lower)
                        
            self.name_to_canonical = name_to_canonical
            self.all_lookup_terms = all_lookup_terms
            self.term_to_canonical = term_to_canonical
            self.id_to_canonical = id_to_canonical
            
            print(f"[SkillNormalizer] Loaded {len(self.canonical_skills)} skills and {len(all_lookup_terms)} lookup terms.")
        except Exception as e:
            print(f"[SkillNormalizer] Error loading taxonomy from DB: {e}")

    def normalize(self, term: str) -> Optional[str]:
        """
        Runs the cascading normalization pipeline.
        Returns the canonical skill name if resolved, otherwise None.
        """
        if not term or not term.strip():
            return None
            
        term_clean = term.strip()
        term_lower = term_clean.lower()
        
        # --- TIER 1: Direct exact match on name or registered alias ---
        if term_lower in self.term_to_canonical:
            return self.term_to_canonical[term_lower]
            
        # --- TIER 2: Levenshtein Fuzzy String Matching (Edit Distance) ---
        if process and fuzz and self.all_lookup_terms:
            # Find the best match among all aliases and canonical names
            best_match = process.extractOne(term_lower, self.all_lookup_terms, scorer=fuzz.WRatio)
            if best_match:
                matched_term, score, _ = best_match
                # score is in [0, 100], convert to [0.0, 1.0]
                if (score / 100.0) >= self.similarity_threshold:
                    resolved = self.term_to_canonical[matched_term]
                    # Cache the result to save future CPU cycles
                    self.term_to_canonical[term_lower] = resolved
                    return resolved
                    
        # --- TIER 3: Semantic Cosine Proximity via Sentence-BERT ---
        resolved_semantic = self._normalize_semantic(term_clean)
        if resolved_semantic:
            # Cache the result
            self.term_to_canonical[term_lower] = resolved_semantic
            return resolved_semantic
            
        return None

    def _normalize_semantic(self, term: str) -> Optional[str]:
        """Performs semantic vector search against canonical skills."""
        # Load embedding model and database embeddings lazily on first semantic match call
        if not self._load_semantic_resources():
            return None
            
        try:
            # Generate embedding for the query term
            query_vector = self._embedding_model.encode(term, convert_to_numpy=True)
            # Normalize query vector for cosine similarity
            query_norm = np.linalg.norm(query_vector)
            if query_norm == 0:
                return None
            query_vector = query_vector / query_norm
            
            # Compute dot product (cosine similarity since vectors are normalized)
            similarities = np.dot(self.skill_embeddings_matrix, query_vector)
            best_idx = np.argmax(similarities)
            best_score = similarities[best_idx]
            
            if best_score >= self.semantic_threshold:
                matched_id = self.embedding_skill_ids[best_idx]
                return self.id_to_canonical.get(matched_id)
        except Exception as e:
            print(f"[SkillNormalizer] Semantic matching failed: {e}")
            
        return None

    def _load_semantic_resources(self) -> bool:
        """Loads S-BERT model and cached SQL embedding matrix into memory."""
        if self._embedding_model is not None and self.skill_embeddings_matrix is not None:
            return True
            
        if not SentenceTransformer:
            print("[SkillNormalizer] Warning: sentence-transformers library not installed. Skipping Tier 3.")
            return False
            
        try:
            print("[SkillNormalizer] Initializing S-BERT model and loading embedding matrix...")
            # Load S-BERT Model
            from app.config import get_settings
            settings = get_settings()
            self._embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
            
            # Load embeddings from database
            embeddings = self.db.query(SkillEmbedding).all()
            if not embeddings:
                print("[SkillNormalizer] Warning: No skill embeddings cached in database. Cannot run Tier 3.")
                return False
                
            embedding_vectors = []
            embedding_skill_ids = []
            
            for emb in embeddings:
                # Deserialize numpy array from binary BLOB
                vector = np.frombuffer(emb.vector, dtype=np.float32)
                # Normalize vector to allow simple dot product cosine similarity
                norm = np.linalg.norm(vector)
                if norm > 0:
                    vector = vector / norm
                embedding_vectors.append(vector)
                embedding_skill_ids.append(emb.skill_id)
                
            self.skill_embeddings_matrix = np.vstack(embedding_vectors)
            self.embedding_skill_ids = embedding_skill_ids
            return True
        except Exception as e:
            print(f"[SkillNormalizer] Error loading semantic resources: {e}")
            return False
