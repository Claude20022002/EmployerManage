import { useEffect, useState } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'

function App() {
  const [apiStatus, setApiStatus] = useState<'checking' | 'ok' | 'error'>('checking')

  useEffect(() => {
    fetch(`${API_URL}/health/`)
      .then((res) => (res.ok ? setApiStatus('ok') : setApiStatus('error')))
      .catch(() => setApiStatus('error'))
  }, [])

  return (
    <main>
      <h1>Gestion des congés — Ministère de l'Économie, des Finances et du Budget</h1>
      <p>
        API backend :{' '}
        {apiStatus === 'checking' && 'vérification en cours…'}
        {apiStatus === 'ok' && '✅ connectée'}
        {apiStatus === 'error' && '❌ injoignable'}
      </p>
    </main>
  )
}

export default App
