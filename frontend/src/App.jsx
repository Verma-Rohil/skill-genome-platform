import React, { useState } from 'react';
import Dashboard from './pages/Dashboard';
import Explorer from './pages/Explorer';
import CareerIntel from './pages/CareerIntel';
import Simulator from './pages/Simulator';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Shared user profile state. When user extracts or selects skills in the Explorer,
  // they carry over to Career Intelligence for gap analysis and recommendations!
  const [userSkills, setUserSkills] = useState(['Python', 'SQL', 'Git']);

  const addSkillToProfile = (skillName) => {
    const clean = skillName.trim();
    if (clean && !userSkills.some(s => s.toLowerCase() === clean.toLowerCase())) {
      setUserSkills([...userSkills, clean]);
    }
  };

  const removeSkillFromProfile = (skillName) => {
    setUserSkills(userSkills.filter(s => s !== skillName));
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'explorer':
        return (
          <Explorer 
            userSkills={userSkills} 
            addSkill={addSkillToProfile} 
            removeSkill={removeSkillFromProfile} 
          />
        );
      case 'career':
        return (
          <CareerIntel 
            userSkills={userSkills} 
            addSkill={addSkillToProfile} 
            removeSkill={removeSkillFromProfile} 
          />
        );
      case 'simulator':
        return <Simulator />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="logo-container">
          <h1 className="logo-text">SKILL GENOME</h1>
        </div>
        
        <nav>
          <ul className="nav-links">
            <li>
              <button 
                className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
                onClick={() => setActiveTab('dashboard')}
              >
                Dashboard
              </button>
            </li>
            <li>
              <button 
                className={`nav-item ${activeTab === 'explorer' ? 'active' : ''}`}
                onClick={() => setActiveTab('explorer')}
              >
                Skill Explorer
              </button>
            </li>
            <li>
              <button 
                className={`nav-item ${activeTab === 'career' ? 'active' : ''}`}
                onClick={() => setActiveTab('career')}
              >
                Career Intelligence
              </button>
            </li>
            <li>
              <button 
                className={`nav-item ${activeTab === 'simulator' ? 'active' : ''}`}
                onClick={() => setActiveTab('simulator')}
              >
                Disruption Simulator
              </button>
            </li>
          </ul>
        </nav>
      </aside>

      {/* Main Main Content Panel */}
      <main className="main-content">
        {renderContent()}
      </main>
    </div>
  );
}

export default App;
