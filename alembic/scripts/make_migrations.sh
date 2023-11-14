#!/bin/bash

echo "Please, give name to migration:";
read -r input_variable;
export MIGRATION_NAME=$input_variable;
echo MIGRATION_NAME="$MIGRATION_NAME";
$POETRY_PATH -m alembic revision --autogenerate -m "$MIGRATION_NAME";
