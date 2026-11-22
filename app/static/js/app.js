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
  // Escape text before putting it into HTML.
function esc(text) {
  const div = document.createElement("div");
  div.textContent = text == null ? "" : String(text);
  return div.innerHTML;
}

// Call the JSON API. Returns { ok, status, body }.
async function api(url, method = "GET", data = null) {
  const options = { method, headers: {} };
  if (data !== null) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(data);
  }
  const response = await fetch(url, options);
  const body = await response.json().catch(() => ({}));
  return { ok: response.ok, status: response.status, body };
}

function prettyDate(iso) {
  return new Date(iso + "T00:00:00").toLocaleDateString("en-GB", {
    day: "2-digit", month: "short", year: "numeric",
  });
}

function eventCardHtml(e) {
  const spots = e.spots_left > 0
    ? `<span class="spots spots-open">${e.spots_left} spots left</span>`
    : `<span class="spots spots-full">Fully booked</span>`;
  const image = e.image_url
    ? `<img src="${esc(e.image_url)}" alt="" class="event-card-img">`
    : `<div class="event-card-img event-card-placeholder"><i class="bi bi-calendar-event"></i></div>`;
  return `
  <div class="col-md-6 col-lg-4">
    <article class="event-card h-100">
      ${image}
      <div class="event-card-body">
        <span class="badge badge-category">${esc(e.category)}</span>
        <h3 class="event-card-title">${esc(e.title)}</h3>
        <ul class="event-meta list-unstyled">
          <li><i class="bi bi-calendar3"></i> ${prettyDate(e.event_date)} &middot; ${esc(e.start_time)}</li>
          <li><i class="bi bi-geo-alt"></i> ${esc(e.venue)}</li>
        </ul>
        <div class="d-flex justify-content-between align-items-center mt-auto">
          ${spots}
          <a href="/events/${e.id}" class="btn btn-sm btn-primary">View details</a>
        </div>
      </div>
    </article>
  </div>`;
}

function emptyStateHtml(icon, title, text) {
  return `<div class="empty-state"><i class="bi ${icon}"></i><h3>${esc(title)}</h3><p>${esc(text)}</p></div>`;
}