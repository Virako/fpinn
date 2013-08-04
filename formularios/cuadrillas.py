#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
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
## facturar_albaranes.py - Genera facturas "en batería".
###################################################################
##
###################################################################

import os
import gtk
import gtk.glade

from formularios import utils
from formularios.ventana import Ventana
from framework import pclases


class Cuadrillas(Ventana):

    def __init__(self, objeto=None, usuario=None):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        self.usuario = usuario
        Ventana.__init__(self, os.path.join("ui",
                'cuadrillas.glade'), objeto)
        connections = {'b_add/clicked': self.add_cuadrilla,
                       'b_remove/clicked': self.remove_cuadrilla,
                       'b_alta/clicked': self.alta_empleado,
                       'b_baja/clicked': self.baja_empleado,
                       'treeview_empleados/cursor-changed': self.sel_empleado}
        self.add_connections(connections)
        cols_empleados = (
                ('Empleado', 'gobject.TYPE_STRING', False, True, True, None),
                ('Alias', 'gobject.TYPE_STRING', False, True, True, None),
                ('Estado', 'gobject.TYPE_STRING', False, True, True, None),
                ('id', 'gobject.TYPE_INT', False, True, True, None))
        cols_cuadrillas = (
                ('Sel', 'gobject.TYPE_BOOLEAN', True, True, False,
                        self.sel_cuadrilla),
                ('Cuadrilla', 'gobject.TYPE_STRING', False, True, True, None),
                ('Encargado', 'gobject.TYPE_BOOLEAN', True, True, False,
                        self.sel_encargado),
                ('id', 'gobject.TYPE_INT', False, True, True, None))
        utils.preparar_listview(self.wids['treeview_empleados'],
                cols_empleados)
        utils.preparar_listview(self.wids['treeview_cuadrillas'],
                cols_cuadrillas)
        #self.wids['tv_datos'].connect("row-activated", self.abrir_factura,
        #        self.usuario, self)
        #col = self.wids['tv_datos'].get_column(3)
        #for cell in col.get_cell_renderers():
        #    cell.set_property("xalign", 1.0)
        #col = self.wids['tv_datos'].get_column(4)
        #for cell in col.get_cell_renderers():
        #    cell.set_property("xalign", 0.5)
        self.rellenar_empleados()
        self.wids['ventana'].resize(800, 600)
        gtk.main()

    def rellenar_empleados(self):
        model = self.wids['treeview_empleados'].get_model()
        model.clear()
        for e in pclases.Empleado.select():
            # correo_electronico utilizado para guardar el alias
            model.append((e.nombre, e.correoElectronico, e.observaciones,
                    e.id))
        self.colorear(self.wids['treeview_empleados'])

    def rellenar_cuadrillas(self, empleado):
        model = self.wids['treeview_cuadrillas'].get_model()
        model.clear()
        for c in pclases.Cuadrilla.select():
            objeto = self.is_cuadrilla_empleado(c.id, empleado)
            if objeto:
                pertenece = True
                encargado = objeto.encargado
            else:
                pertenece = False
                encargado = False
            model.append((pertenece, c.nombre, encargado, c.id))
        self.empleado = empleado

    def sel_cuadrilla(self, cell, path):
        model = self.wids['treeview_cuadrillas'].get_model()
        model[path][0] = not cell.get_active()
        id_cuadrilla = int(model[path][-1])
        id_empleado = self.empleado
        if model[path][0]:
            objeto = self.is_cuadrilla_empleado(id_cuadrilla, id_empleado)
            if not objeto:
                pclases.CuadrillaEmpleado(cuadrillaID=id_cuadrilla,
                        empleadoID=id_empleado, encargado=model[path][2])
        else:
            objeto = self.is_cuadrilla_empleado(id_cuadrilla, id_empleado)
            if objeto:
                objeto.destroySelf()

    def sel_encargado(self, cell, path):
        model = self.wids['treeview_cuadrillas'].get_model()
        model[path][2] = not cell.get_active()
        if not model[path][0]:
            return
        id_cuadrilla = int(model[path][-1])
        id_empleado = self.empleado
        objeto = self.is_cuadrilla_empleado(id_cuadrilla, id_empleado)
        if objeto:
            objeto.encargado = model[path][2]

    def sel_empleado(self, widget):
        tmodel = widget.get_selection().get_selected()
        if isinstance(tmodel[1], gtk.TreeIter):
            id_empleado = int(tmodel[0].get_value(tmodel[1],
                    len(widget.get_columns())))
            empleado = pclases.Empleado.get(id_empleado)
            self.wids['photo'].set_image(empleado.get_gtkimage(maximo=90))
        self.rellenar_cuadrillas(id_empleado)

    def is_cuadrilla_empleado(self, id_c, id_e):
        objeto = pclases.CuadrillaEmpleado.select(pclases.AND(
                pclases.CuadrillaEmpleado.q.cuadrillaID == id_c,
                pclases.CuadrillaEmpleado.q.empleadoID == id_e))
        try:
            return objeto[0]
        except:
            return 0

    def add_cuadrilla(self, widget):
        nombre = utils.dialogo_entrada(
                titulo="Nueva cuadrilla",
                texto="Introduzca el nombre de la cuadrilla: ",
                padre=self.wids['ventana'])
        # comprobar que no exista
        if nombre is not None:
            pclases.Cuadrilla(nombre=nombre)
        self.rellenar_empleados()

    def remove_cuadrilla(self, widget):
        model = self.wids['treeview_cuadrillas'].get_selection().get_selected()
        if isinstance(model[1], gtk.TreeIter):
            id_cuadrilla = int(model[0].get_value(model[1],
                    len(self.wids['treeview_cuadrillas'].get_columns())))
        objeto = pclases.Cuadrilla.get(id_cuadrilla)
        objeto.destroySelf()
        self.rellenar_empleados()

    def alta_empleado(self, widget):
        tmodel = self.wids['treeview_empleados'].get_selection().get_selected()
        if isinstance(tmodel[1], gtk.TreeIter):
            id_empleado = int(tmodel[0].get_value(tmodel[1],
                    len(self.wids['treeview_empleados'].get_columns())))
            empleado = pclases.Empleado.get(id_empleado)
            empleado.observaciones = ''
        self.rellenar_empleados()

    def baja_empleado(self, widget):
        tmodel = self.wids['treeview_empleados'].get_selection().get_selected()
        if isinstance(tmodel[1], gtk.TreeIter):
            id_empleado = int(tmodel[0].get_value(tmodel[1],
                    len(self.wids['treeview_empleados'].get_columns())))
            empleado = pclases.Empleado.get(id_empleado)
            empleado.observaciones = 'de baja'
        self.rellenar_empleados()

    def colorear(self, tv):

        def cell_func(column, cell, model, itr):
            color = None
            if model[itr][2]: # si está de baja
                color = "gray"
                cell.set_property("cell-background", color)
                return
            emp = pclases.Empleado.get(int(model[itr][-1]))
            if emp.cuadrillas: # dentro de alguna cuadrilla
                for c in emp.cuadrillas:
                    if c.encargado:
                        color = "light blue"
                        cell.set_property("cell-background", color)
                        return
                color = "light green"
            else:
                color = 'orange'
            cell.set_property("cell-background", color)
        cols = tv.get_columns()
        for i in xrange(len(cols)):
            column = cols[i]
            cells = column.get_cell_renderers()
            for cell in cells:
                column.set_cell_data_func(cell, cell_func)

if __name__ == '__main__':
    t = Cuadrillas()
