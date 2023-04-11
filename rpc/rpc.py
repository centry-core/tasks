import json
from typing import Optional

from pylon.core.tools import web, log
from tools import rpc_tools

from ..models.tasks import Task
from ..tools.TaskManager import TaskManager


class RPC:
    @web.rpc('tasks_count')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def tasks_count(self, project_id: Optional[int] = None, mode: str = 'default') -> int:
        return TaskManager(project_id=project_id, mode=mode).count_tasks()

    @web.rpc('list_tasks')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def list_tasks(self, project_id: Optional[int] = None, mode: str = 'default') -> list:
        return TaskManager(project_id=project_id, mode=mode).list_tasks()

    @web.rpc('tasks_update_env')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def update_env(self, *, task_id: int, env_vars: str, rewrite: bool = True, **kwargs) -> bool:
        return TaskManager.update_task_env(task_id=task_id, env_vars=env_vars, rewrite=rewrite)
