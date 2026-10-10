/* Dashboard charts. All values come from the server-rendered JSON block. */
(function () {
  "use strict";

  var source = document.getElementById("chart-data");
  if (!source || typeof Chart === "undefined") { return; }

  var data;
  try {
    data = JSON.parse(source.textContent);
  } catch (err) {
    return;
  }

  var ACCENT = "#1f5fbf";
  var TEAL = "#17806d";
  var TEXT = "#3f4a57";
  var GRID = "#e3e8ee";

  Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;
  Chart.defaults.color = TEXT;

  function bar(canvasId, series, color, horizontal) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) { return; }
    var countAxis = {
      beginAtZero: true,
      ticks: { precision: 0 },
      grid: { color: GRID },
      title: { display: true, text: "Students" }
    };
    var labelAxis = { grid: { display: false } };

    new Chart(canvas, {
      type: "bar",
      data: {
        labels: series.labels,
        datasets: [{
          label: "Students",
          data: series.values,
          backgroundColor: color,
          borderRadius: 3,
          maxBarThickness: 44
        }]
      },
      options: {
        indexAxis: horizontal ? "y" : "x",
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: horizontal ? { x: countAxis, y: labelAxis } : { x: labelAxis, y: countAxis }
      }
    });
  }

  bar("chart-course", data.course, ACCENT, false);
  bar("chart-department", data.department, ACCENT, true);
  bar("chart-semester", data.semester, ACCENT, false);
  bar("chart-bands", data.bands, TEAL, false);
})();
