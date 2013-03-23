#!/bin/sh

# 0.- Preparo directorio de trabajo:
DIR_BAK="bakfpinn"
FILE_BAK="bakfpinn.tar.bz2"
TMPDIR=/tmp
rm -rf $TMPDIR/$DIR_BAK 2>/dev/null
rm -f $TMPDIR/$FILE_BAK 2>/dev/null
mkdir $TMPDIR/$DIR_BAK
# 1.- Copia de la BD
./backup_bd.sh 
cp dump_datos.sql $TMPDIR/$DIR_BAK
# 2.- Copia del log
cp ../formularios/ginn.log $TMPDIR/$DIR_BAK
# 3.- Copia de compartido
cp -a ../compartido $TMPDIR/$DIR_BAK
# 4.- Copia de adjuntos
cp -a ../adjuntos $TMPDIR/$DIR_BAK
# 5.- Comprimo todo en un bzip2.
cd $TMPDIR
tar cvjf $FILE_BAK $DIR_BAK
cd -

echo
echo Los directorios de adjuntos y compartido, el log y una copia de la BD están en $TMPDIR/$FILE_BAK

