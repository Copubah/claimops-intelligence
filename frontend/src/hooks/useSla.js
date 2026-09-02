import { useEffect, useState } from 'react'
import { getSlaSnapshot } from '../services/claims.js'

export function useSla({ status, partner, limit }) {
  const [result, setResult] = useState({ key: null, data: null, error: null })
  const key = JSON.stringify({ status, partner, limit })

  useEffect(() => {
    const controller = new AbortController()
    getSlaSnapshot({ status, partner, limit, signal: controller.signal })
      .then((data) => setResult({ key, data, error: null }))
      .catch((error) => { if (error.name !== 'AbortError') setResult({ key, data: null, error }) })
    return () => controller.abort()
  }, [key, status, partner, limit])

  return { data: result.key === key ? result.data : null,
    error: result.key === key ? result.error : null, loading: result.key !== key }
}
