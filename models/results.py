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
from typing import Optional

from ..constants import TASK_STATUS
from sqlalchemy import String, Column, Integer, Text, Float, JSON, DateTime

from tools import db, db_tools, data_tools
from pylon.core.tools import log


class TaskResults(db_tools.AbstractBaseMixin, db.Base):
    __tablename__ = "task_results"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=True)
    mode = Column(String(64), unique=False, nullable=False, default='default')
    task_id = Column(String(128), unique=False, nullable=True)
    # ts = Column(Integer, unique=False, nullable=True)
    results = Column(Text, unique=False, nullable=True)
    log = Column(Text, unique=False, nullable=True)
    task_duration = Column(Float, unique=False, nullable=True)
    task_status = Column(Text, unique=False, nullable=True, default=str(TASK_STATUS.IN_PROGRESS))
    task_result_id = Column(String(128), unique=True, nullable=False)
    task_stats = Column(JSON, nullable=True, unique=False)
    created_at = Column(DateTime, server_default=data_tools.utcnow())

    @property
    def ts(self) -> Optional[int]:
        return self.__get_ts()

    @ts.setter
    def ts(self, value: int) -> None:
        log.warning('TaskResults.ts property is deprecated. Use TaskResults.created_at instead. '
                    'Value is not set and check if you needed it')

    def __get_ts(self, skip_warning: bool = False) -> Optional[int]:
        if not skip_warning:
            log.warning('TaskResults.ts property is deprecated. Use TaskResults.created_at instead')
        try:
            return int(self.created_at.timestamp())
        except AttributeError:
            return

    def to_json(self, **kwargs) -> dict:
        serialized = super().to_json(**kwargs)
        serialized['ts'] = self.__get_ts(True)
        return serialized
