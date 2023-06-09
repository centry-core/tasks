const TasksUpdateModal = {
    components: {
        'input-stepper': InputStepper,
    },
    props: ['runtimes', 'selected-task', 'integrations'],
    data() {
        return this.initial_state()
    },
    mounted() {
        const vm = this;
        $("#UpdateTaskModal").on("show.bs.modal", function (e) {
            vm.fetchTaskInfo().then((data) => {
                vm.setTaskData(data.rows[0])
            })
        });
        $('#selectUpdatedRuntime').on('change', (e) => {
            this.runtime = e.target.value;
        })
        $('#task_modal_parallel').closest('div.custom-input').hide();
    },
    computed: {
        test_parameters() {
            return ParamsTable.Manager("updateTaskModal_test_params")
        },
        isValidDA() {
            return this.isSubmitted && !this.previewFile;
        },
    },
    methods: {
        setTaskData(taskData) {
            this.$nextTick(() => {
                $('#selectUpdatedRuntime').val(taskData.runtime);
                $('#selectUpdatedRuntime').selectpicker('refresh');
            })
            this.runtime = taskData.runtime;
            this.task_name = taskData.task_name;
            this.task_handler = taskData.task_handler;
            this.previewFile = taskData.zippath;
            const envVars = JSON.parse(taskData.env_vars);
            this.monitoring_settings = envVars.monitoring_settings  || this.initial_state().monitoring_settings;
            if (envVars.task_parameters) {
                this.test_parameters.set(envVars.task_parameters);
            }
        },
        async fetchTaskInfo() {
            const api_url = this.$root.build_api_url('tasks', 'tasks')
            const res = await fetch(`${api_url}/${getSelectedProjectId()}/${this.selectedTask.task_id}`, {
                method: 'GET',
            })
            return res.json();
        },
        initial_state() {
            return {
                task_name: null,
                runtime: null,
                task_handler: null,
                isLoading: false,
                previewFile: '',
                file: null,
                isSubmitted: false,
                monitoring_settings: {
                    integration: null,
                    failed_tasks: 5,
                    recipients: [],
                },
            }
        },
        get_data() {
            return {
                "task_name": this.task_name,
                "task_handler": this.task_handler,
                "runtime": this.runtime,
                "task_package": this.previewFile,
                "task_parameters": this.test_parameters.get(),
                "monitoring_settings": this.monitoring_settings,
            }
        },
        uploadFile(e) {
            const file = e.target.files[0];
            this.previewFile = file.name
            this.file = file
            return file
        },
        onDrop(e) {
            const file = e.dataTransfer.files[0];
            this.previewFile = file.name
            this.file = file
            return file
        },
        async updateTaskAPI(data) {
            const api_url = this.$root.build_api_url('tasks', 'tasks')
            const resp = await fetch(`${api_url}/${getSelectedProjectId()}/${this.selectedTask.task_id}`, {
                method: 'PUT',
                body: data,
            })
            return resp.json()
        },
        removeFile() {
            this.previewFile = null;
            this.file = null;
        },
        saveTask() {
            const form = document.getElementById('formUpdate');
            if (!this.isSubmitted) {
                form.classList.add('was-validated');
            }
            this.isSubmitted = true;
            if (form.checkValidity() === true && this.previewFile) {
                this.isLoading = true;
                let data = new FormData();
                if (this.file) data.append('file', this.file);
                const prepareData = this.file ? this.get_data() : {...this.get_data(), "task_package": ""}
                data.append('data', JSON.stringify(prepareData));
                this.updateTaskAPI(data).then(response => {
                    showNotify('SUCCESS', 'Task Updated.');
                    this.$emit('update-tasks-list', response.task_id);
                    $('#UpdateTaskModal').modal('hide');
                    form.classList.remove('was-validated');
                    this.removeFile();
                })
                    .catch(err => {
                        showNotify('ERROR', err);
                    }).finally(() => {
                    this.isLoading = false;
                })
            }
        },
    },
    template: `
        <div class="modal modal-base fixed-left fade shadow-sm" tabindex="-1" role="dialog" id="UpdateTaskModal" xmlns="http://www.w3.org/1999/html">
            <div class="modal-dialog modal-dialog-aside" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <div class="row w-100">
                            <div class="col">
                                <h2>Update task</h2>
                            </div>
                            <div class="col-xs d-flex">
                                <button type="button" class="btn  btn-secondary mr-2" data-dismiss="modal" aria-label="Close">
                                    Cancel
                                </button>
                                <button type="button" 
                                    class="btn btn-basic d-flex align-items-center"
                                    @click="saveTask"
                                >Save<i v-if="isLoading" class="preview-loader__white ml-2"></i></button>
                            </div>
                        </div>
                    </div>
                    <div class="modal-body">
                        <div class="section">
                            <form class="needs-validation needs-validation__custom d-grid grid-column-2 gap-50" id="formUpdate" novalidate>
                                <div class="form-group">
                                    <p class="font-h5 font-bold">Task Name</p>
                                    <p class="font-h6 font-weight-400">Enter name that describes the purpose of your function</p>
                                    <div class="custom-input mb-3 mt-2">
                                        <input type="text"
                                            class="form-control"
                                            required
                                            placeholder="Task Name"
                                            v-model='task_name'>
                                    </div>
                                
                                    <p class="font-h5 font-bold">Task Package</p>
                                    <p class="font-h6 font-weight-400">Upload .zip or .jar file with the code and any dependencies.</p>
                                    <div id="dragDropAreaUpdate" 
                                        class="drop-area mb-3 mt-2" 
                                        :class="{'drop-area__invalid': isValidDA }"
                                        @dragover.prevent @drop.stop.prevent="onDrop">
                                          <input type="file" id="dropInputUpdate" multiple accept="*" @change="uploadFile">
                                          <label for="dropInputUpdate" class="mb-0 d-flex align-items-center justify-content-center">Drag & drop file or <span>&nbsp;browse</span></label>
                                    </div>
                                    <span v-show="previewFile" class="preview-area_item"> 
                                        {{ previewFile }}
                                        <i class="icon__16x16 icon-close__16" @click="removeFile"></i>
                                    </span>
                                </div>
                                <div class="form-group">
                                    <p class="font-h5 font-bold">Runtime</p>
                                    <p class="font-h6 font-weight-400">Choose the language to use to write your function</p>
                                    <div class=" w-100-imp">
                                        <select class="selectpicker bootstrap-select__need-validation mb-3 mt-2" 
                                            id="selectUpdatedRuntime"
                                            data-style="btn"
                                            required
                                            >
                                            <option v-for="runtime in runtimes">
                                                {{ runtime }}
                                            </option>
                                        </select>
                                    </div>
                                    <p class="font-h5 font-bold">Task Handler</p>
                                    <p class="font-h6 font-weight-400">Function used to invoke a task</p>
                                    <div class="custom-input mb-3 mt-2">
                                        <input 
                                            id="CreateTaskFields"
                                            type="text"
                                            required
                                            v-model="task_handler" 
                                            class="form-control"
                                            placeholder="Handler name (e.g. lambda.handler)">
                                    </div>
                                </div>
                            </form>
                            <slot></slot>
                            <tasks-monitoring v-if="integrations.length > 0"
                                :integrations="integrations"
                                :monitoring_settings="monitoring_settings"
                            ></tasks-monitoring>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
}
