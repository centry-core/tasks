const Tasks = {
    props: ['session', 'locations', 'runtimes'],
    components: {
        'create-task-modal': CreateTaskModal,
        'tasks-list-aside': TasksListAside,
        'tasks-table': TasksTable,
    },
    data() {
        return {
            selectedTask: null,
            selectedTaskRowIndex: null,
            loadingDelete: false,
            isInitDataFetched: false,
            showConfirm: false,
            taskInfo: {
                "webhook": null,
                "task_id": null
            },
        }
    },
    mounted() {
        const vm = this;
        this.fetchTasks().then(data => {
            $("#task-aside-table").bootstrapTable('append', data.rows);
            this.bucketCount = data.rows.length;
            this.isInitDataFetched = true;
            if (data.rows.length > 0) {
                this.selectFirstTask();
            }
            return data
        }).then(data => {
            this.fetchTasksInfo().then(taskInfo => {
                vm.taskInfoFetched = taskInfo
            })
            return data
        }).then((taskRows) => {
            if (taskRows.rows.length > 0) {
                 vm.fetchTaskResults().then(resultRows => {
                     vm.setTaskEvent(taskRows.rows, resultRows.rows);
                })
            }
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
        setTaskEvent(taskList, resultList) {
            const vm = this;
            // console.log('s', this.locations)
            $('#task-aside-table').on('click', 'tbody tr:not(.no-records-found)', function(event) {
                const selectedUniqId = this.getAttribute('data-uniqueid');
                vm.selectedTaskObj = taskList.find(row => row.task_name === selectedUniqId);
                $(this).addClass('highlight').siblings().removeClass('highlight');
                vm.selectedTask = vm.selectedTaskObj.name
                const taskName = vm.selectedTaskObj.task_name

                // TODO: need to optimize ? it's being called on each click with full json obj.
                vm.taskInfo = vm.getTaskInfo(vm.taskInfoFetched, taskName)

                if (resultList.hasOwnProperty(taskName)){
                    vm.tableData = resultList[taskName]
                    vm.refreshTaskTable(vm.tableData);
                }
            });
        },
        async fetchTasksInfo() {
            // TODO rewrite session
            const res = await fetch (`/api/v1/tasks/tasks/${this.session}?get_size=false`,{
                method: 'GET',
            })
            return res.json();
        },
        async fetchTasks() {
            // TODO rewrite session
            const res = await fetch (`/api/v1/tasks/tasks/${this.session}?get_size=true`,{
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
        getTaskNameCallIndex(row) {
            let taskCallIndex;
            row.childNodes.forEach((node, index) => {
                const isTaskNameCell = node.className.split(' ').includes('task-name');
                if (isTaskNameCell) {
                    taskCallIndex = index;
                }
            })
            return taskCallIndex;
        },
        selectFirstTask() {
            const vm = this;
            $('#task-aside-table tbody tr').each(function(i, item) {
                if(i === 0) {
                    const firstRow = $(item);
                    firstRow.addClass('highlight');
                    vm.selectedTaskRowIndex = 0;
                    vm.selectedBucked = this.childNodes[vm.getTaskNameCallIndex(this)].innerHTML;
                }
            })
        },
        refresh() {
            this.refreshBucketTable();
            this.refreshArtifactTable(this.selectedBucked, true);
        },

        openConfirm(type) {
            this.bucketDeletingType = type;
            this.showConfirm = !this.showConfirm;
        },
    },
    computed: {
        // taskDetail() {
        //     const {
        //         env_vars,
        //         id,
        //         last_run,
        //         project_id,
        //         region,
        //         runtime,
        //         task_handler,
        //         task_id,
        //         task_name,
        //         webhook,
        //         zippath,
        //     } = this
        //     console.log('yaaxxaaa', env_vars)
        //     return {env_vars, id, last_run, project_id, region, runtime, task_handler, task_id, task_name, webhook, zippath}
        // },
    },
    template: `
        <main class="d-flex align-items-start justify-content-center mb-3">
            <tasks-list-aside
                @open-confirm="openConfirm"
                :selected-task-row-index="selectedTaskRowIndex"
                :is-init-data-fetched="isInitDataFetched">
            </tasks-list-aside>
            <tasks-table
                :selected-task="selectedTask"
                :task-info="taskInfo"
                @refresh="refresh">
            </tasks-table>
            <create-task-modal
                @refresh-bucket="refreshBucketTable"
                :locations="locations"
                :runtimes="runtimes"
                >
                
                <slot name='test_parameters'></slot>
            </create-task-modal>
            <artifact-confirm-modal
                v-if="showConfirm"
                @close-confirm="openConfirm"
                :loading-delete="loadingDelete"
                @delete-bucket="switcherDeletingBucket">
            </artifact-confirm-modal>
        </main>
    `
};

register_component('tasks', Tasks);
