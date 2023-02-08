const TasksTable = {
    props: ['selected-task', 'task-info'],
    data() {
        return {
            webhook: '/task/eb6827fa-192b-4acf-b8c7-8780e3ea8613',
        }
    },
    methods: {
        copyWebhook() {
            const copiedText = document.querySelector('.web-hook-copy');
            const textInput = document.createElement("input");
            textInput.value = copiedText.textContent;
            document.body.appendChild(textInput);
            textInput.select();
            document.execCommand("copy");
            textInput.remove();
            showNotify('SUCCESS', 'Copied to clipboard')
        },
    },
    template: `
        <div class="card mt-3 mr-3 p-28 card-table-sm w-100">
            <div class="d-flex justify-content-between">
                <p class="font-h4 font-bold">{{ selectedTask.task_name }}</p>
                <div class="d-flex justify-content-end">
                    <button class="btn btn-secondary btn-icon btn-icon__purple mr-2"
                         data-toggle="modal" 
                         data-target="#RunTaskModal">
                        <i class="icon__18x18 icon-run"></i>
                    </button>
                    <button class="btn btn-secondary btn-icon btn-icon__purple">
                        <i class="fas fa-sync"></i>
                    </button>
                </div>
            </div>
            <table class="mt-24" style="width: max-content">
                <tr>
                    <td class="font-h6 text-gray-500 font-semibold font-uppercase pr-3">webhook</td>
                    <td class="font-h5 d-flex align-items-center">
                        <span class="web-hook-copy">{{ webhook }}</span>
                        <i class="icon__18x18 icon-multichoice ml-3" @click="copyWebhook"></i>
                    </td>
                </tr>
                <tr>
                    <td class="text-gray-500 font-h6 font-semibold font-uppercase pr-3">task id</td>
                    <td class="font-h5">46276428</td>
                </tr>
            </table>
        </div>
    `
}