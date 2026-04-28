const BASE = '/api'

async function get(path) {
  const res = await fetch(BASE + path)
  if (!res.ok) throw new Error(`${res.status} ${path}`)
  return res.json()
}

export const getJobs = async (filters = {}) => {
  const p = new URLSearchParams()
  if (filters.source) p.append('source', filters.source)
  if (filters.status && filters.status !== 'all') p.append('status', filters.status)
  if (filters.q) p.append('q', filters.q)
  const data = await get(`/jobs?${p}`)
  return data.jobs ?? []
}

export const getSources = async () => {
  const data = await get('/sources')
  return data.sources ?? []
}

export const getStatus = () => get('/status')

export const getScannerStatus = async () => {
  const data = await get('/scanner')
  return data.sources ?? []
}

export const triggerScan = () =>
  fetch(BASE + '/scan', { method: 'POST' }).then(r => r.json())
