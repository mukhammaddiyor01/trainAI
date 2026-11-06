"use strict";

const movementForm = document.getElementById("movement-form");
if (movementForm) {
  const message = document.getElementById("movement-message");
  const fields = document.getElementById("movement-fields");
  const button = movementForm.querySelector('button[type="submit"]');
  movementForm.addEventListener("change", () => {
    const notice = document.getElementById("movement-saved-notice");
    if (notice) notice.hidden = true;
    message.textContent = "";
  });
  movementForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (button.disabled) return;
    const selected = movementForm.querySelector('input[name="status"]:checked');
    if (!selected) {
      message.textContent = "Choose one answer before saving.";
      return;
    }
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    fields.disabled = true;
    movementForm.setAttribute("aria-busy", "true");
    message.textContent = "Saving your movement answer…";
    try {
      const response = await fetch(movementForm.action, {
        method: "PUT", credentials: "same-origin", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: selected.value }), signal: controller.signal,
      });
      const result = await response.json();
      if (!response.ok) {
        message.textContent = response.status === 401 ? "Your session expired. Sign in again before saving."
          : (typeof result.detail === "string" ? result.detail : "The answer could not be saved.");
        return;
      }
      window.location.assign("/movement-limitations?saved=1");
    } catch (error) {
      message.textContent = error.name === "AbortError" ? "The request timed out. Reload to check whether your answer was saved."
        : "Could not reach TrainAI. Reload to check whether your answer was saved.";
    } finally {
      clearTimeout(timeout);
      fields.disabled = false;
      movementForm.removeAttribute("aria-busy");
    }
  });
}
