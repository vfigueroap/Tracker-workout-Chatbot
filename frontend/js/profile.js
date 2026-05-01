const FIELDS = ["name", "age", "fitness_level", "weight_kg", "height_cm",
  "primary_goal", "preferred_workout_days", "session_duration_min", "injuries_limitations"];

async function init() {
  try {
    const profile = await api.getProfile();
    FIELDS.forEach((f) => {
      const el = document.getElementById(f);
      if (el && profile[f] != null) el.value = profile[f];
    });
  } catch (e) {
    showToast("Error cargando perfil", "error");
  }
}

document.getElementById("profile-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = document.getElementById("save-btn");
  btn.disabled = true;
  btn.textContent = "Guardando...";

  const data = {};
  FIELDS.forEach((f) => {
    const el = document.getElementById(f);
    if (!el) return;
    const val = el.value.trim();
    if (val === "") return;
    if (["age", "height_cm", "session_duration_min"].includes(f)) {
      const n = parseInt(val);
      if (!isNaN(n)) data[f] = n;
    } else if (f === "weight_kg") {
      const n = parseFloat(val);
      if (!isNaN(n)) data[f] = n;
    } else {
      data[f] = val;
    }
  });

  try {
    await api.updateProfile(data);
    showToast("Perfil guardado");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Guardar cambios";
  }
});

init();
