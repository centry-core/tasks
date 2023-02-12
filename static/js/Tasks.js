const Tasks = {
    props: ['session', 'locations', 'runtimes'],
    components: {
        'create-task-modal': TasksCreateModal,
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
            selectedTaskRowIndex: null,
            loadingDelete: false,
            isInitDataFetched: false,
            showConfirm: false,
            showModalRunTest: false,
            bucketCount: null,
            taskInfo: {
                "webhook": null,
                "task_id": null
            },
            checkedBucketsList: [],
        }
    },
    mounted() {
        const vm = this;
        this.fetchTasks().then(data => {
            $("#task-aside-table").bootstrapTable('append', data.rows);
            this.setBucketEvent(data.rows);
            this.bucketCount = data.rows.length;
            this.isInitDataFetched = true;
            if (data.rows.length > 0) {
                vm.selectedTask = data.rows[0];
                this.selectFirstTask();
            }
            return data
        })
    },
    methods: {
        getTaskInfo(data, taskName){
            const taskInfo = {}
            Object.values(data.rows).forEach(value => {
                if (value["task_name"] === taskName){
                    taskInfo["task_id"] = value.task_id
                    taskInfo["webhook"] = value.webhook
                }
            });
            return taskInfo
        },
        setBucketEvent(taskList, resultList) {
            const vm = this;
            $('#task-aside-table').on('click', 'tbody tr:not(.no-records-found)', function(event) {
                const selectedUniqId = this.getAttribute('data-uniqueid');
                vm.selectedTask = taskList.find(row => row.task_name === selectedUniqId);
                $(this).addClass('highlight').siblings().removeClass('highlight');
            });
        },
        async fetchTasks() {
            // TODO rewrite session
            const res = await fetch (`/api/v1/tasks/tasks/${this.session}`,{
                method: 'GET',
            })
            return res.json();
        },
        async fetchTaskResults() {
            // TODO rewrite session
            const res = await fetch(`/api/v1/tasks/results/${this.session}`, {
                method: 'GET',
            })
            return res.json();
        },
        refreshTaskTable(taskResults) {
            $("#task-table").bootstrapTable('load', taskResults);
        },
        refreshBucketTable() {
            this.fetchTasks().then(data => {
                $("#task-table").bootstrapTable('load', data.rows);
            })
        },
        selectFirstTask() {
            const vm = this;
            $('#task-aside-table tbody tr').each(function(i, item) {
                if(i === 0) {
                    const firstRow = $(item);
                    firstRow.addClass('highlight');
                    vm.selectedTaskRowIndex = 0;
                }
            })
        },
        refresh() {
            this.refreshBucketTable();
            this.refreshArtifactTable(this.selectedTask, true);
        },
        openConfirm() {
            this.showConfirm = !this.showConfirm;
        },
        updateBucketList(buckets) {
            this.checkedBucketsList = buckets;
        },
        deleteTask() {
            this.loadingDelete = true;
            setTimeout(() => {
                showNotify('SUCCESS', 'Bucket delete.');
                this.loadingDelete = false;
                this.showConfirm = !this.showConfirm;
            }, 1000);
        },
    },
    template: `
        <main class="d-flex align-items-start justify-content-center mb-3">
            <tasks-list-aside
                @open-confirm="openConfirm"
                @update-bucket-list="updateBucketList"
                :checked-buckets-list="checkedBucketsList"
                :bucket-count="bucketCount"
                :selected-="selectedTask"
                :selected-task-row-index="selectedTaskRowIndex"
                :is-init-data-fetched="isInitDataFetched">
            </tasks-list-aside>
            <tasks-table
                :selected-task="selectedTask"
                :session="session"
                :task-info="taskInfo"
                @refresh="refresh">
            </tasks-table>
            <create-task-modal
                @refresh-task="refreshTaskTable"
                :locations="locations"
                :runtimes="runtimes"
                >
                <slot name='test_parameters'></slot>
            </create-task-modal>
            <tasks-confirm-modal
                v-if="showConfirm"
                @close-confirm="openConfirm"
                :loading-delete="loadingDelete"
                @delete-task="deleteTask">
            </tasks-confirm-modal>
            <tasks-run-task-modal>
                <slot name='test_parameters'></slot>
            </tasks-run-task-modal>
        </main>
    `
};

register_component('tasks', Tasks);
