document.addEventListener("DOMContentLoaded", function () {
    const dataElement = document.getElementById("benchmark-chart-data");

    if (!dataElement || typeof Plotly === "undefined") {
        console.error("Données du tableau de bord ou Plotly indisponibles.");
        return;
    }

    const data = JSON.parse(dataElement.textContent);

    const labels = data.labels || [];
    const accuracies = data.accuracies || [];
    const passed = data.passed || [];
    const failed = data.failed || [];

    const trajectoryLabels = data.trajectory_labels || [];
    const trajectoryValues = data.trajectory_values || [];

    const layoutBase = {
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: {
            family: "Inter, Segoe UI, Arial, sans-serif",
            color: "#77766f",
            size: 11
        },
        margin: { t: 20, r: 15, b: 45, l: 45 },
        showlegend: false
    };

    const config = {
        responsive: true,
        displayModeBar: false
    };

    const accuracyElement = document.getElementById("accuracyChart");

    if (accuracyElement) {
        Plotly.newPlot(
            accuracyElement,
            [{
                x: labels,
                y: accuracies,
                type: "bar",
                marker: {
                    color: "#a52d32",
                    line: { width: 0 },
                    opacity: 0.9
                },
                text: accuracies.map(value => value + "%"),
                textposition: "outside",
                hovertemplate: "%{x}<br>Taux de réussite : %{y}%<extra></extra>"
            }],
            {
                ...layoutBase,
                yaxis: {
                    range: [0, 110],
                    ticksuffix: "%",
                    gridcolor: "#eeece7",
                    zeroline: false
                },
                xaxis: { showgrid: false }
            },
            config
        );
    }

    const taskElement = document.getElementById("taskChart");

    if (taskElement) {
        Plotly.newPlot(
            taskElement,
            [
                {
                    x: labels,
                    y: passed,
                    name: "Réussies",
                    type: "bar",
                    marker: { color: "#287b58" }
                },
                {
                    x: labels,
                    y: failed,
                    name: "Échouées",
                    type: "bar",
                    marker: { color: "#a52d32" }
                }
            ],
            {
                ...layoutBase,
                barmode: "stack",
                showlegend: true,
                legend: {
                    orientation: "h",
                    y: 1.12,
                    x: 0
                },
                yaxis: {
                    gridcolor: "#eeece7",
                    zeroline: false,
                    rangemode: "tozero"
                },
                xaxis: { showgrid: false }
            },
            config
        );
    }

    const trajectoryElement = document.getElementById("trajectoryChart");

    if (trajectoryElement) {
        Plotly.newPlot(
            trajectoryElement,
            [{
                labels: trajectoryLabels,
                values: trajectoryValues,
                type: "pie",
                hole: 0.55,
                textinfo: "percent",
                textposition: "inside",
                hovertemplate: "%{label}<br>Nombre : %{value}<br>Part : %{percent}<extra></extra>",
                marker: {
                    colors: [
                        "#a52d32",
                        "#c65a5e",
                        "#287b58",
                        "#d5a04a",
                        "#64748b",
                        "#9b9185"
                    ]
                }
            }],
            {
                ...layoutBase,
                margin: { t: 15, r: 15, b: 15, l: 15 },
                showlegend: true,
                legend: {
                    orientation: "h",
                    y: -0.12,
                    x: 0.5,
                    xanchor: "center"
                }
            },
            config
        );
    }
});
