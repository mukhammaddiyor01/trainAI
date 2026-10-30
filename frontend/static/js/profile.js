"use strict";

const profileForm = document.getElementById("profile-form");
if (profileForm) {
  profileForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = profileForm.querySelector("button[type=submit]");
    if (button.disabled) return;
    const message = document.getElementById("profile-message");
    const fields = profileForm.querySelector("fieldset");
    const data = {
      age: Number(profileForm.elements.age.value),
      height_cm: Number(profileForm.elements.height_cm.value),
      weight_kg: Number(profileForm.elements.weight_kg.value),
      timezone: profileForm.elements.timezone.value,
    };
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    fields.disabled = true;
    button.disabled = true;
    profileForm.setAttribute("aria-busy", "true");
    message.classList.remove("success");
    message.textContent = "Saving your basic profile…";
    try {
      const response = await fetch(profileForm.action, {
        method: "PUT", credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data), signal: controller.signal,
      });
      const result = await response.json();
      if (!response.ok) {
        message.textContent = response.status === 401
          ? "Your session expired. Sign in again before saving."
          : (typeof result.detail === "string" ? result.detail : "The profile could not be saved.");
        return;
      }
      message.classList.add("success");
      message.textContent = "Basic profile saved. You can now set your goal.";
      const next = document.getElementById("goal-next");
      if (next) next.hidden = false;
    } catch (error) {
      message.textContent = error.name === "AbortError"
        ? "The request timed out. Try again."
        : "Could not reach TrainAI. Check the connection and try again.";
    } finally {
      clearTimeout(timeout);
      fields.disabled = false;
      button.disabled = false;
      profileForm.removeAttribute("aria-busy");
    }
  });
}
