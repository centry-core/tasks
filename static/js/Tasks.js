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
            }
        })
    },
    methods: {
        setBucketEvent(taskList, resultList) {
            const vm = this;
            $('#task-aside-table').on('click', 'tbody tr:not(.no-records-found)', function(event) {
                const selectedUniqId = this.getAttribute('data-uniqueid');
                vm.selectedTask = taskList.find(row => row.task_id === selectedUniqId);
                $(this).addClass('highlight').siblings().removeClass('highlight');
            });
        },
        async fetchTasks() {
            const res = await fetch (`/api/v1/tasks/tasks/${this.session}`,{
                method: 'GET',
            })
            return res.json();
        },
        async deleteTaskApi() {
            const res = await fetch (`/api/v1/tasks/tasks/${this.session}/${this.selectedTask.task_id}`,{
                method: 'DELETE',
            })
        },
        selectFirstTask() {
            $('#task-aside-table tbody tr').each(function(i, item) {
                if(i === 0) {
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
                :selected-task="selectedTask"
                :session="session"
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
                :selected-task="selectedTask">
                <slot name='test_parameters_run'></slot>
            </tasks-run-task-modal>
        </main>
    `
};

register_component('tasks', Tasks);
