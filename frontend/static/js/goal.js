"use strict";

const goalForm = document.getElementById("goal-form");
if (goalForm) {
  const direction = goalForm.elements.direction;
  const target = goalForm.elements.target_weight_kg;
  const targetGroup = document.getElementById("target-group");
  const message = document.getElementById("goal-message");
  goalForm.addEventListener("input", () => {
    const savedNotice = document.getElementById("goal-saved-notice");
    if (savedNotice) savedNotice.hidden = true;
    message.textContent = "";
  });
  function updateTargetField() {
    const needsTarget = direction.value === "gain" || direction.value === "lose";
    targetGroup.hidden = !needsTarget;
    target.disabled = !needsTarget;
    target.required = needsTarget;
    if (!needsTarget) target.value = "";
  }
  direction.addEventListener("change", updateTargetField);
  updateTargetField();
  goalForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = goalForm.querySelector("button[type=submit]");
    if (button.disabled) return;
    const values = { direction: direction.value, target_weight_kg: direction.value === "maintain" ? null : Number(target.value) };
    const fields = goalForm.querySelector("fieldset");
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    fields.disabled = true;
    button.disabled = true;
    goalForm.setAttribute("aria-busy", "true");
    message.textContent = "Saving your goal…";
    try {
      const response = await fetch(goalForm.action, {
        method: "PUT", credentials: "same-origin", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values), signal: controller.signal,
      });
      const result = await response.json();
      if (!response.ok) {
        message.textContent = response.status === 401 ? "Your session expired. Sign in again before saving."
          : (typeof result.detail === "string" ? result.detail : "The goal could not be saved.");
        return;
      }
      window.location.assign("/goal?saved=1");
    } catch (error) {
      message.textContent = error.name === "AbortError" ? "The request timed out. Try again."
        : "Could not reach TrainAI. Check the connection and try again.";
    } finally {
      clearTimeout(timeout);
      fields.disabled = false;
      button.disabled = false;
      goalForm.removeAttribute("aria-busy");
      updateTargetField();
    }
  });
}
