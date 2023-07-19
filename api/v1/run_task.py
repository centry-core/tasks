from flask import request
from sqlalchemy import or_

from ...models.tasks import Task
from ...tools.TaskManager import TaskManager

from tools import api_tools, auth, VaultClient, config as c


class ProjectApi(api_tools.APIModeHandler):
    @staticmethod
    def _get_task(project_id: int, task_id: str):
        return Task.query.filter(
            Task.task_id == task_id,
            or_(
                Task.project_id == project_id,
                Task.mode == c.ADMINISTRATION_MODE
            )
        ).first_or_404()

    @auth.decorators.check_api(["configuration.tasks.tasks.view"])
    def get(self, project_id: int, task_id: str):
        task = self._get_task(project_id, task_id)
        if request.args.get('exec'):
            vault_client = VaultClient(project_id)
            return vault_client.unsecret(task.to_json())
        return task.to_json(), 200

    @auth.decorators.check_api(["configuration.tasks.tasks.create"])
    def post(self, project_id: int, task_id: str):
        task = self._get_task(project_id, task_id)
        try:
            event = [{row['name']: row['default'] for row in request.json}]
        except:
            event = dict(request.json)
        resp = TaskManager(
            project_id=project_id, mode=self.mode
        ).run_task(event, task.task_id)
        return resp, resp.get('code', 200)

    # @auth.decorators.check_api(["configuration.tasks.tasks.edit"])
    # def put(self, project_id: int, task_id: str):
    #     # TODO: this is not how you update tasks!
    #     return None, 404
    #     task = self._get_task(project_id, task_id)
    #     # args = request.json
    #     # task.task_handler = args.get("invoke_func")
    #     # task.region = args.get("region")
    #     # task.env_vars = args.get("env_vars")
    #     # task.commit()
    #     return task.to_json(), 200

    @auth.decorators.check_api(["configuration.tasks.tasks.delete"])
    def delete(self, project_id: int, task_id: str):
        # TODO: maybe we need to delete artifact?
        # TODO: for core tasks we need either update or delete id from secrets
        Task.query.filter(
            Task.task_id == task_id,
            Task.mode == self.mode,
            Task.project_id == project_id
        ).delete()
        return None, 204


class AdminApi(api_tools.APIModeHandler):
    def _get_task(self, task_id: str):
        return Task.query.filter(
            Task.task_id == task_id, Task.mode == self.mode
        ).first_or_404()

    @auth.decorators.check_api(["configuration.tasks.tasks.view"])
    def get(self, task_id: str, **kwargs):
        task = self._get_task(task_id)
        if request.args.get("exec"):
            vault_client = VaultClient()
            return vault_client.unsecret(task.to_json()), 200
        return task.to_json(), 200

    @auth.decorators.check_api(["configuration.tasks.tasks.create"])
    def post(self, task_id: str, **kwargs):
        task = self._get_task(task_id)
        try:
            event = [{row['name']: row['default'] for row in request.json}]
        except:
            event = dict(request.json)
        resp = TaskManager(mode=self.mode).run_task(event, task.task_id)
        return resp, resp['code']

    # @auth.decorators.check_api(["configuration.tasks.tasks.edit"])
    # def put(self, task_id: str, **kwargs):
    #     # TODO: this is not how you update tasks!
    #     return None, 404
    #     # task = self._get_task(task_id)
    #     # task.task_handler = request.json.get("invoke_func", task.task_handler)
    #     # task.region = request.json.get("region", task.region)
    #     # task.env_vars = request.json.get("env_vars", task.env_vars)
    #     # task.commit()
    #     return task.to_json(), 200

    @auth.decorators.check_api(["configuration.tasks.tasks.delete"])
    def delete(self, task_id: str, **kwargs):
        # TODO: maybe we need to delete artifact?
        # TODO: for core tasks we need either update or delete id from secrets
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
