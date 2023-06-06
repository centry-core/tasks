from pylon.core.tools import web, log
from tools import auth, theme

from ..constants import RUNTIME_MAPPING


class Slot:
    @web.slot('administration_tasks_content')
    @auth.decorators.check_slot(["configuration.tasks"], access_denied_reply=theme.access_denied_part)
    def content(self, context, slot, payload):
        public_regions = context.rpc_manager.call.get_rabbit_queues("carrier", True)

        available_integrations = context.rpc_manager.call.integrations_get_administration_integrations_by_name(
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
                    'project_regions': [],
                    'cloud_regions': []
                },
                runtimes=list(RUNTIME_MAPPING.keys()),
                integrations=available_integrations,
            )

    @web.slot('administration_tasks_scripts')
    @auth.decorators.check_slot(["configuration.tasks"])
    def scripts(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'tasks/scripts.html',
            )

    @web.slot('administration_tasks_styles')
    @auth.decorators.check_slot(["configuration.tasks"])
    def styles(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'tasks/styles.html',
            )
