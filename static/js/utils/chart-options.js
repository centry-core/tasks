window.taskCharts = {
    line: null,
    bar: null,
}

const chartLineScales = {
    cpu: {
        display: true,
        position: 'left',
        beginAtZero: true,
        grid: {
            drawOnChartArea: false,
        },
        title: {
            text: 'cpu, %',
            display: true,
        }
    },
    memory: {
        display: true,
        position: 'right',
        beginAtZero: true,
        grid: {
            drawOnChartArea: false,
        },
        title: {
            text: 'memory, Mb',
            display: true,
        }
    },
}

const chartBarOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
        y: {
            beginAtZero: true,
            grid: {
                display: false
            },
            title: {
                text: 'duration, sec',
                display: true,
            }
        },
        x: {
            grid: {
                display: false
            }
        }
    },
    plugins: {
        legend: false,
    }
}

const chartLineOptions = {...chartBarOptions, scales: chartLineScales}