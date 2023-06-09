const EmailRecipient = {
    props: ['email', 'index'],
    emits: ['remove'],
    delimiters: ['[[', ']]'],
    template: `
        <li class="list-group-item d-inline-flex justify-content-between py-2 pr-2 pl-3 border-0">
            <p class="font-h5 font-weight-400">[[ email ]]</p>
            <button
                type="button"
                class="btn btn-default btn-xs btn-icon__xs mr-2"
                title="remove"
                @click.prevent="remove"
            >
                <i class="icon__16x16 icon-close__16"></i>
            </button>
        </li>
    `,
    methods: {
        remove() {
            this.$emit('remove', this.index)
        }
    }
}

const EmailIntegration = {
    delimiters: ['[[', ']]'],
    components: {
        EmailRecipient
    },
    props: ['monitoring_settings'],
    emits: ['update:monitoring_settings'],
    data() {
        return this.initialState()
    },
    computed: {
        hasErrors() {
            return this.errors.length + this.warnings.length > 0
        },
    },
    methods: {
        add(email) {
            if (email === '') return;
            if (!this.validateEmail(email)) {
                this.errors.push(`Email ${email} is invalid`)
                return;
            }
            if (!this.validateUniqueness(email)) {
                this.warnings.push(`Email ${email} is already added`)
                return;
            }
            this.recipients.push(email);
        },
        handleAdd() {
            this.errors = []
            this.warnings = []
            this.email.split(',').forEach(i => {
                this.add(i.trim().toLowerCase())
            })
            if (!this.hasErrors) {
                this.email = ''
            }
        },
        validateUniqueness(email) {
            return this.recipients.find(e => e.toLowerCase() === email.toLowerCase()) === undefined
        },
        validateEmail(email) {
            return /^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/.test(email)
        },
        removeIndex(index) {
            this.recipients.splice(index, 1)
        },

        initialState() {
            return {
                email: '',
                recipients: this.monitoring_settings.recipients || [],
                errors: [],
                warnings: [],
            }
        }
    },
    watch: {
        recipients: {
            handler: function (val) {
                this.$emit('update:monitoring_settings', {
                    ...this.monitoring_settings,
                    recipients: val
                })
            },
            deep: true
        },
        monitoring_settings: {
            handler: function (val) {
                this.recipients = val.recipients || []
            },
            deep: true
        }
    },
    template: `
        <div class="mt-3">
            <p class="font-h5 font-semibold">Recipients</p>
            <div class="input-group d-flex mt-1">
                <div class="custom-input flex-grow-1">
                    <input type="email" placeholder="Recipients' emails comma-separated"
                       v-model="email"
                       :class="{ 'is-invalid': hasErrors }"
                >
                </div>
                <button class="btn btn-lg btn-secondary ml-2" type="button"
                    @click="handleAdd"
                    :disabled="email === ''"
                    :class="{ 'btn-danger': hasErrors }"
                >
                    Add
                </button>
            </div>
            <div class="invalid-feedback"
                 style="display: block"
                 v-if="hasErrors"
            >
                <div v-for="error in errors">
                    [[ error ]]
                </div>
                <div v-for="warning in warnings" class="text-warning">
                    [[ warning ]]
                </div>
            </div>
            <ul class="list-group list-group-flush border rounded mt-2" v-if="recipients.length > 0" style="max-height: 170px; overflow-y: scroll">
                <EmailRecipient
                        v-for="(item, index) in recipients"
                        :key="index"
                        :index="index"
                        :email="item"
                        @remove="removeIndex"
                ></EmailRecipient>
            </ul>
        </div>
    `
}


const TasksMonitoring = {
    delimiters: ['[[', ']]'],
    components: {
        EmailIntegration: EmailIntegration,
    },
    props: ['integrations', 'monitoring_settings', 'modal_id'],
    emits: ['update:monitoring_settings'],
    data() {
        return this.initialState()
    },
    watch: {
        settings(newValue) {
            this.$emit('update:monitoring_settings', newValue)
        },
        monitoring_settings(newValue) {
            this.settings = newValue
            this.$nextTick(this.refresh_pickers)
        }
    },
    methods: {
        initialState() {
            return {
                settings: this.monitoring_settings,
            }
        },
        refresh_pickers() {
            $(this.$el).find('.selectpicker').selectpicker('redner').selectpicker('refresh')
        }
    },
    template: `
    <div class="section" v-if="integrations">
        <div class="row">
            <div class="col">
                <p class="font-h5 font-bold font-uppercase">Monitoring</p>
                <p class="font-h6 font-weight-400">
                    Specify monitoring parameters
                </p>
            </div>
        </div>
        <div class="d-flex py-4">
            <div class="custom-input w-100-imp">
                <p class="custom-input_desc font-semibold mb-1">Monitoring integration</p>
                <select class="selectpicker bootstrap-select__b" data-style="btn" 
                    v-model="settings.integration"
                >   
                    <option :value="null">Nothing selected</option>
                    <option v-for="item in integrations" :value="item.task_id">[[ item.name ]] [[item.description]]</option>
                </select>
            </div>
            <div class="custom-input ml-3">
                <p class="custom-input_desc font-semibold mb-1">Failed tasks </p>
                <input-stepper 
                    :default-value="settings.failed_tasks"
                    :uniq_id="modal_id + 'settings.failed_tasks'"
                    @change="val => (settings.failed_tasks = val)"
                ></input-stepper>
        </div>
        </div>
        <EmailIntegration v-if="monitoring_settings.integration" :monitoring_settings="monitoring_settings" />
    </div>
    `,
}
register_component('tasks-monitoring', TasksMonitoring)