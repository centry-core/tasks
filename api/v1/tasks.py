import json
from typing import Optional

from flask import request
from pydantic import ValidationError

from ...models.tasks import Task
from ...models.validation_pd import TaskCreateModelPD, TaskPutModelPD
from hurry.filesize import size

from ...tools.TaskManager import TaskManager
from tools import api_tools, data_tools, MinioClient, MinioClientAdmin, auth

from pylon.core.tools import log


class ProjectApi(api_tools.APIModeHandler):
    def _get_task(self, project_id: int, task_id: str):
        return self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id), \
            Task.query.filter_by(task_id=task_id, project_id=project_id).first()

    @auth.decorators.check_api({
        "permissions": ["configuration.tasks.tasks.view"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": True, "editor": True},
            "default": {"admin": True, "viewer": True, "editor": True},
            "developer": {"admin": True, "viewer": True, "editor": True},
        }})
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
        rows = []
        for each in files:
            for task in tasks:
                name = each["name"]
                if str(task.zippath).split("/")[-1] == name:
                    each['task_id'] = task.task_id
                    each["task_name"] = task.task_name
                    each['webhook'] = task.webhook
                    each["size"] = size(each["size"])
                    rows.append(each)

        return {"total": len(rows), "rows": rows}, 200

    @auth.decorators.check_api({
        "permissions": ["configuration.tasks.tasks.create"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": False, "editor": True},
            "default": {"admin": True, "viewer": False, "editor": True},
            "developer": {"admin": True, "viewer": False, "editor": True},
        }})
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
        task = TaskManager(project.id, mode=self.mode).create_task(file, task_payload)
        return {"task_id": task.task_id, "message": f"Task {task_payload['funcname']} created"}, 201

    @auth.decorators.check_api({
        "permissions": ["configuration.tasks.tasks.edit"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": False, "editor": True},
            "default": {"admin": True, "viewer": False, "editor": True},
            "developer": {"admin": True, "viewer": False, "editor": True},
        }})
    def put(self, project_id: int, task_id: str):
        file = request.files.get('file')
        data = json.loads(request.form.get('data')) if request.form.get('data') else None

        if data is None:
            return {"message": "Empty data object"}, 400

        try:
            pd_obj = TaskPutModelPD(project_id=project_id, **data)
        except ValidationError as e:
            return e.errors(), 400
        project, task = self._get_task(project_id, task_id)
        if not task:
            return {"message": "No such task in selected in project"}, 404

        task.task_name = pd_obj.dict().get("task_name")

        file_size = None
        if file is not None:
            data['task_package'] = file.filename
            task.zippath = f"tasks/{file.filename}"
            api_tools.upload_file(bucket="tasks", f=file, project=project)
            c = MinioClient(project)
            file_size = size(c.get_file_size('tasks', filename=file.filename))

        task.task_handler = pd_obj.dict().get("task_handler")
        task.env_vars = json.dumps(pd_obj.dict().get("task_parameters"))
        task.commit()
        resp = task.to_json()
        resp['size'] = file_size

        return resp, 200

    @auth.decorators.check_api({
        "permissions": ["configuration.tasks.tasks.edit"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": False, "editor": False},
            "default": {"admin": True, "viewer": False, "editor": False},
            "developer": {"admin": True, "viewer": False, "editor": False},
        }})
    def delete(self, project_id: int, task_id: str):
        project, task = self._get_task(project_id, task_id)
        if not task:
            return {"message": "No such task in selected in project"}, 404

        c = MinioClient(project=project)
        c.remove_file('tasks', str(task.zippath).split("/")[-1])
        task.delete()
        return None, 204


class AdminApi(api_tools.APIModeHandler):
    def _get_list(self) -> dict:
        files = MinioClientAdmin().list_files('tasks')
        total, tasks = api_tools.get(
            None, request.args, Task,
            mode=self.mode,
            rpc_manager=self.module.context.rpc_manager,
            additional_filters=[Task.zippath.in_([
                f'tasks/{i["name"]}' for i in files
            ])]
        )
        return {"total": total, "rows": [i.to_json() for i in tasks]}

    def _get_details(self, task: Task, with_params: bool = False) -> dict:
        if with_params:
            return {"total": 1, "rows": [{
                "task_id": task.task_id,
                "task_name": task.task_name,
                "task_parameters": json.loads(task.env_vars).get('task_parameters'),
            }]}
        else:
            return {"total": 1, "rows": [task.to_json()]}

    @auth.decorators.check_api({
        "permissions": ["configuration.tasks.tasks.view"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": True, "editor": True},
            "default": {"admin": True, "viewer": True, "editor": True},
            "developer": {"admin": True, "viewer": True, "editor": True},
        }})
    def get(self, task_id: Optional[str] = None, **kwargs):
        if task_id:
            task = Task.query.filter(Task.task_id == task_id, Task.mode == self.mode).first()
            if not task:
                return {"message": "No such task in selected project"}, 404
            get_params = request.args.get('get_parameters', 'false')
            return self._get_details(task, with_params=get_params.lower() == 'true'), 200

        return self._get_list(), 200

    @auth.decorators.check_api({
        "permissions": ["configuration.tasks.tasks.create"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": False, "editor": True},
            "default": {"admin": True, "viewer": False, "editor": True},
            "developer": {"admin": True, "viewer": False, "editor": True},
        }})
    def post(self, **kwargs):
        file = request.files.get('file')
        data = json.loads(request.form.get('data')) if request.form.get('data') else None
        if data is None:
            return {"message": "Empty data object"}, 400
        data['mode'] = self.mode

        try:
            data['task_package'] = file.filename
        except AttributeError:
            ...
        try:
            log.info('HERE IS POST 1')
            pd_obj = TaskCreateModelPD.parse_obj(data)
            log.info('HERE IS POST 2')
        except ValidationError as e:
            log.info('HERE IS POST 3')
            return e.errors(), 400
        log.info('HERE IS POST 4')

        if file is None:
            return {"message": "Validations are passed. Upload task_package file."}, 200

        task_payload = pd_obj.dict()
        task_payload['env_vars'] = json.dumps(pd_obj._env_vars)
        # todo: fix
        task_payload['funcname'] = pd_obj.task_name
        task_payload['invoke_func'] = pd_obj.task_handler
        task_payload['region'] = pd_obj.engine_location
        log.info('HERE IS POST 5')

        task = TaskManager(mode=self.mode).create_task(file, task_payload)
        log.info('HERE IS POST 6')
        return {"task_id": task.task_id, "message": f"Task {task.task_name} created"}, 201

    @auth.decorators.check_api({
        "permissions": ["configuration.tasks.tasks.edit"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": False, "editor": True},
            "default": {"admin": True, "viewer": False, "editor": True},
            "developer": {"admin": True, "viewer": False, "editor": True},
        }})
    def put(self, task_id: str, **kwargs):
        file = request.files.get('file')
        data = json.loads(request.form.get('data')) if request.form.get('data') else None

        if data is None:
            return {"message": "Empty data object"}, 400

        try:
            pd_obj = TaskPutModelPD(**data)
        except ValidationError as e:
            return e.errors(), 400

        # project, task = self._get_task(project_id, task_id)
        task = Task.query.filter(Task.task_id == task_id, Task.mode == self.mode).first()
        if not task:
            return {"message": "No such task in selected in project"}, 404

        if file is None:
            mc = MinioClientAdmin()
            file_size = size(mc.get_file_size(bucket='tasks', filename=task.file_name))
        else:
            # data['task_package'] = file.filename
            task.zippath = f"tasks/{file.filename}"
            api_tools.upload_file_admin(bucket="tasks", f=file)
            file_size = size(file)

        task.task_name = pd_obj.task_name
        task.task_handler = pd_obj.task_handler
        task.env_vars = json.dumps(pd_obj.task_parameters)
        task.commit()

        resp = task.to_json()
        resp['size'] = file_size

        return resp, 200

    @auth.decorators.check_api({
        "permissions": ["configuration.tasks.tasks.delete"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": False, "editor": False},
            "default": {"admin": True, "viewer": False, "editor": False},
            "developer": {"admin": True, "viewer": False, "editor": False},
        }})
    def delete(self, task_id: str, **kwargs):
        task = Task.query.filter(Task.task_id == task_id, Task.mode == self.mode).first()
        # project, task = self._get_task(project_id, task_id)
        if not task:
            return {"message": "No such task in project"}, 404

        mc = MinioClientAdmin()
        mc.remove_file('tasks', task.file_name)
        task.delete()
        return None, 204


class API(api_tools.APIBase):
    url_params = [
        # '<string:project_id>',
        '<string:mode>/<string:project_id>',
        # '<string:project_id>/<string:task_id>',
        '<string:mode>/<string:project_id>/<string:task_id>',
    ]

    mode_handlers = {
        'default': ProjectApi,
        'administration': AdminApi,
    }
