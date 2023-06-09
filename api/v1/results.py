from collections import defaultdict
from uuid import uuid4

from flask import request, make_response
from flask_restful import abort

from ...models.pd.results import ResultsGetModel
from ...models.results import TaskResults
from ...models.tasks import Task

from tools import api_tools, auth

from ...utils import write_task_run_logs_to_minio_bucket


class ProjectApi(api_tools.APIModeHandler):
    @auth.decorators.check_api(["configuration.tasks.tasks.view"])
    def get(self, project_id: int, task_id: str):
        task = Task.query.filter(Task.task_id == task_id).first()

        if not task:
            abort(404)

        task_results = TaskResults.query.filter(
            TaskResults.mode == self.mode,
            TaskResults.task_id == task_id,
            TaskResults.project_id == project_id,
        ).all()

        rows = [ResultsGetModel.parse_obj(i.to_json()).dict() for i in task_results]
        return {"total": len(rows), "rows": rows}, 200

    @auth.decorators.check_api(["configuration.tasks.tasks.create"])
    def post(self, project_id: int):
        data = request.json
        task_result = TaskResults(
            project_id=project_id,
            task_id=data.get('task_id'),
            results=data.get('results'),
            log=data.get('log'),
            task_duration=data.get('task_duration'),
            task_status=data.get('task_status'),
            task_result_id=data.get('task_result_id'),
            task_stats=data.get('task_stats'),
            mode=self.mode
        )
        task_result.insert()
        return {"message": "Created", "code": 201, "task_id": task_result.id}, 201

    @auth.decorators.check_api(["configuration.tasks.tasks.edit"])
    def put(self, project_id: int):
        data = request.json
        args = request.args
        task_result_id = args.get('task_result_id')
        task_result = TaskResults.query.filter_by(project_id=project_id,
                                                  task_result_id=task_result_id).first()
        if not task_result:
            return {"message": "No such task_result_id in selected in project"}, 404

        task_result.task_duration = data.get('task_duration')
        task_result.log = data.get('log')
        task_result.results = data.get('results')
        task_result.task_status = data.get('task_status')
        task_result.task_stats = data.get('task_stats')
        task_result.commit()

        self.module.context.event_manager.fire_event(f'task_finished', task_result.to_json())

        write_task_run_logs_to_minio_bucket(task_result)
        resp = {"message": "Accepted", "code": 202,
                "task_result_id": task_result.task_result_id}
        return make_response(resp, resp.get('code', 202))


class AdminApi(api_tools.APIModeHandler):
    @auth.decorators.check_api(["configuration.tasks.tasks.view"])
    def get(self, task_id: str, **kwargs):
        args = request.args
        rows = defaultdict(list)

        task = Task.query.filter(Task.task_id == task_id, Task.mode == self.mode).first()
        if not task:
            abort(404)
        task_results = TaskResults.query.filter(
            TaskResults.mode == self.mode,
            TaskResults.task_id == task_id
        ).all()

        rows = [ResultsGetModel.parse_obj(i.to_json()).dict() for i in task_results]
        return {"total": len(rows), "rows": rows}, 200

    @auth.decorators.check_api(["configuration.tasks.tasks.create"])
    def post(self, **kwargs):
        data = request.json
        # task_result = create_task_result(project_id, data)
        task_result = TaskResults(
            mode=self.mode,
            task_id=data.get('task_id', uuid4()),
            results=data.get('results'),
            log=data.get('log'),
            task_duration=data.get('task_duration'),
            task_status=data.get('task_status'),
            task_result_id=data.get('task_result_id'),
            task_stats=data.get('task_stats'),
        )
        task_result.insert()
        return {"message": "Created", "code": 201, "task_id": task_result.id}, 201

    @auth.decorators.check_api(["configuration.tasks.tasks.edit"])
    def put(self, **kwargs):
        data = request.json
        args = request.args
        task_result_id = args.get('task_result_id')
        task_result = TaskResults.query.filter(
            TaskResults.mode == self.mode,
            TaskResults.task_result_id == task_result_id
        ).first()
        if not task_result:
            return {"message": "No such task_result_id"}, 404

        task_result.task_duration = data.get('task_duration')
        task_result.log = data.get('log')
        task_result.results = data.get('results')
        task_result.task_status = data.get('task_status')
        task_result.task_stats = data.get('task_stats')
        task_result.commit()

        self.module.context.event_manager.fire_event(f'task_finished', task_result.to_json())


        write_task_run_logs_to_minio_bucket(task_result)
        return {"message": "Accepted", "code": 202,
                "task_result_id": task_result.task_result_id}, 202


class API(api_tools.APIBase):
    url_params = [
        '<string:project_id>',
        '<string:mode>/<string:project_id>',
        '<string:project_id>/<string:task_id>',
        '<string:mode>/<string:project_id>/<string:task_id>',
    ]

    mode_handlers = {
        'default': ProjectApi,
        'administration': AdminApi,
    }
