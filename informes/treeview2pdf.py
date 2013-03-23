#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2005-2008 Francisco José Rodríguez Bogado,                   #
#                          Diego Muñoz Escalante.                             #
# (pacoqueen@users.sourceforge.net, escalant3@users.sourceforge.net)          #
#                                                                             #
# This file is part of F.P.-INN .                                             #
#                                                                             #
# F.P.-INN  is free software; you can redistribute it and/or modify           #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation; either version 2 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# F.P.-INN  is distributed in the hope that it will be useful,                #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with F.P.-INN ; if not, write to the Free Software                    #
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA  #
###############################################################################

import sys, os
import geninformes
try:
    import utils
    from trazabilidad import Trazabilidad
except ImportError:
    sys.path.append(os.path.join('..', 'formularios'))
    import utils
    from trazabilidad import Trazabilidad
import mx, mx.DateTime
try:
    import pclases
except ImportError:
    sys.path.append(os.path.join('..', 'framework'))
    import pclases
from informes import abrir_pdf
from tempfile import gettempdir

def treeview2pdf(tv, titulo = None, fecha = None, apaisado = None):
    """
    A partir de un TreeView crea un PDF con su contenido.
    1.- Asigna un nombre de archivo en función del nombre del TreeView.
    2.- Si titulo es None, asigna como título el nombre del TreeView.
    3.- El ancho de los campos será el ancho relativo en porcentaje que ocupa el 
        ancho de la columna (get_width) a la que correspondería. El título del campo será el 
        título (get_title) de la columna.
    4.- Si fecha no es None debe ser una cadena de texto. Si no es None, se usará la 
        fecha actual del sistema.
    5.- Si la suma del ancho de las columnas del TreeView es superior a 800 píxeles el 
        PDF generado será apaisado, a no ser que se fuerce mediante el parámetro 
        "apaisado" que recibe la función.
    """
    archivo = get_nombre_archivo_from_tv(tv)
    if titulo == None:
        titulo = get_titulo_from_tv(tv)
    campos, pdf_apaisado, cols_a_derecha = get_campos_from_tv(tv)
    datos = get_datos_from_tv(tv)
    if fecha == None:
        fecha = utils.str_fecha(mx.DateTime.localtime())
    if apaisado != None:
        pdf_apaisado = apaisado
    return geninformes.imprimir2(archivo, titulo, campos, datos, fecha, apaisado = pdf_apaisado, cols_a_derecha = cols_a_derecha)

def get_nombre_archivo_from_tv(tv):
    """
    Devuelve el nombre del archivo que se generará a partir
    del nombre del widget TreeView.
    """
    nomtreeview = tv.get_name().replace(" ", "_")
    nomarchivo = os.path.join(gettempdir(), "%s_%s.pdf" % (nomtreeview, geninformes.give_me_the_name_baby()))
    return nomarchivo

def get_datos_from_tv(tv):
    """
    Devuelve una lista de tuplas. Cada tupla contiene los datos de las cells 
    del TreeView para cada fila.
    Si la fila es padre de otra fila, añade debajo de la misma las filas hijas 
    con espacios a su izquierda y un separador horizontal al final.
    """
    datos = []
    model = tv.get_model()
    numcols = len(tv.get_columns())
    for fila in model:
        filadato = []
        for i in xrange(numcols):
            filadato.append(fila[i])
        datos.append(filadato)
        if hasattr(fila, 'iterchildren'):
            filas_hijas = agregar_hijos(fila, numcols, 1)
            if filas_hijas != [] and len(datos) > 1 and datos[-2][0] != "---":
                datos.insert(-1, ("---", ) * numcols)
            for fila_hija in filas_hijas:
                datos.append(fila_hija)
            if filas_hijas != []:
                datos.append(("---", ) * numcols)
    # Elimino líneas duplicadas consecutivas:
    #datosbak = datos[:]
    #datos = []
    #for i in xrange(len(datosbak)-1)
    #    if datos[i] != datos[i+1]:
            
    return datos

def agregar_hijos(fila, numcols, numespacios):
    """
    Devuelve una lista con los hijos de "fila", y éstos a 
    su vez con sus hijos, etc... en diferentes niveles.
    numespacios normalmente será el nivel de profundidad de 
    la recursión * 2.
    """
    iterator_hijos = fila.iterchildren()
    if iterator_hijos == None:
        return []
    else:
        filas = []
        for hijo in iterator_hijos:
            filahijo = []
            for col in xrange(numcols):
                if col == 0:
                    filahijo.append("%s%s" % ("> " * numespacios, hijo[col]))
                else:
                    filahijo.append("%s" % (hijo[col]))     # Por si acaso trae un entero, un float o algo asina.
            filas += [filahijo] + agregar_hijos(hijo, numcols, numespacios + 1)
        return filas

def get_nombre_archivo_from(tv):
    """
    Devuelve el nombre del widget "tv".
    """
    return tv.get_name()

def get_titulo_from_tv(tv):
    """
    Devuelve el nombre del widget "tv".
    """
    return tv.get_name()

def get_campos_from_tv(tv):
    """
    Devuelve una tupla de tuplas. Cada tupla "interior" tiene el nombre 
    del campo y el ancho relativo en tanto porciento respecto al total 
    del TreeView.
    Devuelve también un boolean que será True si el ancho total de las 
    columnas supera los 800 píxeles.
    """
    cols = []
    anchotv = 0
    for column in tv.get_columns():
        anchocol = column.get_width()
        if anchocol == 0:
            anchocol = column.get_fixed_width()
            if anchocol == 0:
                anchocol = 100 / len(tv.get_columns())
        anchotv += anchocol
        cell = column.get_cell_renderers()[0]   # Nunca uso más de un cell por columna. La alineación del primero me basta.
        xalign = cell.get_property("xalign")
        if xalign < 0.4:
            alineacion = -1     # Izquierda
        elif 0.4 <= xalign <= 0.6:
            alineacion = 0      # Centro
        else:
            alineacion = 1      # Derecha
        cols.append({'título': column.get_title(), 'ancho': anchocol, 'alineación': alineacion})
    res = []
    cols_a_derecha = []
    for col, i in zip(cols, range(len(cols))):
        col['ancho'] = (col['ancho'] * 100) / anchotv
        res.append((col['título'], col['ancho']))
        if col['alineación'] == 1:
            cols_a_derecha.append(i)
    return res, anchotv >= 800, cols_a_derecha

def probar():
    """
    Test
    """
    #abrir_pdf(treeview2pdf(tv, titulo, fecha))
    esto_habria_que_annadirlo_al_scrip_inicial = "abrir_pdf(treeview2pdf(self.wids['tv_datos']))"
    Trazabilidad(pclases.Rollo.select(orderBy = "-id")[0], locals_adicionales = {'treeview2pdf': treeview2pdf, 'abrir_pdf': abrir_pdf})

if __name__ == "__main__":
    probar()

