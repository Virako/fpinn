#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2005-2007  Francisco José Rodríguez Bogado,                   #
#                          (pacoqueen@users.sourceforge.net                   #
# Copyright (C) 2013  Victor Ramirez de la Corte, virako.9@gmail.com          #
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
## agenda.py - Agenda telefónica de clientes y proveedores.
###################################################################
## NOTAS:
##  
###################################################################
## Changelog:
## 6 de enero de 2007 -> Inicio
## 
###################################################################

import os
from formularios import utils
import pygtk
pygtk.require('2.0')
import gtk, gtk.glade
from framework import pclases
from formularios.ventana import Ventana

class Agenda(Ventana):
    VENTANA = os.path.join("ui", "agenda_telefonos.glade")
    def __init__(self, objeto = None, usuario = None):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        self.usuario = usuario
        Ventana.__init__(self, self.VENTANA, objeto)
        self.inicializar_ventana()
        self.add_connections({"b_salir/clicked": self.salir})
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
        # Inicialización del resto de widgets:
        cols = (('Nombre', 'gobject.TYPE_STRING', False, True, True, None), 
                ('Teléfono', 'gobject.TYPE_STRING', False, True, False, None),
                ('ID', 'gobject.TYPE_STRING', False, False, False, None))
        utils.preparar_listview(self.wids['tv_resultados'], cols)
        self.wids['a_buscar'].connect("changed", self.rellenar_telefonos)
        self.wids['ventana'].resize(640, 480)
        self.wids['b_guardar'] = gtk.Button("N/A")
        self.wids['b_guardar'].set_property("visible", False)
        self.wids['b_guardar'].set_sensitive(False)

    def es_diferente(self):
        return False
    
    def activar_widgets(self, s, chequear_permisos = True):
        """
        Activa o desactiva (sensitive=True/False) todos 
        los widgets de la ventana que dependan del 
        objeto mostrado.
        Entrada: s debe ser True o False. En todo caso
        se evaluará como boolean.
        """
        ws = self.wids.keys()
        for w in ws:
            try:
                self.wids[w].set_sensitive(s)
            except Exception, msg:
                print "Widget problemático:", w, "Excepción:", msg
                #import traceback
                #traceback.print_last()
        if chequear_permisos:
            self.check_permisos(nombre_fichero_ventana = "agenda.py")

    def rellenar_widgets(self):
        """
        Introduce la información de la cuenta actual
        en los widgets.
        No se chequea que sea != None, así que
        hay que tener cuidado de no llamar a 
        esta función en ese caso.
        """
        self.rellenar_telefonos()

    def rellenar_telefonos(self, editable = None):
        """
        Introduce los adjuntos del objeto en la tabla de adjuntos.
        """
        model = self.wids['tv_resultados'].get_model()
        model.clear()
        a_buscar = self.wids['a_buscar'].get_text()
        if a_buscar:
            palabras = a_buscar.split()
            resultados = []
            for clase in (pclases.Cliente, pclases.Proveedor, pclases.Empleado):
                if len(palabras) > 1:
                    subcriterios_nombre = [clase.q.nombre.contains(t)
                                            for t in palabras]
                    subcriterios_nombre = pclases.AND(*subcriterios_nombre)
                    subcriterios_telefono = [clase.q.telefono.contains(t)
                                                for t in palabras]
                    subcriterios_telefono = pclases.AND(*subcriterios_telefono)
                else:
                    subcriterios_nombre = clase.q.nombre.contains(a_buscar)
                    subcriterios_telefono = clase.q.telefono.contains(a_buscar)
                tmpresultados = clase.select(pclases.OR(subcriterios_nombre, 
                                                        subcriterios_telefono))
                resultados += tuple(tmpresultados)
            for resultado in resultados:
                model.append((resultado.nombre, 
                              resultado.telefono, 
                              "%s:%d"%(resultado.sqlmeta.table, resultado.id)))

if __name__ == "__main__":
    p = Agenda()

