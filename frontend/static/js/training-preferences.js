"use strict";

const trainingForm = document.getElementById("training-form");
if (trainingForm) {
  const message = document.getElementById("training-message");
  const fields = document.getElementById("training-fields");
  const dayInputs = [...trainingForm.querySelectorAll('input[name="weekdays"]')];
  const button = trainingForm.querySelector('button[type="submit"]');
  trainingForm.addEventListener("input", () => {
    const notice = document.getElementById("training-saved-notice");
    if (notice) notice.hidden = true;
    dayInputs[0].setCustomValidity("");
    message.textContent = "";
  });
  trainingForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (button.disabled) return;
    const weekdays = dayInputs.filter(input => input.checked).map(input => Number(input.value));
    if (weekdays.length === 0) {
      dayInputs[0].setCustomValidity("Choose at least one available day.");
      dayInputs[0].reportValidity();
      message.textContent = "Choose at least one available day.";
      return;
    }
    const values = {
      experience: trainingForm.elements.experience.value,
      activity: trainingForm.elements.activity.value,
      weekdays,
      session_minutes: Number(trainingForm.elements.session_minutes.value),
      equipment: [...trainingForm.querySelectorAll('input[name="equipment"]:checked')].map(input => input.value),
    };
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    fields.disabled = true;
    button.disabled = true;
    trainingForm.setAttribute("aria-busy", "true");
    message.textContent = "Saving your training preferences…";
    try {
      const response = await fetch(trainingForm.action, {
        method: "PUT", credentials: "same-origin", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values), signal: controller.signal,
      });
      const result = await response.json();
      if (!response.ok) {
        message.textContent = response.status === 401 ? "Your session expired. Sign in again before saving."
          : (typeof result.detail === "string" ? result.detail : "The preferences could not be saved.");
        return;
      }
      window.location.assign("/training-preferences?saved=1");
    } catch (error) {
      message.textContent = error.name === "AbortError" ? "The request timed out. Try again."
        : "Could not reach TrainAI. Check the connection and try again.";
    } finally {
      clearTimeout(timeout);
      fields.disabled = false;
      button.disabled = false;
      trainingForm.removeAttribute("aria-busy");
    }
  });
}
