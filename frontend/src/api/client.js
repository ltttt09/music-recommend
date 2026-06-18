const BASE = import.meta.env.VITE_API_BASE || "/api"

export function clearAuthState() {
  localStorage.removeItem("token")
  localStorage.removeItem("user_id")
  localStorage.removeItem("username")
  window.dispatchEvent(new CustomEvent("auth-expired"))
}

export async function apiFetch(path, options = {}) {
  const token = localStorage.getItem("token")
  const headers = { ...(options.headers || {}) }
  if (token) headers.Authorization = `Bearer ${token}`
  const res = await fetch(`${BASE}${path}`, { ...options, headers })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    if (res.status === 401) clearAuthState()
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}
