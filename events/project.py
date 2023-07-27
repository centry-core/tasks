from pylon.core.tools import log, web


class Event:
    @web.event("project_created")
    def run_queue_checker(self, context, event, project: dict):
        self.check_rabbit_queues()
