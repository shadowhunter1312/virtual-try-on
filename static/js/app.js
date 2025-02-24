document.addEventListener("DOMContentLoaded", function () {
  createShadeButtons();
});

function createShadeButtons() {
  const matteShades = ["#4B0000", "#760000", "#A00000", "#C10000", "#5D0000", "#8A0000", "#B60000", "#DA0000", "#752E2E", "#A54545", "#D25E5E", "#FA7474", "#924F4F", "#B76969", "#DC8A8A", "#F5A3A3"];
  const glossyShades = ["#3E0A0A", "#6A1D1D", "#952F2F", "#BF4242", "#4F1A1A", "#7A2C2C", "#A53E3E", "#CF5050", "#663333", "#8F4A4A", "#B86161", "#E17878"];

  const matteContainer = document.getElementById("matte-shades");
  const glossyContainer = document.getElementById("glossy-shades");

  matteContainer.innerHTML = "";
  glossyContainer.innerHTML = "";

  matteShades.forEach(color => {
      const button = createShadeButton(color, "matte");
      matteContainer.appendChild(button);
  });

  glossyShades.forEach(color => {
      const button = createShadeButton(color, "glossy");
      glossyContainer.appendChild(button);
  });
}

function createShadeButton(color, finish) {
  const button = document.createElement("button");
  button.style.backgroundColor = color;
  button.classList.add("shade-btn", finish);
  button.addEventListener("click", () => applyShade(color, finish));
  return button;
}

function applyShade(color, finish) {
  fetch("/apply_makeup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ shade: color, finish: finish }) // Send finish type
  })
  .then(response => response.json())
  .then(data => console.log("💄 Makeup applied:", data))
  .catch(error => console.error("❌ Error:", error));

  updateLipstickEffect(finish);
}


function updateLipstickEffect(finish) {
  const cameraFeed = document.getElementById("camera-feed");

  if (finish === "matte") {
      cameraFeed.style.filter = "contrast(110%) brightness(90%)";
  } else if (finish === "glossy") {
      cameraFeed.style.filter = "contrast(100%) brightness(100%) drop-shadow(0px 0px 15px rgba(255,255,255,0.3))";
  }
}

