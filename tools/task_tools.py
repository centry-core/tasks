from uuid import uuid4
from werkzeug.utils import secure_filename
from sqlalchemy import and_
from arbiter import Arbiter

from ..models.tasks import Task
from tools import constants as c, api_tools, rpc_tools, data_tools, secrets_tools


def get_arbiter():
    return Arbiter(host=c.RABBIT_HOST, port=c.RABBIT_PORT, user=c.RABBIT_USER, password=c.RABBIT_PASSWORD)


def create_task(project, file, args):
    if isinstance(file, str):
        file = data_tools.files.File(file)
    filename = str(uuid4())
    filename = secure_filename(filename)
    api_tools.upload_file(bucket="tasks", f=file, project=project)
    task = Task(
        task_id=filename,
        project_id=project.id,
        zippath=f"tasks/{file.filename}",
        task_name=args.get("funcname"),
        task_handler=args.get("invoke_func"),
        runtime=args.get("runtime"),
        region=args.get("region"),
        env_vars=args.get("env_vars")
    )
    task.insert()
    return task


def check_task_quota(task, project_id=None, quota='tasks_executions'):
    # TODO: we need to calculate it based on VUH, if we haven't used VUH quota then run
    return {"message", "ok"}


def run_task(project_id, event, task_id=None) -> dict:
    rpc = rpc_tools.RpcMixin().rpc
    secrets = secrets_tools.get_project_hidden_secrets(project_id=project_id)
    secrets.update(secrets_tools.get_project_secrets(project_id=project_id))
    task_id = task_id if task_id else secrets["control_tower_id"]
    task = Task.query.filter(and_(Task.task_id == task_id)).first().to_json()
    check_task_quota(task)
    rpc.call.add_task_execution(project_id=task['project_id'])
    arbiter = get_arbiter()
    task_kwargs = {
        "task": secrets_tools.unsecret(value=task, secrets=secrets, project_id=project_id),
        "event": secrets_tools.unsecret(value=event, secrets=secrets, project_id=project_id),
        "galloper_url": secrets_tools.unsecret(
            value="{{secret.galloper_url}}",
            secrets=secrets,
            project_id=task['project_id']
        ),
        "token": secrets_tools.unsecret(value="{{secret.auth_token}}", secrets=secrets, project_id=task['project_id'])
    }
    arbiter.apply("execute_lambda", queue=c.RABBIT_QUEUE_NAME, task_kwargs=task_kwargs)
    arbiter.close()
    return {"message": "Accepted", "code": 200, "task_id": task_id}
