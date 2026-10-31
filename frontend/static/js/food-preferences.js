"use strict";

const foodForm = document.getElementById("food-form");
if (foodForm) {
  const message = document.getElementById("food-message");
  const fields = document.getElementById("food-fields");
  const status = foodForm.elements.allergy_status;
  const allergies = foodForm.elements.allergies;
  const allergyGroup = document.getElementById("allergy-group");
  const rows = document.getElementById("meal-rows");
  const add = document.getElementById("add-meal");
  const submit = foodForm.querySelector('button[type="submit"]');
  const maximum = Number(rows.dataset.maxMeals);
  let nextMealId = rows.children.length;
  function clearFeedback() {
    const notice = document.getElementById("food-saved-notice");
    if (notice) notice.hidden = true;
    message.textContent = "";
  }
  function updateAllergyFields() {
    const listed = status.value === "listed";
    allergyGroup.hidden = !listed;
    allergies.disabled = !listed || fields.disabled;
    allergies.required = listed;
  }
  function updateMealControls() {
    [...rows.children].forEach((row, index) => {
      row.querySelector("label").textContent = `Meal time ${index + 1}`;
      const remove = row.querySelector("button");
      remove.disabled = rows.children.length === 1;
      remove.setAttribute("aria-label", `Remove meal time ${index + 1}`);
    });
    add.disabled = rows.children.length >= maximum;
  }
  foodForm.addEventListener("input", clearFeedback);
  status.addEventListener("change", updateAllergyFields);
  rows.addEventListener("click", event => {
    const remove = event.target.closest("[data-remove-meal]");
    if (!remove || fields.disabled || rows.children.length <= 1) return;
    const row = remove.closest("[data-meal-row]");
    row.remove();
    updateMealControls();
    clearFeedback();
    add.focus();
  });
  add.addEventListener("click", () => {
    if (fields.disabled || rows.children.length >= maximum) return;
    const row = document.createElement("div");
    row.className = "meal-row";
    row.dataset.mealRow = "";
    const group = document.createElement("div");
    const input = document.createElement("input");
    input.type = "time";
    input.name = "meal_time";
    input.id = `meal-${nextMealId++}`;
    input.required = true;
    input.step = "60";
    const label = document.createElement("label");
    label.htmlFor = input.id;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "remove-meal";
    remove.dataset.removeMeal = "";
    remove.textContent = "Remove";
    group.append(label, input);
    row.append(group, remove);
    rows.append(row);
    updateMealControls();
    clearFeedback();
    input.focus();
  });
  updateAllergyFields();
  updateMealControls();
  foodForm.addEventListener("submit", async event => {
    event.preventDefault();
    if (submit.disabled) return;
    const values = {
      diet: foodForm.elements.diet.value,
      allergy_status: status.value,
      allergies: status.value === "listed" ? allergies.value.split(/\r?\n/).map(name => name.trim()).filter(Boolean) : [],
      budget_level: foodForm.elements.budget_level.value,
      prep_minutes: Number(foodForm.elements.prep_minutes.value),
      meal_times: [...rows.querySelectorAll('input[name="meal_time"]')].map(input => input.value),
    };
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    fields.disabled = true;
    submit.disabled = true;
    foodForm.setAttribute("aria-busy", "true");
    message.textContent = "Saving your food preferences…";
    try {
      const response = await fetch(foodForm.action, {
        method: "PUT", credentials: "same-origin", headers: {"Content-Type": "application/json"},
        body: JSON.stringify(values), signal: controller.signal,
      });
      const result = await response.json();
      if (!response.ok) {
        message.textContent = response.status === 401 ? "Your session expired. Sign in again before saving."
          : (typeof result.detail === "string" ? result.detail : "The preferences could not be saved.");
        return;
      }
      window.location.assign("/food-preferences?saved=1");
    } catch (error) {
      message.textContent = error.name === "AbortError" ? "The request timed out. Try again."
        : "Could not reach TrainAI. Check the connection and try again.";
    } finally {
      clearTimeout(timeout);
      fields.disabled = false;
      submit.disabled = false;
      foodForm.removeAttribute("aria-busy");
      updateAllergyFields();
      updateMealControls();
    }
  });
}
