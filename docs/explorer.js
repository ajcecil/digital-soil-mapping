// ============================================================
// CALS Soil Data Explorer
// ============================================================

const CSV_URL = "content/data/current_data.csv";

// Change this to the actual categorical column in your CSV.
// Examples: "soil_order", "county", "crop", "site_id"
const CATEGORY_COLUMN = "Farm Group";

// Color palette used for unique values in the selected split column.
const BAR_COLORS = [
  "#C8102E", // Pantone 186C - Primary
  "#F1BE48", // Pantone 142C - Primary
  "#3E4827", // Pantone 5743C - Secondary
  "#76881D", // Pantone 7496C - Secondary
  "#A2A569", // Pantone 5777C - Secondary
  "#003D4C", // Pantone 5548C - Secondary
  "#006BA6",  // Pantone 307C - Secondary
  "#7A99AC", // Pantone 5425C - Secondary
  "#7C2529", // Pantone 1815C - Secondary
  "#9A3324", // Pantone 484C - Secondary
  "#BE531C", // Pantone 167C - Secondary
  "#524727", // Pantone 449C - Primary - Neutral
  "#9B945F", // Pantone 451C - Primary - Neutral
  "#CAC7A7", // Pantone 454C - Primary - Neutral
  "#8B5B29", // Pantone 464C - Secondary - Neutral
  "#B9975B", // Pantone 465C - Secondary - Neutral
  "#EED484", // Pantone 7403C - Secondary - Neutral
  "#6E6259", // Pantone Warm Grey 11C - Secondary - Neutral
  "#707372", // Pantone 424C - Secondary - Neutral
  "#ACA39A", // Pantone Warm Grey 5C - Secondary - Neutral
];

const DEFAULT_COLOR = "#7f7f7f";

// DOM elements
const categoryFilter = document.getElementById("categoryFilter");
const splitSelect = document.getElementById("splitSelect");
const ySelect = document.getElementById("ySelect");
const minYInput = document.getElementById("minY");
const maxYInput = document.getElementById("maxY");
const resetBtn = document.getElementById("resetBtn");

// Data
let rows = [];
let numericColumns = [];
let categoricalColumns = [];

// Maps each unique value in the selected split column to a color.
let splitColumnColorMap = new Map();

// ============================================================
// Load CSV
// ============================================================

Papa.parse(CSV_URL, {
  download: true,
  header: true,
  dynamicTyping: true,
  skipEmptyLines: true,
  complete: function (results) {
    rows = results.data;
    setupExplorer();
    updateExplorer();
  },
  error: function (error) {
    console.error("Failed to load CSV:", error);
  }
});

// ============================================================
// Setup controls
// ============================================================

function isNumericColumn(column) {
  return rows.every(row => {
    const value = row[column];
    return value === null || value === "" || typeof value === "number";
  });
}

function setupExplorer() {
  if (!rows.length) return;

  const columns = Object.keys(rows[0]);

  numericColumns = columns.filter(isNumericColumn);
  categoricalColumns = columns.filter(
    column => !numericColumns.includes(column)
  );

  // Category filter
  const categories = [...new Set(rows.map(row => row[CATEGORY_COLUMN]))]
    .filter(value => value !== null && value !== undefined && value !== "")
    .sort();

  categories.forEach(value => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    categoryFilter.append(option);
  });

  // Split-by filter
  categoricalColumns.forEach(column => {
    const option = document.createElement("option");
    option.value = column;
    option.textContent = column;
    splitSelect.append(option);
  });

  // Numeric Y variable selector
  numericColumns.forEach(column => {
    const option = document.createElement("option");
    option.value = column;
    option.textContent = column;
    ySelect.append(option);
  });

  splitSelect.value = categoricalColumns[0] ?? "";
  ySelect.value = numericColumns[0] ?? "";

  buildSplitColumnColorMap();

  // Attach update events
  [
    categoryFilter,
    splitSelect,
    ySelect,
    minYInput,
    maxYInput
  ].forEach(element => {
    element.addEventListener("input", updateExplorer);
    element.addEventListener("change", updateExplorer);
  });

  // Rebuild stable colors only when the split column changes
  splitSelect.addEventListener("change", () => {
    buildSplitColumnColorMap();
    updateExplorer();
  });

  resetBtn.addEventListener("click", () => {
    categoryFilter.value = "";
    minYInput.value = "";
    maxYInput.value = "";
    updateExplorer();
  });
}

// ============================================================
// Stable colors for split-column values
// ============================================================

function buildSplitColumnColorMap() {
  splitColumnColorMap = new Map();

  const selectedSplitColumn = splitSelect.value;

  if (!selectedSplitColumn) return;

  const uniqueValues = [
    ...new Set(rows.map(row => row[selectedSplitColumn]))
  ]
    .filter(value => value !== null && value !== undefined && value !== "")
    .sort();

  uniqueValues.forEach((value, index) => {
    splitColumnColorMap.set(
      String(value),
      BAR_COLORS[index % BAR_COLORS.length]
    );
  });
}

// ============================================================
// Filtering
// ============================================================

function getFilteredRows() {
  const selectedCategory = categoryFilter.value;
  const yColumn = ySelect.value;
  const minY = parseFloat(minYInput.value);
  const maxY = parseFloat(maxYInput.value);

  return rows.filter(row => {
    // First filter: category column
    if (
      selectedCategory &&
      String(row[CATEGORY_COLUMN]) !== selectedCategory
    ) {
      return false;
    }

    // Min/max filters apply to the selected numeric Y column
    const yValue = Number(row[yColumn]);

    if (!Number.isNaN(minY) && yValue < minY) return false;
    if (!Number.isNaN(maxY) && yValue > maxY) return false;

    return true;
  });
}

// ============================================================
// Aggregation
// ============================================================

function calculateGroupSummary(data, splitColumn, yColumn) {
  const groups = new Map();

  data.forEach(row => {
    const rawGroupValue = row[splitColumn];

    const groupValue =
      rawGroupValue === null ||
      rawGroupValue === undefined ||
      rawGroupValue === ""
        ? "Missing"
        : String(rawGroupValue);

    const yValue = Number(row[yColumn]);

    if (!groups.has(groupValue)) {
      groups.set(groupValue, {
        sum: 0,
        rowCount: 0,
        validCount: 0
      });
    }

    const group = groups.get(groupValue);
    group.rowCount += 1;

    if (!Number.isNaN(yValue)) {
      group.sum += yValue;
      group.validCount += 1;
    }
  });

  return [...groups.entries()]
    .map(([group, values]) => ({
      group,
      mean: values.validCount ? values.sum / values.validCount : null,
      rowCount: values.rowCount,
      validCount: values.validCount
    }))
    .sort((a, b) =>
      a.group.localeCompare(b.group, undefined, {
        numeric: true,
        sensitivity: "base"
      })
    );
}

// ============================================================
// Update page
// ============================================================

function updateExplorer() {
  const filteredRows = getFilteredRows();

  renderPlot(filteredRows);
  renderTable(filteredRows);
}

// ============================================================
// Bar chart
// ============================================================

function renderPlot(data) {
  const splitColumn = splitSelect.value;
  const yColumn = ySelect.value;

  if (!splitColumn || !yColumn) {
    Plotly.react(
      "plot",
      [],
      {
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: { color: "inherit" }
      },
      {
        responsive: true,
        displayModeBar: true
      }
    );
    return;
  }

  const summary = calculateGroupSummary(data, splitColumn, yColumn);

  // One stable color per unique split-column value
  const barColors = summary.map(item =>
    splitColumnColorMap.get(item.group) ?? DEFAULT_COLOR
  );

  const trace = {
    x: summary.map(item => item.group),
    y: summary.map(item => item.mean),
    type: "bar",
    name: `Mean ${yColumn}`,
    marker: {
      color: barColors
    },
    customdata: summary.map(item => [
      item.rowCount,
      item.validCount
    ]),
    hovertemplate:
      `<b>%{x}</b><br>` +
      `Mean ${yColumn}: %{y:.3f}<br>` +
      `Rows: %{customdata[0]}<br>` +
      `Valid values: %{customdata[1]}` +
      `<extra></extra>`
  };

  const layout = {
    margin: {
      t: 30,
      r: 20,
      b: 80,
      l: 70
    },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    font: {
      color: "inherit"
    },
    xaxis: {
      title: splitColumn,
      gridcolor: "rgba(255,255,255,0.15)",
      tickangle: -35
    },
    yaxis: {
      title: `Mean ${yColumn}`,
      gridcolor: "rgba(255,255,255,0.15)"
    },
    bargap: 0.25,
    showlegend: false
  };

  Plotly.react(
    "plot",
    [trace],
    layout,
    {
      responsive: true,
      displayModeBar: true
    }
  );
}

// ============================================================
// Data table
// ============================================================

function renderTable(data) {
  const table = document.getElementById("dataTable");
  const thead = table.querySelector("thead");
  const tbody = table.querySelector("tbody");

  const columns = rows.length ? Object.keys(rows[0]) : [];

  thead.innerHTML =
    "<tr>" +
    columns.map(column => `<th>${column}</th>`).join("") +
    "</tr>";

  tbody.innerHTML = data
    .slice(0, 500)
    .map(row =>
      "<tr>" +
      columns
        .map(column => `<td>${row[column] ?? ""}</td>`)
        .join("") +
      "</tr>"
    )
    .join("");
}