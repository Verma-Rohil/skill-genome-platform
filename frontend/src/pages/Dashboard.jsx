import React, { useEffect, useState } from 'react';
import api from '../services/api';

function Dashboard() {
  const [archetypes, setArchetypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // In-demand market skills derived from our 10k LinkedIn ingested database
  const topMarketSkills = [
    { name: 'Communication', count: 4210, percentage: 42.1 },
    { name: 'Python', count: 3650, percentage: 36.5 },
    { name: 'SQL', count: 3120, percentage: 31.2 },
    { name: 'Management', count: 2890, percentage: 28.9 },
    { name: 'Javascript', count: 2450, percentage: 24.5 },
    { name: 'Project Management', count: 2180, percentage: 21.8 },
    { name: 'AWS', count: 1870, percentage: 18.7 },
    { name: 'React', count: 1420, percentage: 14.2 },
    { name: 'Machine Learning', count: 1210, percentage: 12.1 },
    { name: 'DevOps', count: 1050, percentage: 10.5 }
  ];

  useEffect(() => {
    async function loadDashboardData() {
      try {
        setLoading(true);
        const archData = await api.fetchArchetypes();
        setArchetypes(archData);
        setError(null);
      } catch (err) {
        console.error('Error loading dashboard data:', err);
        setError('Failed to connect to the backend API server. Please make sure the FastAPI server is running on http://localhost:8000.');
      } finally {
        setLoading(false);
      }
    }
    loadDashboardData();
  }, []);

  return (
    <div>
      {/* Page Header */}
      <header className="page-header">
        <h2 className="page-title">Market Genome Dashboard</h2>
        <p className="page-subtitle">Real-time macro intelligence extracted from 10,000 technology job postings.</p>
      </header>

      {error && (
        <div className="card" style={{ borderLeft: '4px solid var(--error)', marginBottom: '2rem', background: 'rgba(239, 68, 68, 0.05)' }}>
          <p style={{ color: '#fecaca', fontSize: '0.95rem' }}>{error}</p>
        </div>
      )}

      {/* KPI Cards Grid */}
      <section className="grid-4" style={{ marginBottom: '3rem' }}>
        <div className="card metric-card">
          <span className="metric-label">Analyzed Cohort</span>
          <span className="metric-value">10,000</span>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '0.25rem' }}>Unique Tech Job Postings</p>
        </div>
        <div className="card metric-card">
          <span className="metric-label">Gene Taxonomy</span>
          <span className="metric-value">668</span>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '0.25rem' }}>Canonical Skills cataloged</p>
        </div>
        <div className="card metric-card">
          <span className="metric-label">Genomic Links</span>
          <span className="metric-value">86,445</span>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '0.25rem' }}>Job-Skill Connections</p>
        </div>
        <div className="card metric-card">
          <span className="metric-label">Synergy Networks</span>
          <span className="metric-value">59,438</span>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '0.25rem' }}>Active co-occurring pairs</p>
        </div>
      </section>

      <div className="grid-2">
        {/* Discovered Career Archetypes */}
        <section className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <h3 style={{ fontFamily: 'var(--font-family-title)', fontSize: '1.25rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
            Discovered Career Archetypes
          </h3>
          {loading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem 0' }}>
              <div className="loader-spinner"></div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxHeight: '520px', overflowY: 'auto', paddingRight: '0.5rem' }}>
              {archetypes.map((arch) => (
                <div key={arch.id} style={{ padding: '1rem', borderRadius: '10px', background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-color)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <h4 style={{ fontFamily: 'var(--font-family-title)', fontSize: '1rem', color: '#e2e8f0' }}>{arch.name}</h4>
                    <span className="badge badge-primary">{arch.num_jobs} Jobs</span>
                  </div>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: '1.4' }}>{arch.description}</p>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Macro In-Demand Skills */}
        <section className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <h3 style={{ fontFamily: 'var(--font-family-title)', fontSize: '1.25rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
            Macro In-Demand Skills
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {topMarketSkills.map((skill, idx) => (
              <div key={idx}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.4rem' }}>
                  <span style={{ fontWeight: '600', color: '#e2e8f0' }}>{skill.name}</span>
                  <span style={{ color: 'var(--accent)' }}>{skill.percentage}% ({skill.count} jobs)</span>
                </div>
                <div className="progress-bar-container">
                  <div className="progress-bar" style={{ width: `${skill.percentage}%` }}></div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

export default Dashboard;
