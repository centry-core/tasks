const TasksRunTaskModal = {
    data() {
        return {
            isLoading: false,
            testParams: [],
        }
    },
    mounted() {

    },
    methods: {
        fetchParameters() {

        }
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
                                    >Run<i v-if="isLoading" class="preview-loader__white ml-2"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                    <div class="modal-body">
                        <div class="section">
                            <div class="row">
                                <div class="col">
                                    <p class="font-h5 font-bold font-uppercase">Task parameters</p>
                                    <p class="font-h6 font-weight-400">Environment variables for the task</p>
                                </div>
                            </div>
                            <div class="row mt-4">
                                <div class="col">
                                    <div class="test_parameters_error"></div>
                                    <table class="table table-borderless params-table"
                                            id="testParams"
                                            data-toggle="table">
                                        <thead class="thead-light">
                                        <tr>
                                            <th scope="col" data-sortable="true" data-field="name"
                                                data-formatter="{{ custom_formatters.get('name', 'ParamsTable.inputFormatter') }}"
                                                data-width="144" data-width-unit="px"
                                            >
                                                Name
                                            </th>
                                            <th scope="col" data-sortable="true" data-field="default"
                                                data-formatter="{{ custom_formatters.get('default', 'ParamsTable.inputFormatter') }}"
                                            >
                                                Default value
                                            </th>
                                            <th scope="col" data-sortable="true" data-field="description"
                                                data-formatter="{{ custom_formatters.get('description', 'ParamsTable.inputFormatter') }}"
                                            >
                                                Description
                                            </th>
                                            <th scope="col" data-field="action"
                                                data-formatter="{{ custom_formatters.get('action', 'ParamsTable.parametersDeleteFormatter') }}"
                                                data-width="56" data-width-unit="px"
                                            >&nbsp;</th>
                                        </tr>
                                    </table>
                                </div>
                            </div>
                            <div class="row pt-2">
                                <div class="col">
                                    <button type="button" class="btn btn-sm btn-secondary">
                                        <i class="fas fa-plus mr-2"></i>Add Parameter
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
}