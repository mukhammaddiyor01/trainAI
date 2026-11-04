"use strict";

const previewForm = document.getElementById("calorie-preview-form");
if (previewForm) {
  const input = previewForm.elements.adjustment_kcal;
  const fields = document.getElementById("preview-fields");
  const message = document.getElementById("preview-message");
  const resultPanel = document.getElementById("preview-result");
  const button = previewForm.querySelector('button[type="submit"]');
  const saveButton = document.getElementById("save-proposal");
  let previewedAmount = null;
  const kcal = (value) => `${Math.round(value).toLocaleString("en-US")} kcal/day`;

  input.addEventListener("input", () => {
    previewedAmount = null;
    resultPanel.hidden = true;
    previewedAmount = null;
    message.classList.remove("success");
    message.textContent = "";
  });

  previewForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (button.disabled) return;
    const raw = input.value.trim();
    const amount = Number(raw);
    const direction = previewForm.dataset.direction;
    resultPanel.hidden = true;
    message.classList.remove("success");
    if (!/^\d+$/.test(raw) || !Number.isInteger(amount) || amount > 250 ||
        (direction === "maintain" ? amount !== 0 : amount < 1)) {
      message.textContent = direction === "maintain"
        ? "Enter 0 explicitly for a maintenance preview."
        : "Enter a whole number from 1 to 250 kcal/day.";
      return;
    }
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    fields.disabled = true;
    previewForm.setAttribute("aria-busy", "true");
    message.textContent = "Calculating your preview…";
    try {
      const response = await fetch(previewForm.action, {
        method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ adjustment_kcal: amount }), signal: controller.signal,
      });
      const data = await response.json();
      if (!response.ok) {
        message.textContent = response.status === 401 ? "Your session expired. Sign in again before previewing."
          : (typeof data.detail === "string" ? data.detail : "The preview could not be calculated.");
        return;
      }
      document.getElementById("preview-value").textContent = kcal(data.preview_kcal_per_day);
      document.getElementById("preview-maintenance").textContent = kcal(data.maintenance_kcal_per_day);
      document.getElementById("preview-adjustment").textContent = `${data.adjustment_kcal_per_day > 0 ? "+" : ""}${data.adjustment_kcal_per_day} kcal/day`;
      document.getElementById("preview-direction").textContent = data.goal_direction;
      document.getElementById("preview-method").textContent = data.energy_method_version;
      document.getElementById("preview-policy").textContent = data.policy_version;
      resultPanel.hidden = false;
      previewedAmount = amount;
      message.classList.add("success");
      message.textContent = "Preview calculated. No target or plan was saved.";
    } catch (error) {
      message.textContent = error.name === "AbortError" ? "The request timed out. Try again."
        : "Could not reach TrainAI. Check the connection and try again.";
    } finally {
      clearTimeout(timeout);
      fields.disabled = false;
      previewForm.removeAttribute("aria-busy");
    }
  });

  saveButton.addEventListener("click", async () => {
    if (previewedAmount === null || Number(input.value) !== previewedAmount || saveButton.disabled) return;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    saveButton.disabled = true;
    fields.disabled = true;
    previewForm.setAttribute("aria-busy", "true");
    message.classList.remove("success");
    message.textContent = "Saving your pending proposal…";
    try {
      const response = await fetch("/api/calorie-proposals", {
        method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ adjustment_kcal: previewedAmount }), signal: controller.signal,
      });
      const data = await response.json();
      if (!response.ok) {
        message.textContent = response.status === 401 ? "Your session expired. Sign in again before saving."
          : (typeof data.detail === "string" ? data.detail : "The proposal could not be saved.");
        if (response.status === 409 || response.status === 404) {
          previewedAmount = null;
          resultPanel.hidden = true;
        }
        return;
      }
      window.location.assign(`/calorie-proposals/${encodeURIComponent(data.proposal_id)}`);
    } catch (error) {
      message.textContent = error.name === "AbortError" ? "The save request timed out. It may have succeeded; retrying can create another draft."
        : "Could not reach TrainAI. The request may have succeeded; retrying can create another draft.";
    } finally {
      clearTimeout(timeout);
      saveButton.disabled = false;
      fields.disabled = false;
      previewForm.removeAttribute("aria-busy");
    }
  });
}
