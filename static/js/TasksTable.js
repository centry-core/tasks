const TasksTable = {
    props: ['selected-task', 'task-info', 'tags_mapper', 'isShowLastLogs', 'runningTasksList', 'isLoadingWebsocket'],
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
            selectedResultId: null,
        }
    },
    mounted() {
        $('#selectResult').on('change', (e) => {
            this.selectedResultId = e.target.value;
            this.$emit('select-result-id', e.target.value)
        })
    },
    watch: {
        selectedTask(newValue) {
            this.isLoading = true;
            this.labels = [];
            this.generateContent(newValue.task_id)
        },
        runningTasksList(val, oldVal) {
            const isEmptyList = !val.length && !oldVal.length;
            const isListChanged = val.length && val.length !== oldVal.length;
            const isListCleaned = !val.length && oldVal.length;
            if(isEmptyList) return
            if (isListChanged) {
                this.fetchTableData(this.selectedTask.task_id);
                this.$nextTick(() => {
                    $('#selectResult').selectpicker('refresh');
                    const hasListPreviousResult = val.includes(this.selectedResultId);
                    if (hasListPreviousResult) {
                        $('#selectResult').val(this.selectedResultId);
                    } else {
                        this.selectedResultId = this.runningTasksList.slice(-1);
                        this.$emit('select-result-id', this.selectedResultId);
                        $('#selectResult').val(this.selectedResultId);
                    }
                    $('#selectResult').selectpicker('refresh');
                })
            }
            if (isListCleaned) {
                if (Object.values(window.taskCharts).some(chart => chart !== null)) {
                    for (const key in window.taskCharts) {
                        window.taskCharts[key].destroy();
                        window.taskCharts[key] = null;
                    }
                    this.labels = [];
                }
                this.isLoading = true;
                this.generateContent(this.selectedTask.task_id)
            }
        }
    },
    methods: {
        fetchTableData(taskId) {
            ApiTasksResult(taskId)
                .then(data => {
                    const taskData = Object.values(data.rows).flat().map(item => ({...item, task_name: this.selectedTask.task_name }));
                    $('#logs-table').bootstrapTable('load', taskData);
                })
        },
        generateContent(taskId) {
            ApiTasksResult(taskId)
                .then(data => {
                    const taskData = Object.values(data.rows).flat().map(item => ({...item, task_name: this.selectedTask.task_name }));
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
                    $('#logs-table').bootstrapTable('load', taskData);
                    taskData.forEach(result => {
                        const ts = result.ts;
                        this.labels.push(ts);
                        const memory_usage = result.task_stats?.memory_usage ? Number(result.task_stats?.memory_usage.substring(0, result.task_stats?.memory_usage.length - 1)) : 0;
                        const cpu_usage = result.task_stats?.cpu_usage ? result.task_stats?.cpu_usage : 0;
                        const task_duration = result.task_duration ? result.task_duration / 1000 : 0;
                        barDatasets[0].data.push(task_duration);
                        lineDatasets[0].data.push(cpu_usage);
                        lineDatasets[1].data.push(memory_usage);
                    });
                    this.chartBarDatasets = barDatasets;
                    this.chartLineDatasets = lineDatasets;
                })
                .finally(() => {
                    this.isLoading = false;
                });
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
        <div style="width: calc(100% - 370px)">
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
            <div class="card card-table mt-3 mr-3">
                <div class="card-header">
                    <div class="d-flex justify-content-between">
                        <p class="font-h3 font-bold">Runtime</p>
                        <div class="d-flex">
                            <label class="custom-checkbox d-flex align-items-center">
                                <input type="checkbox" 
                                    :checked="isShowLastLogs"
                                    @click="$emit('change-scroll-logs')"><span class="ml-2">Show last logs</span>
                            </label>
                            <div v-show="runningTasksList.length > 0">
                                <select id="selectResult" 
                                    class="selectpicker bootstrap-select__b ml-3" data-style="btn">
                                    <option v-for="(result, index) in runningTasksList" :key="index">{{ result }}</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="layout-spinner" v-if="isLoadingWebsocket">
                    <div class="spinner-centered">
                        <i class="spinner-loader__32x32"></i>
                    </div>
                </div>
                <div class="card-body card-table" 
                    v-show="tags_mapper.length > 0"
                    style="padding-bottom: 30px !important;">
                    <div class="container-logs border p-3" style="border-radius: 4px;">
                        <table id="tableLogs" class="table-logs"></table>
                    </div>
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
                    'data-sort-name': 'id',
                    'data-sort-order': 'desc',
                    'id': 'logs-table',
                    'data-side-pagination': 'client',
                    'data-pagination-parts': ['pageInfo', 'pageList', 'pageSize']
                }"
                container_classes="mt-3 mr-3"
            >
                <template #table_headers>
                    <th data-field="id" data-sortable="true">Id</th>
                    <th scope="col" 
                        data-sortable="true" 
                        class="min-w-36"
                        data-sort-name="timestamp" 
                        data-field="ts">Date</th>
                    <th scope="col" 
                        data-sortable="true" 
                        class="w-100"
                        data-field="task_result_id">Result id</th>
                    <th scope="col" data-sortable="true" data-field="task_status"
                        data-formatter="report_formatters.reportsStatusFormatter">Status
                    </th>
                    <th scope="coll" data-sortable="false" data-field="task_name"
                        data-formatter="filesFormatter.actions"></th>
                </template>
            </Table-Card>
        </div>
    `
}