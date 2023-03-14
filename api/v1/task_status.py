import logging

from flask_restful import Resource

from ...models.results import TaskResults


class API(Resource):
    url_params = [
        '<int:project_id>/<string:task_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int, task_id: str):
        INPROGRESS = "In progress..."
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        logging.info(project, project.id)
        task_results_progress = TaskResults.query.filter_by(project_id=project.id, task_id=task_id, task_status=INPROGRESS).all()
        if task_results_progress:
            task_result_ids = [x.task_result_id for x in task_results_progress]
            return {"code": 200, "IN_PROGRESS": True, "task_result_ids": task_result_ids}
        return {"code": 200, "IN_PROGRESS": False}
