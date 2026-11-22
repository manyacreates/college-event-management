const form = document.getElementById("authForm");
const errorBox = document.getElementById("formError");
const submitButton = document.getElementById("submitButton");

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove("d-none");
}

async function postJson(url, data) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const body = await response.json().catch(() => ({}));
  return { ok: response.ok, body };
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorBox.classList.add("d-none");

  const mode = form.dataset.mode;
  const email = form.elements.email.value.trim();
  const password = form.elements.password.value;

  if (!email || !password) {
    showError("Please fill in all fields.");
    return;
  }

  submitButton.disabled = true;
  const originalText = submitButton.textContent;
  submitButton.textContent = "Please wait...";

  try {
    if (mode === "register") {
      const name = form.elements.name.value.trim();
      if (!name) {
        showError("Please enter your name.");
        return;
      }
      const created = await postJson("/api/auth/register", { name, email, password });
      if (!created.ok) {
        showError(created.body.message || "Registration failed.");
        return;
      }
    }

    const login = await postJson("/api/auth/login", { email, password });
    if (!login.ok) {
      showError(login.body.message || "Login failed.");
      return;
    }

    // The admin login page only lets admins through.
    if (mode === "admin" && login.body.user.role !== "admin") {
      await fetch("/api/auth/logout", { method: "POST" });
      showError("This account is not an administrator.");
      return;
    }

    // Dashboards are built in the next steps, so go home for now.
    window.location.href = "/";
  } catch (error) {
    showError("Could not reach the server. Please try again.");
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = originalText;
  }
});