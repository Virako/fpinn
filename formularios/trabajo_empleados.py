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
import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade

from framework import pclases
from formularios.ventana import Ventana
from formularios import utils
from Xlib import display


class TrabajoEmpleados(Ventana):

    def __init__(self, objeto=None, usuario=None):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        self.usuario = usuario
        self.clase = pclases.Trabajo
        Ventana.__init__(self, os.path.join("ui", 'trabajo_empleados.glade'),
               objeto)
        connections = {'b_borrar/clicked': self.borrar_jornada,
                'b_modificar/clicked': self.modificar_jornada,
                'b_anticipo/clicked': self.dar_anticipo,
                'b_save/clicked': self.guardar_jornada,
                'b_quitar_seleccion/clicked': self.quitar_seleccion,
                'b_imprimir/clicked': self.imprimir,
                'mostrar_fecha/clicked': self.mostrar_calendario,
                'rb_vista_diaria/clicked': self.rellenar_tabla_diaria,
                'rb_vista_mensual/clicked': self.rellenar_tabla_mensual,
                'entry_h_campo/changed': self.comprobar_numero_valido,
                'entry_h_manipulacion/changed': self.comprobar_numero_valido,
                'treeview_visual_diaria/cursor-changed': self.sel_empleado,
                'treeview_visual_mensual/cursor-changed': self.sel_empleado,
                'treeview_apuntar/cursor-changed': self.sel_empleado,
                'combo_grupo/changed': self.filtrar_empleados,
                'calendar/day-selected-double-click': self.sel_day_calendar}
                # TODO cerrar el calendario a mano falla
        self.add_connections(connections)
        self.update_fecha()
        utils.preparar_listview(self.wids['treeview_visual_mensual'],
                self.get_cols_mensual())
        utils.preparar_listview(self.wids['treeview_visual_diaria'],
                self.get_cols_diaria())
        utils.preparar_listview(self.wids['treeview_apuntar'],
                self.get_cols_apuntar())
        #col = self.wids['treeview_visual'].get_column(3)
        #for cell in col.get_cell_renderers():
        #    cell.set_property("xalign", 1.0)
        #col = self.wids['treeview_visual'].get_column(4)
        #for cell in col.get_cell_renderers():
        #    cell.set_property("xalign", 1.0)
        self.rellenar_tabla_diaria(self.wids['rb_vista_diaria'])
        self.wids['combo_grupo'].set_active(0)
        self.wids['entry_h_campo'].set_text("0")
        self.wids['entry_h_manipulacion'].set_text("0")
        self.wids['popup_w'].set_transient_for(self.wids['ventana'])
        gtk.main()

    def get_cols_diaria(self):
        return (('Empleado', 'gobject.TYPE_STRING', False, True, True, None),
                ('Alias', 'gobject.TYPE_STRING', False, True, True, None),
                ('J', 'gobject.TYPE_BOOLEAN', False, True, True, None),
                ('C', 'gobject.TYPE_STRING', False, True, True, None),
                ('M', 'gobject.TYPE_STRING', False, True, True, None),
                ('id', 'gobject.TYPE_INT', False, True, True, None))

    def get_cols_mensual(self, days=31):
        cols = []
        cols_names = ('Empleado', 'Alias', 'SS', 'Nomina', 'Sobre', 'Anticipo',
                'Total')
        for col in cols_names:
            cols.append((col, 'gobject.TYPE_STRING', False, True, True, None))
        for d in xrange(1, days + 1):
            cols.append(('J%d' % d, 'gobject.TYPE_BOOLEAN', False, True, True,
                    None))
            cols.append(('C%d' % d, 'gobject.TYPE_STRING', False, True, True,
                    None))
            cols.append(('M%d' % d, 'gobject.TYPE_STRING', False, True, True,
                    None))
        cols.append(('id', 'gobject.TYPE_INT', False, True, True, None))
        return cols

    def get_cols_apuntar(self):
        return (('Sel', 'gobject.TYPE_BOOLEAN', True, True, False,
                    self.change_sel),
                ('Empleado', 'gobject.TYPE_STRING', False, True, True, None),
                ('Alias', 'gobject.TYPE_STRING', False, True, True, None),
                ('id', 'gobject.TYPE_INT', False, True, True, None))

    def change_sel(self, cell, path):
        model = self.wids['treeview_apuntar'].get_model()
        model[path][0] = not cell.get_active()

    def rellenar_empleados(self, cuadrilla=""):
        """ Rellena el treeview con los empleados, filtrando por cuadrilla en
        caso de seleccionarse.  """
        model = self.wids['treeview_apuntar'].get_model()
        model.clear()
        for e in pclases.Empleado.select():
            # correo_electronico utilizado para guardar el alias
            if e.cuadrilla1.count(cuadrilla) or e.cuadrilla2.count(cuadrilla):
                sel = True
            else:
                sel = False
            model.append((sel, e.nombre, e.correoElectronico, e.id))

    def rellenar_tabla(self, mode='diaria'):
        """ Rellena el model con los items de la consulta. """

        if mode == 'diaria':
            model = self.wids['treeview_visual_diaria'].get_model()
            model.clear()
            fecha = "%04d-%02d-%02d" % (self.fecha[0], self.fecha[1],
                    self.fecha[2])
            for t in pclases.Trabajo.select(pclases.Trabajo.q.fecha == fecha):
                model.append((t.empleado.nombre, t.empleado.correoElectronico,
                        t.jornada, t.horasCampo, t.horasManipulacion,
                        t.empleadoID))
            self.colorear(self.wids['treeview_visual_diaria'])
        elif mode == 'mensual':
            model = self.wids['treeview_visual_mensual'].get_model()
            model.clear()

            f_ini = "%04d-%02d-01" % (self.fecha[0], self.fecha[1])
            if self.fecha[1] == 12:
                f_fin = "%04d-01-01" % (self.fecha[0] + 1)
            else:
                f_fin = "%04d-%02d-01" % (self.fecha[0], self.fecha[1] + 1)
            for e in pclases.Empleado.select():
                fila = [e.nombre, e.correoElectronico, '0', '0', '0', '0',
                        '0'] + [False, '-', '-'] * 31 + [e.id]
                for trabajo in e.get_trabajo_mes(f1=f_ini, f2=f_fin):
                    dia = int(trabajo.fecha.__str__()[-2:])
                    pos = 7 + (dia - 1) * 3
                    fila[pos] = trabajo.jornada
                    fila[pos + 1] = trabajo.horasCampo
                    fila[pos + 2] = trabajo.horasManipulacion
                model.append(fila)
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

    def mostrar_calendario(self, button):
        coords = display.Display().screen().root.query_pointer()._data
        self.wids['popup_w'].move(coords['root_x'] - 80, coords['root_y'] + 40)
        if button.get_active():
            self.wids['popup_w'].show()
        else:
            self.wids['popup_w'].hide()

    def sel_day_calendar(self, widget):
        self.wids['popup_w'].hide()
        self.wids['mostrar_fecha'].set_active(False)
        self.update_fecha()
        if self.wids['rb_vista_diaria'].get_active():
            mode = 'diaria'
        else:
            mode = 'mensual'
        self.rellenar_tabla(mode=mode)

    def update_fecha(self):
        self.fecha = self.wids['calendar'].get_date() # (año, mes, dia)
        self.wids['mostrar_fecha'].set_label('Fecha\n%02d-%02d-%04d' %
                (self.fecha[2], self.fecha[1], self.fecha[0]))

    def borrar_jornada(self, widget):
        model = self.wids['treeview_visual_diaria']
        tmodel = model.get_selection().get_selected()
        if isinstance(tmodel[1], gtk.TreeIter):
            id_empleado = int(tmodel[0].get_value(tmodel[1],
                    len(self.wids['treeview_visual_diaria'].get_columns())))
            fecha = "%04d-%02d-%02d" % (self.fecha[0], self.fecha[1],
                    self.fecha[2])
            self.objeto = self.clase.select(pclases.AND(
                    pclases.Trabajo.q.empleadoID == id_empleado,
                    pclases.Trabajo.q.fecha == fecha))[0]
            self.objeto.destroySelf()
            self.objeto = None
            self.rellenar_tabla_diaria(self.wids['rb_vista_diaria'])

    def modificar_jornada(self, widget):
        model = self.wids['treeview_visual_diaria']
        tmodel = model.get_selection().get_selected()
        if isinstance(tmodel[1], gtk.TreeIter):
            id_empleado = int(tmodel[0].get_value(tmodel[1],
                    len(self.wids['treeview_visual_diaria'].get_columns())))
            fecha = "%04d-%02d-%02d" % (self.fecha[0], self.fecha[1],
                    self.fecha[2])
            self.objeto = self.clase.select(pclases.AND(
                    pclases.Trabajo.q.empleadoID == id_empleado,
                    pclases.Trabajo.q.fecha == fecha))[0]
            nueva_c = utils.dialogo_entrada(titulo = "HORAS CAMPO",
                    texto = "Introduzca nuevas horas de campo",
                    padre = self.wids['ventana'])
            nueva_m = utils.dialogo_entrada(titulo = "HORAS MANIPULACION",
                    texto = "Introduzca nuevas horas de manipulacion",
                    padre = self.wids['ventana'])
            if utils.is_float(nueva_c):
                self.objeto.horasCampo = float(nueva_c)
            if utils.is_float(nueva_m):
                self.objeto.horasManipulacion = float(nueva_m)
        self.objeto.notificador.activar(self.aviso_actualizacion)
        self.rellenar_tabla_diaria(self.wids['rb_vista_diaria'])

    def dar_anticipo(self, widget):
        print 'dar_anticipo'

    def comprobar_numero_valido(self, widget):
        h_campo = self.wids['entry_h_campo'].get_text()
        h_mani = self.wids['entry_h_manipulacion'].get_text()
        try:
            float(h_campo.replace(",", "."))
            float(h_mani.replace(",", "."))
            self.wids['b_save'].set_sensitive(True)
        except ValueError:
            self.wids['b_save'].set_sensitive(False)

    def existe_empleado_fecha(self, id_empleado, fecha):
        """ Buscar si un empleado tiene un trabajo hecho en una fecha """
        try:
            self.clase.select(pclases.AND(
                    pclases.Trabajo.q.empleadoID == id_empleado,
                    pclases.Trabajo.q.fecha == fecha))[0]
            return True
        except:
            return False

    def guardar_jornada(self, widget):
        empleados = []
        h_campo = float(self.wids['entry_h_campo'].get_text())
        h_mani = float(self.wids['entry_h_manipulacion'].get_text())
        j_completa = self.wids['rb_j_completa'].get_active()
        fecha = "%04d-%02d-%02d" % (self.fecha[0], self.fecha[1],
                self.fecha[2])
        model = self.wids['treeview_apuntar'].get_model()
        for fila in range(len(model)):
            if not model[fila][0]:
                continue
            empleados.append(pclases.Empleado.get(model[fila][-1]))

        objeto_anterior = self.objeto
        if objeto_anterior:
            objeto_anterior.notificador.desactivar()

        ids = self.clase.select(orderBy='-id')
        try:
            id_t = ids[0].id + 1
        except:
            id_t = 1
        for empleado in empleados:
            if self.existe_empleado_fecha(empleado.id, fecha):
                continue
            self.objeto = self.clase(id=id_t, empleadoID=empleado.id,
                    fecha=fecha, jornada=j_completa, horasCampo=h_campo,
                    horasManipulacion=h_mani)
            id_t += 1
        self.objeto.notificador.activar(self.aviso_actualizacion)
        self.rellenar_tabla_diaria(self.wids['rb_vista_diaria'])

    def filtrar_empleados(self, widget):
        self.rellenar_empleados(widget.get_active_text())

    def sel_empleado(self, widget):
        tmodel = widget.get_selection().get_selected()
        if isinstance(tmodel[1], gtk.TreeIter):
            id_empleado = int(tmodel[0].get_value(tmodel[1],
                    len(widget.get_columns())))
            empleado = pclases.Empleado.get(id_empleado)
            self.wids['photo'].set_image(empleado.get_gtkimage(maximo=90))
            # Cambiar nombre, horas de campo totales, y horas de man totales
            self.wids['nombre_empleado'].set_text(empleado.nombre)
            if self.wids['rb_vista_diaria'].get_active():
                self.wids['horas_campo'].set_text('')
                self.wids['horas_manipulacion'].set_text('')
            elif (self.wids['rb_vista_mensual'].get_active() and
                    len(widget.get_columns()) > 30):
                h_campo = 0
                h_manipulacion = 0
                x = 0
                for x in xrange(0, 31):
                    c = tmodel[0].get_value(tmodel[1], 8 + x * 3)
                    m = tmodel[0].get_value(tmodel[1], 9 + x * 3)
                    if utils.is_float(c):
                        h_campo += float(c)
                    if utils.is_float(m):
                        h_manipulacion += float(m)
                    x += 1
                self.wids['horas_campo'].set_text(
                        "Horas de campo totales: %.2f h" % h_campo)
                self.wids['horas_manipulacion'].set_text(
                        "Horas de manipulacion totales: %.2f h" % h_manipulacion)

    def quitar_seleccion(self, widget):
        self.rellenar_empleados("no filtrar")

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
