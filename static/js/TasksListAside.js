const TasksListAside = {
    props: ['isInitDataFetched', 'selectedBucket', 'selectedTaskRowIndex', 'checkedBucketsList', 'bucketCount'],
    data() {
        return {
            canSelectItems: false,
            loadingDelete: false,
        }
    },
    computed: {
        isAnyBucketSelected() {
            return this.checkedBucketsList.length > 0;
        },
        responsiveTableHeight() {
            return `${(window.innerHeight - 210)}px`;
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
            $('#task-aside-table').on('check.bs.table', (row, $element) => {
                const buckets = [...this.checkedBucketsList, $element.name]
                this.$emit('update-bucket-list', buckets);
            });
            $('#task-aside-table').on('uncheck.bs.table', (row, $element) => {
                const buckets = this.checkedBucketsList.filter(bucket => {
                    return $element.name !== bucket
                })
                this.$emit('update-bucket-list', buckets);
            });
            $('#task-aside-table').on('uncheck-all.bs.table', (row, $element) => {
                this.$emit('update-bucket-list', []);
            });
            $('#task-aside-table').on('check-all.bs.table', (rowsAfter, rowsBefore) => {
                const buckets = rowsBefore.map(row => row.name);
                this.$emit('update-bucket-list', buckets);
            });
            $('#task-aside-table').on('sort.bs.table', function (name, order) {
                vm.$nextTick(() => {
                    $('#task-aside-table').find(`[data-uniqueid='${vm.selectedBucket.id}']`).addClass('highlight');
                })
            });
        },
        switchSelectItems() {
            this.canSelectItems = !this.canSelectItems;
            const action = this.canSelectItems ? 'hideColumn' : 'showColumn';
            $('#task-aside-table').bootstrapTable(action, 'select');
            document.getElementById("task-aside-table")
                .rows[this.selectedBucketRowIndex + 1]
                .classList.add('highlight');
        },
    },
    template: `
        <aside class="m-3 card card-table-sm" style="width: 450px">
            <div class="row p-4">
                <div class="col-4">
                    <h4>Tasks</h4>
                </div>
                <div class="col-8">
                    <div class="d-flex justify-content-end">
                        <button type="button"
                             data-toggle="modal" 
                             data-target="#CreateTaskModal"
                             class="btn btn-secondary btn-sm btn-icon__sm mr-2">
                            <i class="fas fa-plus"></i>
                        </button>
<!--                        <button type="button" class="btn btn-secondary btn-sm btn-icon__sm mr-2"-->
<!--                            @click="switchSelectItems">-->
<!--                            <i class="icon__18x18 icon-multichoice"></i>-->
<!--                        </button>-->
<!--                        <button type="button" -->
<!--                            @click="$emit('open-confirm', 'multiple')"-->
<!--                            :disabled="!isAnyBucketSelected"-->
<!--                            class="btn btn-secondary btn-sm btn-icon__sm mr-2">-->
<!--                            <i class="fas fa-trash-alt"></i>-->
<!--                        </button>-->
                    </div>
                </div>
            </div>
            <div class="card-body">
                <table class="table table-borderless table-fix-thead"
                    id="task-aside-table"
                    data-toggle="table"
                    data-unique-id="task_name">
                    <thead class="thead-light bg-transparent">
                        <tr>
                            <th data-checkbox="true" data-visible="false" data-field="select"></th>
                            <th data-sortable="true" data-field="name" class="bucket-name">NAME</th>
                            <th data-sortable="true" data-cell-style="nameStyle" data-field="size" class="bucket-size">SIZE</th>
                            <th data-cell-style="nameStyle" 
                                data-formatter='<div class="d-none">
                                    <button class="btn btn-default btn-xs btn-table btn-icon__xs bucket_delete"><i class="fas fa-trash-alt"></i></button>
                                    <button class="btn btn-default btn-xs btn-table btn-icon__xs bucket_setting"><i class="fas fa-gear"></i></button>
                                </div>'
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
    "click .bucket_delete": function (e, value, row, index) {
        e.stopPropagation();
        const vm = vueVm.registered_components.artifact
        vm.openConfirm('single');
    },
    "click .bucket_setting": function (e, value, row, index) {
        console.log("bucket_setting", row, index)
    }
}
