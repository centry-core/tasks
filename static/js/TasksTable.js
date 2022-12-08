const TasksTable = {
    props: ['selected-task', 'task-info'],
    methods: {

    },
    template: `
        <div class="card mt-3 mr-3 card-table-sm w-100" @dragover.prevent @drop.prevent>
            <div class="row p-3">
                <div class="col-4">
                    <h4>{{ selectedTask }}</h4>
                    <br>
                    <div>
                     <h4 class="text-gray-500 text-uppercase"> webhook  </h4> 
                      <p> {{ taskInfo.webhook }}</p>
                      
                      <h4 class="text-gray-500 text-uppercase"> task id </h4> 
                     <p> {{ taskInfo.task_id }} </p>
                     </div>
                     
                   
                </div>
                <div class="col-8">
                    <div class="d-flex justify-content-end">
                        <button type="button" class="btn btn-secondary btn-sm btn-icon__sm mr-2">
                            <i class="fas fa-sync"></i>
                        </button>
                        <button type="button" 
                            @click=""
                            class="btn btn-secondary btn-sm btn-icon__sm mr-2">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                </div>
            </div>
            <div class="card-body" @drop="">
                <table class="table table-borderless"
                    id="task-table"
                    data-toggle="table"
                    data-page-list="[5, 10, 15]"
                    data-pagination="true"
                    data-pagination-pre-text="<img src='/design-system/static/assets/ico/arrow_left.svg'>"
                    data-pagination-next-text="<img src='/design-system/static/assets/ico/arrow_right.svg'>"
                    data-page-size=5>
                    <thead class="thead-light">
                        <tr>
                            <th scope="col" data-checkbox="true"></th>
                            <th scope="col" data-sortable="true" data-field="ts">Date</th>
                            <th scope="col" data-sortable="true" data-field="task_id">Type</th>
                            <th scope="col" data-sortable="true" data-field="log" class="w-100">Log</th>
                        </tr>
                    </thead>
                    <tbody>
                    </tbody>
                </table>
            </div>
        </div>
    `
}