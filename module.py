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
        # add_resource_to_api(self.context.api, TaskApi, "/task/<int:project_id>/<string:task_id>")
        # add_resource_to_api(self.context.api, TasksApi, "/task/<int:project_id>")
        # add_resource_to_api(self.context.api, TaskUpgradeApi, "/upgrade/<int:project_id>/task")

        self.descriptor.init_rpcs()
        # from .rpc_worker import tasks_count, create, list_tasks
        # self.context.rpc_manager.register_function(create, name='task_create')
        # self.context.rpc_manager.register_function(list_tasks)
        # self.context.rpc_manager.register_function(tasks_count)

    def deinit(self):  # pylint: disable=R0201
        """ De-init module """
        log.info("De-initializing module Tasks")
