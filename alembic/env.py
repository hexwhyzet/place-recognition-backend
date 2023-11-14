from logging.config import fileConfig

from alembic import context
from geoalchemy2 import Geometry, Geography, Raster
from geoalchemy2.admin import _check_spatial_type
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlmodel import SQLModel
from models import *

from db.postgres import DATABASE_URL

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.
config.set_main_option('sqlalchemy.url', DATABASE_URL)


def render_item(obj_type, obj, autogen_context):
    """Apply custom rendering for selected items."""
    if obj_type == 'type' and isinstance(obj, (Geometry, Geography, Raster)):
        import_name = obj.__class__.__name__
        autogen_context.imports.add(f"from geoalchemy2 import {import_name}")
        return "%r" % obj

    # for the cumstomed type
    # if obj_type == 'type' and isinstance(obj, (ThreeDGeometry,)):
    #     import_name = obj.__class__.__name__
    #     autogen_context.imports.add(f"from jobs.migrate.test.models import {import_name}")
    #     return "%r" % obj

    # default rendering for other objects
    return False


def include_object(obj, name, obj_type, reflected, compare_to):
    """Do not include spatial indexes if they are automatically created by GeoAlchemy2."""
    if obj_type == "index":
        if len(obj.expressions) == 1:
            try:
                col = obj.expressions[0]
                if (
                        _check_spatial_type(col.type, (Geometry, Geography, Raster))
                        and col.type.spatial_index
                ):
                    return False
            except AttributeError:
                pass
    if obj_type == "table" and name == "spatial_ref_sys":
        return False

    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_item=render_item,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_item=render_item,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
