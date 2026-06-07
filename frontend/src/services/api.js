import axios from 'axios';

// Create API Axios client
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '', // Dynamic base URL for public deployment, fallback to proxy locally
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // --- Skills Endpoints ---
  async fetchSkills(search = '', skip = 0, limit = 100) {
    const params = { skip, limit };
    if (search) params.search = search;
    const response = await apiClient.get('/api/skills', { params });
    return response.data;
  },

  async fetchSkillDetails(id) {
    const response = await apiClient.get(`/api/skills/${id}`);
    return response.data;
  },

  async fetchSimilarSkills(id, topN = 10) {
    const response = await apiClient.get(`/api/skills/${id}/similar`, {
      params: { top_n: topN },
    });
    return response.data;
  },

  async fetchSynergySkills(id) {
    const response = await apiClient.get(`/api/skills/${id}/synergy`);
    return response.data;
  },

  async extractSkills(text) {
    const response = await apiClient.post('/api/skills/extract', { text });
    return response.data;
  },

  // --- Careers / Archetypes Endpoints ---
  async fetchArchetypes() {
    const response = await apiClient.get('/api/careers/archetypes');
    return response.data;
  },

  async fetchArchetypeDetails(id) {
    const response = await apiClient.get(`/api/careers/archetypes/${id}`);
    return response.data;
  },

  async analyzeGap(currentSkills, targetArchetypeId) {
    const response = await apiClient.post('/api/careers/gap', {
      current_skills: currentSkills,
      target_archetype_id: parseInt(targetArchetypeId, 10),
    });
    return response.data;
  },

  // --- Recommendations Endpoint ---
  async fetchRecommendations(currentSkills, targetArchetypeId = null, topK = 10) {
    const payload = {
      current_skills: currentSkills,
      top_k: topK,
    };
    if (targetArchetypeId !== null) {
      payload.target_archetype_id = parseInt(targetArchetypeId, 10);
    }
    const response = await apiClient.post('/api/recommendations', payload);
    return response.data;
  },

  // --- Simulator Endpoints ---
  async runSimulation(skillShocks, decayFactor = 0.5) {
    const response = await apiClient.post('/api/simulator/simulate', {
      skill_shocks: skillShocks,
      decay_factor: parseFloat(decayFactor),
    });
    return response.data;
  },

  async fetchVulnerability() {
    const response = await apiClient.get('/api/simulator/vulnerability');
    return response.data;
  },
};

export default api;
