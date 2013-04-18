#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2013  Victor Ramirez de la Corte (virako.9@gmail.com)         #
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


###############################################################################
## trabajo_empleados.py - Agenda para el trabajo diario de cada empleado
###############################################################################

import os
from ventana import Ventana
import utils
import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade


class TrabajoEmpleados(Ventana):

    def __init__(self, objeto=None, usuario=None):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        self.usuario = usuario
        Ventana.__init__(self, os.path.join("..", "ui",
                'trabajo_empleados.glade'), objeto)
        connections = {'b_borrar/clicked': self.borrar_jornada,
                       'b_modificar/clicked': self.modificar_jornada,
                       'b_anticipo/clicked': self.dar_anticipo,
                       'b_save/clicked': self.guardar_jornada,
                       'b_quitar_seleccion/clicked': self.quitar_seleccion,
                       'b_imprimir/clicked': self.imprimir,
                       'rb_vista_diaria/clicked': self.rellenar_tabla_diaria,
                       'rb_vista_mensual/clicked': self.rellenar_tabla_mensual,
                       }
        self.add_connections(connections)
        utils.preparar_listview(self.wids['treeview_visual_mensual'],
                self.get_cols_mensual())
        utils.preparar_listview(self.wids['treeview_visual_diaria'],
                self.get_cols_diaria())
        #col = self.wids['treeview_visual'].get_column(3)
        #for cell in col.get_cell_renderers():
        #    cell.set_property("xalign", 1.0)
        #col = self.wids['treeview_visual'].get_column(4)
        #for cell in col.get_cell_renderers():
        #    cell.set_property("xalign", 1.0)
        self.rellenar_tabla_diaria(self.wids['rb_vista_diaria'])
        gtk.main()

    def get_cols_diaria(self):
        return (('Empleado', 'gobject.TYPE_STRING', False, True, True, None),
                ('Alias', 'gobject.TYPE_STRING', False, True, True, None),
                ('J', 'gobject.TYPE_BOOLEAN', False, True, True, None),
                ('C', 'gobject.TYPE_STRING', False, True, True, None),
                ('M', 'gobject.TYPE_STRING', False, True, True, None),
                ('id', 'gobject.TYPE_INT', False, True, True, None))

    def get_cols_mensual(self):
        return (('Empleado', 'gobject.TYPE_STRING', False, True, True, None),
                ('Alias', 'gobject.TYPE_STRING', False, True, True, None),
                ('1', 'gobject.TYPE_BOOLEAN', False, True, True, None),
                ('2', 'gobject.TYPE_BOOLEAN', False, True, True, None),
                ('3', 'gobject.TYPE_BOOLEAN', False, True, True, None),
                ('id', 'gobject.TYPE_INT', False, True, True, None))

    def rellenar_tabla(self, mode='diaria'):
        " Rellena el model con los items de la consulta. """

        if mode == 'diaria':
            model = self.wids['treeview_visual_diaria'].get_model()
            model.clear()
            jornadas = []
            jornadas.append(["Pepe", "carvo", True, str(5.0), str(3.0)])
            jornadas.append(["Pepe", "carvo", True, str(5.0), str(3.0)])
            jornadas.append(["Pedro", "tss", False, str(4.0), str(3.30)])
            jornadas.append(["Vic", "Virako", True, str(2.15), str(4.45)])
            jornadas.append(["Pepe", "carvo", True, str(5.0), str(3.0)])
            jornadas.append(["Pedro", "tss", False, str(4.0), str(3.30)])
            jornadas.append(["Vic", "Virako", True, str(2.15), str(4.45)])
            jornadas.append(["Pepe", "carvo", True, str(5.0), str(3.0)])
            jornadas.append(["Pedro", "tss", False, str(4.0), str(3.30)])
            jornadas.append(["Vic", "Virako", True, str(2.15), str(4.45)])
            jornadas.append(["Pepe", "carvo", True, str(5.0), str(3.0)])
            jornadas.append(["Pedro", "tss", False, str(4.0), str(3.30)])
            jornadas.append(["Vic", "Virako", True, str(2.15), str(4.45)])
            jornadas.append(["Pepe", "carvo", True, str(5.0), str(3.0)])
            jornadas.append(["Pedro", "tss", False, str(4.0), str(3.30)])
            jornadas.append(["Vic", "Virako", True, str(2.15), str(4.45)])
            jornadas.append(["Pepe", "carvo", True, str(5.0), str(3.0)])
            jornadas.append(["Pedro", "tss", False, str(4.0), str(3.30)])
            jornadas.append(["Vic", "Virako", True, str(2.15), str(4.45)])
            jornadas.append(["Pepe", "carvo", True, str(5.0), str(3.0)])
            jornadas.append(["Pedro", "tss", False, str(4.0), str(3.30)])

            for jornada in jornadas:
                model.append((jornada[0], jornada[1], jornada[2], jornada[3],
                        jornada[4], 0))
            self.colorear(self.wids['treeview_visual_diaria'])
        elif mode == 'mensual':
            model = self.wids['treeview_visual_mensual'].get_model()
            model.clear()
            jornadas = []
            jornadas.append(["Pepe", "carvo", True, True, False])
            jornadas.append(["Pedro", "tss", False, True, False])
            jornadas.append(["Vic", "Virako", True, True, False])
            for jornada in jornadas:
                model.append((jornada[0], jornada[1], jornada[2], jornada[3],
                        jornada[4], 0))
            self.colorear(self.wids['treeview_visual_mensual'])
        else:
            print 'Error inesperado'
            exit()

    def colorear(self, cols):

        def cell_func(column, cell, model, itr):
            estado = model[itr][2]
            if estado:
                color = "green"
            else:
                color = "orange"
            cell.set_property("cell-background", color)

        for i in xrange(len(cols)):
            column = cols[i]
            cells = column.get_cell_renderers()
            for cell in cells:
                column.set_cell_data_func(cell, cell_func)

    def borrar_jornada(self, widget):
        print 'borrar_jornada'

    def modificar_jornada(self, widget):
        print 'modificar_jornada'

    def dar_anticipo(self, widget):
        print 'dar_anticipo'

    def guardar_jornada(self, widget):
        print 'guardar_jornada'

    def quitar_seleccion(self, widget):
        print 'quitar_seleccion'

    def imprimir(self, widget):
        print 'imprimir'

    def rellenar_tabla_mensual(self, widget):
        if widget.get_active():
            self.wids['treeview_visual_diaria'].hide()
            self.wids['scroll_visual_d'].hide()
            self.wids['scroll_visual_m'].show()
            self.wids['treeview_visual_mensual'].show()
            self.rellenar_tabla(mode='mensual')

    def rellenar_tabla_diaria(self, widget):
        if widget.get_active():
            self.wids['treeview_visual_mensual'].hide()
            self.wids['scroll_visual_m'].hide()
            self.wids['scroll_visual_d'].show()
            self.wids['treeview_visual_diaria'].show()
            self.rellenar_tabla(mode='diaria')

if __name__ == "__main__":
    p = TrabajoEmpleados()
