// Highlight active nav item based on current page
(function () {
  const page = location.pathname.split("/").pop() || "chat.html";
  document.querySelectorAll(".nav-item").forEach((el) => {
    const href = el.getAttribute("href") || "";
    if (href && page.startsWith(href.replace(".html", ""))) {
      el.classList.add("active");
    }
  });
})();

// Toast helper — available globally
function showToast(message, type = "success", duration = 3000) {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), duration);
}
