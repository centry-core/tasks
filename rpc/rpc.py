import json

from pylon.core.tools import web, log
from tools import rpc_tools

from ..models.tasks import Task
from ..tools.task_tools import create_task


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

    @web.rpc('tasks_update_env')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def update_env(self, project_id: int, task_id: int, env_vars: str, rewrite: bool = True) -> bool:
        project = self.context.rpc_manager.call.project_get_or_404(project_id)
        if rewrite:
            Task.query.filter(Task.task_id == task_id).update({Task.env_vars: env_vars})
        else:
            task_vars = Task.query.with_entities(Task.env_vars).filter(Task.task_id == task_id).first()
            try:
                task_vars = task_vars[0]
            except IndexError:
                log.error('Cannot find task with id: %s', task_id)
                return False
            task_vars = json.loads(task_vars)
            task_vars.update(**json.loads(env_vars))
            Task.query.filter(Task.task_id == task_id).update({Task.env_vars: task_vars})
        Task.commit()
        return True
