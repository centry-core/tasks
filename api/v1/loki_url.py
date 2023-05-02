from flask import request
from ...models.tasks import Task
from ...models.results import TaskResults

from tools import constants as c, api_tools, auth


class ProjectApi(api_tools.APIModeHandler):
    @auth.decorators.check_api(["configuration.tasks.results.view"])
    def get(self, project_id: int):

        task_id = request.args.get("task_id", None)
        task_result_id = request.args.get("task_result_id", None)

        if not task_id and not task_result_id:
            return {"message": "task_id and task_result_id is not provided."}, 404

        task = Task.query.filter_by(task_id=task_id).first()
        # TODO: to check if this is not bug and is proper solution to get last task_result_id by latest id.
        if task_id and not task_result_id:
            task_result_id = TaskResults.query.filter_by(task_id=task_id, project_id=project_id).order_by(TaskResults.id.desc()).first_or_404().task_result_id
        if task_id and task_result_id:
            task_result_id = TaskResults.query.filter_by(task_id=task_id, project_id=project_id, task_result_id=task_result_id).first().task_result_id
        if not task:
            return {"message": f"no such task_id found {task_id}"}, 404
        websocket_base_url = c.APP_HOST.replace("http://", "ws://").replace("https://", "wss://")
        websocket_base_url += "/loki/api/v1/tail"
        logs_query = "{" + f'hostname="{task.task_name}", task_id="{task.task_id}",project="{project_id}", task_result_id="{task_result_id}"' + "}"

        logs_start = 0
        logs_limit = 10000000000

        return {
            "websocket_url": f"{websocket_base_url}?query={logs_query}&start={logs_start}&limit={logs_limit}"
        }, 200


class AdminApi(api_tools.APIModeHandler):
    @auth.decorators.check_api(["configuration.tasks.results.view"])
    def get(self, **kwargs):

        task_id = request.args.get('task_id')
        task_result_id = request.args.get('task_result_id')

        task_result_query = TaskResults.query.filter(
            TaskResults.mode == self.mode
        )

        if task_result_id:
            result = task_result_query.filter(
                TaskResults.task_result_id == task_result_id
            ).first_or_404()
        elif task_id:
            result = task_result_query.filter(
                TaskResults.task_id == task_id
            ).order_by(
                TaskResults.id.desc()
            ).first_or_404()
        else:
            return {"message": "specify task_id or task_result_id"}, 404

        return {
            "websocket_url": self._get_loki_url(result.task_result_id)
        }, 200


class API(api_tools.APIBase):
    url_params = [
        '<string:project_id>',
        '<string:mode>/<string:project_id>',
    ]
    mode_handlers = {
        'default': ProjectApi,
        'administration': AdminApi,
    }

    @staticmethod
    def _get_loki_url(task_result_id: str) -> str:
        websocket_base_url = c.APP_HOST.replace("http://", "ws://").replace("https://", "wss://")
        websocket_base_url += "/loki/api/v1/tail"
        logs_query = "{" + f'task_result_id="{task_result_id}"' + "}"

        logs_start = 0
        logs_limit = 10000000000

        return f"{websocket_base_url}?query={logs_query}&start={logs_start}&limit={logs_limit}"
