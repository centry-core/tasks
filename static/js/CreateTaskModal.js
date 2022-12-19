const CreateTaskModal = {
    delimiters: ['[[', ']]'],
    components: {
        'input-stepper': InputStepper,
    },
    props: ['locations', 'runtimes'],
    data() {
        return {
            task_name: null,
            error: {},

            location: 'default',
            cpu_quota: null,
            memory_quota: null,
            cloud_settings: {},
            timeout: 0,

            applyClicked: false,
            isValidBucket: false,
            isLoading: false,
        }
    },
     get_data() {

         return {
                task_name: this.task_name,
                runtime: this.runtime,
                task_handler: this.task_handler,
                location: this.location,
                parallel_runners: this.parallel_runners,
                cpu: this.cpu,
                memory: this.memory,
                cloud_settings: this.cloud_settings
            }
        },
    mounted() {
        $('#task_modal_parallel').closest('div.custom-input').hide()
        // this.get_data()
    },
    watch: {
    },
    methods: {
        handleFiles(e) {
            console.log('files', e)
            const file = e.target.files
            console.log(file)
            //([...files]).forEach(uploadFile)
        },
     uploadFile(e) {
            this.File = e.target.files;
        },
      onDrop(e) {
        console.log(e)
        this.File = e.dataTransfer.files;
        console.log(this.File)
        },
        setTimeout(val){
            this.timeout = val;
            console.log(this.timeout)
        },
        saveTask() {
            this.applyClicked = true;
            if (this.isValidBucket) {
                this.isLoading = true;
                fetch(`/api/v1/artifacts/buckets/${getSelectedProjectId()}`,{
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', dataType: 'json'},
                    body: JSON.stringify({
                        "name": this.bucketData.name,
                        "expiration_measure": (this.bucketData.retention).toLowerCase(),
                        "expiration_value": String(this.bucketData.expiration),
                    })
                }).then((response) => {
                    if (response.status === 200) {
                        return response.json();
                    } else if (response.status === 400){
                        throw new Error('Bucket\'s name is exist!');
                    }
                }).then(data => {
                    this.isLoading = false;
                    this.applyClicked = false;
                    this.bucketData.name = '';
                    $('#bucketModal').modal('hide');
                    this.$emit('refresh-bucket', data.id);
                    showNotify('SUCCESS', 'Bucket created.');
                }).catch(err => {
                    this.isLoading = false;
                    showNotify('ERROR', err);
                })
            }
        },
        hasError(value) {
            return value.length > 0;
        },
        showError(value) {
            return this.applyClicked ? value.length > 0 : true;
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
                                <div class="form-group col-6">
                                    <h5>Task Name</h5>
                                    <p>
                                        <h13>Enter name that describes the purpose of your function</h13>
                                    </p>
                                    <input 
                                          id="CreateTaskFields"
                                          type="text"
                                          v-model="task_name" 
                                          class="form-control form-control-alternative"
                                          placeholder="Task Name"
                                          :class="{ 'is-invalid': error.task_name }">
                                     
                                    <h5>Task Package</h5>
                                          <p>
                                            <h13>Upload .zip or .jar file with the code and any dependencies. Set the appropriate security permissions.</h13>
                                        </p>
                                     
                                    <div id="dragDropArea" class="drop-area" @dragover.prevent @drop.stop.prevent="onDrop">
                                          <input type="file" id="dropInput" multiple accept="*"@change="handleFiles">
                                          <label for="dropInput" class="mb-0 d-flex align-items-center justify-content-center">Drag & drop file or <span>&nbsp;browse</span></label>
                                    </div>
                                    
                            </div>
                            <div class="form-group col-6">
                                    <h5>Runtime</h5>
                                    <p>
                                        <h13>Choose the language to use to write your function</h13>
                                    </p>
                                     <select class="selectpicker bootstrap-select__b" data-style="btn" 
                                        id="CreateTaskFields"
                                        data-style="btn"
                                        v-model="runtime"
                                        :class="{ 'is-invalid': error.runtime }"
                                        >
                                            <option v-for="runtime in runtimes">
                                                [[runtime]]
                                            </option>
                                    </select>
                                     
                                     <h5>Task Handler</h5>
                                          <p>
                                            <h13>Function used to invoke a task</h13>
                                        </p>
                                        <input 
                                          id="CreateTaskFields"
                                          type="text"
                                          v-model="task_handler" 
                                          class="form-control form-control-alternative"
                                          placeholder="Handler name (e.g. lambda.handler)"
                                          :class="{ 'is-invalid': error.task_handler }">
                                </div>
                            </div>
                            <div class="d-flex align-items-center">
                             <Locations 
                                        v-model:location="location"
                                        v-model:cpu="cpu_quota"
                                        v-model:memory="memory_quota"
                                        v-model:cloud_settings="cloud_settings"
                                        modal_id="task_modal"
                                        v-bind="locations"
                                        >
                             </Locations>
                          <div class="custom-input ml-3">
                            <p class="custom-input_desc mb-1">Timeout, Sec</p>
                            <input-stepper 
                                :default-value="0"
                                @change="setTimeout"
                                :uniq_id="task_modal"
                            ></input-stepper>
                            </div>
                            
                            </div>
                            
                             <slot> </slot>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
}
