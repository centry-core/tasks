try:
    from enum import StrEnum
except ImportError:
    from enum import Enum

    class StrEnum(str, Enum):
        pass

RUNTIME_MAPPING = {
    "Python 3.7": 'lambda:python3.7',
    "Python 3.8": 'lambda:python3.8',
    "Python 3.6": 'lambda:python3.6',
    "Python 2.7": 'lambda:python2.7',
    ".NET Core 2.0 (C#)": 'lambda:dotnetcore2.0',
    ".NET Core 2.1 (C#/PowerShell)": 'lambda:dotnetcore2.1',
    "Go 1.x": "lambda:go1.x",
    "Java 8": "lambda:java8",
    "Java 11": "lambda:java11",
    "Node.js 6.10": 'lambda:nodejs6.10',
    "Node.js 8.10": 'lambda:nodejs8.10',
    "Node.js 10.x": 'lambda:nodejs10.x',
    "Node.js 12.x": 'lambda:nodejs12.x',
    "Ruby 2.5": 'lambda:ruby2.5'
}


class TASK_STATUS(StrEnum):
    IN_PROGRESS = 'In progress...'
    DONE = 'Done'
    FAILED = 'Failed'
