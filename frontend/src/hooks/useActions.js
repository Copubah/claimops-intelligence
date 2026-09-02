import { useEffect, useState } from 'react'
import { getActions } from '../services/claims.js'

export function useActions(refreshKey = 0, priority = 'ALL') {
  const [result, setResult] = useState({ refreshKey: null, data: null, error: null })

  useEffect(() => {
    const controller = new AbortController()
    getActions({ priority, signal: controller.signal })
      .then((data) => setResult({ refreshKey, data, error: null }))
      .catch((error) => {
        if (error.name !== 'AbortError') setResult({ refreshKey, data: null, error })
      })
    return () => controller.abort()
  }, [refreshKey, priority])

  return {
    data: result.refreshKey === refreshKey ? result.data : null,
    error: result.refreshKey === refreshKey ? result.error : null,
    loading: result.refreshKey !== refreshKey,
  }
}
