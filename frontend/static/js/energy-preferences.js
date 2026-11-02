"use strict";

const energyForm = document.getElementById("energy-form");
if (energyForm) {
  const message = document.getElementById("energy-message");
  const fields = document.getElementById("energy-fields");
  const button = energyForm.querySelector('button[type="submit"]');
  energyForm.addEventListener("input", () => {
    const notice = document.getElementById("energy-saved-notice");
    if (notice) notice.hidden = true;
    document.getElementById("energy-result").hidden = true;
    message.textContent = "";
  });
  energyForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (button.disabled) return;
    const values = {
      equation_sex: energyForm.elements.equation_sex.value,
      activity_category: energyForm.elements.activity_category.value,
      context: energyForm.elements.context.value,
    };
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    document.getElementById("energy-result").hidden = true;
    fields.disabled = true;
    button.disabled = true;
    energyForm.setAttribute("aria-busy", "true");
    message.textContent = "Saving your energy preferences…";
    try {
      const response = await fetch(energyForm.action, {
        method: "PUT", credentials: "same-origin", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values), signal: controller.signal,
      });
      const result = await response.json();
      if (!response.ok) {
        message.textContent = response.status === 401 ? "Your session expired. Sign in again before saving."
          : (typeof result.detail === "string" ? result.detail : "The preferences could not be saved.");
        return;
      }
      window.location.assign("/energy-preferences?saved=1");
    } catch (error) {
      message.textContent = error.name === "AbortError" ? "The request timed out. Try again."
        : "Could not reach TrainAI. Check the connection and try again.";
    } finally {
      clearTimeout(timeout);
      fields.disabled = false;
      button.disabled = false;
      energyForm.removeAttribute("aria-busy");
    }
  });
}
