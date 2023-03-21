from flask import request, make_response
from flask_restful import Resource

from ...models.tasks import Task
from ...models.results import TaskResults
from ...tools.task_tools import run_task

from tools import secrets_tools


class API(Resource):
    url_params = [
        '<int:project_id>/<string:task_id>',
    ]

    def __init__(self, module):
        self.module = module

    def _get_task(self, project_id: int, task_id: str):
        return self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id), \
               Task.query.filter_by(task_id=task_id).first()

    def get(self, project_id: int, task_id: str):
        # args = self.get_parser.parse_args(strict=False)
        args = request.args
        project, task = self._get_task(project_id, task_id)  # todo: why do we extra query project?
        if args.get("exec"):
            return secrets_tools.unsecret(
                value=task.to_json(), project_id=project_id)
        return task.to_json(), 200

    def post(self, project_id: int, task_id: str):
        project, task = self._get_task(project_id, task_id)  # todo: why do we extra query project?
        try:
            event = [{row['name']: row['default'] for row in request.json}]
        except:
            event = request.json
        resp = run_task(project.id, event, task.task_id)
        task_result_id = TaskResults.query.filter_by(task_id=task_id, project_id=project_id).order_by(
            TaskResults.id.desc()).first()
        if resp['code'] == 200 and task_result_id:
            task_result_id.task_status = "In progress..."
            task_result_id.commit()
        return resp, resp.get('code', 200)

    def put(self, project_id: int, task_id: str):
        args = request.json
        project, task = self._get_task(project_id, task_id)
        task.task_handler = args.get("invoke_func")
        task.region = args.get("region")
        task.env_vars = args.get("env_vars")
        task.commit()
        return task.to_json(), 200

    def delete(self, project_id: int, task_id: str):
        project, task = self._get_task(project_id, task_id)  # todo: why do we extra query project?
        task.delete()
        return None, 204
