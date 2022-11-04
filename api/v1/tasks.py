from flask import request
from flask_restful import Resource
# from werkzeug.datastructures import FileStorage

# from ...shared.utils.restApi import RestResource
# from ...shared.data_utils.file_utils import File
# from ...shared.utils.api_utils import build_req_parser, get

from ...models.tasks import Task
from ...tools.task_tools import create_task

from tools import api_tools, data_tools


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):
        args = request.args
        reports = []
        total, res = api_tools.get(project_id, args, Task)
        for each in res:
            reports.append(each.to_json())
        return {"total": total, "rows": reports}, 200

    def post(self, project_id: int):
        args = request.json
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        if args.get("file"):
            file = args["file"]
            if file.filename == "":
                return {"message": "file not selected", "code": 400}, 400
        elif args.get("url"):
            file = data_tools.files.File(args.get("url"))
        else:
            return {"message": "Task file is not specified", "code": 400}, 400
        # TODO: we need to check on storage quota here
        task_id = create_task(project, file, args).task_id
        return {"file": task_id, "code": 0}, 200
