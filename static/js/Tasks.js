const Tasks = {
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
            selectedTaskRowIndex: null,
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
                vm.selectedTask = taskList.find(row => row.task_name === selectedUniqId);
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
            console.log(this.selectedTask)
            const res = await fetch (`/api/v1/tasks/tasks/${this.session}/${this.selectedTask.task_id}`,{
                method: 'DELETE',
            })
            console.log(res)
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
        selectTaskById(taskId) {
            const vm = this;
            $('#task-aside-table tbody tr').each(function(i, item) {
                if(i === 0) {
                    const firstRow = $(item);
                    firstRow.addClass('highlight');
                    vm.selectedTaskRowIndex = 0;
                }
            })
        },
        updateTasksList(taskId = null) {
            this.fetchTasks().then(data => {
                $("#task-aside-table").bootstrapTable('load', data.rows);
                this.setBucketEvent(data.rows);
                this.tasksCount = data.rows.length;
                this.isInitDataFetched = true;
                if (data.rows.length > 0) {
                    this.selectedTask = data.rows[0];
                    this.selectFirstTask();
                    // this.selectTaskById(taskId)
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
                :selected-="selectedTask"
                :selected-task-row-index="selectedTaskRowIndex"
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
                <slot name='test_parameters'></slot>
            </create-task-modal>
            <tasks-update-modal
                :locations="locations"
                :runtimes="runtimes"
                :selected-task="selectedTask"
                @update-tasks-list="updateTasksList"
                >
                <slot name='test_parameters'></slot>
            </tasks-update-modal>
            <tasks-confirm-modal
                v-if="showConfirm"
                @close-confirm="openConfirm"
                :loading-delete="loadingDelete"
                @delete-task="deleteTask">
            </tasks-confirm-modal>
            <tasks-run-task-modal>
                <slot name='test_parameters' id="werwerewrewr"></slot>
            </tasks-run-task-modal>
        </main>
    `
};

register_component('tasks', Tasks);
