#   Copyright 2021 getcarrier.io
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

""" Module """
from pylon.core.tools import log  # pylint: disable=E0611,E0401
from pylon.core.tools import module  # pylint: disable=E0611,E0401
import json

from .models.tasks import Task
from .tools.TaskManager import TaskManager

from tools import theme, constants as c, VaultClient, api_tools


class Module(module.ModuleModel):
    """ Task module """

    def __init__(self, context, descriptor):
        self.context = context
        self.descriptor = descriptor

    def init(self):
        """ Init module """
        log.info("Initializing module Tasks")

        from .init_db import init_db
        init_db()

        self.descriptor.init_api()
        self.descriptor.init_blueprint()
        self.descriptor.init_rpcs()

        theme.register_subsection(
            "configuration", "tasks",
            "Tasks",
            title="Tasks",
            kind="slot",
            permissions={
                "permissions": ["configuration.tasks"],
                "recommended_roles": {
                    "administration": {"admin": True, "viewer": True, "editor": True},
                    "default": {"admin": True, "viewer": True, "editor": True},
                    "developer": {"admin": True, "viewer": True, "editor": True},
                }},
            prefix="tasks_",
            weight=5,
        )

        theme.register_mode_subsection(
            "administration", "configuration",
            "tasks", "Tasks",
            title="Tasks",
            kind="slot",
            permissions={
                "permissions": ["configuration.tasks"],
                "recommended_roles": {
                    "administration": {"admin": True, "viewer": True, "editor": True},
                    "default": {"admin": True, "viewer": True, "editor": True},
                    "developer": {"admin": True, "viewer": True, "editor": True},
                }},
            prefix="administration_tasks_",
            # icon_class="fas fa-server fa-fw",
            # weight=2,
        )

        self.descriptor.init_slots()

        self.descriptor.register_tool('TaskManager', TaskManager)

        vault_client = VaultClient()
        secrets = vault_client.get_all_secrets()

        if 'control_tower_id' not in secrets:
            cc = self.create_control_tower_task()
            secrets['control_tower_id'] = cc.task_id

        if 'rabbit_queue_checker_id' not in secrets:
            rqc = self.create_rabbit_queue_checker_task()
            secrets['rabbit_queue_checker_id'] = rqc.task_id
        vault_client.set_secrets(secrets)

    def create_control_tower_task(self) -> Task:
        cc_args = {
            "funcname": "control_tower",
            "invoke_func": "lambda.handler",
            "runtime": "Python 3.7",
            "region": "default",
            "env_vars": json.dumps({
                "token": "{{secret.auth_token}}",
                "galloper_url": "{{secret.galloper_url}}",
                "GALLOPER_WEB_HOOK": '{{secret.post_processor}}',
                "project_id": '{{secret.project_id}}',
                "loki_host": '{{secret.loki_host}}'
            })
        }
        task_manager = TaskManager(mode='administration')
        return task_manager.create_task(
            self.descriptor.config('control_tower_task_path'),
            cc_args
        )

    def create_rabbit_queue_checker_task(self) -> Task:
        rabbit_queue_checker_args = {
            "funcname": "rabbit_queue_checker",
            "invoke_func": "lambda.handler",
            "runtime": "Python 3.8",
            "region": "default",
            "env_vars": json.dumps({
                "token": '{{secret.auth_token}}',
                # "callback_url": ''.join([
                #     '{{secret.galloper_url}}',
                #     api_tools.build_api_url('projects', 'rabbitmq', mode=mode)
                # ]),
                "rabbit_host": '{{secret.rabbit_host}}',
                "rabbit_user": '{{secret.rabbit_user}}',
                "rabbit_password": '{{secret.rabbit_password}}',
                "AWS_LAMBDA_FUNCTION_TIMEOUT": 120,
                'vhost_template': 'project_{project_id}_vhost',
                'core_vhost': 'carrier',
                'put_url': ''.join([
                    '{{secret.galloper_url}}',
                    api_tools.build_api_url('projects', 'rabbitmq',
                                            mode='administration', trailing_slash=True),
                    'None'
                ]),
                'project_ids_get_url': ''.join([
                    '{{secret.galloper_url}}',
                    api_tools.build_api_url('projects', 'rabbitmq',
                                            mode='administration', trailing_slash=True),
                    'None'
                ]),
            })
        }

        task_manager = TaskManager(mode='administration')
        return task_manager.create_task(
            self.descriptor.config('rabbit_queue_checker_task_path'),
            rabbit_queue_checker_args,
            'rabbit_queue_checker.zip'
        )

    def deinit(self):  # pylint: disable=R0201
        """ De-init module """
        log.info("De-initializing module Tasks")
