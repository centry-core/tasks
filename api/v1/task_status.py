import logging

from flask_restful import Resource

from ...models.results import TaskResults


class API(Resource):
    url_params = [
        '<int:project_id>/<string:task_result_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int, task_result_id: str):
        logging.info(project_id, task_result_id)
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        logging.info(project, project.id)
        task_status = TaskResults.query.filter_by(project_id=project.id, task_result_id=task_result_id).first()
        return {"code": 200, "status": task_status.task_status}
