const CHART_DEFAULTS = {
  color: "#a0a0a0",
  borderColor: "#2a2a2a",
  font: { family: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif", size: 11 },
};

Chart.defaults.color = CHART_DEFAULTS.color;
Chart.defaults.borderColor = CHART_DEFAULTS.borderColor;
Chart.defaults.font = CHART_DEFAULTS.font;

async function init() {
  try {
    const [snapshot, volume, muscles] = await Promise.all([
      api.getDashboard(),
      api.getVolume(56, "week"),
      api.getMuscleGroups(30),
    ]);
    renderStats(snapshot);
    renderVolumeChart(volume);
    renderMuscleChart(muscles);
    renderRecentSessions(snapshot.recent_sessions || []);
  } catch (e) {
    document.getElementById("stats-grid").innerHTML =
      `<p style="color:var(--danger);grid-column:1/-1;padding:var(--space-4)">Error cargando datos: ${e.message}</p>`;
  }
}

function renderStats(data) {
  document.getElementById("stats-grid").innerHTML = `
    <div class="stat-card">
      <div class="stat-value">${data.streak_days ?? 0}</div>
      <div class="stat-label">🔥 Racha días</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">${data.sessions_this_month ?? 0}</div>
      <div class="stat-label">Sesiones (mes)</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">${data.total_sessions ?? 0}</div>
      <div class="stat-label">Total sesiones</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">${Math.round(data.volume_this_month_kg ?? 0).toLocaleString()}</div>
      <div class="stat-label">Volumen kg (mes)</div>
    </div>
  `;
}

function renderVolumeChart(data) {
  const labels = data.map((d) => {
    const [y, m, day] = d.period.split("-");
    return `${day}/${m}`;
  });
  const values = data.map((d) => d.total_volume_kg);

  new Chart(document.getElementById("volume-chart"), {
    type: "bar",
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: "rgba(74,222,128,0.25)",
        borderColor: "#4ade80",
        borderWidth: 1.5,
        borderRadius: 4,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false } },
        y: {
          beginAtZero: true,
          ticks: { callback: (v) => `${v}kg` },
        },
      },
    },
  });
}

function renderMuscleChart(data) {
  if (!data.length) return;
  const top = data.slice(0, 8);

  new Chart(document.getElementById("muscle-chart"), {
    type: "radar",
    data: {
      labels: top.map((d) => d.muscle_group),
      datasets: [{
        data: top.map((d) => d.volume_kg),
        backgroundColor: "rgba(74,222,128,0.15)",
        borderColor: "#4ade80",
        borderWidth: 2,
        pointBackgroundColor: "#4ade80",
        pointRadius: 3,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        r: {
          grid: { color: "#2a2a2a" },
          angleLines: { color: "#2a2a2a" },
          ticks: { display: false },
          pointLabels: { font: { size: 10 } },
        },
      },
    },
  });
}

function renderRecentSessions(sessions) {
  const el = document.getElementById("recent-sessions");
  if (!sessions.length) {
    el.innerHTML = `<div class="empty-state"><p>Sin sesiones completadas aún.</p></div>`;
    return;
  }
  el.innerHTML = sessions.map((s) => `
    <div class="card" style="margin-bottom:var(--space-2);display:flex;align-items:center;justify-content:space-between;gap:var(--space-3)">
      <div>
        <div style="font-weight:600;font-size:var(--text-sm)">${s.routine_day_name}</div>
        <div style="color:var(--text-muted);font-size:var(--text-xs)">${s.date}</div>
      </div>
      <div style="text-align:right">
        <div style="font-weight:700;color:var(--accent);font-size:var(--text-sm)">${Math.round(s.total_volume_kg ?? 0)}kg</div>
        <div style="color:var(--text-muted);font-size:var(--text-xs)">${s.duration_min ? s.duration_min + " min" : "—"}</div>
      </div>
      ${s.overall_feeling ? `<div style="font-size:18px">${["😞","😐","🙂","😄","🤩"][s.overall_feeling-1]}</div>` : ""}
    </div>
  `).join("");
}

init();
