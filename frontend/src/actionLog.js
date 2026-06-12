const BASE = import.meta.env.VITE_API_BASE || "/api";
const SESSION_KEY = "music_session_id";

function sessionId() {
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    localStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

export function logAction(actionType, payload = {}) {
  const token = localStorage.getItem("token");
  const body = {
    session_id: sessionId(),
    action_type: actionType,
    entity_type: payload.entity_type || "",
    entity_id: payload.entity_id ?? null,
    status: payload.status || "",
    page_url: window.location.href,
    message: payload.message || "",
    metadata: payload.metadata || {},
  };
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;

  fetch(`${BASE}/users/actions`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
    keepalive: true,
  }).catch(() => {});
}
