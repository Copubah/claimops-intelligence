const OVERVIEW_FIXTURE_URL = '/data/overview.json'

export async function getOverview({ signal } = {}) {
  const response = await fetch(OVERVIEW_FIXTURE_URL, { signal })
  if (!response.ok) {
    throw new Error(`Overview request failed with status ${response.status}`)
  }
  const payload = await response.json()
  if (payload.data_classification !== 'SYNTHETIC' || !payload.metrics) {
    throw new Error('Overview payload is invalid')
  }
  return payload
}

