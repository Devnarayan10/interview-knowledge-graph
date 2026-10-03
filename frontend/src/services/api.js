import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
const http = axios.create({ baseURL: API_BASE, timeout: 60000 });

const clean = (p = {}) => Object.fromEntries(Object.entries(p).filter(([, v]) => v !== '' && v != null));
const get = (url, params) => http.get(url, { params: clean(params) }).then((r) => r.data);
const post = (url, body) => http.post(url, body).then((r) => r.data);
const put = (url, body) => http.put(url, body).then((r) => r.data);
const del = (url) => http.delete(url).then((r) => r.data);
const enc = encodeURIComponent;

export const errMsg = (e) => {
  const d = e?.response?.data?.detail;
  if (Array.isArray(d)) return d.map((x) => `${x.loc?.slice(-1)[0]}: ${x.msg}`).join('; ');
  return d || e?.message || 'Request failed';
};

export const api = {
  health: () => axios.get(API_BASE.replace(/\/api\/?$/, '') + '/health').then((r) => r.data),
  seed: () => post('/seed'),
  dashboard: () => get('/dashboard/summary'),

  candidates: (p) => get('/candidates', p),
  candidate: (id) => get(`/candidates/${enc(id)}`),
  createCandidate: (b) => post('/candidates', b),
  updateCandidate: (id, b) => put(`/candidates/${enc(id)}`, b),
  deleteCandidate: (id) => del(`/candidates/${enc(id)}`),

  questions: (p) => get('/questions', p),
  question: (id) => get(`/questions/${enc(id)}`),
  createQuestion: (b) => post('/questions', b),
  updateQuestion: (id, b) => put(`/questions/${enc(id)}`, b),
  deleteQuestion: (id) => del(`/questions/${enc(id)}`),

  interviews: (p) => get('/interviews', p),
  interview: (id) => get(`/interviews/${enc(id)}`),
  createInterview: (b) => post('/interviews', b),
  updateInterview: (id, b) => put(`/interviews/${enc(id)}`, b),
  deleteInterview: (id) => del(`/interviews/${enc(id)}`),

  evaluation: (id) => get(`/evaluation/${enc(id)}`),
  graph: (p) => get('/graph', p),
  candidateGraph: (id) => get(`/graph/candidate/${enc(id)}`),

  analyticsOverview: () => get('/analytics/overview'),
  analyticsSkills: (p) => get('/analytics/skills', p),
  analyticsRoles: () => get('/analytics/roles'),
  analyticsDifficulties: () => get('/analytics/difficulties'),
  analyticsGds: () => get('/analytics/gds'),
  analyticsMongo: () => get('/analytics/mongo'),

  roleRecs: (id) => get(`/recommendations/candidate/${enc(id)}`),
  similar: (id) => get(`/recommendations/similar/${enc(id)}`),
  skillGap: (id, roleId) => get(`/recommendations/skill-gap/${enc(id)}`, { role_id: roleId }),

  skills: () => get('/skills'),
  roles: () => get('/roles'),

  dbNeo4j: () => get('/database/neo4j'),
  dbMongo: () => get('/database/mongodb'),
  dbIndexes: () => get('/database/indexes'),
};