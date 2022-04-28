from flask import make_response, request
from flask_restful import Resource
from sqlalchemy import and_

# from ...shared.utils.restApi import RestResource
# from ...shared.data_utils.file_utils import File
# from ...shared.utils.api_utils import upload_file, build_req_parser
# from ...shared.constants import POST_PROCESSOR_PATH, CONTROL_TOWER_PATH, APP_HOST, REDIS_PASSWORD, \
#     APP_IP, EXTERNAL_LOKI_HOST, INFLUX_PORT, LOKI_PORT, RABBIT_USER, RABBIT_PASSWORD, INFLUX_PASSWORD, INFLUX_USER

from ...models.tasks import Task

from tools import data_tools, constants as c, api_tools, secrets_tools


class API(Resource):
    def __init__(self, module):
        self.module = module

    @staticmethod
    def create_cc_task(project):
        api_tools.upload_file(bucket="tasks", f=data_tools.files.File(c.CONTROL_TOWER_PATH), project=project)
        task = Task.query.filter(and_(Task.task_name == "control_tower", Task.project_id == project.id)).first()
        setattr(task, "zippath", "tasks/control-tower.zip")
        task.commit()

    @staticmethod
    def create_pp_task(project):
        api_tools.upload_file(bucket="tasks", f=data_tools.files.File(c.POST_PROCESSOR_PATH), project=project)
        task = Task.query.filter(and_(Task.task_name == "post_processor", Task.project_id == project.id)).first()
        setattr(task, "zippath", "tasks/post_processing.zip")
        task.commit()

    def get(self, project_id):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        args = request.args
        if args['name'] not in ['post_processor', 'control_tower', 'all']:
            return {"message": "You shall not pass", "code": 400}, 400
        secrets = secrets_tools.get_project_hidden_secrets(project_id=project.id)
        project_secrets = {}
        if args['name'] == 'post_processor':
            self.create_pp_task(project)
        elif args['name'] == 'control_tower':
            self.create_cc_task(project)
        elif args['name'] == 'all':
            self.create_pp_task(project)
            self.create_cc_task(project)
            project_secrets["galloper_url"] = c.APP_HOST
            project_secrets["project_id"] = project.id
            secrets["redis_host"] = c.APP_IP
            secrets["loki_host"] = c.EXTERNAL_LOKI_HOST.replace("https://", "http://")
            secrets["influx_ip"] = c.APP_IP
            secrets["influx_port"] = c.INFLUX_PORT
            secrets["influx_user"] = c.INFLUX_USER
            secrets["influx_password"] = c.INFLUX_PASSWORD
            secrets["loki_port"] = c.LOKI_PORT
            secrets["redis_password"] = c.REDIS_PASSWORD
            secrets["rabbit_host"] = c.APP_IP
            secrets["rabbit_user"] = c.RABBIT_USER
            secrets["rabbit_password"] = c.RABBIT_PASSWORD
            secrets = secrets_tools.set_project_secrets(
                project_id=project.id,
                secrets=project_secrets
            )
        else:
            return make_response({"message": "go away", "code": 400}, 400)
        secrets_tools.set_project_hidden_secrets(
            project_id=project.id,
            secrets=secrets
        )
        return make_response({"message": "Done", "code": 200}, 200)
