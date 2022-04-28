from flask import request, make_response
from flask_restful import Resource

from .utils import run_task
from ...models.tasks import Task


class API(Resource):
    def __init__(self, module):
        self.module = module

    def _get_task(self, project_id, task_id):
        return self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id), \
               Task.query.filter_by(task_id=task_id).first()

    def get(self, project_id: int, task_id: str):
        # args = self.get_parser.parse_args(strict=False)
        args = request.args
        project, task = self._get_task(project_id, task_id)  # todo: why do we extra query project?
        if args.get("exec"):
            return self.module.context.rpc_manager.call.unsecret_key(
                value=task.to_json(), project_id=project_id)
        return make_response(task.to_json(), 200)

    def post(self, project_id: int, task_id: str):
        project, task = self._get_task(project_id, task_id)  # todo: why do we extra query project?
        event = request.json
        resp = run_task(project.id, event, task.task_id)
        return make_response(resp, resp.get('code', 200))

    def put(self, project_id: int, task_id: str):
        args = request.json
        project, task = self._get_task(project_id, task_id)
        task.task_handler = args.get("invoke_func")
        task.region = args.get("region")
        task.env_vars = args.get("env_vars")
        task.commit()
        return make_response(task.to_json(), 200)

    def delete(self, project_id: int, task_id: str):
        project, task = self._get_task(project_id, task_id)  # todo: why do we extra query project?
        task.delete()
        return make_response(None, 204)
