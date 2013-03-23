#!/bin/sh

if [ ! $# -eq 1 ]; then 
    echo Debe especificar el archivo de la copia de seguridad.
    exit 1
fi

TMPDIR="/tmp"
FILE_BAK=$1

DIR_BD=$(pwd)
cp $FILE_BAK $TMPDIR
cd $TMPDIR
BAK_DIR=$(tar xvjf $FILE_BAK | tail -n 1 | cut -d "/" -f 1)

# Restauro BD
cp $BAK_DIR/dump_datos.sql $DIR_BD
cd $DIR_BD
USER=$(grep user ../framework/ginn.conf | awk '{print $2}')
PASS=$(grep pass ../framework/ginn.conf | awk '{print $2}')
BD=$(grep dbname ../framework/ginn.conf | awk '{print $2}')
./reorder_dump.py tablas.sql dump_datos.sql > dump_datos_r.sql
./init_db.sh $BD $USER $PASS dump_datos_r.sql
# Restauro LOG
cp -f $TMPDIR/$BAK_DIR/ginn.log ../formularios
# Restauro compartido
cp -af $TMPDIR/$BAK_DIR/compartido/* ../compartido
# Restauro adjuntos
cp -af $TMPDIR/$BAK_DIR/adjuntos/* ../adjuntos

