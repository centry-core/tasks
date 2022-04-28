from tools import db


def init_db():
    from .models.results import Results
    from .models.tasks import Task
    db.Base.metadata.create_all(bind=db.engine)

