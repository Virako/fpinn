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
## buscar_albaranes.py - Búsqueda mejorada de albaranes de salida.
###################################################################
## NOTAS:
##  
###################################################################

import os
from formularios import utils
import pygtk
pygtk.require('2.0')
import gtk, gtk.glade, time, mx, mx.DateTime
from framework import pclases
from formularios.ventana import Ventana
import gobject

class BuscarAlbaranes(Ventana):
    VENTANA = os.path.join("ui", "buscar_albaranes.glade")
    def __init__(self, objeto = None, usuario = None):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        self.usuario = usuario
        Ventana.__init__(self, self.VENTANA, objeto)
        self.inicializar_ventana()
        self.add_connections({"b_salir/clicked": self.salir, 
                              "b_abrir/clicked": self.abrir_albaran})
        self.rellenar_widgets()
        gtk.main()

    def abrir_albaran(self, boton):
        """
        Abre el albarán seleccionado.
        """
        model, iter = self.wids['tv_resultados'].get_selection().get_selected()
        id = model[iter][-1]
        a = pclases.AlbaranSalida.get(id)
        import albaranes_de_salida
        v = albaranes_de_salida.AlbaranesDeSalida(a, usuario = self.usuario)

    def abrir_albaran_from_tv(self, tv, path, col):
        """
        Abre el albarán al que se le ha hecho doble clic en el TreeView.
        """
        from facturar_albaranes import abrir_albaran
        abrir_albaran(tv, path, col, self.usuario, self)

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
        cols = (('Número', 'gobject.TYPE_STRING', False, True, True, None), 
                ('Cliente', 'gobject.TYPE_STRING', False, True, False, None),
                ('Fecha', 'gobject.TYPE_STRING', False, True, False, None),
                ('Importe (IVA incl.)', 'gobject.TYPE_STRING', 
                    False, True, False, None),
                ('Estado', 'gobject.TYPE_STRING', False, True, False, None),
                ('ID', 'gobject.TYPE_INT64', False, False, False, None))
        utils.preparar_listview(self.wids['tv_resultados'], cols)
        nmodel = gtk.ListStore(gobject.TYPE_STRING, 
                               gobject.TYPE_STRING, 
                               gobject.TYPE_STRING, 
                               gobject.TYPE_STRING, 
                               gobject.TYPE_STRING, 
                               gobject.TYPE_INT64, 
                               gobject.TYPE_INT64)
        self.wids['tv_resultados'].set_model(nmodel)
        col = self.wids['tv_resultados'].get_column(3)
        for cell in col.get_cell_renderers():
            cell.set_property("xalign", 1)
        self.wids['tv_resultados'].connect("row-activated", 
                                           self.abrir_albaran_from_tv)
        self.wids['a_buscar'].connect("changed", self.rellenar_albaranes)
        self.wids['ventana'].resize(640, 480)
        self.wids['b_guardar'] = gtk.Button("N/A")
        self.wids['b_guardar'].set_property("visible", False)
        self.wids['b_guardar'].set_sensitive(False)
        self.colorear(self.wids['tv_resultados'])

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
            self.check_permisos(nombre_fichero_ventana = "buscar_albaranes.py")

    def rellenar_widgets(self):
        """
        Introduce la información de la cuenta actual
        en los widgets.
        No se chequea que sea != None, así que
        hay que tener cuidado de no llamar a 
        esta función en ese caso.
        """
        self.rellenar_albaranes()

    def actualizar_ventana(self, *args, **kw):
        model = self.wids['tv_resultados'].get_model()
        for path in range(len(model)):
            id = model[path][-1]
            a = pclases.AlbaranSalida.get(id)
            for ldv in a.lineasDeVenta:
                ldv.sync()
            a.sync()
        self.rellenar_widgets()

    def rellenar_albaranes(self, editable = None):
        """
        Introduce los adjuntos del objeto en la tabla de adjuntos.
        """
        model = self.wids['tv_resultados'].get_model()
        model.clear()
        a_buscar = self.wids['a_buscar'].get_text()
        if not a_buscar:
            albaranes = pclases.AlbaranSalida.select(orderBy = "fecha")
            resultados = list(albaranes)
        else:
            palabras = a_buscar.split()
            resultados = []
            clase = pclases.AlbaranSalida
            if len(palabras) > 1:
                subcriterios_numalbaran = [clase.q.numalbaran.contains(t)
                                           for t in palabras]
            else:
                subcriterios_numalbaran = clase.q.numalbaran.contains(a_buscar)
            tmpresultados = clase.select(subcriterios_numalbaran)
            resultados = list(tmpresultados)
        clientes = pclases.Cliente.select(
            pclases.Cliente.q.nombre.contains(a_buscar))
        if clientes.count():
            idsc = [c.id for c in clientes]
            resultados += [a for a in pclases.AlbaranSalida.select() 
                           if a.clienteID in idsc and a not in resultados]
        for albaran in resultados:
            estado = albaran.get_estado()
            model.append(
                (albaran.numalbaran, 
                 albaran.cliente and albaran.cliente.nombre or "", 
                 utils.str_fecha(albaran.fecha), 
                 utils.float2str(albaran.calcular_importe(iva = True)), 
                 albaran.get_str_estado(estado), 
                 estado, 
                 albaran.id))

    def colorear(self, tv):
        def cell_func(column, cell, model, itr):
            estado = model[itr][-2]
            if estado == pclases.AlbaranSalida.SIN_CLIENTE:
                color = "red"
            elif estado == pclases.AlbaranSalida.VACIO:
                color = "light blue"
            elif estado == pclases.AlbaranSalida.INCOMPLETO:
                color = "orange"
            elif estado == pclases.AlbaranSalida.PENDIENTE_FACTURAR:
                color = "yellow"
            elif estado == pclases.AlbaranSalida.PENDIENTE_COBRO:
                color = "light green"
            elif estado == pclases.AlbaranSalida.COBRADO:
                color = "green"
            else:
                color = None
            cell.set_property("cell-background", color)

        cols = tv.get_columns()
        for i in xrange(len(cols)):
            column = cols[i]
            cells = column.get_cell_renderers()
            for cell in cells:
                column.set_cell_data_func(cell,cell_func)


if __name__ == "__main__":
    p = BuscarAlbaranes()

