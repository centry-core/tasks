var tableFormatter = {
    actions(value, row, index) {
        const is_disabled = V.mode !== 'administration' && row.mode === 'administration'
        if (!is_disabled) {
            return `
            <div class="d-none">
                <button class="btn btn-default btn-xs btn-table btn-icon__xs task_delete">
                    <i class="fas fa-trash-alt"></i>
                </button>
                <button class="btn btn-default btn-xs btn-table btn-icon__xs task_setting">
                    <i class="fas fa-gear"></i>
                </button>
            </div>
            `
        } else {
            return `
            <div class="d-none">
                <button disabled class="btn btn-default btn-xs btn-table btn-icon__xs task_delete">
                    <i class="fas fa-trash-alt"></i>
                </button>
                <button disabled class="btn btn-default btn-xs btn-table btn-icon__xs task_setting">
                    <i class="fas fa-gear"></i>
                </button>
            </div>
            `
        }
    }
}

const TasksListAside = {
    props: ['isInitDataFetched', 'selectedTask', 'checkedBucketsList', 'bucketCount'],
    data() {
        return {
            loadingDelete: false,
        }
    },
    computed: {
        responsiveTableHeight() {
            return `${(window.innerHeight - 270)}px`;
        }
    },
    watch: {
        isInitDataFetched() {
            this.setBucketEvents();
        }
    },
    methods: {
        setBucketEvents() {
            const vm = this;
            $('#task-aside-table').on('sort.bs.table', function (name, order) {
                vm.$nextTick(() => {
                    $('#task-aside-table').find(`[data-uniqueid='${vm.selectedTask.task_id}']`).addClass('highlight');
                })
            });
        },
    },
    template: `
        <aside class="m-3 card card-table-sm" style="width: 340px">
            <div class="row p-4">
                <div class="col-4">
                    <h4>Tasks</h4>
                </div>
                <div class="col-8">
                    <div class="d-flex justify-content-end">
                        <button type="button"
                             data-toggle="modal" 
                             data-target="#CreateTaskModal"
                             class="btn btn-basic btn-sm btn-icon__sm">
                            <i class="fas fa-plus"></i>
                        </button>
                    </div>
                </div>
            </div>
            <div class="card-body" style="padding-top: 0">
                <table class="table table-borderless table-fix-thead"
                    id="task-aside-table"
                    data-toggle="table"
                    data-unique-id="task_id">
                    <thead class="thead-light bg-transparent">
                        <tr>
                            <th data-visible="false" data-field="task_id">index</th>
                            <th data-checkbox="true" data-visible="false" data-field="select"></th>
                            <th data-sortable="true" data-field="task_name" class="bucket-name">NAME</th>
                            <th data-sortable="true" data-cell-style="nameStyle" data-field="size" class="bucket-size">SIZE</th>
                            <th data-cell-style="nameStyle" 
                                data-formatter='tableFormatter.actions'
                                data-events="bucketEvents">
                            </th>
                        </tr>
                    </thead>
                    <tbody :style="{'height': responsiveTableHeight}">
                    </tbody>
                </table>
                <div class="p-3">
                    <span class="font-h5 text-gray-600">{{ bucketCount }} items</span>
                </div>
            </div>
        </aside>
    `
}

var bucketEvents = {
    "click .task_delete": function (e, value, row, index) {
        e.stopPropagation();
        const vm = vueVm.registered_components.tasks;
        vm.openConfirm();
    },
    "click .task_setting": function (e, value, row, index) {
        e.stopPropagation();
        $('#UpdateTaskModal').modal('show');
    }
}
