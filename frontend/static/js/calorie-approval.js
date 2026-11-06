"use strict";

const approveButton = document.getElementById("approve-proposal");
if (approveButton) {
  const message = document.getElementById("approval-message");
  approveButton.addEventListener("click", async () => {
    if (approveButton.disabled) return;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    approveButton.disabled = true;
    message.textContent = "Approving your calorie target…";
    try {
      const proposalId = encodeURIComponent(approveButton.dataset.proposalId);
      const response = await fetch(`/api/calorie-proposals/${proposalId}/approve`, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirm: true }),
        signal: controller.signal,
      });
      const data = await response.json();
      if (!response.ok) {
        message.textContent = response.status === 401
          ? "Your session expired. Sign in again before approving."
          : response.status === 409
            ? "Your inputs or active target changed. Create a new preview and save a new proposal."
            : (typeof data.detail === "string" ? data.detail : "The target could not be approved.");
        return;
      }
      window.location.reload();
    } catch (error) {
      message.textContent = "The request status is uncertain. Reload this page to check whether approval succeeded.";
    } finally {
      clearTimeout(timeout);
      approveButton.disabled = false;
    }
  });
}
