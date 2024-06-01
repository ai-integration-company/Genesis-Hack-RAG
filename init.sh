#!/bin/bash
set -e

psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS vector;
EOSQL