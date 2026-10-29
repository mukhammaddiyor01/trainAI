"use strict";

const form = document.querySelector("form[data-auth], form[data-logout]");

if (form) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = form.querySelector("button[type=submit]");
    if (button.disabled) return;
    const message = document.getElementById("form-message");
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    const options = {
      method: "POST",
      credentials: "same-origin",
      signal: controller.signal,
    };
    const isLogout = form.hasAttribute("data-logout");
    if (!isLogout) {
      options.headers = { "Content-Type": "application/json" };
      options.body = JSON.stringify({
        username: form.elements.username.value,
        password: form.elements.password.value,
      });
      form.elements.password.value = "";
    }
    button.disabled = true;
    form.setAttribute("aria-busy", "true");
    message.textContent = isLogout ? "Signing out…" : "Checking your account…";
    try {
      const response = await fetch(form.action, options);
      if (!response.ok) {
        const result = await response.json();
        message.textContent = typeof result.detail === "string"
          ? result.detail : "The request could not be completed. Try again.";
        return;
      }
      if (isLogout) window.location.assign("/login");
      else if (form.dataset.auth === "register") window.location.assign("/login?created=1");
      else window.location.assign("/account");
    } catch (error) {
      message.textContent = error.name === "AbortError"
        ? "The request timed out. Try again."
        : "Could not reach TrainAI. Check the connection and try again.";
    } finally {
      clearTimeout(timeout);
      button.disabled = false;
      form.removeAttribute("aria-busy");
    }
  });
}
