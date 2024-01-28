from enum import Enum

from loguru import logger
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


def get_or_create(session, model, defaults=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).one_or_none()
    if instance:
        return instance, False
    else:
        kwargs |= defaults or {}
        instance = model(**kwargs)
        try:
            session.add(instance)
            session.commit()
        except (Exception,) as e:
            logger.info("DB exception occurred:", e)
            session.rollback()
            instance = session.query(model).filter_by(**kwargs).one()
            return instance, False
        else:
            return instance, True
