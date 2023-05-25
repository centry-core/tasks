import json

from pylon.core.tools import log, web

from ..models.pd.results import ResultsGetModel
from ..models.results import TaskResults
from tools import constants as c
from ..models.tasks import Task
from ..tools.TaskManager import TaskManager

FAILED_TASKS_THRESHOLD = 5


class Event:

    @web.event(f"task_finished")
    def task_finished(self, context, event, payload):
        task_results = TaskResults.query.filter(
            TaskResults.mode == payload['mode'],
            TaskResults.task_id == payload['task_id'],
            TaskResults.project_id == payload['project_id'],
        ).all()

        task = Task.query.filter(
            Task.task_id == payload['task_id'],
        ).first()
        monitoring_settings = json.loads(task.env_vars).get("monitoring_settings")
        log.info(f"{monitoring_settings=}")
        if not monitoring_settings:
            return
        log.info(f"event called {payload=} {event=}")
        rows = [ResultsGetModel.parse_obj(i.to_json()).dict() for i in task_results]
        rows = [(task['task_result_id'], task["task_status"])
                for task in rows
                ][-monitoring_settings['failed_tasks']:]

        log.info(f'{rows=}')

        if not all([task[1].lower() == 'failed' for task in rows]):
            log.info('No failed tasks')
            return
        notification_task_id = monitoring_settings['integration']
        if notification_task_id == payload['task_id']:
            log.info('Notification task id is equal to failed task id')
            return
        recipients = [{
            'email': email,
            'roles': []
        } for email in monitoring_settings['recipients']]

        TaskManager(project_id=payload['project_id'], mode=c.ADMINISTRATION_MODE).run_task(
            [{
                'recipients': recipients,
                'subject': f'Task  {task.task_name} has been failed',
                'task_name': task.task_name,
            }], notification_task_id)

        log.info(f'task finished event called {rows=} \n')
