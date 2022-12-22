import json

from flask import request
from flask_restful import Resource

from pydantic import ValidationError
# from werkzeug.datastructures import FileStorage

# from ...shared.utils.restApi import RestResource
# from ...shared.data_utils.file_utils import File
# from ...shared.utils.api_utils import build_req_parser, get

from ...models.tasks import Task
from ...models.validation_pd import TaskCreateModelPD
from hurry.filesize import size
from tools import api_tools, data_tools, MinioClient
from ...tools import task_tools


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):
        args = request.args
        get_size = args.get('get_size')
        total, tasks = api_tools.get(project_id, args, Task)

        if get_size and get_size.lower() == 'true':
            project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
            c = MinioClient(project)
            files = c.list_files('tasks')
            for each in files:
                name = each["name"]
                task_name = [x.task_name for x in tasks if str(x.zippath).split("/")[-1] == name]
                task_name = task_name[0] if task_name else ""
                each["task_name"] = task_name
                each["size"] = size(each["size"])
            return {"total": len(files), "rows": files}, 200
        else:
            reports = []
            for each in tasks:
                reports.append(each.to_json())
            return {"total": total, "rows": reports}, 200

    def post(self, project_id: int):
        file = request.files.get('file')
        data = json.loads(request.form.get('data')) if request.form.get('data') else None
        if data is None:
            return {"message": "Empty data object"}, 400

        if file is not None:
            data['task_package'] = file.filename

        try:
            pd_obj = TaskCreateModelPD(project_id=project_id, **data)
        except ValidationError as e:
            return e.errors(), 400

        if file is None:
            return {"message": "Validations are passed. Upload task_package file."}, 200

        task_payload = {
            "funcname": pd_obj.dict().pop('task_name'),
            "invoke_func": pd_obj.dict().pop('task_handler'),
            "region": pd_obj.dict().pop('engine_location'),
            "runtime": pd_obj.dict().pop('runtime'),
            "env_vars": json.dumps({
                "cpu_cores": pd_obj.dict().pop('cpu_cores'),
                "memory": pd_obj.dict().pop('memory'),
                "timeout": pd_obj.dict().pop('timeout'),
                **pd_obj.dict().pop('task_parameters')
            })
        }

        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        task = task_tools.create_task(
            project=project,
            file=file,
            args=task_payload

        )
        return {"task_id": task.id, "message": f"Task {task_payload['funcname']} created"}, 201
