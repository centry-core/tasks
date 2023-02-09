const TasksCreateModal = {
    delimiters: ['[[', ']]'],
    components: {
        'input-stepper': InputStepper,
    },
    props: ['locations', 'runtimes'],
    data() {
        return this.initial_state()
    },
    mounted() {
        $('#task_modal_parallel').closest('div.custom-input').hide()
        // this.get_data()
    },
    computed: {
         test_parameters() {
            return ParamsTable.Manager("CreateTaskModal_test_params")
        },

    },
    methods: {
        initial_state() {
            return {
            task_name: null,

            runtime: null,
            task_handler: null,

            location: 'default',
            cpu_quota: 1,
            memory_quota: 4,
            cloud_settings: {},
            timeout: 5,

            isLoading: false,
            previewFile: null,
            file: null,
            error: {}
        }
        },
        get_data() {
         return {
             "task_name": this.task_name,
             "task_package": this.previewFile,
             "runtime": this.runtime,
             "task_handler": this.task_handler,
             "engine_location": this.location,
             "cpu_cores": this.cpu_quota,
             "memory": this.memory_quota,
             "timeout": this.timeout,
             "task_parameters": this.test_parameters.get()
         }
    },
     uploadFile(e) {
         const file =  e.target.files[0];
         console.log(file)
          this.previewFile = file.name
         this.file = file
         return file
        },
      onDrop(e) {
         const file =  e.dataTransfer.files[0];
         this.previewFile = file.name
          console.log(file)
          this.file = file
          return file
        },
        setTimeout(val){
            this.timeout = val;
        },
        async createTask(data){
            const resp = await fetch(`/api/v1/tasks/tasks/${getSelectedProjectId()}`,{
                method: 'POST',
                body: data,
            })
                return resp.json()
        },

        handleError(response) {
            try {
                response.json().then(
                    errorData => {
                        errorData.forEach(item => {
                            this.error = {[item.loc[0]]: item.msg}
                        })
                    }
                )
            } catch (e) {
                alertMain.add(e, 'danger-overlay')
            }
        },
        hasError(value) {
            return value.length > 0;
        },
        saveTask() {
            this.isLoading = true;
            let data = new FormData()
            console.log(this.get_data())
            data.append('data', JSON.stringify(this.get_data()))


           this.createTask(data).then(response => {
                if (response.ok) {
                    console.log('ok')
                    return response.json();
                } else if (response.status === 400){
                   this.handleError(response)
                }
            }).then(response => {
                data.append('file',this.file)
                this.createTask(data).then( response => {
                    if (response.ok) {
                        return response.json();
                    }
                    else if (response.status === 400){
                        this.handleError(response)
                }
                })
                $('#TasksCreateModal').modal('hide');
                showNotify('SUCCESS', 'Task Created.');
            }).catch(err => {
                this.isLoading = false;
                showNotify('ERROR', err);
            })

        },
    },
    template: `
        <div class="modal modal-base fixed-left fade shadow-sm" tabindex="-1" role="dialog" id="CreateTaskModal" xmlns="http://www.w3.org/1999/html">
            <div class="modal-dialog modal-dialog-aside" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <div class="row w-100">
                            <div class="col">
                                <h2>Create task</h2>
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
                            <div class="row" id="CreateTaskFields">
                                <div class="form-group col">
                                    <p class="font-h5 font-bold">Task Name</p>
                                    <p class="font-h6 font-weight-400">Enter name that describes the purpose of your function</p>
                                    <input 
                                          id="CreateTaskFields"
                                          type="text"
                                          v-model="task_name" 
                                          class="form-control form-control-alternative mb-3 mt-2"
                                          placeholder="Task Name"
                                          :class="{ 'is-invalid': error.task_name }">
                                    <p class="font-h5 font-bold">Task Package</p>
                                    <p class="font-h6 font-weight-400">Upload .zip or .jar file with the code and any dependencies.</p>
                                     
                                    <div id="dragDropArea" class="drop-area mb-3 mt-2" @dragover.prevent @drop.stop.prevent="onDrop">
                                          <input type="file" id="dropInput" multiple accept="*" @change="uploadFile">
                                          <label for="dropInput" class="mb-0 d-flex align-items-center justify-content-center">Drag & drop file or <span>&nbsp;browse</span></label>
                                    </div>
                                    <span v-show="previewFile" class="preview-area_item preview-area_close"> [[previewFile]]</span>
                                </div>
                                <div class="form-group col">
                                    <p class="font-h5 font-bold">Runtime</p>
                                    <p class="font-h6 font-weight-400">Choose the language to use to write your function</p>
                                    <div class="custom-input w-100-imp">
                                        <select class="selectpicker bootstrap-select__b mb-3 mt-2" 
                                            id="CreateTaskFields"
                                            data-style="btn"
                                            v-model="runtime"
                                            :class="{ 'is-invalid': error.runtime }"
                                            >
                                                <option v-for="runtime in runtimes">
                                                    [[runtime]]
                                                </option>
                                        </select>
                                    </div>
                                    <p class="font-h5 font-bold">Task Handler</p>
                                    <p class="font-h6 font-weight-400">Function used to invoke a task</p>
                                        <input 
                                            id="CreateTaskFields"
                                            type="text"
                                            v-model="task_handler" 
                                            class="form-control form-control-alternative mb-3 mt-2"
                                            placeholder="Handler name (e.g. lambda.handler)"
                                            :class="{ 'is-invalid': error.task_handler }">
                                </div>
                            </div>
                            <Locations 
                                v-model:location="location"
                                v-model:cpu="cpu_quota"
                                v-model:memory="memory_quota"
                                v-model:cloud_settings="cloud_settings"
                                v-bind="locations"
                                >
                            </Locations>
                            <slot></slot>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
}
