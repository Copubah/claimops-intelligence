import { useEffect, useState } from 'react'
import { buildClaimsQuery, getClaims } from '../services/claims.js'

export function useClaims(filters) {
  const query = buildClaimsQuery(filters)
  const [result, setResult] = useState({ query: null, data: null, error: null })

  useEffect(() => {
    const controller = new AbortController()
    getClaims(filters, { signal: controller.signal })
      .then((data) => setResult({ query, data, error: null }))
      .catch((error) => {
        if (error.name !== 'AbortError') setResult({ query, data: null, error })
      })
    return () => controller.abort()
  }, [query]) // eslint-disable-line react-hooks/exhaustive-deps

  return {
    data: result.query === query ? result.data : null,
    error: result.query === query ? result.error : null,
    loading: result.query !== query,
  }
}

