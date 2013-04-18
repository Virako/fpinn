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
## produccion_por_empleado.py - Producción diaria por empleado.
###################################################################
## NOTAS:
##  
###################################################################
## Changelog:
## 24 de enero de 2007 -> Inicio
## 
###################################################################

import os
from formularios import utils
import pygtk
pygtk.require('2.0')
import gtk, gtk.glade, mx, mx.DateTime
from framework import pclases
from formularios.ventana import Ventana
from treeview2pdf import treeview2pdf
from treeview2csv import treeview2csv
from informes import abrir_pdf, abrir_csv

class ProduccionPorEmpleado(Ventana):
    VENTANA = os.path.join("ui", "produccion_por_empleado.glade")
    def __init__(self, objeto = None, usuario = None):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        self.usuario = usuario
        Ventana.__init__(self, self.VENTANA, objeto)
        self.add_connections({"b_salir/clicked": self.salir, 
                              "b_imprimir/clicked": self.imprimir, 
                              "b_exportar/clicked": self.exportar, 
                              "cb_empleado/changed": self.mostrar_produccion})
        self.inicializar_ventana()
        if objeto != None:
            utils.combo_set_from_db(self.wids['cb_empleado'], objeto.id)
        gtk.main()

    def imprimir(self, boton):
        """
        Exporta a PDF.
        """
        idempl = utils.combo_get_value(self.wids['cb_empleado'])
        if idempl:
            nomempl = pclases.Empleado.get(idempl)
            titulo = "%s: producción diaria." % nomempl.nombre
        else:
            titulo = "Producción diaria"
        strfecha = utils.str_fechahora(mx.DateTime.localtime())
        abrir_pdf(treeview2pdf(self.wids['tv_datos'], 
                               titulo = titulo, 
                               fecha = strfecha))

    def exportar(self, boton):
        """
        Exporta a CSV.
        """
        abrir_csv(treeview2csv(self.wids['tv_datos']))

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
        empls = [(c.id, c.nombre) 
                 for c in pclases.Empleado.select(orderBy = "nombre")]
        utils.rellenar_lista(self.wids['cb_empleado'], empls)
        self.wids['b_guardar'] = gtk.Button("N/A")
        self.wids['b_guardar'].set_property("visible", False)
        self.wids['b_guardar'].set_sensitive(False)
        cols = (("Día", "gobject.TYPE_STRING", False, True, True, None), 
                ("Rendimiento", "gobject.TYPE_STRING", False,True,False,None), 
                ("Producción personal", "gobject.TYPE_STRING", False, True, 
                    False, None), 
                ("Ratio diario", "gobject.TYPE_STRING", False, True, False, 
                    None), 
                ("Media global", "gobject.TYPE_STRING", False, True, False, 
                    None), 
                ("nihil", "gobject.TYPE_INT64", False, False, False, None))
        tv = self.wids['tv_datos']
        utils.preparar_listview(tv, cols)
        tv.get_column(1).get_cell_renderers()[0].set_property('xalign', 0.9)
        tv.get_column(2).get_cell_renderers()[0].set_property('xalign', 0.9)
        tv.get_column(3).get_cell_renderers()[0].set_property('xalign', 0.9)
        tv.get_column(4).get_cell_renderers()[0].set_property('xalign', 0.9)
        self.colorear(tv)

    def colorear(self, tv):
        def cell_func(column, cell, model, itr):
            p = utils.parse_float(model[itr][2])
            d = utils.parse_float(model[itr][3])
            if p < d:
                color = "red"
            elif p > d:
                color = "green"
            else:
                color = "blue"
            cell.set_property("foreground", color)
        def cell_func2(column, cell, model, itr):
            p = utils.parse_float(model[itr][2])
            m = utils.parse_float(model[itr][4])
            if p < m:
                color = "red"
            elif p > m:
                color = "green"
            else:
                color = "blue"
            cell.set_property("foreground", color)
        cols = tv.get_columns()
        column = cols[2]
        cells = column.get_cell_renderers()
        for cell in cells:
            column.set_cell_data_func(cell,cell_func)
        column = cols[4]
        cells = column.get_cell_renderers()
        for cell in cells:
            column.set_cell_data_func(cell,cell_func2)

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
            self.check_permisos(nombre_fichero_ventana = "produccion_por_parcela.py")

    def rellenar_widgets(self):
        """
        Introduce la información de la cuenta actual
        en los widgets.
        No se chequea que sea != None, así que
        hay que tener cuidado de no llamar a 
        esta función en ese caso.
        """
        self.mostrar_produccion()

    def mostrar_produccion(self, cb = None):
        model = self.wids['tv_datos'].get_model()
        id = utils.combo_get_value(self.wids['cb_empleado'])
        model.clear()
        if id > 0:
            empleado = pclases.Empleado.get(id)
            ratio = empleado.calcular_ratio()
            for dia, rendimiento, produccion \
             in get_rendimiento_empleado_por_dias(empleado):
                media_global = pclases.Jornal.calcular_media_global(dia)
                model.append((utils.str_fecha(dia), 
                              "%s kg/planta" % utils.float2str(rendimiento), 
                              "%s kg" % utils.float2str(produccion), 
                              "%s kg" % utils.float2str(ratio), 
                              "%s kg" % utils.float2str(media_global), 
                              0))

def get_rendimiento_empleado_por_dias(e):
    """
    Devuelve una lista de tuplas (día, rendimiento en kg/planta, producción) 
    del empleado recibido.
    El rendimiento se calcula en kg/planta. Para ello divide la producción 
    entre el número de plantas de la parcela donde trabajó.
    """
    dias = {}
    for j in e.jornales:
        if j.fechahoraInicio not in dias:
            dias[j.fechahoraInicio] = [j.produccion, j.parcela.numeroDePlantas]
        else:
            dias[j.fechahoraInicio][0] += j.produccion
            dias[j.fechahoraInicio][1] += j.parcela.numeroDePlantas
    for dia in dias:
        try:
            rend = dias[dia][0] / dias[dia][1]
        except ZeroDivisionError:
            rend = 0
        dias[dia] = (rend, dias[dia][0])
    claves = dias.keys()
    claves.sort()
    rends = []
    for dia in claves:
        tripla = [dia]
        tripla.extend(dias[dia])
        rends.append(tripla)
    return rends

if __name__ == "__main__":
    p = ProduccionPorEmpleado()

