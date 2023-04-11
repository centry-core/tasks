const TasksLocation = {
    delimiters: ['[[', ']]'],
    props: ['public_regions', 'cloud_settings', 'project_regions', 'cloud_regions', 'location', 'parallel_runners', 'timeout', 'cpu', 'memory', 'modal_id'],
    emits: ['update:location', 'update:parallel_runners', 'update:cpu', 'update:timeout', 'update:memory', 'update:cloud_settings'],
    template: `
    <div class="section">
    <div class="row">
        <div class="col">
            <p class="font-h5 font-bold font-uppercase">Load configuration</p>
            <p class="font-h6 font-weight-400">Specify engine region and load profile. CPU Cores and Memory are distributed for each parallel
                runner
            </p>
        </div>
    </div>
    <div class="d-flex py-4">
        <div class="custom-input w-100-imp">
            <p class="custom-input_desc font-semibold mb-1">Engine location</p>
            <select class="selectpicker bootstrap-select__b" data-style="btn" 
                v-model="location_"
            >
                <optgroup label="Public pool" v-if="public_regions_.length > 0">
                    <option v-for="item in public_regions_">[[ item ]]</option>
                </optgroup>
                <optgroup label="Project pool" v-if="project_regions_.length > 0">
                    <option v-for="item in project_regions_">[[ item ]]</option>
                </optgroup>
                <optgroup label="Cloud pool" v-if="cloud_regions_.length > 0">
                    <option v-for="item in cloud_regions_">[[ item.name ]]</option>
                </optgroup>
            </select>
        </div>
        
        <div class="custom-input ml-3">
            <p class="custom-input_desc font-semibold mb-1">CPU Cores</p>
            <input-stepper 
                :default-value="cpu"
                :uniq_id="modal_id + '_cpu'"
                @change="val => (cpu_ = val)"
            ></input-stepper>
        </div>
        <div class="custom-input ml-3">
            <p class="custom-input_desc font-semibold mb-1">Memory, Gb</p>
            <input-stepper 
                :default-value="memory"
                :uniq_id="modal_id + '_memory'"
                @change="val => (memory_ = val)"
            ></input-stepper>
        </div>
        <div class="custom-input mx-3">
            <p class="custom-input_desc font-semibold mb-1">Timeout, Sec</p>
            <input-stepper 
                :default-value="timeout"
                :uniq_id="modal_id + '_timeout'"
                @change="val => (timeout_ = val)"
            ></input-stepper>
        </div>

    </div>
</div>
    `,
    data() {
        return {
            location_: 'default',
            cpu_: 1,
            memory_: 4,
            // timeout_: 500,
            public_regions_: ['default'],
            project_regions_: [],
            cloud_regions_: [],
        }
    },
    computed: {
        is_cloud_location() {
            return this.cloud_regions_.filter(el => el.name === this.location_).length !== 0;
        },
        chosen_location_settings() {
            if (!this.is_cloud_location) return {}
            return this.cloud_regions_.find(el => el.name === this.location_).cloud_settings
        }
    },
    mounted() {
        $(document).on('vue_init', () => {
            this.fetch_locations()
            if (this.$props.location) this.location_ = this.$props.location
            if (this.$props.cpu) this.cpu_ = this.$props.cpu
            if (this.$props.memory) this.memory_ = this.$props.memory
            if (this.$props.timeout) this.timeout_ = this.$props.timeout
            if (this.$props.public_regions) this.public_regions_ = this.$props.public_regions
            if (this.$props.project_regions) this.project_regions_ = this.$props.project_regions
            if (this.$props.cloud_regions) this.cloud_regions_ = this.$props.cloud_regions
            this.$nextTick(this.refresh_pickers)
            this.$nextTick(this.refresh_pickers)
        })
    },
    watch: {
        location_(newValue) {
            this.$emit('update:location', newValue)
            if (this.$props.cloud_settings.id === this.chosen_location_settings.id) {
                this.cloud_settings_ = {...this.chosen_location_settings, ...this.$props.cloud_settings}
            } else
                this.cloud_settings_ = this.chosen_location_settings
            this.$emit('update:cloud_settings', this.cloud_settings_)
        },
        location(newValue) {
            this.location_ = newValue
        },
        cpu_(newValue) {
            this.$emit('update:cpu', newValue)
        },
        cpu(newValue) {
            this.cpu_ = newValue
        },
        timeout_(newValue) {
            this.$emit('update:timeout', newValue)
        },
        timeout(newValue) {
            this.timeout_ = newValue
        },
        memory_(newValue) {
            this.$emit('update:memory', newValue)
        },
        memory(newValue) {
            this.memory_ = newValue
        },
        public_regions_(newValue) {
            this.$nextTick(this.refresh_pickers)
        },
        project_regions_(newValue) {
            this.$nextTick(this.refresh_pickers)
        },
        cloud_regions_(newValue) {
            this.$nextTick(this.refresh_pickers)
        },
    },
    methods: {
        async fetch_locations() {
            const api_url = this.$root.build_api_url('shared', 'locations')
            const resp = await fetch(`${api_url}/${getSelectedProjectId()}`)
            if (resp.ok) {
                const {public_regions, project_regions, cloud_regions} = await resp.json()
                this.public_regions_ = public_regions
                this.project_regions_ = project_regions
                this.cloud_regions_ = cloud_regions
            } else {
                console.warn('Couldn\'t fetch locations. Resp code: ', resp.status)
            }
        },
        refresh_pickers() {
            $(this.$el).find('.selectpicker').selectpicker('redner').selectpicker('refresh')
        }
    }
}