const TasksRunTaskModal = {
    props: ['selectedTask', 'isLoadingRun'],
    data() {
        return {
            isLoading: false,
        }
    },
    mounted() {
        const vm = this;
        $("#RunTaskModal").on("show.bs.modal", function (e) {
            vm.fetchParameters().then((data) => {
                const taskParams = data.rows[0].task_parameters;
                if (taskParams) {
                    vm.test_parameters.set(taskParams);
                } else (
                    vm.test_parameters.set([])
                )
            })
        });
    },
    computed: {
        test_parameters() {
            return ParamsTable.Manager("runTaskModal_test_params")
        },
    },
    methods: {
        async fetchParameters() {
            const api_url = this.$root.build_api_url('tasks', 'tasks')
            const res = await fetch (`${api_url}/${getSelectedProjectId()}/${this.selectedTask.task_id}?get_parameters=true`,{
                method: 'GET',
            })
            return res.json();
        },
        handleRunTask() {
            this.$emit('is-loading');
            this.runTask().then(() => {
                this.$emit('run-task');
            })
        },
        async runTask() {
            // const params = [
            //         { name: "user", default: "user", type: "string", description: "", action: "" },
            //         { name: "password", default: "password", type: "string", description: "", action: "" },
            //         { name: "vhost", default: "carrier", type: "string", description: "", action: "" }
            //     ]
            const api_url = this.$root.build_api_url('tasks', 'run_task')
            const resp = await fetch(`${api_url}/${getSelectedProjectId()}/${this.selectedTask.task_id}`,{
                method: 'POST',
                headers: {
                    "Content-Type": "application/json",
                },
                body:  JSON.stringify(this.test_parameters.get()),
                // body:  JSON.stringify(params),
            })
            return resp.json()
        },

    },
    template: `
    <div class="modal modal-base fixed-left fade shadow-sm" tabindex="-1" role="dialog" id="RunTaskModal" xmlns="http://www.w3.org/1999/html">
            <div class="modal-dialog modal-dialog-aside" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <div class="row w-100">
                            <div class="col">
                                <h2>Run Task</h2>
                            </div>
                            <div class="col-xs d-flex">
                                <button type="button" class="btn  btn-secondary mr-2" data-dismiss="modal" aria-label="Close">
                                    Cancel
                                </button>
                                <button type="button" 
                                    class="btn btn-basic d-flex align-items-center"
                                    @click="handleRunTask"
                                    >Run<i v-if="isLoadingRun" class="preview-loader__white ml-2"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                    <div class="modal-body">
                        <div class="section">
                            <slot></slot>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
}
