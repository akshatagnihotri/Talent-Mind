const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') localStorage.setItem('talentmind_token', token);
  }

  getToken() {
    if (this.token) return this.token;
    if (typeof window !== 'undefined') this.token = localStorage.getItem('talentmind_token');
    return this.token;
  }

  clearToken() {
    this.token = null;
    if (typeof window !== 'undefined') localStorage.removeItem('talentmind_token');
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const token = this.getToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(url, { ...options, headers });
    if (!response.ok) {
      if (response.status === 401) {
        this.clearToken();
        if (typeof window !== 'undefined') {
          window.location.href = '/auth';
        }
      }
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || 'Request failed');
    }
    return response.json();
  }

  async login(email: string, password: string) {
    const response = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!response.ok) throw new Error('Invalid credentials');
    const data = await response.json();
    this.setToken(data.access_token);
    return data;
  }

  async register(name: string, email: string, password: string) {
    return this.request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    });
  }

  async getMe() {
    return this.request('/api/auth/me');
  }

  // Resumes
  async uploadResume(file: File, jobDescriptionId?: string) {
    const formData = new FormData();
    formData.append('file', file);
    if (jobDescriptionId) formData.append('job_description_id', jobDescriptionId);
    const token = this.getToken();
    const response = await fetch(`${API_BASE}/api/resumes/upload`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    if (!response.ok) throw new Error('Upload failed');
    return response.json();
  }

  async getResumes() {
    return this.request('/api/resumes/');
  }

  async deleteResume(id: string) {
    return this.request(`/api/resumes/${id}`, { method: 'DELETE' });
  }

  // Analysis
  async analyzeResume(resumeId: string, jobDescriptionId?: string) {
    if (jobDescriptionId) {
      return this.request(`/api/analysis/resume/${resumeId}/job/${jobDescriptionId}`, {
        method: 'POST',
      });
    } else {
      return this.request(`/api/analysis/resume/${resumeId}`, {
        method: 'POST',
      });
    }
  }

  async getAnalysis(analysisId: string) {
    return this.request(`/api/analysis/${analysisId}`);
  }

  async getAnalysisByResume(resumeId: string) {
    return this.request(`/api/analysis/resume/${resumeId}`);
  }

  // Job Descriptions
  async createJob(data: {
    title: string;
    company: string;
    description: string;
    required_skills: string[];
  }) {
    return this.request('/api/jobs/', { method: 'POST', body: JSON.stringify(data) });
  }

  async getJobs() {
    return this.request('/api/jobs/');
  }

  async deleteJob(id: string) {
    return this.request(`/api/jobs/${id}`, { method: 'DELETE' });
  }

  // Ranking
  async rankCandidates(jobDescriptionId: string, resumeIds: string[]) {
    return this.request('/api/ranking/rank', {
      method: 'POST',
      body: JSON.stringify({ job_description_id: jobDescriptionId, resume_ids: resumeIds }),
    });
  }

  async getLeaderboard(jobDescriptionId: string) {
    return this.request(`/api/ranking/leaderboard/${jobDescriptionId}`);
  }

  // Analytics
  async getDashboardAnalytics() {
    return this.request('/api/analytics/dashboard');
  }

  async getSkillDemand() {
    return this.request('/api/analytics/skill-demand');
  }

  // Copilot Chat
  async chatWithCopilot(resumeId: string, message: string) {
    return this.request(`/api/recruiter/${resumeId}/chat`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  }
}

export const apiClient = new ApiClient();
export default apiClient;
