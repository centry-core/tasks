from typing import Optional, Union, Callable, Iterable, TypedDict
from uuid import uuid4
from werkzeug.utils import secure_filename

from arbiter import Arbiter, EventNode, RedisEventNode, SocketIOEventNode
import json
import ssl

from sqlalchemy import or_, and_
from ..models.pd.task import TaskCreateModel
from ..models.results import TaskResults
from ..models.tasks import Task
from tools import constants as c, api_tools, rpc_tools, data_tools, VaultClient
from pylon.core.tools import log


class TaskManagerBase:
    AVAILABLE_MODES = {'default', 'administration'}

    def __init__(self, project_id: Optional[int] = None, mode: str = 'default'):
        assert mode in self.AVAILABLE_MODES, f'TaskManager unknown mode: {mode}'
        assert project_id or mode != 'default', 'project id required for mode [default]'
        self.project_id = project_id
        self.mode = mode
        log.info('TaskManager init %s', [self.project_id, self.mode])

    @staticmethod
    def get_cc_env_vars():
        arbiter_vhost = "carrier"
        result = {
            "ARBITER_RUNTIME": c.ARBITER_RUNTIME,
        }
        #
        if c.ARBITER_RUNTIME == "rabbitmq":
            result.update({
                "RABBIT_HOST": c.RABBIT_HOST,
                "RABBIT_USER": c.RABBIT_USER,
                "RABBIT_PASSWORD": c.RABBIT_PASSWORD,
                "RABBIT_VHOST": arbiter_vhost,
            })
        #
        if c.ARBITER_RUNTIME == "redis":
            result.update({
                "REDIS_HOST": c.REDIS_HOST,
                "REDIS_PASSWORD": c.REDIS_PASSWORD,
                "REDIS_VHOST": arbiter_vhost,
            })
        #
        if c.ARBITER_RUNTIME == "socketio":
            result.update({
                "SIO_URL": c.SIO_URL,
                "SIO_PASSWORD": c.SIO_PASSWORD,
                "SIO_VHOST": arbiter_vhost,
            })
        #
        return result.copy()

    @staticmethod
    def get_arbiter() -> Arbiter:
        arbiter_vhost = "carrier"
        if c.ARBITER_RUNTIME == "rabbitmq":
            ssl_context=None
            ssl_server_hostname=None
            #
            if c.RABBIT_USE_SSL:
                ssl_context = ssl.create_default_context()
                if c.RABBIT_SSL_VERIFY is True:
                    ssl_context.verify_mode = ssl.CERT_REQUIRED
                    ssl_context.check_hostname = True
                    ssl_context.load_default_certs()
                else:
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                ssl_server_hostname = c.RABBIT_HOST
            #
            event_node = EventNode(
                host=c.RABBIT_HOST,
                port=int(c.RABBIT_PORT),
                user=c.RABBIT_USER,
                password=c.RABBIT_PASSWORD,
                vhost=arbiter_vhost,
                event_queue="tasks",
                hmac_key=None,
                hmac_digest="sha512",
                callback_workers=c.EVENT_NODE_WORKERS,
                ssl_context=ssl_context,
                ssl_server_hostname=ssl_server_hostname,
                mute_first_failed_connections=10,
            )
        elif c.ARBITER_RUNTIME == "redis":
            event_node = RedisEventNode(
                host=c.REDIS_HOST,
                port=int(c.REDIS_PORT),
                password=c.REDIS_PASSWORD,
                event_queue=arbiter_vhost,
                hmac_key=None,
                hmac_digest="sha512",
                callback_workers=c.EVENT_NODE_WORKERS,
                mute_first_failed_connections=10,  # pylint: disable=C0301
                use_ssl=c.REDIS_USE_SSL,
            )
        elif c.ARBITER_RUNTIME == "socketio":
            event_node = SocketIOEventNode(
                url=c.SIO_URL,
                password=c.SIO_PASSWORD,
                room=arbiter_vhost,
                hmac_key=None,
                hmac_digest="sha512",
                callback_workers=c.EVENT_NODE_WORKERS,
                mute_first_failed_connections=10,  # pylint: disable=C0301
                ssl_verify=c.SIO_SSL_VERIFY,
            )
        else:
            raise ValueError(f"Unsupported arbiter runtime: {c.ARBITER_RUNTIME}")
        #
        return Arbiter(
            event_node=event_node,
        )

    def run_task(self, *args, **kwargs):
        raise NotImplementedError


BackendReportConfig = TypedDict('BackendReportConfig', {'integrations': Optional[dict], 'runner': str})
BackendReport = TypedDict('BackendReport', {
    'id': int,
    'name': str,
    'build_id': str,
    'test_config': BackendReportConfig
})


class PostProcessingManager(TaskManagerBase):
    def run_task(self,
                 report: BackendReport,
                 influx_db: str,
                 queue_name: Optional[str] = None,
                 logger_stop_words: Iterable = tuple(),
                 **kwargs):
        if not queue_name:
            queue_name = c.RABBIT_QUEUE_NAME
        if self.mode == 'default':
            vault_client = VaultClient.from_project(self.project_id)
        else:
            vault_client = VaultClient()
        vault_client.track_used_secrets = True

        logger_stop_words = set(logger_stop_words)

        exec_params = {
            'influxdb_host': '{{secret.influx_ip}}',
            'influxdb_port': '{{secret.influx_port}}',
            'influxdb_user': '{{secret.influx_user}}',
            'influxdb_password': '{{secret.influx_password}}',
            'influxdb_database': influx_db,
            'influxdb_comparison': '{{secret.comparison_db}}',
            'influxdb_telegraf': '{{secret.telegraf_db}}',
            'loki_host': '{{secret.loki_host}}',
            'loki_port': '{{secret.loki_port}}',
        }
        # ep_good.json = lambda: json.dumps(ep_good)

        pp_kwargs = {
            'galloper_url': '{{secret.galloper_url}}',
            'project_id': self.project_id,
            'build_id': report['build_id'],
            'report_id': report['id'],
            'bucket': str(report['name']).replace("_", "").replace(" ", "").lower(),
            'token': '{{secret.auth_token}}',
            'integrations': report['test_config'].get('integrations'),
            'exec_params': exec_params,
            'manual_run': True
        }

        vault_client.unsecret(pp_kwargs)
        logger_stop_words.update(vault_client.used_secrets)
        pp_kwargs['logger_stop_words'] = list(logger_stop_words)
        log.info('TaskManagerBase YASK KWARGS %s', pp_kwargs)

        arbiter = self.get_arbiter()
        arbiter.apply('post_process', queue=queue_name, task_kwargs=pp_kwargs)
        arbiter.close()

        return {"message": "Accepted", "code": 200}


class TaskManager(TaskManagerBase, rpc_tools.RpcMixin, rpc_tools.EventManagerMixin):
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
        s3_settings = task_args.get('s3_settings', {})
        if isinstance(file, str):
            file = data_tools.files.File(file, file_name)
        task_id = secure_filename(str(uuid4()))
        model_data = dict()
        model_data.update(task_args)
        model_data.update(dict(
            mode=self.mode,
            project_id=self.project_id,
            zippath={
                'integration_id': s3_settings.get('integration_id'),
                'is_local': s3_settings.get('is_local'),
                'bucket_name': 'tasks',
                'file_name': file.filename
            },
            task_id=task_id,
        ))
        log.info('model_data: %s', model_data)
        task_model = TaskCreateModel.parse_obj(model_data)

        self.upload_func(bucket="tasks", f=file, project=self.project_id, **s3_settings)

        task = Task(**task_model.dict())
        task.insert()
        log.info('Task created: [id: %s, name: %s]', task.id, task.task_name)
        return task

    def run_task(self, event: list | dict, task_id: Optional[str] = None,
                 queue_name: Optional[str] = None, logger_stop_words: Iterable = tuple(),
                 **kwargs) -> dict:
        log.info('YASK run event: %s, task_id: %s, queue_name: %s', event, task_id, queue_name)
        if isinstance(event, dict):
            event = [event]
        if not queue_name:
            queue_name = c.RABBIT_QUEUE_NAME
        if self.mode == 'default':
            vault_client = VaultClient.from_project(self.project_id)
        else:
            vault_client = VaultClient()

        vault_client.track_used_secrets = True
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
        logger_stop_words = set(logger_stop_words)
        # logger_stop_words.update(secrets.values())

        task_kwargs = {
            "task": vault_client.unsecret(value=task_json, secrets=secrets),
            "event": vault_client.unsecret(value=event, secrets=secrets),
            "galloper_url": vault_client.unsecret(value="{{secret.galloper_url}}", secrets=secrets),
            "token": vault_client.unsecret(value="{{secret.auth_token}}", secrets=secrets),
            "mode": self.mode,
            "token_type": 'Bearer',
            "api_version": 1,
        }
        logger_stop_words.update(vault_client.used_secrets)
        task_kwargs['logger_stop_words'] = list(logger_stop_words)

        task_result = self.create_result(task)
        task_kwargs['task']['task_result_id'] = task_result.task_result_id
        log.info('YASK KWARGS %s', task_kwargs)

        arbiter.apply('execute_lambda', queue=queue_name, task_kwargs=task_kwargs)
        arbiter.close()

        self.handle_usage(task_json, task_result, event[0])

        return {"message": "Accepted", "code": 200, "task_id": task_id}

    def handle_usage(self, task_json: dict, task_result: TaskResults, event: dict) -> None:
        # need to add this functionality to event handler
        if self.mode == 'default':
            self.rpc.call.projects_add_task_execution(project_id=self.project_id)

        task_json['task_result_id'] = task_result.id
        task_json['start_time'] = task_result.created_at
        task_json['test_report_id'] = event.get('cc_env_vars', {}).get('REPORT_ID')

        self.event_manager.fire_event('usage_create_task_resource_usage', task_json)

    def create_result(self, task: Task) -> TaskResults:
        result_id = str(uuid4())
        task_result = TaskResults(
            mode=self.mode,
            task_id=task.task_id,
            task_result_id=result_id,
            project_id=self.project_id
        )
        task_result.insert()
        return task_result

    @property
    def query(self):
        return Task.query.filter(
            or_(
                and_(
                    Task.mode == self.mode,
                    Task.project_id == self.project_id,
                ),
                Task.mode == c.ADMINISTRATION_MODE
            )
        )

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
