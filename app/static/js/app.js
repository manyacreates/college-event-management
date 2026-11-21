// Show a small popup message. type: "success" or "danger".
function showToast(message, type = "success") {
    const area = document.getElementById("toastArea");
    const toast = document.createElement("div");
    toast.className = `toast align-items-center text-bg-${type} border-0`;
    toast.setAttribute("role", "alert");
    toast.innerHTML = `
      <div class="d-flex">
        <div class="toast-body"></div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>`;
    toast.querySelector(".toast-body").textContent = message; // textContent keeps it safe from HTML injection
    area.appendChild(toast);
  
    const instance = new bootstrap.Toast(toast, { delay: 3500 });
    instance.show();
    toast.addEventListener("hidden.bs.toast", () => toast.remove());
  }
  
  // Logout button in the navbar: call the API, then go home.
  const logoutButton = document.getElementById("logoutButton");
  if (logoutButton) {
    logoutButton.addEventListener("click", async () => {
      await fetch("/api/auth/logout", { method: "POST" });
      window.location.href = "/";
    });
  }