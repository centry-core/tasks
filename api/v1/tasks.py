import json

from flask import request
from flask_restful import Resource

from pydantic import ValidationError
# from werkzeug.datastructures import FileStorage

# from ...shared.utils.restApi import RestResource
# from ...shared.data_utils.file_utils import File
# from ...shared.utils.api_utils import build_req_parser, get

from ...models.tasks import Task
from ...models.validation_pd import TaskCreateModelPD, TaskPutModelPD
from hurry.filesize import size
from tools import api_tools, data_tools, MinioClient
from ...tools import task_tools


class API(Resource):
    url_params = [
        '<int:project_id>',
        '<int:project_id>/<string:task_id>',
    ]

    def __init__(self, module):
        self.module = module

    def _get_task(self, project_id: int, task_id: str):
        return self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id), \
            Task.query.filter_by(task_id=task_id, project_id=project_id).first()

    def get(self, project_id: int, task_id: str = None):
        args = request.args
        get_params = args.get('get_parameters', 'false')

        if task_id:
            _, task = self._get_task(project_id, task_id)

            if not task:
                return {"message": "No such task in selected in project"}, 404

            if get_params.lower() == 'true':
                resp = [{
                    "task_id": task.task_id,
                    "task_name": task.task_name,
                    "task_parameters": json.loads(task.env_vars).get('task_parameters'),
                }]
                return {"total": len(resp), "rows": resp}, 200
            else:
                resp = [task.to_json()]
                return {"total": len(resp), "rows": resp}, 200

        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        c = MinioClient(project)
        files = c.list_files('tasks')
        total, tasks = api_tools.get(project_id, args, Task)
        for each in files:
            for task in tasks:
                name = each["name"]
                if str(task.zippath).split("/")[-1] == name:
                    each['task_id'] = task.task_id
                    each["task_name"] = task.task_name
                    each['webhook'] = task.webhook
                    each["size"] = size(each["size"])

        return {"total": len(files), "rows": files}, 200

    def post(self, project_id: int):
        file = request.files.get('file')
        data = json.loads(request.form.get('data')) if request.form.get('data') else None
        if data is None:
            return {"message": "Empty data object"}, 400
        data['project_id'] = project_id

        if file is not None:
            data['task_package'] = file.filename
        try:
            pd_obj = TaskCreateModelPD(**data)
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
                "task_parameters": pd_obj.dict().pop('task_parameters')
            })
        }

        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        task = task_tools.create_task(
            project=project,
            file=file,
            args=task_payload

        )
        return {"task_id": task.id, "message": f"Task {task_payload['funcname']} created"}, 201

    def put(self, project_id: int, task_id: str):
        file = request.files.get('file')
        data = json.loads(request.form.get('data')) if request.form.get('data') else None
        if file is not None:
            data['task_package'] = file.filename

        if data is None:
            return {"message": "Empty data object"}, 400

        try:
            pd_obj = TaskPutModelPD(project_id=project_id, **data)
        except ValidationError as e:
            return e.errors(), 400
        project, task = self._get_task(project_id, task_id)
        if not task:
            return {"message": "No such task in selected in project"}, 404

        api_tools.upload_file(bucket="tasks", f=file, project=project)
        task.task_name = pd_obj.dict().get("task_name")
        task.zippath = f"tasks/{file.filename}"
        task.task_package = pd_obj.dict().get("task_package")
        task.task_handler = pd_obj.dict().get("task_handler")
        task.env_vars = json.dumps(pd_obj.dict().get("task_parameters"))
        task.commit()
        resp = task.to_json()
        c = MinioClient(project)
        resp['size'] = size(c.get_file_size('tasks', filename=file.filename))
        return resp, 200

    def delete(self, project_id: int, task_id: str):
        project, task = self._get_task(project_id, task_id)
        if not task:
            return {"message": "No such task in selected in project"}, 404

        c = MinioClient(project=project)
        c.remove_file('tasks', str(task.zippath).split("/")[-1])
        task.delete()
        return None, 204
