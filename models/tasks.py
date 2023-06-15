#     Copyright 2020 getcarrier.io
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON

from tools import db, db_tools


class Task(db_tools.AbstractBaseMixin, db.Base):
    __tablename__ = "task"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=True)
    mode = Column(String(64), unique=False, nullable=False, default='default')
    task_id = Column(String(128), unique=True, nullable=False)
    zippath = Column(JSON, unique=False, nullable=False)
    task_name = Column(String(128), unique=False, nullable=False)
    task_handler = Column(String(128), unique=False, nullable=False)
    runtime = Column(String(128), unique=False, nullable=False)
    region = Column(String(128), unique=False, nullable=False)
    webhook = Column(String(128), unique=False, nullable=True)
    env_vars = Column(Text, unique=False, nullable=True)

    def insert(self):
        if not self.webhook:
            self.webhook = f"/task/{self.task_id}"
        if not self.env_vars:
            self.env_vars = "{}"
        super().insert()

    @property
    def file_name(self) -> str:
        return self.zippath.get('file_name')
    
    @property
    def s3_bucket_name(self) -> str:
        return self.zippath.get('bucket_name')
    
    @property
    def s3_integration_id(self) -> str:
        return self.zippath.get('integration_id')
    
    @property
    def s3_is_local(self) -> str:
        return self.zippath.get('is_local')

    # def to_json(self, exclude_fields: Optional[set] = None, **kwargs):
    #     plugin_name = self.file_name
    #     try:
    #         return self.rpc.call_function_with_timeout(
    #             func=f'serializer',
    #             timeout=2,
    #             exclude_fields=exclude_fields
    #         )
    #     except Empty:
    #         return super().to_json()

