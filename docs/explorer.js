const CSV_URL = "content/data/current_data.csv";

// Change this to the actual categorical column in your CSV.
// Examples: "soil_order", "county", "crop", "site_id"
const CATEGORY_COLUMN = "category";

const categoryFilter = document.getElementById("categoryFilter");
const xSelect = document.getElementById("xSelect");
const ySelect = document.getElementById("ySelect");
const minYInput = document.getElementById("minY");
const maxYInput = document.getElementById("maxY");
const resetBtn = document.getElementById("resetBtn");

let rows = [];
let numericColumns = [];

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

  // Category options
  const categories = [...new Set(rows.map(row => row[CATEGORY_COLUMN]))]
    .filter(value => value !== null && value !== "")
    .sort();

  categories.forEach(value => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    categoryFilter.append(option);
  });

  // Numeric X/Y options
  numericColumns.forEach(column => {
    [xSelect, ySelect].forEach(select => {
      const option = document.createElement("option");
      option.value = column;
      option.textContent = column;
      select.append(option);
    });
  });

  xSelect.value = numericColumns[0] ?? "";
  ySelect.value = numericColumns[1] ?? numericColumns[0] ?? "";

  [
    categoryFilter,
    xSelect,
    ySelect,
    minYInput,
    maxYInput
  ].forEach(element => {
    element.addEventListener("input", updateExplorer);
    element.addEventListener("change", updateExplorer);
  });

  resetBtn.addEventListener("click", () => {
    categoryFilter.value = "";
    minYInput.value = "";
    maxYInput.value = "";
    updateExplorer();
  });
}

function getFilteredRows() {
  const selectedCategory = categoryFilter.value;
  const yColumn = ySelect.value;
  const minY = parseFloat(minYInput.value);
  const maxY = parseFloat(maxYInput.value);

  return rows.filter(row => {
    if (
      selectedCategory &&
      String(row[CATEGORY_COLUMN]) !== selectedCategory
    ) {
      return false;
    }

    const yValue = Number(row[yColumn]);

    if (!Number.isNaN(minY) && yValue < minY) return false;
    if (!Number.isNaN(maxY) && yValue > maxY) return false;

    return true;
  });
}

function updateExplorer() {
  const filteredRows = getFilteredRows();
  renderPlot(filteredRows);
  renderTable(filteredRows);
}

function renderPlot(data) {
  const xColumn = xSelect.value;
  const yColumn = ySelect.value;

  const trace = {
    x: data.map(row => row[xColumn]),
    y: data.map(row => row[yColumn]),
    text: data.map(row => JSON.stringify(row)),
    mode: "markers",
    type: "scattergl",
    marker: {
      size: 7,
      opacity: 0.8,
      color: data.map(row => row[CATEGORY_COLUMN]),
      colorscale: "Viridis"
    },
    hovertemplate: "%{text}<extra></extra>"
  };

  const layout = {
    margin: { t: 30, r: 20, b: 50, l: 60 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    font: { color: "inherit" },
    xaxis: {
      title: xColumn,
      gridcolor: "rgba(255,255,255,0.15)"
    },
    yaxis: {
      title: yColumn,
      gridcolor: "rgba(255,255,255,0.15)"
    },
    showlegend: false
  };

  Plotly.react("plot", [trace], layout, {
    responsive: true,
    displayModeBar: true
  });
}

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