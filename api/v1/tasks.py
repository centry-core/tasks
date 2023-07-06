import json
from typing import Optional, List
from io import BytesIO

from flask import request
from pydantic import ValidationError
from sqlalchemy import or_, and_

from ...models.tasks import Task
from ...models.validation_pd import TaskCreateModelPD, TaskPutModelPD
from hurry.filesize import size

from ...tools.TaskManager import TaskManager
from tools import api_tools, MinioClient, MinioClientAdmin, auth, VaultClient, constants as c

from pylon.core.tools import log


class TaskChecker:
    def __init__(self, tasks: List[Task], total: int, mode: str):
        self.mode = mode
        self.tasks = tasks
        self.total = total
        self.result = []

    def zip_exists(self):
        for task in self.tasks:
            zippath = task.zippath
            if task.mode == c.ADMINISTRATION_MODE:
                client = MinioClientAdmin(integration_id=zippath['integration_id'])
            else:
                client = MinioClient.from_project_id(
                    task.project_id,
                    integration_id=zippath['integration_id'],
                    is_local=zippath['is_local']
                )
            files = client.list_files(zippath['bucket_name'])
            sizes = {i['name']: size(i["size"]) for i in files}
            if zippath['file_name'] in sizes:
                result = task.to_json()
                result["size"] = sizes.get(zippath['file_name'])
                self.result.append(result)
            else:
                self.total -= 1


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

        total, tasks = api_tools.get(
            project_id, request.args, Task,
            mode=self.mode,
            rpc_manager=self.module.context.rpc_manager,
            custom_filter=or_(
                and_(
                    Task.mode == self.mode,
                    Task.project_id == project_id,
                ),
                Task.mode == c.ADMINISTRATION_MODE
            )
        )
        task_checker = TaskChecker(tasks, total, self.mode)
        task_checker.zip_exists()

        return {"total": task_checker.total, "rows": task_checker.result}, 200

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
        data['mode'] = self.mode

        if file is not None:
            data['task_package'] = file.filename
        try:
            pd_obj = TaskCreateModelPD(**data)
        except ValidationError as e:
            return e.errors(), 400

        if file is None:
            return {"message": "Validations are passed. Upload task_package file."}, 200

        obj_dict = pd_obj.dict()
        task_payload = {
            "funcname": obj_dict.pop('task_name'),
            "invoke_func": obj_dict.pop('task_handler'),
            "region": obj_dict.pop('engine_location'),
            "runtime": obj_dict.pop('runtime'),
            "env_vars": json.dumps({
                "cpu_cores": obj_dict.pop('cpu_cores'),
                "memory": obj_dict.pop('memory'),
                "timeout": obj_dict.pop('timeout'),
                "task_parameters": obj_dict.pop('task_parameters'),
                "monitoring_settings": obj_dict.pop('monitoring_settings')
            }),
            's3_settings': obj_dict.pop('s3_settings')
        }

        project = self.module.context.rpc_manager.call.project_get_or_404(
            project_id=project_id)
        task = TaskManager(project.id, mode=self.mode).create_task(file, task_payload)
        return {"task_id": task.task_id,
                "message": f"Task {task_payload['funcname']} created"}, 201

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
        data['mode'] = self.mode

        try:
            pd_obj = TaskPutModelPD(project_id=project_id, **data)
        except ValidationError as e:
            return e.errors(), 400
        project, task = self._get_task(project_id, task_id)
        if not task:
            return {"message": "No such task in selected in project"}, 404

        tasks_bucket = MinioClient.TASKS_BUCKET
        if file is None:
            file_name = task.file_name
            if (task.s3_integration_id == pd_obj.s3_settings.integration_id and
                    task.s3_is_local == pd_obj.s3_settings.is_local
            ):
                mc = MinioClient(project, task.s3_integration_id, task.s3_is_local)
            else:
                old_mc = MinioClient(project, task.s3_integration_id, task.s3_is_local)
                old_file = old_mc.download_file(tasks_bucket, task.file_name)
                mc = MinioClient(project, **pd_obj.s3_settings.dict())
                mc.upload_file(tasks_bucket, BytesIO(old_file), task.file_name)
                old_mc.remove_file(tasks_bucket, task.file_name)
            file_size = size(mc.get_file_size(bucket=tasks_bucket, filename=task.file_name))
        else:
            file_name = file.filename
            if (task.s3_integration_id == pd_obj.s3_settings.integration_id and
                    task.s3_is_local == pd_obj.s3_settings.is_local
            ):
                api_tools.upload_file(tasks_bucket, file, project,
                                      task.s3_integration_id, task.s3_is_local)
                mc = MinioClient(project, task.s3_integration_id, task.s3_is_local)
            else:
                api_tools.upload_file(tasks_bucket, file, project, **pd_obj.s3_settings.dict())
                mc = MinioClient(project, **pd_obj.s3_settings.dict())
            file_size = size(mc.get_file_size(bucket=tasks_bucket, filename=file_name))
            old_mc = MinioClient(project, task.s3_integration_id, task.s3_is_local)
            old_mc.remove_file(tasks_bucket, task.file_name)

        task.zippath = {
            'integration_id': pd_obj.s3_settings.integration_id,
            'is_local': pd_obj.s3_settings.is_local,
            'bucket_name': tasks_bucket,
            'file_name': file_name
        }
        env_vars = json.loads(task.env_vars)
        env_vars['task_parameters'] = pd_obj.task_parameters
        env_vars['monitoring_settings'] = pd_obj.monitoring_settings
        task.task_name = pd_obj.task_name
        task.task_handler = pd_obj.task_handler
        task.env_vars = json.dumps(env_vars)
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

        c = MinioClient(project, task.s3_integration_id, task.s3_is_local)
        c.remove_file(c.TASKS_BUCKET, task.file_name)
        task.delete()
        return None, 204


class AdminApi(api_tools.APIModeHandler):
    def _get_list(self) -> dict:
        total, tasks = api_tools.get(
            None, request.args, Task,
            mode=self.mode,
            rpc_manager=self.module.context.rpc_manager,
        )
        task_checker = TaskChecker(tasks, total, self.mode)
        task_checker.zip_exists()
        return {"total": task_checker.total, "rows": task_checker.result}

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
            pd_obj = TaskCreateModelPD.parse_obj(data)
        except ValidationError as e:
            return e.errors(), 400

        if file is None:
            return {"message": "Validations are passed. Upload task_package file."}, 200
        task_payload = pd_obj.dict()
        task_payload['env_vars'] = json.dumps(pd_obj.env_vars)
        # todo: fix
        task_payload['funcname'] = pd_obj.task_name
        task_payload['invoke_func'] = pd_obj.task_handler
        task_payload['region'] = pd_obj.engine_location

        task = TaskManager(mode=self.mode).create_task(file, task_payload)
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
        data['mode'] = self.mode

        try:
            pd_obj = TaskPutModelPD(**data)
        except ValidationError as e:
            return e.errors(), 400

        task = Task.query.filter(Task.task_id == task_id, Task.mode == self.mode).first()
        if not task:
            return {"message": "No such task in selected in project"}, 404

        tasks_bucket = MinioClientAdmin.TASKS_BUCKET
        if file is None:
            file_name = task.file_name
            if (task.s3_integration_id == pd_obj.s3_settings.integration_id and
                    task.s3_is_local == pd_obj.s3_settings.is_local
            ):
                mc = MinioClientAdmin(task.s3_integration_id)
            else:
                old_mc = MinioClientAdmin(task.s3_integration_id)
                old_file = old_mc.download_file(tasks_bucket, task.file_name)
                mc = MinioClientAdmin(pd_obj.s3_settings.integration_id)
                mc.upload_file(tasks_bucket, BytesIO(old_file), task.file_name)
                old_mc.remove_file(tasks_bucket, task.file_name)
            file_size = size(mc.get_file_size(bucket=tasks_bucket, filename=task.file_name))
        else:
            file_name = file.filename
            if (task.s3_integration_id == pd_obj.s3_settings.integration_id and
                    task.s3_is_local == pd_obj.s3_settings.is_local
            ):
                api_tools.upload_file_admin(tasks_bucket, file, task.s3_integration_id)
                mc = MinioClientAdmin(task.s3_integration_id)
            else:
                api_tools.upload_file_admin(tasks_bucket, file, pd_obj.s3_settings.integration_id)
                mc = MinioClientAdmin(pd_obj.s3_settings.integration_id)
            file_size = size(mc.get_file_size(bucket=tasks_bucket, filename=file_name))
            old_mc = MinioClientAdmin(task.s3_integration_id)
            old_mc.remove_file(tasks_bucket, task.file_name)

        task.zippath = {
            'integration_id': pd_obj.s3_settings.integration_id,
            'is_local': pd_obj.s3_settings.is_local,
            'bucket_name': tasks_bucket,
            'file_name': file_name
        }
        env_vars = json.loads(task.env_vars)
        env_vars['task_parameters'] = pd_obj.task_parameters
        env_vars['monitoring_settings'] = pd_obj.monitoring_settings
        task.task_name = pd_obj.task_name
        task.task_handler = pd_obj.task_handler
        task.env_vars = json.dumps(env_vars)
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

        mc = MinioClientAdmin(task.s3_integration_id)
        mc.remove_file(mc.TASKS_BUCKET, task.file_name)
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
