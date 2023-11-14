from enum import Enum

from sqlmodel import Session


class CreationType(int, Enum):
    NONE = 1
    FLUSH = 2
    COMMIT = 3


def get_arg(args, kwargs, arg_type):
    for arg in list(args) + list(kwargs.values()):
        if isinstance(arg, arg_type):
            return arg
    raise Exception(f'arg of type {arg_type} not found')


def create_wrapper(function):
    def wrapper(*args, **kwargs):
        session: Session = get_arg(args, kwargs, Session)
        creation_type: CreationType = get_arg(args, kwargs, CreationType)

        model = function(*args, **kwargs)
        if creation_type == CreationType.FLUSH:
            session.add(model)
            session.flush()
        elif creation_type == CreationType.COMMIT:
            session.add(model)
            session.commit()
        return model

    return wrapper
