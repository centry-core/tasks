from typing import Optional, Union, Callable
from uuid import uuid4
from werkzeug.utils import secure_filename

from arbiter import Arbiter
import json

from ..models.pd.task import TaskCreateModel
from ..models.tasks import Task
from tools import constants as c, api_tools, rpc_tools, data_tools, MinioClient, VaultClient, MinioClientAdmin
from pylon.core.tools import log


class TaskManager:
    AVAILABLE_MODES = {'default', 'administration'}

    def __init__(self, project_id: Optional[int] = None, mode: str = 'default'):
        assert mode in self.AVAILABLE_MODES, f'TaskManager unknown mode: {mode}'
        assert project_id or mode != 'default', 'project id required for mode [default]'
        self.project_id = project_id
        self.mode = mode
        log.info('TaskManager init %s', [self.project_id, self.mode])

    @staticmethod
    def get_arbiter():
        return Arbiter(
            host=c.RABBIT_HOST, port=c.RABBIT_PORT,
            user=c.RABBIT_USER, password=c.RABBIT_PASSWORD
        )

    @property
    def upload_func(self) -> Callable:
        if self.mode == 'default':
            return api_tools.upload_file
        elif self.mode == 'administration':
            return api_tools.upload_file_admin

    def create_task(self,
                    file: Union[str, 'data_tools.files.File'],
                    task_args: dict,
                    file_name: Optional[str] = None,
                    **kwargs) -> Task:

        if isinstance(file, str):
            file = data_tools.files.File(file, file_name)
        task_id = secure_filename(str(uuid4()))
        model_data = dict()
        model_data.update(task_args)
        model_data.update(dict(
            mode=self.mode,
            project_id=self.project_id,
            zippath=f"tasks/{file.filename}",
            task_id=task_id,
        ))
        log.info('model_data: %s', model_data)
        task_model = TaskCreateModel.parse_obj(model_data)

        self.upload_func(bucket="tasks", f=file, project=self.project_id)

        task = Task(**task_model.dict())
        task.insert()
        log.info('Task created: [id: %s, name: %s]', task.id, task.task_name)
        return task

    def run_task(self, event: list, task_id: Optional[str] = None, queue_name: Optional[str] = None) -> dict:
        log.info('YASK run event: %s, task_id: %s, queue_name: %s', event, task_id, queue_name)
        if not queue_name:
            queue_name = c.RABBIT_QUEUE_NAME
        if self.mode == 'default':
            vault_client = VaultClient.from_project(self.project_id)
        else:
            vault_client = VaultClient()
        secrets = vault_client.get_all_secrets()

        task_id = task_id if task_id else secrets["control_tower_id"]
        task = Task.query.filter(Task.task_id == task_id).first()
        task_json = task.to_json()
        if self.mode == 'default':
            # need to remove that "if" if we want to always
            # set project_id from task manager and not from task
            task_json['project_id'] = self.project_id
        # TODO: we need to calculate it based on VUH, if we haven't used VUH quota then run
        # check_task_quota(task)
        arbiter = self.get_arbiter()
        task_kwargs = {
            "task": vault_client.unsecret(value=task_json, secrets=secrets),
            "event": vault_client.unsecret(value=event, secrets=secrets),
            "galloper_url": vault_client.unsecret(value="{{secret.galloper_url}}", secrets=secrets),
            "token": vault_client.unsecret(value="{{secret.auth_token}}", secrets=secrets),
            "mode": self.mode,
            "token_type": 'Bearer',
            "api_version": 1
        }
        log.info('YASK KWARGS %s', task_kwargs)
        arbiter.apply("execute_lambda", queue=queue_name, task_kwargs=task_kwargs)
        arbiter.close()

        if self.mode == 'default':
            rpc_tools.RpcMixin().rpc.call.projects_add_task_execution(project_id=self.project_id)

        return {"message": "Accepted", "code": 200, "task_id": task_id}

    @property
    def query(self):
        return Task.query.filter(Task.project_id == self.project_id, Task.mode == self.mode)

    def list_tasks(self) -> list:
        return self.query.all()

    def count_tasks(self) -> int:
        return self.query.count()

    @staticmethod
    def update_task_env(task_id: int, env_vars: str, rewrite: bool = True) -> bool:
        if rewrite:
            Task.query.filter(Task.task_id == task_id).update({Task.env_vars: env_vars})
        else:
            task_vars = Task.query.with_entities(Task.env_vars).filter(Task.task_id == task_id).first()
            try:
                task_vars = task_vars[0]
            except IndexError:
                log.error('Cannot find task with id: %s', task_id)
                return False
            task_vars = json.loads(task_vars)
            task_vars.update(**json.loads(env_vars))
            Task.query.filter(Task.task_id == task_id).update({Task.env_vars: task_vars})
        Task.commit()
        return True
