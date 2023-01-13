from pylon.core.tools import web  # pylint: disable=E0611,E0401
from tools import auth  # pylint: disable=E0401
from ..tools.constants import RUNTIME_MAPPING


class Slot:  # pylint: disable=E1101,R0903
    @web.slot('tasks_content')
    def content(self, context, slot, payload):
        from pylon.core.tools import log
        project_id = context.rpc_manager.call.project_get_id()
        public_regions = context.rpc_manager.call.get_rabbit_queues("carrier")
        public_regions.remove("__internal")
        project_regions = context.rpc_manager.call.get_rabbit_queues(f"project_{project_id}_vhost")
        cloud_regions = context.rpc_manager.timeout(5).integrations_get_cloud_integrations(
                project_id)

        log.info('slot: [%s], payload: %s', slot, payload)
        with context.app.app_context():
            return self.descriptor.render_template(
                'tasks/content.html',
                locations={
                    'public_regions': public_regions,
                    'project_regions': project_regions,
                    "cloud_regions": cloud_regions
                },
                runtimes=list(RUNTIME_MAPPING.keys())
            )

    @web.slot('tasks_scripts')
    def scripts(self, context, slot, payload):
        from pylon.core.tools import log
        log.info('slot: [%s], payload: %s', slot, payload)
        with context.app.app_context():
            return self.descriptor.render_template(
                'tasks/scripts.html',
            )

    @web.slot('tasks_styles')
    def styles(self, context, slot, payload):
        from pylon.core.tools import log
        log.info('slot: [%s], payload: %s', slot, payload)
        with context.app.app_context():
            return self.descriptor.render_template(
                'tasks/styles.html',
            )
