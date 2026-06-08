#!/bin/bash
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" <<-EOSQL
	SELECT 'CREATE DATABASE thoughtweaver'
	WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'thoughtweaver')\gexec
	SELECT 'CREATE DATABASE agent_sdk_server'
	WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'agent_sdk_server')\gexec
EOSQL
