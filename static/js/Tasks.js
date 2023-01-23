const Tasks = {
    props: ['session', 'locations', 'runtimes'],
    components: {
        'create-task-modal': CreateTaskModal,
        'tasks-list-aside': TasksListAside,
        'tasks-table': TasksTable,
    },
    data() {
        return {
            selectedBucket: {
                name: null,
            },
            selectedTaskRowIndex: null,
            loadingDelete: false,
            isInitDataFetched: false,
            showConfirm: false,
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
                this.selectFirstTask();
            }
            return data
        }).then(data => {
            this.fetchTasksInfo().then(taskInfo => {
                console.log(taskInfo)
                vm.taskInfoFetched = taskInfo;
            })
            return data
        }).then((taskRows) => {
            if (taskRows.rows.length > 0) {
                 vm.fetchTaskResults().then(resultRows => {
                     console.log(resultRows)
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
        setBucketEvent(taskList, resultList) {
            const vm = this;
            $('#task-aside-table').on('click', 'tbody tr:not(.no-records-found)', function(event) {
                const selectedUniqId = this.getAttribute('data-uniqueid');
                vm.selectedBucket = taskList.find(row => row.task_name === selectedUniqId);
                $(this).addClass('highlight').siblings().removeClass('highlight');
                // vm.selectedTask = vm.selectedBucked.name
                // const taskName = vm.selectedBucked.task_name

                // // TODO: need to optimize ? it's being called on each click with full json obj.
                // vm.taskInfo = vm.getTaskInfo(vm.taskInfoFetched, taskName)
                //
                // if (resultList.hasOwnProperty(taskName)){
                //     vm.tableData = resultList[taskName]
                //     vm.refreshTaskTable(vm.tableData);
                // }
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
                    // vm.selectedBucket = this.childNodes[vm.getTaskNameCallIndex(this)].innerHTML;
                }
            })
        },
        refresh() {
            this.refreshBucketTable();
            this.refreshArtifactTable(this.selectedBucket, true);
        },

        openConfirm(type) {
            this.bucketDeletingType = type;
            this.showConfirm = !this.showConfirm;
        },
        updateBucketList(buckets) {
            this.checkedBucketsList = buckets;
        }
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
                @update-bucket-list="updateBucketList"
                :checked-buckets-list="checkedBucketsList"
                :bucket-count="bucketCount"
                :selected-bucket="selectedBucket"
                :selected-task-row-index="selectedTaskRowIndex"
                :is-init-data-fetched="isInitDataFetched">
            </tasks-list-aside>
            <tasks-table
                :selected-task="selectedBucket"
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
<!--            <artifact-confirm-modal-->
<!--                v-if="showConfirm"-->
<!--                @close-confirm="openConfirm"-->
<!--                :loading-delete="loadingDelete"-->
<!--                @delete-bucket="switcherDeletingBucket">-->
<!--            </artifact-confirm-modal>-->
        </main>
    `
};

register_component('tasks', Tasks);
