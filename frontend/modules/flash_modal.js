document.addEventListener("DOMContentLoaded", () => {
  // Grab any flashed messages from a hidden container rendered server-side.
  // In your index.html (or layout), insert:
  //   <div id="flash-data" data-messages='{{ get_flashed_messages() | tojson }}'></div>
  const flashDataEl = document.getElementById("flash-data");
  if (!flashDataEl) return;

  const messages = JSON.parse(flashDataEl.getAttribute("data-messages") || "[]");
  if (!messages.length) return;

  // Only take the first (or loop if you want multi-step)
  const [category, message] = messages[0]; 

  // Populate the modal
  const overlay = document.getElementById("flash-overlay");
  overlay.querySelector(".flash-content").textContent = message;

  // Optionally style by category:
  overlay.querySelector(".flash-modal")
    .classList.add(`flash-${category}`);

  // Show it
  requestAnimationFrame(() => {
    overlay.classList.add("visible");
  });

  // Setup close handlers
  function hideFlash() {
    overlay.classList.remove("visible");
    // You may also want to clear the data attribute so it doesn't re-trigger
    flashDataEl.removeAttribute("data-messages");
  }

  overlay.querySelector(".flash-close")
         .addEventListener("click", hideFlash);

  overlay.querySelector(".flash-ok-btn")
         .addEventListener("click", hideFlash);
});

export {};
