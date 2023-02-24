var report_formatters = {
    reportsStatusFormatter(value, row, index) {
        if (value) {
            return `<div data-toggle="tooltip" data-placement="top" title="${value}" style="color: var(--green)"><i class="fas fa-exclamation-circle error"></i> ${value}</div>`
        }
        if (!value) {
            return `<div data-toggle="tooltip" data-placement="top" title="${value}" style="color: var(--red)"><i class="fas fa-exclamation-circle error"></i> ${value}</div>`
        }
    }
}

var filesFormatter = {
    actions(value, row, index) {
        return `
        <div class="d-flex justify-content-end">
            <div class="dropdown_multilevel">
                <button class="btn btn-default btn-xs btn-table btn-icon__xs" type="button"
                        data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                        <a download href="/api/v1/artifacts/artifact/"
                            class="d-flex align-items-center">
                            <i class="icon__18x18 icon-download"></i>
                        </a>
                </button>
            </div>
        </div>
    `
    }
}