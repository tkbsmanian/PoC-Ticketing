/**
 * Axios instance — base URL, credentials, and global error handling.
 * All API calls go through this client. Never use axios directly in components.
 */

import axios, { AxiosError } from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  withCredentials: true, // send httpOnly cookie on every request
  headers: { 'Content-Type': 'application/json' },
})

// Redirect to login on 401 — but NOT if already on login page (avoids loop)
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401 && !window.location.pathname.startsWith('/login')) {
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient
