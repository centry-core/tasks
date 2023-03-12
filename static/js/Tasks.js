const Tasks = {
    delimiters: ['[[', ']]'],
    props: ['session', 'locations', 'runtimes'],
    components: {
        'create-task-modal': TasksCreateModal,
        'tasks-update-modal': TasksUpdateModal,
        'tasks-list-aside': TasksListAside,
        'tasks-table': TasksTable,
        'tasks-confirm-modal' : TasksConfirmModal,
        'tasks-run-task-modal' : TasksRunTaskModal,
    },
    data() {
        return {
            selectedTask: {
                task_name: null,
            },
            loadingDelete: false,
            isInitDataFetched: false,
            showConfirm: false,
            showModalRunTest: false,
            tasksCount: null,
            taskInfo: {
                "webhook": null,
                "task_id": null
            },
            checkedBucketsList: [],
            tags_mapper: [],
            isShowLastLogs: true,
        }
    },
    mounted() {
        const vm = this;
        this.fetchTasks().then(data => {
            $("#task-aside-table").bootstrapTable('append', data.rows);
            this.setBucketEvent(data.rows);
            this.tasksCount = data.rows.length;
            this.isInitDataFetched = true;
            if (data.rows.length > 0) {
                vm.selectedTask = data.rows[0];
                this.selectFirstTask();
                fetch (`/api/v1/api/v1/task_status/${getSelectedProjectId()}`,{
                    method: 'GET',
                }).then(res => {
                    console.log(res)
                })
            }
        });
    },
    watch: {
        selectedTask(newValue) {
            $('#tableLogs').empty();
            this.tags_mapper = [];
        }
    },
    methods: {
        // GET -> api/v1/task_status/<project_id>/<task_result_id> - для получения статуса у таска
        // GET -> api/v1/loki_url/<project_id>/?task_id=<>&task_result_id=<> - для получения конкретного лога
        prefetchLogsByResultId() {
            this.fetchWebsocketURL(this.selectedTask.task_id).then(data => {
                this.$emit('run-task', data)
            })
        },
        async fetchWebsocketURL(taskId) { // возвращает последний запущеный
            const res = await fetch (`/api/v1/tasks/loki_url/${getSelectedProjectId()}/?task_id=${taskId}`,{
                method: 'GET',
            })
            return res.json();
        },
        async fetchTaskStatus(taskId) {
            const res = await fetch (`/api/v1/task_status/${getSelectedProjectId()}/?task_id=${taskId}`,{
                method: 'GET',
            })
            return res.json();
        },
        setBucketEvent(taskList, resultList) {
            const vm = this;
            $('#task-aside-table').on('click', 'tbody tr:not(.no-records-found)', function (event) {
                const selectedUniqId = this.getAttribute('data-uniqueid');
                vm.selectedTask = taskList.find(row => row.task_id === selectedUniqId);
                $(this).addClass('highlight').siblings().removeClass('highlight');
            });
        },
        async fetchTasks() {
            const res = await fetch(`/api/v1/tasks/tasks/${this.session}`, {
                method: 'GET',
            })
            return res.json();
        },
        async deleteTaskApi() {
            const res = await fetch(`/api/v1/tasks/tasks/${this.session}/${this.selectedTask.task_id}`, {
                method: 'DELETE',
            })
        },
        selectFirstTask() {
            $('#task-aside-table tbody tr').each(function (i, item) {
                if (i === 0) {
                    const firstRow = $(item);
                    firstRow.addClass('highlight');
                }
            })
        },
        updateTasksList(taskId = null) {
            this.fetchTasks().then(data => {
                $("#task-aside-table").bootstrapTable('load', data.rows);
                this.setBucketEvent(data.rows);
                this.tasksCount = data.rows.length;
                this.isInitDataFetched = true;
                if (taskId) {
                    this.selectedTask = data.rows.find(row => row.task_id === taskId);
                    $('#task-aside-table')
                        .find(`[data-uniqueid='${taskId}']`)
                        .addClass('highlight');
                } else {
                    if (data.rows.length > 0) {
                        this.selectFirstTask();
                        this.selectedTask = data.rows[0];
                    }
                }
            })
        },
        openConfirm() {
            this.showConfirm = !this.showConfirm;
        },
        updateBucketList(buckets) {
            this.checkedBucketsList = buckets;
        },
        deleteTask() {
            this.loadingDelete = true;
            this.deleteTaskApi().then(() => {
                showNotify('SUCCESS', 'Task delete.');
                this.loadingDelete = false;
                this.showConfirm = !this.showConfirm;
                this.updateTasksList();
            })
        },
        runTask(payload) {
            this.init_websocket(payload.websocket_url)
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
            const tagColors = [
                '#f89033',
                '#e127ff',
                '#2BD48D',
                '#2196C9',
                '#6eaecb',
                '#385eb0',
                '#7345fc',
                '#94E5B0',
            ]

            const data = JSON.parse(message.data);

            const logsTag = data.streams.map(logTag => {
                return logTag.stream.hostname;
            })

            const uniqTags = [...new Set(logsTag)].filter(tag => !!(tag))
            uniqTags.forEach(tag => {
                if (!this.tags_mapper.includes(tag)) {
                    this.tags_mapper.push(tag)
                }
            })

            data.streams.forEach((stream_item, streamIndex) => {
                stream_item.values.forEach((message_item, messageIndex) => {
                    console.log(message_item[1])
                    const timestamp = `<td>${this.normalizeDate(message_item)}</td>`;

                    const indexColor = this.tags_mapper.indexOf(stream_item.stream.hostname);
                    const coloredTag = `<td><span style="color: ${tagColors[indexColor]}" class="ml-4">[${stream_item.stream.hostname}]</span></td>`

                    const log_level = stream_item.stream.level;
                    const coloredText = `<td><span class="colored-log colored-log__${log_level}">${log_level}</span></td>`

                    const message = message_item[1]

                    const row = `<tr>${timestamp}${coloredTag}${coloredText}<td class="log-message__${streamIndex}-${messageIndex}"></td></tr>`
                    $('#tableLogs').append(row);
                    $(`.log-message__${streamIndex}-${messageIndex}`).append(`<plaintext>${message}`);

                    if (this.isShowLastLogs) this.scrollLogsToEnd();
                })
            })
        },
        on_websocket_close(message) {
            // console.log(message)
        },
        on_websocket_error(message) {
            // console.log(message)
        },
        normalizeDate(message_item) {
            const d = new Date(Number(message_item[0]) / 1000000)
            const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
            return d.toLocaleString("en-GB", {timeZone: tz})
        },
        scrollLogsToEnd() {
            const elem = document.querySelector('.container-logs');
            elem.scrollTop = elem.scrollHeight;
        },
        setShowLastLogs() {
            this.isShowLastLogs = !this.isShowLastLogs;
            if (this.isShowLastLogs) {
                const elem = document.querySelector('.container-logs');
                elem.scrollTop = elem.scrollHeight;
            }
        },
    },
    template: `
        <main class="d-flex align-items-start justify-content-center mb-3">
            <tasks-list-aside
                @open-confirm="openConfirm"
                @update-bucket-list="updateBucketList"
                :checked-buckets-list="checkedBucketsList"
                :bucket-count="tasksCount"
                :selected-task="selectedTask"
                :is-init-data-fetched="isInitDataFetched">
            </tasks-list-aside>
            <tasks-table
                @change-scroll-logs="setShowLastLogs"
                :selected-task="selectedTask"
                :session="session"
                :is-show-last-logs="isShowLastLogs"
                :tags_mapper="tags_mapper"
                :task-info="taskInfo">
            </tasks-table>
            <create-task-modal
                :locations="locations"
                :runtimes="runtimes"
                @update-tasks-list="updateTasksList"
                >
                <slot name='test_parameters_create'></slot>
            </create-task-modal>
            <tasks-update-modal
                :locations="locations"
                :runtimes="runtimes"
                :selected-task="selectedTask"
                @update-tasks-list="updateTasksList"
                >
                <slot name='test_parameters_update'></slot>
            </tasks-update-modal>
            <tasks-confirm-modal
                v-if="showConfirm"
                @close-confirm="openConfirm"
                :loading-delete="loadingDelete"
                @delete-task="deleteTask">
            </tasks-confirm-modal>
            <tasks-run-task-modal
                @run-task="runTask"
                :selected-task="selectedTask">
                <slot name='test_parameters_run'></slot>
            </tasks-run-task-modal>
        </main>
    `
};

register_component('tasks', Tasks);
