import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export async function listPages(params = {}) {
  const { data } = await api.get('/wiki/pages', { params })
  return data.pages
}

export async function getPage(path) {
  const { data } = await api.get(`/wiki/pages/${path}`)
  return data
}

export async function savePage(path, payload) {
  const { data } = await api.put(`/wiki/pages/${path}`, payload)
  return data
}

export async function patchPageMeta(path, meta) {
  const { data } = await api.patch(`/wiki/pages/${path}/meta`, meta)
  return data
}

export async function deletePage(path) {
  const { data } = await api.delete(`/wiki/pages/${path}`)
  return data
}

export async function listDeleted() {
  const { data } = await api.get('/wiki/deleted')
  return data.items
}

export async function searchWiki(q) {
  const { data } = await api.get('/wiki/search', { params: { q } })
  return data.results
}

export async function getGraph() {
  const { data } = await api.get('/wiki/graph')
  return data
}

export async function getEntity(kind, name) {
  const { data } = await api.get(`/wiki/entities/${kind}/${encodeURIComponent(name)}`)
  return data
}

export async function uploadImage(file) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/wiki/upload', form)
  return data
}

export async function listWeekly() {
  const { data } = await api.get('/weekly')
  return data
}

export async function getWeekly(path) {
  const { data } = await api.get(`/weekly/${path}`)
  return data
}

export async function askQuestion(question) {
  const { data } = await api.post('/ask', { question })
  return data
}

export async function listSkills() {
  const { data } = await api.get('/skills')
  return data.skills
}

export async function listExperiments() {
  const { data } = await api.get('/exp')
  return data.experiments
}

export async function getExperiment(id) {
  const { data } = await api.get(`/exp/${id}`)
  return data
}

export async function getExperimentFile(id, rel) {
  const { data } = await api.get(`/exp/${id}/file/${rel}`)
  return data
}

export async function listThreads() {
  const { data } = await api.get('/threads')
  return data.threads
}

export async function getThread(id) {
  const { data } = await api.get(`/threads/${id}`)
  return data
}

export async function createThread(payload) {
  const { data } = await api.post('/threads', payload)
  return data
}

export async function patchThread(id, payload) {
  const { data } = await api.patch(`/threads/${id}`, payload)
  return data
}

export async function threadsForPaper(path) {
  const { data } = await api.get(`/threads/by-paper/${path}`)
  return data.thread_ids
}

export async function threadsForExp(expId) {
  const { data } = await api.get(`/threads/by-exp/${expId}`)
  return data.thread_ids
}

export async function runThreadDelta(id, payload = {}) {
  const { data } = await api.post(`/threads/${id}/delta`, payload)
  return data
}

export async function getThreadClaimSuggestions(id) {
  const { data } = await api.get(`/threads/${id}/claims/suggestions`)
  return data
}

export async function acceptThreadClaim(id, payload) {
  const { data } = await api.post(`/threads/${id}/claims/accept`, payload)
  return data
}

export async function getThreadContext(id) {
  const { data } = await api.get(`/threads/${id}/context`)
  return data
}

export async function listThreadEvidences(id, params = {}) {
  const { data } = await api.get(`/threads/${id}/evidences`, { params })
  return data.evidences
}

export async function createThreadEvidence(id, payload) {
  const { data } = await api.post(`/threads/${id}/evidences`, payload)
  return data
}

export async function setThreadEvidenceGate(id, evidenceId, gate) {
  const { data } = await api.post(`/threads/${id}/evidences/${evidenceId}/gate`, { gate })
  return data
}

export async function getThreadEvidenceMap(id) {
  const { data } = await api.get(`/threads/${id}/evidence-map`)
  return data
}

export async function login(username) {
  const { data } = await api.post('/auth/login', { username })
  return data
}
