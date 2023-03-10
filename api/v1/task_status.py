import logging

from flask_restful import Resource

from ...models.results import TaskResults


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):
        INPROGRESS = "In progress..."
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        logging.info(project, project.id)
        if TaskResults.query.filter_by(project_id=project.id, task_status=INPROGRESS).first():
            return {"code": 200, "IN_PROGRESS": True}
        return {"code": 200, "IN_PROGRESS": False}
