async function init() {
  try {
    const data = await api.listRoutines();
    renderRoutines(data.routines || []);
  } catch (e) {
    document.getElementById("routines-list").innerHTML =
      `<p style="color:var(--danger)">Error: ${e.message}</p>`;
  }
}

function renderRoutines(routines) {
  const el = document.getElementById("routines-list");
  if (!routines.length) {
    el.innerHTML = `
      <div class="empty-state">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
        </svg>
        <p>Sin rutinas aún. Sube una o pídele a Flex que te cree una.</p>
      </div>
    `;
    return;
  }

  el.innerHTML = routines.map((r) => `
    <div class="card" style="margin-bottom:var(--space-3)">
      <div class="card-header">
        <div>
          <div style="display:flex;align-items:center;gap:var(--space-2)">
            <span class="card-title">${escHtml(r.name)}</span>
            ${r.is_active ? '<span class="badge badge-green">Activa</span>' : ''}
          </div>
          <div style="color:var(--text-muted);font-size:var(--text-xs);margin-top:2px">
            ${r.frequency_per_week}x/sem · ${escHtml(r.goal || "general")}
          </div>
        </div>
        <div style="display:flex;gap:var(--space-2)">
          ${!r.is_active ? `<button class="btn btn-sm btn-secondary" onclick="activate(${r.id})">Activar</button>` : ""}
          <button class="btn btn-sm btn-ghost" onclick="deleteRoutine(${r.id})">🗑</button>
        </div>
      </div>
      <div id="days-${r.id}">
        ${renderDays(r.days || [])}
      </div>
    </div>
  `).join("");
}

function renderDays(days) {
  if (!days.length) return "";
  return days.map((day) => `
    <div class="accordion-item" id="acc-${day.id}">
      <button class="accordion-trigger" onclick="toggleAccordion('acc-${day.id}')">
        <span>Día ${day.day_number} — ${escHtml(day.name)}</span>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </button>
      <div class="accordion-content">
        ${(day.exercises || []).map((ex) => `
          <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--border);font-size:var(--text-sm)">
            <span>${escHtml(ex.exercise_name || ex.exercise?.name || "")}</span>
            <span style="color:var(--text-muted)">
              ${ex.target_sets}×${ex.target_reps_min ?? "?"}${ex.target_reps_max ? "–" + ex.target_reps_max : ""}
              ${ex.target_weight_kg ? " @ " + ex.target_weight_kg + "kg" : ""}
            </span>
          </div>
        `).join("")}
      </div>
    </div>
  `).join("");
}

function toggleAccordion(id) {
  document.getElementById(id).classList.toggle("open");
}

async function activate(id) {
  try {
    await api.activateRoutine(id);
    showToast("Rutina activada");
    init();
  } catch (e) {
    showToast(e.message, "error");
  }
}

async function deleteRoutine(id) {
  if (!confirm("¿Eliminar esta rutina?")) return;
  try {
    await api.deleteRoutine(id);
    showToast("Rutina eliminada");
    init();
  } catch (e) {
    showToast(e.message, "error");
  }
}

// Upload modal
function openUploadModal() {
  document.getElementById("upload-modal").style.display = "flex";
}

function closeUploadModal(e) {
  if (!e || e.target === document.getElementById("upload-modal")) {
    document.getElementById("upload-modal").style.display = "none";
  }
}

async function uploadRoutine() {
  const text = document.getElementById("upload-text").value.trim();
  if (!text) return;
  const btn = document.getElementById("upload-btn");
  btn.disabled = true;
  btn.textContent = "Analizando...";
  try {
    await api.uploadRoutine(text);
    closeUploadModal();
    showToast("Rutina guardada");
    document.getElementById("upload-text").value = "";
    init();
  } catch (e) {
    showToast(e.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Analizar con IA";
  }
}

function escHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

init();
