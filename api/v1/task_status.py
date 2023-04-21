from ...models.results import TaskResults
from tools import api_tools, auth


class ProjectApi(api_tools.APIModeHandler):
    @auth.decorators.check_api(["configuration.tasks.tasks.view"])
    def get(self, project_id: int, task_id: str):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        # task_results_progress = TaskResults.query.filter(
        #     TaskResults.project_id == project.id,
        #     TaskResults.task_id == task_id,
        #     TaskResults.task_status == self.INPROGRESS,
        #     TaskResults.mode == self.mode
        # ).all()
        # if task_results_progress:
        #     task_result_ids = [x.task_result_id for x in task_results_progress]
        #     return {"code": 200, "IN_PROGRESS": True, "task_result_ids": task_result_ids}
        # return {"code": 200, "IN_PROGRESS": False}
        return self._query_results([
            TaskResults.task_id == task_id,
            TaskResults.project_id == project.id,
            TaskResults.mode == self.mode,
        ])


class AdminApi(api_tools.APIModeHandler):
    def get(self, task_id: str, **kwargs):
        return self._query_results([
            TaskResults.task_id == task_id,
            TaskResults.mode == self.mode,
        ])


class API(api_tools.APIBase):
    url_params = [
        '<string:project_id>/<string:task_id>',
        '<string:mode>/<string:project_id>/<string:task_id>',
    ]

    mode_handlers = {
        'default': ProjectApi,
        'administration': AdminApi,
    }

    def _query_results(self, query_filter: list):
        INPROGRESS = "In progress..."
        resp = TaskResults.query.with_entities(TaskResults.task_result_id).filter(
            TaskResults.task_status == INPROGRESS,
            *query_filter
        ).all()
        if resp:
            task_result_ids = [i[0] for i in resp]
            return {"code": 200, "IN_PROGRESS": True, "task_result_ids": task_result_ids}, 200
        return {"code": 200, "IN_PROGRESS": False}, 200
