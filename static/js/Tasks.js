const Tasks = {
    props: ['locations', 'runtimes', 'integrations'],
    components: {
        'create-task-modal': TasksCreateModal,
        'tasks-update-modal': TasksUpdateModal,
        'tasks-list-aside': TasksListAside,
        'tasks-table': TasksTable,
        'tasks-confirm-modal': TasksConfirmModal,
        'tasks-run-task-modal': TasksRunTaskModal,
    },
    data() {
        return {
            selectedTask: {},
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
            runningTasks: new Map(),
            checkingTimeInterval: null,
            selectedResultId: null,
            isLoadingWebsocket: false,
            isLoadingRun: false,
            s3Integrations: [],
            selectedIntegration: undefined,
            //
            logsSubscribed: false,
            logsSubscribedTo: null,
        }
    },
    computed: {
        runningTasksList() {
            const resultIds = this.runningTasks.get(this.selectedTask.task_id);
            return resultIds ? [...resultIds] : []
        },
        default_integration() {
            return this.s3Integrations.find(item => item.is_default)
        },
    },
    mounted() {
        const vm = this;
        $(document).on('vue_init', () => {
            socket.on("log_data", this.logsProcess);
            ApiFetchTasks().then(data => {
                $("#task-aside-table").bootstrapTable('append', data.rows);
                this.setBucketEvent(data.rows);
                this.tasksCount = data.rows.length;
                this.isInitDataFetched = true;
                if (data.rows.length > 0) {
                    vm.selectedTask = data.rows[0];
                    this.checkTaskStatus(vm.selectedTask.task_id);
                    this.selectFirstTask();
                }
            });
            this.fetchS3Integrations();
        })
    },
    watch: {
        selectedTask(newValue, oldVal) {
            $('#tableLogs').empty();
            this.tags_mapper = [];
            this.isLoadingWebsocket = false;
            if (this.checkingTimeInterval) {
                this.stopCheckStatus();
            }
            this.runningTasks.clear();
            this.logsUnsubscribe();
            if (oldVal.task_id) this.checkTaskStatus(this.selectedTask.task_id);
        }
    },
    methods: {
        logsSubscribe(task_result_id) {
            if (Array.isArray(task_result_id)) {
                return this.logsSubscribe(task_result_id[0]);
            }
            if (this.logsSubscribedTo == task_result_id) {
                return;
            }
            this.logsUnsubscribe();
            this.logsSubscribed = true;
            this.logsSubscribedTo = task_result_id;
            this.isLoadingWebsocket = false;
            socket.emit("task_logs_subscribe", {"task_result_id": this.logsSubscribedTo});
        },
        logsUnsubscribe() {
            if (this.logsSubscribed) {
                socket.emit("task_logs_unsubscribe", {"task_result_id": this.logsSubscribedTo});
                this.logsSubscribedTo = null;
                this.logsSubscribed = false;
                this.tags_mapper = [];
                $('#tableLogs').empty();
            }
        },
        logsProcess(data) {
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

            const logsTag = data.map(logTag => {
                return logTag.labels.hostname;
            })

            const uniqTags = [...new Set(logsTag)].filter(tag => !!(tag))
            uniqTags.forEach(tag => {
                if (!this.tags_mapper.includes(tag)) {
                    this.tags_mapper.push(tag)
                }
            })

            data.forEach((record_item, recordIndex) => {
                const timestamp = `<td>${this.normalizeDate(record_item)}</td>`;

                const indexColor = this.tags_mapper.indexOf(record_item.labels.hostname);
                const coloredTag = `<td><span style="color: ${tagColors[indexColor]}" class="ml-4">[${record_item.labels.hostname}]</span></td>`

                const log_level = record_item.labels.level;
                const coloredText = `<td><span class="colored-log colored-log__${log_level}">${log_level}</span></td>`

                const message = record_item.line;
                const randomIndex = Date.now() + Math.floor(Math.random() * 100);
                const row = `<tr>${timestamp}${coloredTag}${coloredText}<td class="log-message__${randomIndex}"></td></tr>`
                $('#tableLogs').append(row);
                $(`.log-message__${randomIndex}`).append(`<plaintext>${message}`);

                if (this.isShowLastLogs) this.scrollLogsToEnd();
            })
        },
        //
        setBucketEvent(taskList, resultList) {
            const vm = this;
            $('#task-aside-table').on('click', 'tbody tr:not(.no-records-found)', function (event) {
                const selectedUniqId = this.getAttribute('data-uniqueid');
                vm.selectedTask = taskList.find(row => row.task_id === selectedUniqId);
                $(this).addClass('highlight').siblings().removeClass('highlight');
            });
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
            ApiFetchTasks().then(data => {
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
            ApiDeleteTask(this.selectedTask.task_id).then(() => {
                showNotify('SUCCESS', 'Task delete.');
                this.loadingDelete = false;
                this.showConfirm = !this.showConfirm;
                this.updateTasksList();
            })
        },
        runTask() {
            if (this.checkingTimeInterval) {
                this.stopCheckStatus();
            }
            this.logsUnsubscribe();
            this.checkTaskStatus(this.selectedTask.task_id, true);
        },
        checkTaskStatus(taskId, closeModal = false) {
            if (this.checkingTimeInterval) this.stopCheckStatus();
            ApiCheckStatus(this.selectedTask.task_id).then(data => {
                if ($('#RunTaskModal').is(":visible") && closeModal) {
                    $('#RunTaskModal').modal('hide');
                    this.isLoadingRun = false;
                }
                if (data.IN_PROGRESS) {
                    this.checkingTimeInterval = setTimeout(() => this.checkTaskStatus(this.selectedTask.task_id), 5000)
                    if (!this.logsSubscribed) {
                        this.selectedResultId = data.task_result_ids.slice(-1);
                        this.logsSubscribe(this.selectedResultId);
                    }
                    this.runningTasks.set(taskId, data.task_result_ids);
                } else {
                    ApiLastResultId(taskId).then((data) => {
                        if (data.websocket_url) {
                            // FIXME: not using SIO for logs here
                            // this.isLoadingWebsocket = true;
                            this.logsUnsubscribe();
                            this.stopCheckStatus();
                            this.runningTasks.set(taskId, []);
                        }
                    })
                }
            });
        },
        stopCheckStatus() {
            clearTimeout(this.checkingTimeInterval)
            this.checkingTimeInterval = null;
        },
        normalizeDate(message_item) {
            const d = new Date(Number(message_item.time * 1000))
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
        async fetchS3Integrations() {
            const api_url = this.$root.build_api_url('integrations', 'integrations')
            const params = '?' + new URLSearchParams({name: 's3_integration'})
            const res = await fetch(`${api_url}/${getSelectedProjectId()}${params}`, {
                method: 'GET',
            })
            if (res.ok) {
                this.s3Integrations = await res.json()
                this.selectedIntegration = this.get_integration_value(this.default_integration)
                this.$nextTick(() => {
                    $('#selector_integration_create_task').val(this.selectedIntegration)
                    $('#selector_integration_create_task').selectpicker('refresh')
                })
            } else {
                console.warn('Couldn\'t fetch S3 integrations. Resp code: ', res.status)
            }
        },
        get_integration_value(integration) {
            return `${integration?.id}#${integration?.project_id}`
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
                @select-result-id="logsSubscribe"
                :is-loading-websocket="isLoadingWebsocket"
                :selected-task="selectedTask"
                :running-tasks-list="runningTasksList"
                :session="$root.project_id"
                :is-show-last-logs="isShowLastLogs"
                :tags_mapper="tags_mapper"
                :task-info="taskInfo">
            </tasks-table>
            <create-task-modal
                :locations="locations"
                :runtimes="runtimes"
                :integrations="integrations"
                :s3-integrations="s3Integrations"
                :selected-integration="selectedIntegration"
                @update-tasks-list="updateTasksList"
                >
                <slot name='test_parameters_create'></slot>
            </create-task-modal>
            <tasks-update-modal
                :locations="locations"
                :runtimes="runtimes"
                :selected-task="selectedTask"
                :integrations="integrations"
                :s3-integrations="s3Integrations"
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
                @is-loading="isLoadingRun = true"
                :is-loading-run="isLoadingRun"
                :selected-task="selectedTask">
                <slot name='test_parameters_run'></slot>
            </tasks-run-task-modal>
        </main>
    `
};

register_component('tasks', Tasks);
