
document.addEventListener("DOMContentLoaded", function () {
    const dataElement = document.getElementById("benchmark-chart-data");

    if (!dataElement || typeof Plotly === "undefined") {
        console.error("Données du tableau de bord ou Plotly indisponibles.");
        return;
    }

    let data;

    try {
        data = JSON.parse(dataElement.textContent);
    } catch (error) {
        console.error("Erreur lors de la lecture des données du dashboard :", error);
        return;
    }

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

    // 1. TAUX DE RÉUSSITE PAR AGENT

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

    // 2. RÉPARTITION DES TÂCHES RÉUSSIES ET ÉCHOUÉES

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

    // 3. RÉPARTITION DES ÉVÉNEMENTS DES TRAJECTOIRES

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

    // 4. COMPARAISON DÉTERMINISTE / QWEN

    const comparisonLabels = data.comparison_labels || [];

    const comparisonCharts = [
        {
            id: "comparisonAccuracyChart",
            deterministic: data.deterministic_accuracies || [],
            qwen: data.qwen_accuracies || [],
            title: "Taux de réussite",
            suffix: "%",
            hoverSuffix: "%"
        },
        {
            id: "comparisonDurationChart",
            deterministic: data.deterministic_durations || [],
            qwen: data.qwen_durations || [],
            title: "Durée d'exécution",
            suffix: " s",
            hoverSuffix: " s"
        },
        {
            id: "comparisonTokensChart",
            deterministic: data.deterministic_tokens || [],
            qwen: data.qwen_tokens || [],
            title: "Nombre de tokens",
            suffix: "",
            hoverSuffix: ""
        }
    ];

    comparisonCharts.forEach(chart => {
        const element = document.getElementById(chart.id);

        if (!element) {
            return;
        }

        Plotly.newPlot(
            element,
            [
                {
                    x: comparisonLabels,
                    y: chart.deterministic,
                    name: "Déterministe",
                    type: "bar",
                    marker: { color: "#287b58" },
                    hovertemplate:
                        "%{x}<br>Déterministe : %{y}" +
                        chart.hoverSuffix +
                        "<extra></extra>"
                },
                {
                    x: comparisonLabels,
                    y: chart.qwen,
                    name: "Qwen 2.5:3b",
                    type: "bar",
                    marker: { color: "#a52d32" },
                    hovertemplate:
                        "%{x}<br>Qwen 2.5:3b : %{y}" +
                        chart.hoverSuffix +
                        "<extra></extra>"
                }
            ],
            {
                ...layoutBase,
                barmode: "group",
                showlegend: true,
                legend: {
                    orientation: "h",
                    y: 1.12,
                    x: 0
                },
                yaxis: {
                    title: chart.title,
                    ticksuffix: chart.suffix,
                    gridcolor: "#eeece7",
                    zeroline: false,
                    rangemode: "tozero"
                },
                xaxis: {
                    showgrid: false
                }
            },
            config
        );
    });
});
