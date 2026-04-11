(function () {
  function setHiddenValue(id, value) {
    var input = document.getElementById(id);
    if (!input) return;
    if (input.value === value) return;
    input.value = value;
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function clampWidth(width) {
    return Math.max(320, Math.min(960, width));
  }

  function applyShellWidth(shell, width) {
    if (!shell) return;
    shell.style.width = width + "px";
    shell.style.flex = "0 0 " + width + "px";
  }

  function wireResizeHandle() {
    var handle = document.getElementById("nb-plots-resize-handle");
    var shell = document.getElementById("notebook-plots-shell");
    if (!handle || !shell || handle.dataset.resizeBound === "true") return;
    handle.dataset.resizeBound = "true";

    handle.addEventListener("mousedown", function (event) {
      event.preventDefault();
      var row = handle.parentElement;
      if (!row) return;
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";

      function onMove(moveEvent) {
        var rowRect = row.getBoundingClientRect();
        var width = clampWidth(Math.round(rowRect.right - moveEvent.clientX));
        applyShellWidth(shell, width);
      }

      function onUp(upEvent) {
        var rowRect = row.getBoundingClientRect();
        var width = clampWidth(Math.round(rowRect.right - upEvent.clientX));
        applyShellWidth(shell, width);
        setHiddenValue("nb-plots-width-input", String(width));
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
        window.removeEventListener("mousemove", onMove);
        window.removeEventListener("mouseup", onUp);
      }

      window.addEventListener("mousemove", onMove);
      window.addEventListener("mouseup", onUp);
    });
  }

  function syncCardOrder(panel) {
    if (!panel) return;
    var order = Array.from(panel.querySelectorAll(".nb-plot-draggable-card[data-card-key]"))
      .map(function (card) { return card.getAttribute("data-card-key"); })
      .filter(Boolean);
    if (order.length) {
      setHiddenValue("nb-plots-order-input", JSON.stringify(order));
    }
  }

  function wireDraggableCards() {
    var panel = document.getElementById("notebook-plots-panel");
    if (!panel) return;

    Array.from(panel.querySelectorAll(".nb-plot-draggable-card[data-card-key]")).forEach(function (card) {
      if (card.dataset.dragBound === "true") return;
      card.dataset.dragBound = "true";

      card.addEventListener("dragstart", function (event) {
        if (!event.target || !event.target.closest(".nb-plot-drag-handle")) {
          event.preventDefault();
          return;
        }
        card.classList.add("nb-plot-card--dragging");
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("text/plain", card.getAttribute("data-card-key") || "");
      });

      card.addEventListener("dragend", function () {
        card.classList.remove("nb-plot-card--dragging");
        panel.querySelectorAll(".nb-plot-card--drop-target").forEach(function (node) {
          node.classList.remove("nb-plot-card--drop-target");
        });
      });

      card.addEventListener("dragover", function (event) {
        event.preventDefault();
        if (!panel.querySelector(".nb-plot-card--dragging")) return;
        card.classList.add("nb-plot-card--drop-target");
      });

      card.addEventListener("dragleave", function () {
        card.classList.remove("nb-plot-card--drop-target");
      });

      card.addEventListener("drop", function (event) {
        event.preventDefault();
        card.classList.remove("nb-plot-card--drop-target");
        var draggedKey = event.dataTransfer.getData("text/plain");
        if (!draggedKey) return;
        var draggedCard = panel.querySelector('.nb-plot-draggable-card[data-card-key="' + draggedKey + '"]');
        if (!draggedCard || draggedCard === card) return;

        var rect = card.getBoundingClientRect();
        var insertAfter = event.clientY > rect.top + rect.height / 2;
        if (insertAfter) {
          panel.insertBefore(draggedCard, card.nextSibling);
        } else {
          panel.insertBefore(draggedCard, card);
        }
        syncCardOrder(panel);
      });
    });
  }

  function syncNotebookItemOrder(panel) {
    if (!panel) return;
    var order = Array.from(panel.querySelectorAll(".nb-notebook-item[data-item-id]"))
      .map(function (card) { return card.getAttribute("data-item-id"); })
      .filter(Boolean);
    if (order.length) {
      setHiddenValue("nb-item-order-input", JSON.stringify(order));
    }
  }

  function clampNotebookItemWidth(card, panel, width) {
    var computed = window.getComputedStyle(card);
    var minWidth = parseInt(computed.minWidth || "320", 10);
    if (!Number.isFinite(minWidth)) minWidth = 320;
    var maxWidth = Math.max(minWidth, Math.floor(panel.clientWidth));
    return Math.max(minWidth, Math.min(maxWidth, Math.round(width)));
  }

  function clampColumnSplit(leftPct) {
    return Math.max(12, Math.min(88, Math.round(leftPct)));
  }

  function wireNotebookColumnSplitter() {
    var splitter = document.getElementById("notebook-columns-splitter");
    var layout = document.getElementById("notebook-columns-layout");
    var leftColumn = document.getElementById("notebook-cells-column-left");
    var rightColumn = document.getElementById("notebook-cells-column-right");
    if (!splitter || !layout || !leftColumn || !rightColumn || splitter.dataset.splitBound === "true") return;
    splitter.dataset.splitBound = "true";

    splitter.addEventListener("mousedown", function (event) {
      event.preventDefault();
      var layoutRect = layout.getBoundingClientRect();
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";

      function applySplit(clientX) {
        var rawLeftPct = ((clientX - layoutRect.left) / Math.max(1, layoutRect.width)) * 100;
        var leftPct = clampColumnSplit(rawLeftPct);
        leftColumn.style.width = leftPct + "%";
        rightColumn.style.width = (100 - leftPct) + "%";
        return leftPct;
      }

      function onMove(moveEvent) {
        applySplit(moveEvent.clientX);
      }

      function onUp(upEvent) {
        var leftPct = applySplit(upEvent.clientX);
        setHiddenValue("nb-column-split-input", JSON.stringify({ left_pct: leftPct }));
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
        window.removeEventListener("mousemove", onMove);
        window.removeEventListener("mouseup", onUp);
      }

      window.addEventListener("mousemove", onMove);
      window.addEventListener("mouseup", onUp);
    });
  }

  function wireNotebookItems() {
    var panels = [
      document.getElementById("notebook-cells-column-left"),
      document.getElementById("notebook-cells-column-right")
    ].filter(Boolean);
    if (!panels.length) return;

    panels.forEach(function (panel) {
      Array.from(panel.querySelectorAll(".nb-notebook-item[data-item-id]")).forEach(function (card) {
      if (card.dataset.dragBound === "true") return;
      card.dataset.dragBound = "true";

      var resizeHandle = card.querySelector(".nb-item-resize-handle");
      if (resizeHandle && resizeHandle.dataset.resizeBound !== "true") {
        resizeHandle.dataset.resizeBound = "true";
        resizeHandle.addEventListener("mousedown", function (event) {
          event.preventDefault();
          event.stopPropagation();
          card.dataset.dragReady = "";
          var cardRect = card.getBoundingClientRect();
          document.body.style.cursor = "ew-resize";
          document.body.style.userSelect = "none";

          function onMove(moveEvent) {
            var width = clampNotebookItemWidth(card, panel, moveEvent.clientX - cardRect.left);
            card.style.width = width + "px";
          }

          function onUp(upEvent) {
            var width = clampNotebookItemWidth(card, panel, upEvent.clientX - cardRect.left);
            card.style.width = width + "px";
            setHiddenValue("nb-item-width-input", JSON.stringify({
              id: card.getAttribute("data-item-id"),
              width: width
            }));
            document.body.style.cursor = "";
            document.body.style.userSelect = "";
            window.removeEventListener("mousemove", onMove);
            window.removeEventListener("mouseup", onUp);
          }

          window.addEventListener("mousemove", onMove);
          window.addEventListener("mouseup", onUp);
        });
      }

      card.addEventListener("mousedown", function (event) {
        card.dataset.dragReady = event.target && event.target.closest(".nb-item-drag-handle") ? "true" : "";
      });

      card.addEventListener("mouseup", function () {
        card.dataset.dragReady = "";
      });

      card.addEventListener("mouseleave", function () {
        card.dataset.dragReady = "";
      });

      card.addEventListener("dragstart", function (event) {
        if (card.dataset.dragReady !== "true") {
          event.preventDefault();
          return;
        }
        card.classList.add("nb-notebook-item--dragging");
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("text/plain", card.getAttribute("data-item-id") || "");
      });

      card.addEventListener("dragend", function () {
        card.dataset.dragReady = "";
        card.classList.remove("nb-notebook-item--dragging");
        panel.querySelectorAll(".nb-notebook-item--drop-target").forEach(function (node) {
          node.classList.remove("nb-notebook-item--drop-target");
        });
      });

      card.addEventListener("dragover", function (event) {
        event.preventDefault();
        if (!panel.querySelector(".nb-notebook-item--dragging")) return;
        card.classList.add("nb-notebook-item--drop-target");
      });

      card.addEventListener("dragleave", function () {
        card.classList.remove("nb-notebook-item--drop-target");
      });

      card.addEventListener("drop", function (event) {
        event.preventDefault();
        card.classList.remove("nb-notebook-item--drop-target");
        var draggedId = event.dataTransfer.getData("text/plain");
        if (!draggedId) return;
        var draggedCard = panel.querySelector('.nb-notebook-item[data-item-id="' + draggedId + '"]');
        if (!draggedCard || draggedCard === card) return;

        var rect = card.getBoundingClientRect();
        var insertAfter = event.clientY > rect.top + rect.height / 2;
        if (insertAfter) {
          panel.insertBefore(draggedCard, card.nextSibling);
        } else {
          panel.insertBefore(draggedCard, card);
        }
        syncNotebookItemOrder(panel);
      });
    });
    });
  }

  function attachNotebookPlotInteractions() {
    wireResizeHandle();
    wireDraggableCards();
    wireNotebookColumnSplitter();
    wireNotebookItems();
  }

  window.addEventListener("load", function () {
    attachNotebookPlotInteractions();
    var observer = new MutationObserver(attachNotebookPlotInteractions);
    observer.observe(document.body, { childList: true, subtree: true });
  });
})();
