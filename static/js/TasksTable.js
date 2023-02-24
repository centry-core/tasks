const TasksTable = {
    props: ['selected-task', 'task-info'],
    components: {
        'tasks-chart': TasksChart,
    },
    data() {
        return {
            websocket: undefined,
            isLoading: true,
            labels: [],
            chartBarDatasets: [],
            chartLineDatasets: [],
            chartBarOptions,
            chartLineOptions,
        }
    },
    watch: {
        selectedTask(newValue) {
            this.isLoading = true;
            // this.fetchLogs().then(data => {
            //     this.init_websocket(data.websocket_url)
            // })
            this.chartBarDatasets = [];
            this.labels = [];
            this.fetchTasksResult(newValue.task_id)
                .then(data => {
                    const taskData = Object.values(data.rows);
                    const barDatasets = [{
                            data: [],
                            borderWidth: 1,
                            borderColor: ['#5933c6'],
                            backgroundColor: ['#5933c6']
                        }];
                    const lineDatasets = [
                        {
                            data: [],
                            label: 'CPU',
                            borderWidth: 1,
                            borderColor: ['red'],
                            backgroundColor: ['red'],
                            yAxisID: 'cpu',
                        },
                        {
                            data: [],
                            label: 'MEMORY',
                            borderWidth: 1,
                            borderColor: ['#5933c6'],
                            backgroundColor: ['#5933c6'],
                            yAxisID: 'memory',
                        }
                    ];
                    $('#logs-table').bootstrapTable('load', taskData.flat())
                    taskData.flat().forEach(result => {
                        this.labels.push(result.ts);
                        const memory_usage = result.task_stats?.memory_usage ? Number(result.task_stats?.memory_usage.substring(0, result.task_stats?.memory_usage.length - 1)) : 0;
                        barDatasets[0].data.push(result.task_duration)
                        lineDatasets[0].data.push(result.task_stats?.cpu_usage);
                        lineDatasets[1].data.push(memory_usage);
                    });
                    this.chartBarDatasets = barDatasets;
                    this.chartLineDatasets = lineDatasets;
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
        async fetchLogs() {
            const res = await fetch (`/api/v1/tasks/loki_url/${getSelectedProjectId()}/?task_id=${this.selectedTask.task_id}`,{
                method: 'GET',
            })
            return res.json();
        },
        init_websocket(websocketURL) {
            this.websocket = new WebSocket(websocketURL)
            this.websocket.onmessage = this.on_websocket_message
            this.websocket.onopen = this.on_websocket_open
            this.websocket.onclose = this.on_websocket_close
            this.websocket.onerror = this.on_websocket_error
        },
        on_websocket_open(message) {
            // console.log(message)
        },
        on_websocket_message(message) {
            if (message.type !== 'message') {
                console.warn('Unknown message from socket', message)
                return
            }
            const data = JSON.parse(message.data)
            data.streams.forEach(stream_item => {
                stream_item.values.forEach(message_item => {
                    this.logs.push(`${stream_item.stream.level} : ${message_item[1]}`)
                })
            })
        },
        on_websocket_close(message) {
            // console.log(message)
        },
        on_websocket_error(message) {
            // console.log(message)
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
        <div class="w-100">
            <div class="card mt-3 mr-3 p-28 card-table-sm">
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
                <p class="text-gray-500 font-h6 font-semibold font-uppercase mb-2 mt-3">runs</p>
                <div class="d-grid grid-column-2 gap-3">
                    <tasks-chart
                        :key="isLoading"
                        :is-loading="isLoading"
                        chart-id="chartRun"
                        :options="chartBarOptions"
                        :datasets="chartBarDatasets"
                        type="bar"
                        :labels="labels"
                    ></tasks-chart>
                    <tasks-chart
                        :key="isLoading"
                        :is-loading="isLoading"
                        chart-id="chartMemoryCpu"
                        :options="chartLineOptions"
                        :datasets="chartLineDatasets"
                        type="line"
                        :labels="labels"
                    ></tasks-chart>
                </div>
            </div>
            
            <Table-Card
                header='Execution log'
                :adaptive-height="true"
                :borders="true"
                :table_attributes="{
                    'data-pagination': 'true',
                    'data-page-list': '[5, 10, 15, 20]',
                    'data-page-size': 5,
                    'id': 'logs-table',
                    'data-side-pagination': 'client',
                    'data-pagination-parts': ['pageInfo', 'pageList', 'pageSize']
                }"
                container_classes="mt-3 mr-3"
            >
                <template #table_headers>
                    <th data-visible="false" data-field="id">index</th>
                    <th scope="col" data-sortable="true" data-field="name">Name</th>
                    <th scope="col" data-sortable="true" class="w-100" data-field="ts">Date</th>
                    <th scope="col" data-sortable="true" data-field="task_status"
                        data-formatter="report_formatters.reportsStatusFormatter">Status
                    </th>
                    <th scope="coll" data-sortable="false" data-fiels="ts"
                        data-formatter="filesFormatter.actions"></th>
                </template>
            </Table-Card>
        </div>
    `
}