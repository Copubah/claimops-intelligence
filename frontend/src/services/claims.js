const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL || '/api/v1'

export function buildClaimsQuery(filters = {}) {
  const query = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && String(value).trim() !== '') {
      query.set(key, String(value).trim())
    }
  })
  return query.toString()
}

async function apiRequest(path, { signal } = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, { signal, headers: { Accept: 'application/json' } })
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(payload?.error?.message || `Claims request failed with status ${response.status}`)
  }
  return payload
}

export function getClaims(filters, options) {
  const query = buildClaimsQuery(filters)
  return apiRequest(`/claims${query ? `?${query}` : ''}`, options)
}

export function getClaim(claimId, options) {
  return apiRequest(`/claims/${encodeURIComponent(claimId)}`, options)
}
