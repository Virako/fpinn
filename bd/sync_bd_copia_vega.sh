#!/bin/sh

scp fpinn@tetsuo:dump*.sql .
./reorder_dump.py tablas.sql dump_datos_fpinn.sql > dump_datos.sql
./init_db.sh fpinn ufpinn ufpinn dump_datos.sql

# El log.
scp fpinn@tetsuo:ginn.log ../formularios/

