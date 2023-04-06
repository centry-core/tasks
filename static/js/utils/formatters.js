var report_formatters = {
    reportsStatusFormatter(value, row, index) {
        if (value === 'Done') {
            return `<div style="color: #18B64D" class="d-flex align-items-center"><i class="icon__16x16 icon-success__16"></i> Done</div>`
        }
        if (value === 'Failed') {
            return `<div title="${value}" style="color: var(--red)" class="d-flex align-items-center"><i class="icon__16x16 icon-test-failed__16"></i> Failed</div>`
        }
        if (value === 'In progress...') {
            return `<div title="${value}" style="color: var(--blue)" class="d-flex align-items-center"><i class="fas fa-spinner fa-spin fa-secondary"></i><span class="ml-1" style="white-space: nowrap;">In progress...</span></div>`
        }
    },
}

var filesFormatter = {
    actions(value, row, index) {
        const api_url = V.build_api_url('tasks', 'download_task_log')
        const url = row.project_id ? `${api_url}/${row.project_id}/${row.task_name}/${row.task_result_id}` : '';
        if (row.task_status !== 'In progress...') {
            return `
                <div class="d-flex justify-content-end">
                    <div class="dropdown_multilevel">
                        <button class="btn btn-default btn-xs btn-table btn-icon__xs" type="button">
                            <a download href="${url}"
                                class="d-flex align-items-center">
                                <i class="icon__18x18 icon-download"></i>
                            </a>
                        </button>
                    </div>
                </div>
        `
        } else {
            return ''
        }
    }
}
