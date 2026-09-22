import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'

export const client = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  // Le frontend (5173) et l'API (8001) sont sur des ports différents donc des origines distinctes :
  // depuis axios 1.6, l'en-tête XSRF n'est plus envoyé automatiquement en cross-origin sans ce flag
  // (voir GHSA-wf5p-g6vw-rhxx). Cookie/en-tête choisis pour matcher les noms attendus par Django.
  withXSRFToken: true,
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
})

export async function assurerCookieCsrf() {
  await client.get('/auth/csrf/')
}
