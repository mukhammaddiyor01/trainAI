"use strict";

const sleepForm = document.getElementById("sleep-form");
if (sleepForm) {
  const dateInput = sleepForm.elements.local_date;
  const hoursInput = sleepForm.elements.sleep_hours;
  const minutesInput = sleepForm.elements.sleep_minutes;
  const message = document.getElementById("sleep-message");
  const fields = sleepForm.querySelector("fieldset");
  sleepForm.addEventListener("input", () => { message.textContent = ""; });
  document.querySelectorAll(".edit-sleep").forEach((button) => {
    button.addEventListener("click", () => {
      const total = Number(button.dataset.minutes);
      dateInput.value = button.dataset.date;
      hoursInput.value = Math.floor(total / 60);
      minutesInput.value = total % 60;
      message.textContent = "Correcting the observation for " + button.dataset.date + ".";
      hoursInput.focus();
    });
  });
  sleepForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!sleepForm.reportValidity() || fields.disabled) return;
    const hours = Number(hoursInput.value);
    const minutes = Number(minutesInput.value);
    const total = hours * 60 + minutes;
    if (!Number.isInteger(hours) || !Number.isInteger(minutes) ||
        hours < 0 || hours > 24 || minutes < 0 || minutes > 59 || total > 1440) {
      message.textContent = "Enter a total of 0 to 24 hours.";
      return;
    }
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    fields.disabled = true;
    sleepForm.setAttribute("aria-busy", "true");
    message.textContent = "Saving sleep observation…";
    try {
      const response = await fetch(sleepForm.action, {
        method: "PUT", credentials: "same-origin", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ local_date: dateInput.value, sleep_minutes: total }), signal: controller.signal,
      });
      const result = await response.json();
      if (!response.ok) {
        message.textContent = response.status === 401 ? "Your session expired. Sign in again before saving."
          : (typeof result.detail === "string" ? result.detail : "The observation could not be saved.");
        return;
      }
      window.location.assign("/sleep-log?saved=1");
    } catch (error) {
      message.textContent = error.name === "AbortError" ? "The request timed out. Try again."
        : "Could not reach TrainAI. Check the connection and try again.";
    } finally {
      clearTimeout(timeout);
      fields.disabled = false;
      sleepForm.removeAttribute("aria-busy");
    }
  });
}
