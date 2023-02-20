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

from sqlalchemy import String, Column, Integer, Text, Boolean, Float

from tools import db, db_tools


class TaskResults(db_tools.AbstractBaseMixin, db.Base):
    __tablename__ = "task_results"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    task_id = Column(String(128), unique=False, nullable=True)
    ts = Column(Integer, unique=False, nullable=True)
    results = Column(Text, unique=False, nullable=True)
    log = Column(Text, unique=False, nullable=True)
    task_duration = Column(Float, unique=False, nullable=True)
    task_status = Column(Boolean, unique=False, nullable=True, default=False)
    task_result_id = Column(String(128), unique=True, nullable=False)
