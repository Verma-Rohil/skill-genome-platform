import React, { useState, useEffect } from 'react';
import api from '../services/api';

function CareerIntel({ userSkills, addSkill }) {
  const [archetypes, setArchetypes] = useState([]);
  const [selectedArchId, setSelectedArchId] = useState('');
  const [gapAnalysis, setGapAnalysis] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [recLoading, setRecLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load archetypes on boot
  useEffect(() => {
    async function loadArchetypes() {
      try {
        const data = await api.fetchArchetypes();
        setArchetypes(data);
        if (data.length > 0) {
          setSelectedArchId(data[0].id.toString());
        }
      } catch (err) {
        console.error('Error fetching archetypes:', err);
      }
    }
    loadArchetypes();
  }, []);

  // Recalculate gap and recommendations when selected archetype or user skills change!
  useEffect(() => {
    if (!selectedArchId) return;
    
    async function runIntelligence() {
      setLoading(true);
      setError(null);
      try {
        // Run gap analysis
        const gapReport = await api.analyzeGap(userSkills, selectedArchId);
        setGapAnalysis(gapReport);
        
        // Fetch recommendations
        setRecLoading(true);
        const recs = await api.fetchRecommendations(userSkills, selectedArchId, 5);
        setRecommendations(recs.recommendations);
      } catch (err) {
        console.error('Error running career intelligence:', err);
        setError('Failed to calculate gap analysis. Make sure the database is populated and backend is online.');
      } finally {
        setLoading(false);
        setRecLoading(false);
      }
    }

    runIntelligence();
  }, [selectedArchId, userSkills]);

  // Render SVG Radar Chart
  const renderRadarChart = () => {
    if (!gapAnalysis) return null;

    // Combine matching and missing skills to get the top skills of the archetype
    const allSkills = [
      ...gapAnalysis.matching_skills.map(s => ({
        name: s.canonical_name,
        importance: s.importance_score,
        userValue: s.importance_score
      })),
      ...gapAnalysis.missing_skills.map(s => ({
        name: s.canonical_name,
        importance: s.importance_score,
        userValue: s.substitute_credit // partial credit
      }))
    ];

    // Sort by importance descending and pick top 6 skills
    allSkills.sort((a, b) => b.importance - a.importance);
    const topSkills = allSkills.slice(0, 6);

    if (topSkills.length < 3) {
      return (
        <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
          Not enough archetype skill points to generate radar model.
        </div>
      );
    }

    // Geometry parameters
    const cx = 160;
    const cy = 160;
    const rMax = 110;
    const n = topSkills.length;

    // Grid circles
    const gridRadii = [0.25, 0.5, 0.75, 1.0];
    const gridPolygons = gridRadii.map((fraction) => {
      const radius = rMax * fraction;
      const points = [];
      for (let i = 0; i < n; i++) {
        const angle = (i * 2 * Math.PI) / n - Math.PI / 2;
        const x = cx + radius * Math.cos(angle);
        const y = cy + radius * Math.sin(angle);
        points.push(`${x.toFixed(1)},${y.toFixed(1)}`);
      }
      return points.join(' ');
    });

    // Draw Target Archetype Centroid Shape
    const targetPoints = [];
    // Draw User Profile Shape
    const userPoints = [];
    // Draw Skill axis lines & text placements
    const axes = [];

    topSkills.forEach((skill, i) => {
      const angle = (i * 2 * Math.PI) / n - Math.PI / 2;
      
      // Target coordinate (normalize relative to max importance in the set to expand polygon)
      const maxImportance = Math.max(...topSkills.map(s => s.importance));
      const targetFraction = skill.importance / (maxImportance > 0 ? maxImportance : 1.0);
      const targetRadius = rMax * targetFraction;
      const tx = cx + targetRadius * Math.cos(angle);
      const ty = cy + targetRadius * Math.sin(angle);
      targetPoints.push(`${tx.toFixed(1)},${ty.toFixed(1)}`);

      // User coordinate
      const userFraction = skill.userValue / (maxImportance > 0 ? maxImportance : 1.0);
      const userRadius = rMax * userFraction;
      const ux = cx + userRadius * Math.cos(angle);
      const uy = cy + userRadius * Math.sin(angle);
      userPoints.push(`${ux.toFixed(1)},${uy.toFixed(1)}`);

      // Axis lines
      const ax = cx + rMax * Math.cos(angle);
      const ay = cy + rMax * Math.sin(angle);
      
      // Text coordinates (push text slightly outward)
      const textDist = rMax + 20;
      const lx = cx + textDist * Math.cos(angle);
      const ly = cy + textDist * Math.sin(angle);
      
      // Text alignment helper
      let anchor = 'middle';
      if (Math.cos(angle) > 0.1) anchor = 'start';
      if (Math.cos(angle) < -0.1) anchor = 'end';

      axes.push({
        ax, ay, lx, ly, anchor,
        name: skill.name
      });
    });

    return (
      <svg width="100%" height="320" viewBox="0 0 320 320" style={{ display: 'block', margin: '0 auto' }}>
        <defs>
          <radialGradient id="userGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.4" />
            <stop offset="100%" stopColor="var(--accent)" stopOpacity="0.0" />
          </radialGradient>
        </defs>
        
        {/* Concentric grid lines */}
        {gridPolygons.map((poly, idx) => (
          <polygon 
            key={idx} 
            points={poly} 
            fill="none" 
            stroke="rgba(255, 255, 255, 0.05)" 
            strokeWidth="1" 
          />
        ))}

        {/* Axis spoke lines */}
        {axes.map((axis, idx) => (
          <line 
            key={idx} 
            x1={cx} 
            y1={cy} 
            x2={axis.ax} 
            y2={axis.ay} 
            stroke="rgba(255, 255, 255, 0.06)" 
            strokeWidth="1" 
          />
        ))}

        {/* Target Archetype Centroid Polygon (Purple dashed border) */}
        <polygon
          points={targetPoints.join(' ')}
          fill="rgba(168, 85, 247, 0.05)"
          stroke="var(--primary)"
          strokeWidth="1.5"
          strokeDasharray="4 3"
        />

        {/* User Current Skills Polygon (Teal filled & glowing) */}
        <polygon
          points={userPoints.join(' ')}
          fill="rgba(6, 182, 212, 0.18)"
          stroke="var(--accent)"
          strokeWidth="2.5"
        />

        {/* Data points overlay */}
        {topSkills.map((skill, i) => {
          const angle = (i * 2 * Math.PI) / n - Math.PI / 2;
          const maxImportance = Math.max(...topSkills.map(s => s.importance));
          const userFraction = skill.userValue / (maxImportance > 0 ? maxImportance : 1.0);
          const userRadius = rMax * userFraction;
          const ux = cx + userRadius * Math.cos(angle);
          const uy = cy + userRadius * Math.sin(angle);
          
          return (
            <circle 
              key={i} 
              cx={ux} 
              cy={uy} 
              r="4" 
              fill="var(--accent)" 
              stroke="#0b0f19" 
              strokeWidth="1" 
            />
          );
        })}

        {/* Labels */}
        {axes.map((axis, idx) => (
          <text
            key={idx}
            x={axis.lx}
            y={axis.ly}
            textAnchor={axis.anchor}
            fill="var(--text-secondary)"
            fontSize="10"
            fontFamily="var(--font-family-title)"
            fontWeight="600"
            dy="3"
          >
            {axis.name}
          </text>
        ))}
      </svg>
    );
  };

  return (
    <div>
      {/* Page Header */}
      <header className="page-header">
        <h2 className="page-title">Career Intelligence & Gap Analyzer</h2>
        <p className="page-subtitle">Select a target career archetype to analyze skill fit, parse substitute credits, and get roadmap recommendations.</p>
      </header>

      {error && (
        <div className="card" style={{ borderLeft: '4px solid var(--error)', marginBottom: '2rem', background: 'rgba(239, 68, 68, 0.05)' }}>
          <p style={{ color: '#fecaca', fontSize: '0.95rem' }}>{error}</p>
        </div>
      )}

      {/* Selector Controls */}
      <div className="card" style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1, minWidth: '260px' }}>
          <label className="form-label">Target Career Archetype</label>
          <select 
            className="form-input" 
            value={selectedArchId} 
            onChange={(e) => setSelectedArchId(e.target.value)}
            style={{ appearance: 'none', backgroundRepeat: 'no-repeat', backgroundPosition: 'right 1rem center' }}
          >
            {archetypes.map(a => (
              <option key={a.id} value={a.id} style={{ background: '#0b0f19' }}>{a.name}</option>
            ))}
          </select>
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 2, minWidth: '320px' }}>
          <span className="form-label">Profile Context</span>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Comparing your profile of <strong style={{ color: '#e2e8f0' }}>{userSkills.length} skills</strong> against centroid vectors. You can edit skills in the Explorer tab.
          </p>
        </div>
      </div>

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '5rem 0' }}>
          <div className="loader-spinner"></div>
        </div>
      ) : gapAnalysis ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          
          {/* Main Analyzer Grid */}
          <div className="grid-2">
            
            {/* Gap Analysis Stats */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <h3 style={{ fontFamily: 'var(--font-family-title)', fontSize: '1.25rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
                Fit Analysis
              </h3>
              
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Overall Matching Ratio</span>
                  <span style={{ fontSize: '1.15rem', fontWeight: 'bold', color: 'var(--accent)' }}>
                    {(gapAnalysis.match_score * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="progress-bar-container" style={{ height: '12px' }}>
                  <div className="progress-bar" style={{ width: `${gapAnalysis.match_score * 100}%` }}></div>
                </div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                  Calculated based on cluster centroid importance weights, including substitute credits.
                </p>
              </div>

              {/* Grid lists */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                {/* Matching Skills */}
                <div>
                  <h4 style={{ fontSize: '0.9rem', color: 'var(--success)', marginBottom: '0.5rem', fontWeight: '700' }}>
                    Matching Skills ({gapAnalysis.matching_skills.length})
                  </h4>
                  <div className="badge-container">
                    {gapAnalysis.matching_skills.map((s) => (
                      <span key={s.skill_id} className="badge badge-primary" style={{ background: 'rgba(16, 185, 129, 0.1)', borderColor: 'rgba(16, 185, 129, 0.25)', color: '#a7f3d0' }}>
                        {s.canonical_name} ({(s.importance_score * 100).toFixed(0)}%)
                      </span>
                    ))}
                    {gapAnalysis.matching_skills.length === 0 && (
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontStyle: 'italic' }}>No matching skills.</span>
                    )}
                  </div>
                </div>

                {/* Missing Skills with Substitute */}
                <div>
                  <h4 style={{ fontSize: '0.9rem', color: 'var(--error)', marginBottom: '0.5rem', fontWeight: '700' }}>
                    Missing Skill Gaps ({gapAnalysis.missing_skills.length})
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {gapAnalysis.missing_skills.map((s) => (
                      <div key={s.skill_id} style={{ display: 'flex', flexDirection: 'column', padding: '0.75rem', borderRadius: '8px', background: 'rgba(255, 255, 255, 0.015)', border: '1px solid rgba(255,255,255,0.03)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                          <span style={{ fontWeight: '600', fontSize: '0.85rem' }}>{s.canonical_name}</span>
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Centroid Importance: {(s.importance_score * 100).toFixed(0)}%</span>
                        </div>
                        {s.closest_substitute ? (
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                            Partial credit granted for substitute <strong style={{ color: 'var(--accent)' }}>{s.closest_substitute}</strong> (similarity: {(s.substitute_similarity * 100).toFixed(0)}%, credit: +{(s.substitute_credit * 100).toFixed(0)}%)
                          </div>
                        ) : (
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                            No semantic substitute in profile (needs to be learned)
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Radar Chart Visualizer */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ alignSelf: 'stretch', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
                <h3 style={{ fontFamily: 'var(--font-family-title)', fontSize: '1.25rem' }}>
                  Centroid Overlap Radar Model
                </h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                  Visual comparison between target requirements (<span style={{ borderBottom: '1.5px dashed var(--primary)', color: 'var(--primary)', fontWeight: 'bold' }}>dashed purple</span>) and your profile (<span style={{ color: 'var(--accent)', fontWeight: 'bold' }}>solid cyan</span>).
                </p>
              </div>
              {renderRadarChart()}
              <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <div style={{ width: '12px', height: '12px', border: '1px dashed var(--primary)', background: 'rgba(168, 85, 247, 0.05)' }}></div>
                  <span>Target Centroid</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <div style={{ width: '12px', height: '12px', border: '2px solid var(--accent)', background: 'rgba(6, 182, 212, 0.18)' }}></div>
                  <span>Your Profile (With Substitutes)</span>
                </div>
              </div>
            </div>

          </div>

          {/* Recommendations roadmap */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <h3 style={{ fontFamily: 'var(--font-family-title)', fontSize: '1.25rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
              Recommended Learning Roadmap
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              Personalized roadmap built combining target archetype gaps (weight 50%), co-occurrence synergy (weight 30%), and semantic proximity (weight 20%).
            </p>
            {recLoading ? (
              <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem 0' }}>
                <div className="loader-spinner" style={{ width: '30px', height: '30px' }}></div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {recommendations.map((rec) => (
                  <div key={rec.skill_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 1.25rem', borderRadius: '12px', background: 'rgba(255,255,255,0.015)', border: '1px solid var(--border-color)' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <strong style={{ fontSize: '1.05rem', color: '#f8fafc' }}>{rec.canonical_name}</strong>
                        <div style={{ display: 'flex', gap: '0.25rem' }}>
                          {rec.reasons.map((r, idx) => (
                            <span key={idx} className="badge badge-accent" style={{ fontSize: '0.7rem', padding: '0.15rem 0.5rem' }}>{r}</span>
                          ))}
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        <span>Relevance: {(rec.signals.relevance * 100).toFixed(0)}%</span>
                        <span>Synergy: {(rec.signals.synergy * 100).toFixed(0)}%</span>
                        <span>Proximity: {(rec.signals.similarity * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                    
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'end' }}>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Recommender Score</span>
                        <span style={{ fontSize: '1.1rem', fontWeight: 'bold', color: 'var(--primary)' }}>
                          {(rec.score * 100).toFixed(0)}
                        </span>
                      </div>
                      <button 
                        className="btn btn-secondary" 
                        style={{ padding: '0.4rem 0.85rem', fontSize: '0.8rem' }}
                        onClick={() => addSkill(rec.canonical_name)}
                      >
                        + Add to Profile
                      </button>
                    </div>
                  </div>
                ))}
                {recommendations.length === 0 && (
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontStyle: 'italic', textAlign: 'center', padding: '1rem' }}>
                    Perfect Match! You already have all key skills for this archetype.
                  </p>
                )}
              </div>
            )}
          </div>

        </div>
      ) : null}
    </div>
  );
}

export default CareerIntel;
