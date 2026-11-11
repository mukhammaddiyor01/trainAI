"use strict";

const weightForm = document.getElementById("weight-form");
if (weightForm) {
  const dateInput = weightForm.elements.local_date;
  const weightInput = weightForm.elements.weight_kg;
  const message = document.getElementById("weight-message");
  const fields = weightForm.querySelector("fieldset");
  weightForm.addEventListener("input", () => { message.textContent = ""; });
  document.querySelectorAll(".edit-entry").forEach((button) => {
    button.addEventListener("click", () => {
      dateInput.value = button.dataset.date;
      weightInput.value = button.dataset.weight;
      message.textContent = "Correcting the observation for " + button.dataset.date + ".";
      weightInput.focus();
    });
  });
  weightForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!weightForm.reportValidity() || fields.disabled) return;
    const weight = Number(weightInput.value);
    if (!Number.isFinite(weight) || weight < 20 || weight > 500) {
      message.textContent = "Enter a weight from 20 to 500 kg.";
      return;
    }
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    fields.disabled = true;
    weightForm.setAttribute("aria-busy", "true");
    message.textContent = "Saving observation…";
    try {
      const response = await fetch(weightForm.action, {
        method: "PUT", credentials: "same-origin", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ local_date: dateInput.value, weight_kg: weight }), signal: controller.signal,
      });
      const result = await response.json();
      if (!response.ok) {
        message.textContent = response.status === 401 ? "Your session expired. Sign in again before saving."
          : (typeof result.detail === "string" ? result.detail : "The observation could not be saved.");
        return;
      }
      window.location.assign("/weight-log?saved=1");
    } catch (error) {
      message.textContent = error.name === "AbortError" ? "The request timed out. Try again."
        : "Could not reach TrainAI. Check the connection and try again.";
    } finally {
      clearTimeout(timeout);
      fields.disabled = false;
      weightForm.removeAttribute("aria-busy");
    }
  });
}
