from typing import Optional


from pylon.core.tools import web, log
from tools import VaultClient, api_tools

from ..tools.TaskManager import TaskManager


class RPC:
    @web.rpc('tasks_check_rabbit_queues', 'check_rabbit_queues')
    def check_rabbit_queues(self, task_id: Optional[str] = None, event: Optional[dict] = None, **kwargs):
        if not task_id:
            vault_client = VaultClient()
            secrets = vault_client.get_all_secrets()
            task_id = secrets['rabbit_queue_checker_id']
        log.info('check_rabbit_queues rpc %s', task_id)
        event = event or dict()
        task_manager = TaskManager(mode='administration')
        task_manager.run_task([event], task_id=task_id, queue_name="__internal")
