(() => {
  "use strict";

  const RETRY_DELAYS = [0, 80, 250, 650, 1400, 2800];

  function closestPanel(element) {
    return element ? element.closest(".panel") : null;
  }

  function uniquePanels(panels) {
    const seen = new Set();
    return panels.filter((panel) => {
      if (!panel || seen.has(panel)) return false;
      seen.add(panel);
      return true;
    });
  }

  function arrangeSettings() {
    const page = document.getElementById("settingsPage");
    const grid = page?.querySelector(".settings-grid");
    if (!page || !grid) return false;

    const dangerPanel = page.querySelector(".danger-panel");

    const preferredOrder = uniquePanels([
      page.querySelector(".language-settings-panel"),
      closestPanel(page.querySelector("#settingsChooseCvBtn")),
      closestPanel(page.querySelector("#backupBtn")),
      page.querySelector("#dataLocationsPanel"),
      page.querySelector(".notification-settings-panel"),
      page.querySelector(".capture-settings-panel"),
      page.querySelector("#jamUpdateSettingsCard")
    ]).filter((panel) => panel !== dangerPanel);

    const everyOtherPanel = [...page.querySelectorAll(".panel")].filter(
      (panel) => panel !== dangerPanel && !preferredOrder.includes(panel)
    );

    const orderedPanels = [...preferredOrder, ...everyOtherPanel];
    if (!orderedPanels.length) return false;

    let unifiedPanel = grid.querySelector(":scope > .settings-unified-panel");
    if (!unifiedPanel) {
      unifiedPanel = document.createElement("div");
      unifiedPanel.className = "settings-unified-panel";
      unifiedPanel.setAttribute("data-settings-unified", "true");
    }

    orderedPanels.forEach((panel) => {
      panel.classList.add("settings-section-block");
      unifiedPanel.appendChild(panel);
    });

    if (dangerPanel) {
      dangerPanel.classList.remove("settings-section-block");
      grid.replaceChildren(unifiedPanel, dangerPanel);
    } else {
      grid.replaceChildren(unifiedPanel);
    }

    return true;
  }

  function scheduleArrange() {
    RETRY_DELAYS.forEach((delay) => {
      window.setTimeout(arrangeSettings, delay);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", scheduleArrange, { once: true });
  } else {
    scheduleArrange();
  }

  document.addEventListener("click", (event) => {
    const settingsButton = event.target.closest('[data-page="settings"]');
    if (settingsButton) {
      window.setTimeout(arrangeSettings, 0);
      window.setTimeout(arrangeSettings, 180);
    }
  });
})();
