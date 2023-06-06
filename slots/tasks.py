from pylon.core.tools import web, log  # pylint: disable=E0611,E0401
from tools import auth, theme  # pylint: disable=E0401

from ..constants import RUNTIME_MAPPING


class Slot:  # pylint: disable=E1101,R0903
    @web.slot('tasks_content')
    @auth.decorators.check_slot(["configuration.tasks"],
                                access_denied_reply=theme.access_denied_part)
    def content(self, context, slot, payload):
        project_id = context.rpc_manager.call.project_get_id()
        public_regions = context.rpc_manager.call.get_rabbit_queues("carrier", True)
        project_regions = context.rpc_manager.call.get_rabbit_queues(
            f"project_{project_id}_vhost")
        cloud_regions = context.rpc_manager.timeout(5).integrations_get_cloud_integrations(
            project_id)
        available_integrations = context.rpc_manager.call.integrations_get_all_integrations_by_name(
            project_id,
            integration_name='email_template',
        )
        available_integrations = [integration.dict(
            exclude={'section'}
        ) for integration in available_integrations]
        log.info('available_integrations %s', available_integrations)
        with context.app.app_context():
            return self.descriptor.render_template(
                'tasks/content.html',
                locations={
                    'public_regions': public_regions,
                    'project_regions': project_regions,
                    "cloud_regions": cloud_regions
                },
                runtimes=list(RUNTIME_MAPPING.keys()),
                integrations=available_integrations,
            )

    @web.slot('tasks_scripts')
    @auth.decorators.check_slot(["configuration.tasks"])
    def scripts(self, context, slot, payload):
        # log.info('slot: [%s], payload: %s', slot, payload)
        with context.app.app_context():
            return self.descriptor.render_template(
                'tasks/scripts.html',
            )

    @web.slot('tasks_styles')
    @auth.decorators.check_slot(["configuration.tasks"])
    def styles(self, context, slot, payload):
        # log.info('slot: [%s], payload: %s', slot, payload)
        with context.app.app_context():
            return self.descriptor.render_template(
                'tasks/styles.html',
            )
