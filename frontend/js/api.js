const BASE = "/api/v1";

async function apiFetch(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

const api = {
  // Chat
  sendMessage: (message, sessionId) =>
    apiFetch("/chat", { method: "POST", body: { message, session_id: sessionId } }),
  getChatHistory: (limit = 50) =>
    apiFetch(`/chat/history?limit=${limit}`),
  clearHistory: () =>
    apiFetch("/chat/history", { method: "DELETE" }),

  // Profile
  getProfile: () => apiFetch("/profile"),
  updateProfile: (data) => apiFetch("/profile", { method: "PUT", body: data }),

  // Routines
  listRoutines: () => apiFetch("/routines"),
  getRoutine: (id) => apiFetch(`/routines/${id}`),
  activateRoutine: (id) => apiFetch(`/routines/${id}/activate`, { method: "POST" }),
  deleteRoutine: (id) => apiFetch(`/routines/${id}`, { method: "DELETE" }),
  uploadRoutine: (text) => apiFetch("/routines/upload", { method: "POST", body: { text } }),

  // Sessions
  listSessions: (limit = 20) => apiFetch(`/sessions?limit=${limit}`),
  getSession: (id) => apiFetch(`/sessions/${id}`),
  getActiveSession: () => apiFetch("/sessions/active"),

  // Exercises
  searchExercises: (q, category) => {
    const params = new URLSearchParams();
    if (q) params.set("search", q);
    if (category) params.set("category", category);
    return apiFetch(`/exercises?${params}`);
  },

  // Progress
  getDashboard: () => apiFetch("/progress/dashboard"),
  getVolume: (days = 56, groupBy = "week") =>
    apiFetch(`/progress/volume?days=${days}&group_by=${groupBy}`),
  getMuscleGroups: (days = 30) => apiFetch(`/progress/muscle-groups?days=${days}`),
  getExerciseProgress: (id, days = 90) =>
    apiFetch(`/progress/exercise/${id}?days=${days}`),
};
