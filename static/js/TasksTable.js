window.tasksBarChart = null;

const TasksTable = {
    props: ['selected-task', 'task-info'],
    data() {
        return {
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: false,
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            display: false
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            },
            isLoading: true,
        }
    },
    watch: {
        selectedTask(newValue) {
            this.isLoading = true;
            console.log(newValue)
            this.fetchTasksResult(newValue.task_id)
                .then(data => {
                    const taskData = Object.values(data.rows);
                    const labels = [];
                    const datasets = [];
                    taskData.flat().forEach(result => {
                        labels.push(result.ts);
                        datasets.push(result.task_duration)
                    })
                    if (window.tasksBarChart) {
                        this.updateChartRun(datasets, labels);
                    } else {
                        this.createChartRun(datasets, labels);
                    }
                })
                .finally(() => {
                    this.isLoading = false;
                });
        }
    },
    methods: {
        async fetchTasksResult(taskId) {
            // TODO rewrite session
            const res = await fetch (`/api/v1/tasks/results/${getSelectedProjectId()}/${taskId}`,{
                method: 'GET',
            })
            return res.json();
        },
        createChartRun(datasets, labels) {
            const ctx = document.getElementById('chartRun');
            const chart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        data: datasets,
                        borderWidth: 1,
                        borderColor: ['#5933c6'],
                        backgroundColor: ['#5933c6']
                    }]
                },
                options: this.options,
            });
            window.tasksBarChart = chart
        },
        updateChartRun(datasets, labels) {
            window.tasksBarChart.data.labels = labels;
            window.tasksBarChart.data.datasets[0].data = datasets;
            window.tasksBarChart.update();
        },
        copyWebhook() {
            const copiedText = document.querySelector('.web-hook-copy');
            const textInput = document.createElement("input");
            textInput.value = copiedText.textContent;
            document.body.appendChild(textInput);
            textInput.select();
            document.execCommand("copy");
            textInput.remove();
            showNotify('SUCCESS', 'Copied to clipboard')
        },
    },
    template: `
        <div class="card mt-3 mr-3 p-28 card-table-sm w-100">
            <div class="d-flex justify-content-between">
                <p class="font-h4 font-bold">{{ selectedTask.task_name }}</p>
                <div class="d-flex justify-content-end">
                    <button class="btn btn-secondary btn-icon btn-icon__purple mr-2"
                         data-toggle="modal" 
                         data-target="#RunTaskModal">
                        <i class="icon__18x18 icon-run"></i>
                    </button>
                    <button class="btn btn-secondary btn-icon btn-icon__purple">
                        <i class="fas fa-sync"></i>
                    </button>
                </div>
            </div>
            <table class="mt-24" style="width: max-content">
                <tr>
                    <td class="font-h6 text-gray-500 font-semibold font-uppercase pr-3">webhook</td>
                    <td class="font-h5 d-flex align-items-center">
                        <span class="web-hook-copy">{{ selectedTask.webhook }}</span>
                        <i class="icon__18x18 icon-multichoice ml-3" @click="copyWebhook"></i>
                    </td>
                </tr>
                <tr>
                    <td class="text-gray-500 font-h6 font-semibold font-uppercase pr-3">task id</td>
                    <td class="font-h5">{{ selectedTask.task_id }}</td>
                </tr>
            </table>
            
            <div class="d-grid grid-column-2 gap-3 mt-3">
                <div>
                    <p class="text-gray-500 font-h6 font-semibold font-uppercase mb-2">runs</p>
                    <div class="position-relative" style="height: 250px">
                        <div class="layout-spinner" v-if="isLoading">
                            <div class="spinner-centered">
                                <i class="spinner-loader__32x32"></i>
                            </div>
                        </div>
                        <canvas id="chartRun"></canvas>
                    </div>
                </div>
            </div>
        </div>
    `
}