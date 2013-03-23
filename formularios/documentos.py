#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2005-2007  Francisco José Rodríguez Bogado,                   #
#                          (pacoqueen@users.sourceforge.net                   #
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


###################################################################
## documentos.py - Documentos adjuntos.
###################################################################
## NOTAS:
##  Usar ESTA ventana a partir de ahora para crear nuevas.
##  Hereda de ventana y ventana genérica, y la mayoría de funciones
##  están automatizadas partiendo tan solo de la clase y un 
##  diccionario que empareje widgets y atributos.
## ----------------------------------------------------------------
##  
###################################################################
## Changelog:
## 17 de diciembre de 2007 -> Inicio
## 
###################################################################

import sys, os
import utils
import pygtk
pygtk.require('2.0')
import gtk, gtk.glade, time, mx, mx.DateTime
try:
    import pclases
except ImportError:
    sys.path.append(os.path.join('..', 'framework'))
    import pclases
from ventana import Ventana

class Documentos(Ventana):
    CLASE = pclases.Documento
    VENTANA = os.path.join("..", "ui", "documentos.glade")
    def __init__(self, empleado_o_gasto, objeto = None, usuario = None):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        self.usuario = usuario
        self.empleado_o_gasto = empleado_o_gasto
        self.clase = self.CLASE
        Ventana.__init__(self, self.VENTANA, objeto)
        connections = {'b_drop_adjunto/clicked': self.drop_adjunto,
                       'b_add_adjunto/clicked': self.add_adjunto,
                       'b_ver_adjunto/clicked': self.ver_adjunto,
                       'b_salir/clicked': self.salir, 
                      }
        self.add_connections(connections)
        self.inicializar_ventana()
        self.rellenar_documentos()
        gtk.main()

    def inicializar_ventana(self):
        """
        Inicializa los controles de la ventana, estableciendo sus
        valores por defecto, deshabilitando los innecesarios,
        rellenando los combos, formateando el TreeView -si lo hay-...
        """
        # Inicialmente no se muestra NADA. Sólo se le deja al
        # usuario la opción de buscar o crear nuevo.
        self.activar_widgets(False)
        self.wids['ventana'].set_title("Documentos adjuntos - %s"
                                        % self.empleado_o_gasto.nombre)
        # Inicialización del resto de widgets:
        cols = (('Nombre', 'gobject.TYPE_STRING', True, True, True, self.cambiar_nombre_adjunto), 
                ('Observaciones', 'gobject.TYPE_STRING', True, True, False, self.cambiar_observaciones_adjunto),
                ('ID', 'gobject.TYPE_INT64', False, False, False, None))
        utils.preparar_listview(self.wids['tv_adjuntos'], cols)
        self.wids['tv_adjuntos'].connect("row-activated", abrir_adjunto_from_tv)
        return

    def activar_widgets(self, s, chequear_permisos = True):
        """
        Activa o desactiva (sensitive=True/False) todos 
        los widgets de la ventana que dependan del 
        objeto mostrado.
        Entrada: s debe ser True o False. En todo caso
        se evaluará como boolean.
        """
        if self.empleado_o_gasto == None:
            s = False
        ws = self.wids.keys()
        for w in ws:
            try:
                self.wids[w].set_sensitive(s)
            except Exception, msg:
                print "Widget problemático:", w, "Excepción:", msg
                #import traceback
                #traceback.print_last()
        if chequear_permisos:
            self.check_permisos(nombre_fichero_ventana = "documentos.py")

    def rellenar_widgets(self):
        """
        Introduce la información de la cuenta actual
        en los widgets.
        No se chequea que sea != None, así que
        hay que tener cuidado de no llamar a 
        esta función en ese caso.
        """
        self.rellenar_documentos()

    def rellenar_documentos(self):
        """
        Introduce los adjuntos del objeto en la tabla de adjuntos.
        """
        model = self.wids['tv_adjuntos'].get_model()
        model.clear()
        if self.empleado_o_gasto != None:
            docs = self.empleado_o_gasto.documentos[:]
            docs.sort(lambda x, y: utils.orden_por_campo_o_id(x, y, "id"))
            for adjunto in self.empleado_o_gasto.documentos:
                model.append((adjunto.nombre, 
                              adjunto.observaciones, 
                              adjunto.id))

    def cambiar_nombre_adjunto(self, cell, path, texto):
        model = self.wids['tv_adjuntos'].get_model() 
        iddoc = model[path][-1]
        pclases.Documento.get(iddoc).nombre = texto
        model[path][0] = pclases.Documento.get(iddoc).nombre

    def cambiar_observaciones_adjunto(self, cell, path, texto):
        model = self.wids['tv_adjuntos'].get_model() 
        iddoc = model[path][-1]
        pclases.Documento.get(iddoc).observaciones = texto
        model[path][1] = pclases.Documento.get(iddoc).observaciones

    def add_adjunto(self, boton):
        """
        Adjunta un documento a la factura de compra.
        """
        utils.dialogo_adjuntar("ADJUNTAR DOCUMENTO", 
                               self.empleado_o_gasto, 
                               self.wids['ventana'])
        self.rellenar_documentos()

    def drop_adjunto(self, boton):
        """
        Elimina el adjunto seleccionado.
        """
        model, iter = self.wids['tv_adjuntos'].get_selection().get_selected()
        if iter != None and utils.dialogo(titulo = "BORRAR DOCUMENTO", 
                                          texto = '¿Borrar documento adjunto seleccionado?', 
                                          padre = self.wids['ventana']):
            docid = model[iter][-1]
            documento = pclases.Documento.get(docid)
            utils.mover_a_tmp(documento.get_ruta_completa())
            documento.destroySelf()
            self.rellenar_documentos()

    def ver_adjunto(self, boton):
        """
        Intenta abrir el adjunto seleccionado.
        """
        from multi_open import open as mopen
        model, iter = self.wids['tv_adjuntos'].get_selection().get_selected()
        if iter != None:
            docid = model[iter][-1]
            documento = pclases.Documento.get(docid)
            self.wids['ventana'].window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
            while gtk.events_pending(): gtk.main_iteration(False)
            try:
                if not mopen(documento.get_ruta_completa()):
                    utils.dialogo_info(titulo = "NO SOPORTADO", 
                                       texto = "La aplicación no conoce cómo abrir el tipo de fichero.", 
                                       padre = self.wids['ventana'])
            except:
                utils.dialogo_info(titulo = "ERROR", 
                                   texto = "Se produjo un error al abrir el archivo.\nLa plataforma no está soportada, no se conoce el tipo de archivo o no hay un programa asociado al mismo.", 
                                   padre = self.wids['ventana'])
            import gobject
            gobject.timeout_add(2000, lambda *args, **kw: self.wids['ventana'].window.set_cursor(None))


def abrir_adjunto_from_tv(tv, path, col):   # XXX: Código para adjuntos.
    """
    Abre el adjunto con el programa asociado al mime-type del mismo.
    """
    model = tv.get_model()
    id = model[path][-1]
    documento = pclases.Documento.get(id)
    from multi_open import open as mopen
    mopen(documento.get_ruta_completa())


if __name__ == "__main__":
    p = Documentos(pclases.Empleado.select()[0])

