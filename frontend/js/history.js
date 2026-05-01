const FEELINGS = ["😞", "😐", "🙂", "😄", "🤩"];

async function init() {
  try {
    const data = await api.listSessions(30);
    renderSessions(data.sessions || []);
  } catch (e) {
    document.getElementById("sessions-list").innerHTML =
      `<p style="color:var(--danger)">Error: ${e.message}</p>`;
  }
}

function renderSessions(sessions) {
  const el = document.getElementById("sessions-list");
  if (!sessions.length) {
    el.innerHTML = `<div class="empty-state"><p>Sin sesiones completadas aún.<br>¡Empieza tu primer entrenamiento!</p></div>`;
    return;
  }

  const completed = sessions.filter((s) => s.status === "completed");
  const inProgress = sessions.find((s) => s.status === "in_progress");

  let html = "";

  if (inProgress) {
    html += `
      <div class="card" style="margin-bottom:var(--space-3);border-color:var(--accent-border);cursor:pointer" onclick="openSession(${inProgress.id})">
        <div style="display:flex;align-items:center;gap:var(--space-2);margin-bottom:var(--space-2)">
          <span class="badge badge-green">En progreso</span>
          <span style="font-size:var(--text-xs);color:var(--text-muted)">${formatDate(inProgress.started_at)}</span>
        </div>
        <div style="font-weight:600">${inProgress.routine_day_name || "Entrenamiento libre"}</div>
        <div style="color:var(--text-muted);font-size:var(--text-xs);margin-top:4px">
          ${inProgress.exercises_count ?? 0} ejercicios · ${Math.round(inProgress.total_volume_kg ?? 0)}kg
        </div>
      </div>
    `;
  }

  html += completed.map((s) => `
    <div class="card" style="margin-bottom:var(--space-2);cursor:pointer" onclick="openSession(${s.id})">
      <div style="display:flex;align-items:center;justify-content:space-between">
        <div>
          <div style="font-weight:600;font-size:var(--text-sm)">${s.routine_day_name || "Entrenamiento libre"}</div>
          <div style="color:var(--text-muted);font-size:var(--text-xs)">${formatDate(s.started_at)}</div>
        </div>
        <div style="text-align:right;display:flex;align-items:center;gap:var(--space-3)">
          <div>
            <div style="font-weight:700;color:var(--accent);font-size:var(--text-sm)">${Math.round(s.total_volume_kg ?? 0)}kg</div>
            <div style="color:var(--text-muted);font-size:var(--text-xs)">${s.duration_min ? s.duration_min + " min" : "—"}</div>
          </div>
          ${s.overall_feeling ? `<span style="font-size:18px">${FEELINGS[s.overall_feeling - 1]}</span>` : ""}
        </div>
      </div>
    </div>
  `).join("");

  el.innerHTML = html;
}

async function openSession(id) {
  const modal = document.getElementById("session-modal");
  const content = document.getElementById("session-modal-content");
  content.innerHTML = `<div style="text-align:center;padding:var(--space-8)"><div class="spinner" style="margin:0 auto"></div></div>`;
  modal.style.display = "flex";

  try {
    const s = await api.getSession(id);
    content.innerHTML = renderSessionDetail(s);
  } catch (e) {
    content.innerHTML = `<p style="color:var(--danger)">Error: ${e.message}</p>`;
  }
}

function renderSessionDetail(s) {
  const exercises = (s.exercises || []).map((ex) => {
    const working = (ex.sets || []).filter((st) => !st.is_warmup);
    const warmup = (ex.sets || []).filter((st) => st.is_warmup);
    return `
      <div style="margin-bottom:var(--space-4)">
        <div style="font-weight:600;margin-bottom:var(--space-2)">${escHtml(ex.exercise_name || ex.exercise?.name || "")}</div>
        <div style="display:flex;flex-direction:column;gap:4px">
          ${(ex.sets || []).map((set) => `
            <div style="display:flex;gap:var(--space-3);font-size:var(--text-xs);color:${set.is_warmup ? "var(--text-muted)" : "var(--text-primary)"}">
              <span style="width:20px">${set.is_warmup ? "W" : set.set_number}</span>
              <span>${set.reps ? set.reps + " reps" : "—"}</span>
              <span>${set.weight_kg ? set.weight_kg + " kg" : "—"}</span>
              ${set.rpe ? `<span>RPE ${set.rpe}</span>` : ""}
            </div>
          `).join("")}
        </div>
      </div>
    `;
  }).join("");

  return `
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--space-5)">
      <h2 class="modal-title" style="margin-bottom:0">${s.routine_day_name || "Entrenamiento libre"}</h2>
      <button class="btn btn-ghost btn-sm" onclick="closeSessionModal()">✕</button>
    </div>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:var(--space-2);margin-bottom:var(--space-5)">
      <div style="text-align:center">
        <div style="font-size:var(--text-xl);font-weight:700;color:var(--accent)">${Math.round(s.total_volume_kg ?? 0)}</div>
        <div style="font-size:var(--text-xs);color:var(--text-muted)">kg volumen</div>
      </div>
      <div style="text-align:center">
        <div style="font-size:var(--text-xl);font-weight:700;color:var(--accent)">${s.duration_min || "—"}</div>
        <div style="font-size:var(--text-xs);color:var(--text-muted)">minutos</div>
      </div>
      <div style="text-align:center">
        <div style="font-size:var(--text-xl);font-weight:700;color:var(--accent)">${s.overall_feeling ? FEELINGS[s.overall_feeling - 1] : "—"}</div>
        <div style="font-size:var(--text-xs);color:var(--text-muted)">sensación</div>
      </div>
    </div>
    <div class="divider"></div>
    ${exercises || '<p style="color:var(--text-muted);font-size:var(--text-sm)">Sin ejercicios registrados.</p>'}
    ${s.notes ? `<div style="margin-top:var(--space-3);padding:var(--space-3);background:var(--bg-elevated);border-radius:var(--radius-md);font-size:var(--text-sm);color:var(--text-secondary)">${escHtml(s.notes)}</div>` : ""}
    ${s.ai_summary ? `<div style="margin-top:var(--space-3);padding:var(--space-3);background:var(--accent-muted);border:1px solid var(--accent-border);border-radius:var(--radius-md);font-size:var(--text-sm)">${escHtml(s.ai_summary)}</div>` : ""}
  `;
}

function closeSessionModal(e) {
  if (!e || e.target === document.getElementById("session-modal")) {
    document.getElementById("session-modal").style.display = "none";
  }
}

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("es", { weekday: "short", day: "numeric", month: "short", year: "numeric" });
}

function escHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

init();
