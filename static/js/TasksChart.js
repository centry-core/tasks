const TasksChart = {
    props: ['labels', 'datasets', 'options', 'isLoading', 'chartId', 'type'],
    mounted() {
        if (!this.isLoading) {
            console.log(this.options)
            const ctx = document.getElementById(this.chartId);
            const chart = new Chart(ctx, {
                type: this.type,
                data: {
                    labels: this.labels,
                    datasets: this.datasets,
                },
                options: this.options,
            });
            window.tasksBarChart = chart
        }
    },
    template: `
        <div class="position-relative" style="height: 300px">
            <div class="layout-spinner" v-if="isLoading">
                <div class="spinner-centered">
                    <i class="spinner-loader__32x32"></i>
                </div>
            </div>
            <canvas :id="chartId"></canvas>
        </div>
    `
}