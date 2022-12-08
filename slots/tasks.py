from pylon.core.tools import web  # pylint: disable=E0611,E0401
from tools import auth  # pylint: disable=E0401


class Slot:  # pylint: disable=E1101,R0903
    @web.slot('tasks_content')
    def content(self, context, slot, payload):
        from pylon.core.tools import log
        log.info('slot: [%s], payload: %s', slot, payload)
        with context.app.app_context():
            return self.descriptor.render_template(
                'tasks/content.html'
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