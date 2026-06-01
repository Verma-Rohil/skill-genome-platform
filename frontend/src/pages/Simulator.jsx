import React, { useState, useEffect } from 'react';
import api from '../services/api';

function Simulator() {
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [shocks, setShocks] = useState({
    'Machine Learning': 0.8,
    'Python': 0.6
  });
  const [decayFactor, setDecayFactor] = useState(0.5);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch live search suggestions for adding new skills to shock list
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
        console.error('Error loading suggestions:', err);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Run baseline simulation on page load
  useEffect(() => {
    handleRunSimulation();
  }, []);

  const handleAddShockSkill = (skill) => {
    if (!(skill.canonical_name in shocks)) {
      setShocks({ ...shocks, [skill.canonical_name]: 0.5 });
    }
    setSearchQuery('');
    setSuggestions([]);
  };

  const handleRemoveShockSkill = (name) => {
    const updated = { ...shocks };
    delete updated[name];
    setShocks(updated);
  };

  const handleUpdateShockValue = (name, val) => {
    setShocks({ ...shocks, [name]: parseFloat(val) });
  };

  const handleRunSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.runSimulation(shocks, decayFactor);
      setResults(response);
    } catch (err) {
      console.error('Error running simulation:', err);
      setError('Simulation execution failed. Verify the backend and database connection.');
    } finally {
      setLoading(false);
    }
  };

  // Vulnerability helper styling
  const getVulnerabilityBadge = (score) => {
    if (score >= 0.4) return <span className="badge" style={{ background: 'rgba(239, 68, 68, 0.15)', borderColor: 'rgba(239, 68, 68, 0.4)', color: '#fca5a5', fontWeight: 'bold' }}>HIGH IMPACT</span>;
    if (score >= 0.15) return <span className="badge" style={{ background: 'rgba(245, 158, 11, 0.15)', borderColor: 'rgba(245, 158, 11, 0.4)', color: '#fde047', fontWeight: 'bold' }}>MODERATE</span>;
    return <span className="badge" style={{ background: 'rgba(16, 185, 129, 0.15)', borderColor: 'rgba(16, 185, 129, 0.4)', color: '#6ee7b7', fontWeight: 'bold' }}>STABLE</span>;
  };

  const getVulnerabilityColor = (score) => {
    if (score >= 0.4) return 'rgba(239, 68, 68, 0.04)';
    if (score >= 0.15) return 'rgba(245, 158, 11, 0.02)';
    return 'rgba(16, 185, 129, 0.01)';
  };

  return (
    <div>
      {/* Page Header */}
      <header className="page-header">
        <h2 className="page-title">Workforce Disruption Simulator</h2>
        <p className="page-subtitle">Model technology shocks, run 2-hop probability propagation, and trace archetype vulnerability cascade effects.</p>
      </header>

      {error && (
        <div className="card" style={{ borderLeft: '4px solid var(--error)', marginBottom: '2rem', background: 'rgba(239, 68, 68, 0.05)' }}>
          <p style={{ color: '#fecaca', fontSize: '0.95rem' }}>{error}</p>
        </div>
      )}

      <div className="grid-2" style={{ alignItems: 'start', marginBottom: '3rem' }}>
        
        {/* Simulation shock configurations panel */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <h3 style={{ fontFamily: 'var(--font-family-title)', fontSize: '1.25rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
            ⚙️ Shock Configuration
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Specify initial market shocks (demand surge/fall) on specific skills, then trigger a 2-hop decay shock propagation across the co-occurrence synergy network.
          </p>

          {/* Add Skill to Shock List */}
          <div style={{ position: 'relative' }}>
            <input
              type="text"
              className="form-input"
              placeholder="Search skill to add shock..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ fontSize: '0.85rem', padding: '0.65rem 1rem' }}
            />
            {suggestions.length > 0 && (
              <div className="suggestions-dropdown">
                {suggestions.map((s) => (
                  <div 
                    key={s.id} 
                    className="suggestion-item"
                    onClick={() => handleAddShockSkill(s)}
                  >
                    <strong>{s.canonical_name}</strong>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Shock sliders list */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', marginTop: '0.5rem' }}>
            {Object.keys(shocks).map((name) => (
              <div 
                key={name} 
                style={{ 
                  padding: '1rem', 
                  borderRadius: '10px', 
                  background: 'rgba(255, 255, 255, 0.02)', 
                  border: '1px solid var(--border-color)',
                  position: 'relative'
                }}
              >
                <button 
                  onClick={() => handleRemoveShockSkill(name)}
                  style={{ 
                    position: 'absolute', 
                    top: '0.5rem', 
                    right: '0.75rem', 
                    background: 'none', 
                    border: 'none', 
                    color: 'var(--text-muted)', 
                    cursor: 'pointer',
                    fontSize: '1rem'
                  }}
                >
                  ×
                </button>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', marginBottom: '0.5rem', paddingRight: '1rem' }}>
                  <strong style={{ color: '#e2e8f0' }}>{name}</strong>
                  <span style={{ color: 'var(--accent)', fontWeight: 'bold' }}>+{(shocks[name] * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0.0"
                  max="1.0"
                  step="0.05"
                  value={shocks[name]}
                  onChange={(e) => handleUpdateShockValue(name, e.target.value)}
                  style={{ width: '100%', accentColor: 'var(--primary)' }}
                />
              </div>
            ))}
            {Object.keys(shocks).length === 0 && (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontStyle: 'italic', textAlign: 'center', padding: '1rem' }}>
                No active shocks added. Search above to add initial shocks.
              </p>
            )}
          </div>

          {/* Decay Factor Slider */}
          <div style={{ marginTop: '0.5rem', borderTop: '1px solid var(--border-color)', paddingTop: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', marginBottom: '0.5rem' }}>
              <span className="form-label">2-Hop Decay Factor ($\gamma$)</span>
              <strong style={{ color: 'var(--text-primary)' }}>{decayFactor}</strong>
            </div>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.1"
              value={decayFactor}
              onChange={(e) => setDecayFactor(parseFloat(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--accent)' }}
            />
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.4rem' }}>
              Determines weight decay on the second transition hop in the synergy network.
            </p>
          </div>

          <button 
            className="btn btn-primary" 
            style={{ width: '100%', marginTop: '0.5rem' }}
            onClick={handleRunSimulation}
            disabled={loading}
          >
            {loading ? 'Simulating Propagation...' : '⚡ Run Disruption Simulation'}
          </button>
        </div>

        {/* Career archetype vulnerability results */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <h3 style={{ fontFamily: 'var(--font-family-title)', fontSize: '1.25rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
            📉 Archetype Vulnerability Rankings
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Career clusters ranked by disruption index (calculated as the normalized sum of required skills shocked).
          </p>

          {loading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '5rem 0' }}>
              <div className="loader-spinner"></div>
            </div>
          ) : results ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {results.archetype_vulnerabilities.map((v) => (
                <div 
                  key={v.archetype_id} 
                  style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center', 
                    padding: '1.15rem 1.25rem', 
                    borderRadius: '12px', 
                    background: getVulnerabilityColor(v.disruption_score),
                    border: '1px solid var(--border-color)',
                    transition: 'var(--transition-smooth)'
                  }}
                >
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <strong style={{ color: '#e2e8f0', fontSize: '0.95rem' }}>{v.archetype_name}</strong>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Size: {v.num_jobs} jobs in market</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ textAlign: 'right' }}>
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>Vulnerability Index</span>
                      <strong style={{ fontSize: '1.15rem', color: v.disruption_score > 0.4 ? 'var(--error)' : v.disruption_score > 0.15 ? 'var(--warning)' : 'var(--success)' }}>
                        {(v.disruption_score * 100).toFixed(0)}%
                      </strong>
                    </div>
                    {getVulnerabilityBadge(v.disruption_score)}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontStyle: 'italic', textAlign: 'center', padding: '2rem' }}>
              Run simulation to compute vulnerability.
            </p>
          )}
        </div>

      </div>

      {/* Propagated shocks breakdown list */}
      {results && results.skill_shocks.length > 0 && (
        <section className="card" style={{ marginBottom: '2rem' }}>
          <h3 style={{ fontFamily: 'var(--font-family-title)', fontSize: '1.25rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem', marginBottom: '1.25rem' }}>
            💥 Skill-Level Propagated Shocks Breakdown
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1.5rem' }}>
            List of skills affected by the cascade shock propagation, sorted by total propagated shock index.
          </p>

          <div className="table-container">
            <table className="table-styled">
              <thead>
                <tr>
                  <th>Skill Name</th>
                  <th>Initial Direct Shock</th>
                  <th>Propagated Network Shock</th>
                  <th>Cascade Change</th>
                </tr>
              </thead>
              <tbody>
                {results.skill_shocks.map((s) => {
                  const isDirect = s.initial_shock > 0;
                  const delta = s.propagated_shock - s.initial_shock;
                  
                  return (
                    <tr key={s.skill_id}>
                      <td style={{ fontWeight: '600', color: '#e2e8f0' }}>
                        {s.canonical_name}
                        {isDirect && <span className="badge badge-primary" style={{ fontSize: '0.65rem', padding: '0.1rem 0.35rem', marginLeft: '0.5rem' }}>DIRECT SOURCE</span>}
                      </td>
                      <td>{(s.initial_shock * 100).toFixed(0)}%</td>
                      <td style={{ fontWeight: 'bold', color: 'var(--accent)' }}>
                        {(s.propagated_shock * 100).toFixed(0)}%
                      </td>
                      <td style={{ color: delta > 0.05 ? '#fdba74' : 'var(--text-muted)' }}>
                        {delta > 0.001 ? `+${(delta * 100).toFixed(0)}% (Cascade)` : '—'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}

export default Simulator;
