from pylon.core.tools import web, log
from tools import rpc_tools

from ..models.tasks import Task
from ..utils import create_task


class RPC:
    @web.rpc('tasks_count')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def tasks_count(self, project_id):
        return Task.tasks_count(project_id)

    @web.rpc('list_tasks')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def list_tasks(self, project_id):
        return Task.list_tasks(project_id)

    @web.rpc('task_create')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def create(self, project, filename, args):
        log.info(f"Filename: {filename}")
        return create_task(project, filename, args)
