import logging

from flask import request
from flask_restful import Resource
from ....shared.tools.constants import APP_HOST
from ...models.tasks import Task
from ...models.results import TaskResults


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):

        task_id = request.args.get("task_id", None)
        task_name = request.args.get("task_name", None)
        logging.info(f'task_id {task_id} task_name {task_name}')
        task_result_id = TaskResults.query.get_or_404(task_id).task_result_id

        if not task_id or not task_name:
            return {"message": ""}, 404

        task = Task.query.filter_by(project_id=project_id, task_id=task_id, task_name=task_name).first()
        if not task:
            return {"message": f"no such task_id found {task_id}"}, 404
        websocket_base_url = APP_HOST.replace("http://", "ws://").replace("https://", "wss://")
        websocket_base_url += "/loki/api/v1/tail"
        logs_query = "{" + f'hostname="{task_name}", task_id="{task.task_id}",project="{project_id}", task_result_id="{task_result_id}"' + "}"

        logs_start = 0
        logs_limit = 10000000000

        return {
            "websocket_url": f"{websocket_base_url}?query={logs_query}&start={logs_start}&limit={logs_limit}"
        }, 200
