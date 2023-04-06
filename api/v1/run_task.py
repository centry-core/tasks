from flask import request

from ...models.tasks import Task
from ...models.results import TaskResults

from tools import VaultClient
from pylon.core.tools import log

from ...tools.TaskManager import TaskManager
from tools import api_tools


class ProjectApi(api_tools.APIModeHandler):
    def _get_task(self, project_id: int, task_id: str):
        return self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id), \
               Task.query.filter(Task.task_id == task_id, Task.mode == self.mode).first()

    def get(self, project_id: int, task_id: str):
        # args = self.get_parser.parse_args(strict=False)
        args = request.args
        project, task = self._get_task(project_id, task_id)  # todo: why do we extra query project?

        if args.get("exec"):
            vault_client = VaultClient.from_project(project)
            return vault_client.unsecret(task.to_json())
        return task.to_json(), 200

    def post(self, project_id: int, task_id: str):
        project, task = self._get_task(project_id, task_id)  # todo: why do we extra query project?
        try:
            event = [{row['name']: row['default'] for row in request.json}]
        except:
            event = request.json
        # resp = TaskManager(project.id).run_task(event, task.task_id)
        resp = TaskManager(project_id=project.id, mode=self.mode).run_task(event, task.task_id)
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


class AdminApi(api_tools.APIModeHandler):
    def _get_task(self, task_id: str):
        return Task.query.filter(Task.task_id == task_id, Task.mode == self.mode).first()

    def get(self, task_id: str, **kwargs):
        task = self._get_task(task_id)
        if request.args.get("exec"):
            vault_client = VaultClient()
            return vault_client.unsecret(task.to_json()), 200
        return task.to_json(), 200

    def post(self, task_id: str, **kwargs):
        task = self._get_task(task_id)
        try:
            event = [{row['name']: row['default'] for row in request.json}]
        except:
            event = request.json
        resp = TaskManager(mode=self.mode).run_task(event, task.task_id)
        # todo: why do you think task_result_id will be correct?
        task_result_id = TaskResults.query.filter(
            TaskResults.task_id == task_id
        ).order_by(
            TaskResults.id.desc()
        ).first()
        if resp['code'] == 200 and task_result_id:
            task_result_id.task_status = "In progress..."
            task_result_id.commit()
        return resp, resp['code']

    def put(self, task_id: str, **kwargs):
        task = self._get_task(task_id)
        task.task_handler = request.json.get("invoke_func", task.task_handler)
        task.region = request.json.get("region", task.region)
        task.env_vars = request.json.get("env_vars", task.env_vars)
        task.commit()
        return task.to_json(), 200

    def delete(self, task_id: str, **kwargs):
        # task = self._get_task(task_id)
        # task.delete()
        Task.query.filter(Task.task_id == task_id, Task.mode == self.mode).delete()
        return None, 204


class API(api_tools.APIBase):
    url_params = [
        '<string:project_id>/<string:task_id>',
        '<string:mode>/<string:project_id>/<string:task_id>',
    ]

    mode_handlers = {
        'default': ProjectApi,
        'administration': AdminApi,
    }
