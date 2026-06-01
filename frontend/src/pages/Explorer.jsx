import React, { useState, useEffect, useRef } from 'react';
import api from '../services/api';
import { Network } from 'vis-network/standalone';

function Explorer({ userSkills, addSkill, removeSkill }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [selectedSkill, setSelectedSkill] = useState(null);
  const [similarSkills, setSimilarSkills] = useState([]);
  const [synergySkills, setSynergySkills] = useState([]);
  const [extractText, setExtractText] = useState('');
  const [extractedSkills, setExtractedSkills] = useState([]);
  const [loading, setLoading] = useState(false);
  const [extractLoading, setExtractLoading] = useState(false);
  
  const networkContainerRef = useRef(null);
  const networkInstanceRef = useRef(null);

  // Load live suggestions as user types
  useEffect(() => {
    if (searchQuery.trim().length < 2) {
      setSuggestions([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const results = await api.fetchSkills(searchQuery, 0, 10);
        setSuggestions(results);
      } catch (err) {
        console.error('Error fetching search suggestions:', err);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Load detailed analysis for selected skill (similar + synergies)
  const handleSelectSkill = async (skill) => {
    setSelectedSkill(skill);
    setSearchQuery('');
    setSuggestions([]);
    setLoading(true);
    try {
      const similar = await api.fetchSimilarSkills(skill.id, 8);
      const synergy = await api.fetchSynergySkills(skill.id);
      setSimilarSkills(similar);
      // Sort synergy by lift descending and take top 8
      setSynergySkills(synergy.slice(0, 8));
    } catch (err) {
      console.error('Error loading skill detail:', err);
    } finally {
      setLoading(false);
    }
  };

  // Run NLP Skill Extractor
  const handleExtract = async () => {
    if (!extractText.trim()) return;
    setExtractLoading(true);
    try {
      const results = await api.extractSkills(extractText);
      setExtractedSkills(results.extracted_skills);
    } catch (err) {
      console.error('Error extracting skills:', err);
    } finally {
      setExtractLoading(false);
    }
  };

  // Render vis-network graph for selected skill and its synergies
  useEffect(() => {
    if (!selectedSkill || !networkContainerRef.current) return;

    // Build graph nodes
    const nodes = [
      { 
        id: selectedSkill.id, 
        label: selectedSkill.canonical_name, 
        color: { background: '#a855f7', border: '#c084fc', highlight: { background: '#a855f7', border: '#d8b4fe' } },
        shape: 'dot',
        size: 30,
        font: { color: '#ffffff', face: 'Outfit', size: 16, bold: true }
      }
    ];

    const edges = [];

    // Add top 6 synergy neighbors
    synergySkills.slice(0, 6).forEach((syn) => {
      nodes.push({
        id: syn.skill_id,
        label: syn.canonical_name,
        color: { background: '#0e7490', border: '#06b6d4', highlight: { background: '#0891b2', border: '#22d3ee' } },
        shape: 'dot',
        size: 18 + Math.min(12, syn.confidence * 15),
        font: { color: '#94a3b8', face: 'Inter', size: 12 }
      });

      edges.push({
        from: selectedSkill.id,
        to: syn.skill_id,
        value: syn.lift,
        title: `P(${syn.canonical_name} | ${selectedSkill.canonical_name}) = ${(syn.confidence * 100).toFixed(1)}%`,
        color: { color: 'rgba(6, 182, 212, 0.4)', highlight: 'rgba(6, 182, 212, 0.8)' },
        width: 1 + syn.confidence * 4
      });
    });

    const data = { nodes, edges };
    const options = {
      physics: {
        forceAtlas2Based: {
          gravitationalConstant: -26,
          centralGravity: 0.005,
          springLength: 120,
          springConstant: 0.18,
        },
        maxVelocity: 146,
        solver: 'forceAtlas2Based',
        timestep: 0.35,
        stabilization: { iterations: 150 },
      },
      interaction: {
        hover: true,
        tooltipDelay: 200,
        zoomView: true,
        dragView: true,
      }
    };

    // Clean up previous instance
    if (networkInstanceRef.current) {
      networkInstanceRef.current.destroy();
    }

    networkInstanceRef.current = new Network(networkContainerRef.current, data, options);

    return () => {
      if (networkInstanceRef.current) {
        networkInstanceRef.current.destroy();
        networkInstanceRef.current = null;
      }
    };
  }, [selectedSkill, synergySkills]);

  return (
    <div>
      {/* Page Header */}
      <header className="page-header">
        <h2 className="page-title">Skill Explorer & Taxonomy</h2>
        <p className="page-subtitle">Search canonical skills, query semantic peer similarity, and map co-occurrence networks.</p>
      </header>

      <div className="grid-2" style={{ alignItems: 'start', marginBottom: '3rem' }}>
        
        {/* Left Column: Search & Profile */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          
          {/* Skill Search Box */}
          <div className="card" style={{ position: 'relative' }}>
            <h3 style={{ fontFamily: 'var(--font-family-title)', fontSize: '1.15rem', marginBottom: '1rem' }}>
              🔍 Search Skill Genome
            </h3>
            <div style={{ position: 'relative' }}>
              <input
                type="text"
                className="form-input"
                placeholder="Type a skill (e.g. Python, React, Kubernetes)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              {suggestions.length > 0 && (
                <div className="suggestions-dropdown">
                  {suggestions.map((s) => (
                    <div 
                      key={s.id} 
                      className="suggestion-item"
                      onClick={() => handleSelectSkill(s)}
                    >
                      <strong>{s.canonical_name}</strong>
                      {s.aliases && s.aliases.length > 0 && (
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginLeft: '0.5rem' }}>
                          (aka {s.aliases.slice(0, 2).join(', ')})
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.75rem' }}>
              Type at least 2 characters to trigger live database lookup.
            </p>
          </div>

          {/* User Profile Skills Section */}
          <div className="card">
            <h3 style={{ fontFamily: 'var(--font-family-title)', fontSize: '1.15rem', marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>👤 Your Core Profile Skills</span>
              <span className="badge badge-accent">{userSkills.length} Skills</span>
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
              These skills will automatically carry over to run career gap analyzer and recommenders.
            </p>
            <div className="badge-container">
              {userSkills.map((sk) => (
                <span key={sk} className="badge badge-primary">
                  {sk}
                  <button 
                    onClick={() => removeSkill(sk)} 
                    style={{ background: 'none', border: 'none', color: '#c084fc', marginLeft: '0.4rem', cursor: 'pointer', fontWeight: 'bold' }}
                  >
                    ×
                  </button>
                </span>
              ))}
              {userSkills.length === 0 && (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontStyle: 'italic' }}>
                  No skills in your profile. Extract or search to add some!
                </p>
              )}
            </div>

            {/* Quick Manual Add Input */}
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1.5rem' }}>
              <input 
                id="manual-skill-input"
                type="text" 
                className="form-input" 
                placeholder="Add skill manually..." 
                style={{ padding: '0.5rem 0.75rem', fontSize: '0.85rem' }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    addSkill(e.target.value);
                    e.target.value = '';
                  }
                }}
              />
              <button 
                className="btn btn-secondary" 
                style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}
                onClick={() => {
                  const input = document.getElementById('manual-skill-input');
                  if (input && input.value) {
                    addSkill(input.value);
                    input.value = '';
                  }
                }}
              >
                Add
              </button>
            </div>
          </div>

        </div>

        {/* Right Column: NLP Extractor */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <h3 style={{ fontFamily: 'var(--font-family-title)', fontSize: '1.15rem' }}>
            🔮 NLP Skill Extractor (Trie Matcher)
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Paste a job posting description or resume below to parse out matching canonical technology terms in linear time $O(N)$ with greedy lookahead.
          </p>
          
          <textarea
            className="form-input textarea-input"
            placeholder="Paste raw text here... e.g. 'We are hiring a Lead Python engineer who knows React, Git, and Docker. Experience with PyTorch is a plus.'"
            value={extractText}
            onChange={(e) => setExtractText(e.target.value)}
          ></textarea>

          <button 
            className="btn btn-primary"
            onClick={handleExtract}
            disabled={extractLoading || !extractText.trim()}
          >
            {extractLoading ? 'Extracting...' : '🧬 Extract Skills'}
          </button>

          {extractedSkills.length > 0 && (
            <div style={{ marginTop: '1rem', borderTop: '1px solid var(--border-color)', paddingTop: '1.25rem' }}>
              <h4 style={{ fontFamily: 'var(--font-family-title)', fontSize: '0.95rem', color: '#e2e8f0', marginBottom: '0.75rem' }}>
                Extracted Skills:
              </h4>
              <div className="badge-container" style={{ marginBottom: '1.25rem' }}>
                {extractedSkills.map((sk) => {
                  const alreadyHave = userSkills.includes(sk);
                  return (
                    <span 
                      key={sk} 
                      className={`badge badge-interactive ${alreadyHave ? 'badge-primary' : 'badge-accent'}`}
                      onClick={() => addSkill(sk)}
                      title={alreadyHave ? 'Already in profile' : 'Click to add to profile'}
                    >
                      {sk} {alreadyHave ? '✓' : '+'}
                    </span>
                  );
                })}
              </div>
              <button 
                className="btn btn-secondary" 
                style={{ width: '100%', fontSize: '0.85rem', padding: '0.6rem' }}
                onClick={() => {
                  extractedSkills.forEach(s => addSkill(s));
                }}
              >
                Add All Unregistered Skills to Profile
              </button>
            </div>
          )}
        </div>

      </div>

      {/* Selected Skill Analysis Section */}
      {selectedSkill && (
        <section className="card" style={{ marginBottom: '2rem' }}>
          <div style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '1.5rem', marginBottom: '1.5rem' }}>
            <span className="badge badge-primary" style={{ marginBottom: '0.5rem' }}>Selected Entity</span>
            <h3 style={{ fontFamily: 'var(--font-family-title)', fontSize: '1.75rem', fontWeight: '800', color: '#f8fafc' }}>
              {selectedSkill.canonical_name}
            </h3>
            {selectedSkill.aliases && selectedSkill.aliases.length > 0 && (
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.25rem' }}>
                Registered Aliases: <span style={{ color: 'var(--accent)', fontStyle: 'italic' }}>{selectedSkill.aliases.join(', ')}</span>
              </p>
            )}
          </div>

          {loading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem 0' }}>
              <div className="loader-spinner"></div>
            </div>
          ) : (
            <div className="grid-2">
              
              {/* Similar Skills & Synergies List */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                
                {/* S-BERT Cosine Similarity peers */}
                <div>
                  <h4 style={{ fontFamily: 'var(--font-family-title)', fontSize: '1.05rem', color: '#e2e8f0', marginBottom: '0.75rem' }}>
                    🧬 Semantic Similarity Peers (S-BERT)
                  </h4>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '1rem' }}>
                    Nearest neighbors in the S-BERT 384-dimensional space (cosine similarity). Shows equivalent/substitute tools.
                  </p>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    {similarSkills.map((sim) => (
                      <span 
                        key={sim.skill_id} 
                        className="badge badge-interactive"
                        onClick={() => handleSelectSkill({ id: sim.skill_id, canonical_name: sim.canonical_name })}
                        title={`Cosine Similarity: ${(sim.similarity_score * 100).toFixed(1)}%`}
                      >
                        {sim.canonical_name}
                        <span style={{ color: 'var(--accent)', fontSize: '0.7rem', marginLeft: '0.25rem' }}>
                          {(sim.similarity_score * 100).toFixed(0)}%
                        </span>
                      </span>
                    ))}
                    {similarSkills.length === 0 && (
                      <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontStyle: 'italic' }}>No similar skills found.</p>
                    )}
                  </div>
                </div>

                {/* Co-occurrence market synergy */}
                <div>
                  <h4 style={{ fontFamily: 'var(--font-family-title)', fontSize: '1.05rem', color: '#e2e8f0', marginBottom: '0.75rem' }}>
                    🤝 Market Synergy (Co-occurrence)
                  </h4>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '1rem' }}>
                    Highly correlated skills in postings. Ordered by Lift (measure of synergy strength relative to random chance).
                  </p>
                  
                  <div className="table-container">
                    <table className="table-styled">
                      <thead>
                        <tr>
                          <th>Skill</th>
                          <th>Co-occurrences</th>
                          <th>P(B | Selected)</th>
                          <th>Lift</th>
                        </tr>
                      </thead>
                      <tbody>
                        {synergySkills.slice(0, 5).map((syn) => (
                          <tr 
                            key={syn.skill_id}
                            style={{ cursor: 'pointer' }}
                            onClick={() => handleSelectSkill({ id: syn.skill_id, canonical_name: syn.canonical_name })}
                          >
                            <td style={{ fontWeight: '600', color: '#e2e8f0' }}>{syn.canonical_name}</td>
                            <td>{syn.cooccurrence_count} jobs</td>
                            <td>{(syn.confidence * 100).toFixed(1)}%</td>
                            <td style={{ color: 'var(--accent)', fontWeight: 'bold' }}>{syn.lift.toFixed(2)}x</td>
                          </tr>
                        ))}
                        {synergySkills.length === 0 && (
                          <tr>
                            <td colSpan="4" style={{ textAlign: 'center', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                              No co-occurrence data found for this skill.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>

              </div>

              {/* Vis-network Graph Panel */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <h4 style={{ fontFamily: 'var(--font-family-title)', fontSize: '1.05rem', color: '#e2e8f0' }}>
                  🕸️ Local Synergy Network Graph
                </h4>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                  Interactive visualization of the node and its co-occurring neighbors. Node sizes reflect conditional probabilities. Zoom, pan, or drag elements.
                </p>
                <div 
                  ref={networkContainerRef}
                  style={{ 
                    height: '350px', 
                    borderRadius: '12px', 
                    border: '1px solid var(--border-color)', 
                    background: 'rgba(10, 15, 25, 0.6)', 
                    marginTop: '0.5rem' 
                  }}
                ></div>
              </div>

            </div>
          )}
        </section>
      )}
    </div>
  );
}

export default Explorer;
