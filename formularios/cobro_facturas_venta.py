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
from ventana import Ventana
import utils
import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade
import mx
import mx.DateTime
import sys
from os.path import join as pathjoin
sys.path.append(pathjoin("..", "framework"))
import pclases
sys.path.append("../utilidades")
from scan import scan
from enviar_correo import enviar_correo


class CobroFacturasVenta(Ventana):

    def __init__(self, objeto=None, usuario=None):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        self.usuario = usuario
        Ventana.__init__(self, os.path.join("..", "ui",
                'cobro_facturas_venta.glade'), objeto)
        connections = {'b_salir/clicked': self.salir,
                       'b_add_cobro/clicked': self.add_cobro,
                       'b_remove_cobro/clicked': self.remove_cobro}
        self.add_connections(connections)
        cols = (('ID', 'gobject.TYPE_INT', False, True, True, None),
                ('Número', 'gobject.TYPE_STRING', False, True, True, None),
                ('Cliente', 'gobject.TYPE_STRING', False, True, False, None),
                ('Fecha', 'gobject.TYPE_STRING', False, True, False, None),
                ('Importe', 'gobject.TYPE_STRING', False, True, False, None),
                ('Estado', 'gobject.TYPE_STRING', False, True, False, None),
                ('Fecha vto', 'gobject.TYPE_STRING', False, True, False, None),
                ('Pagado en', 'gobject.TYPE_STRING', False, True, False, None),
                ('id', 'gobject.TYPE_STRING', False, False, False, None))
        utils.preparar_listview(self.wids['tv_datos'], cols)
        #self.wids['tv_datos'].connect("row-activated", self.abrir_factura,
        #        self.usuario, self)
        col = self.wids['tv_datos'].get_column(3)
        for cell in col.get_cell_renderers():
            cell.set_property("xalign", 1.0)
        col = self.wids['tv_datos'].get_column(4)
        for cell in col.get_cell_renderers():
            cell.set_property("xalign", 0.5)
        self.rellenar_widgets()
        self.wids['ventana'].resize(800, 600)
        gtk.main()

    def rellenar_widgets(self):
        series = [(s.id, s.get_next_numfactura(commit=False))
                  for s in pclases.SerieFacturasVenta.select()]
        series.insert(0, (-1, "Usar el predefinido de cada cliente"))
        self.rellenar_tabla()

    def rellenar_tabla(self, filtro=None):
        " Rellena el model con los items de la consulta. """
        facturas = pclases.FacturaVenta.select(orderBy='fecha')

        model = self.wids['tv_datos'].get_model()
        model.clear()
        for factura in facturas:
            if filtro == factura.estado():
                continue
            if factura.estado() == "No enviado":
                pdf = "factura_" + factura.numfactura.__str__()
                pdf.replace("/", "_")
                if (factura.cliente.email and enviar_correo("Factura",
                        factura.cliente.email, "Texto de prueba", [pdf])):
                    factura.observaciones = "Correo enviado"
            importe = factura.calcular_importe_total(iva=True)
            model.append((factura.id,
                    factura.numfactura,
                    factura.cliente.nombre,
                    utils.str_fecha(factura.fecha),
                    #utils.float2str(importe),
                    str(importe),
                    factura.estado(),#TODO "Pagado o no pagado
                    utils.str_fecha(factura.fecha_vencimiento()),
                    utils.str_fecha(factura.fecha_pago()),
                    factura.id))
        self.colorear(self.wids['tv_datos'])

    def colorear(self, tv):

        def cell_func(column, cell, model, itr):
            estado = model[itr][5]
            if estado == "Vencido":
                color = "orange"
            elif estado == "Enviado":
                color = "light green"
            elif estado == "No enviado":
                color = "light blue"
            elif estado == "Cobrado":
                color = "green"
            elif estado == "ERROR":
                color = "red"
            else:
                color = None
            cell.set_property("cell-background", color)

        cols = tv.get_columns()
        for i in xrange(len(cols)):
            column = cols[i]
            cells = column.get_cell_renderers()
            for cell in cells:
                column.set_cell_data_func(cell, cell_func)

    def add_cobro(self, boton):
        """ Add cobro a factura seleccionada"""
        model, path = self.wids['tv_datos'].get_selection().get_selected()
        # TODO Ver diferencia entre importe total (IVA) e importe or cobrar
        if path:
            idfactura = model[path][0]
            importe = self.add_documento(model[path][1])
            importe = float(model[path][4])
            scan(factura=model[path][1])
            # Abrir ventana para adjuntar archivo y poner un importe
            pclases.Cobro(facturaVenta=idfactura, importe=importe,
                    fecha=mx.DateTime.localtime(), observaciones="")
            self.rellenar_tabla()

    def remove_cobro(self, boton):
        """ Borrar un cobro de la factura seleccionada"""
        model, path = self.wids['tv_datos'].get_selection().get_selected()
        if path:
            idfactura = model[path][0]
            factura = pclases.FacturaVenta.get(idfactura)
            cobros = factura.cobros[:]
            if len(cobros) > 1:
                #print "Borrado ultimo cobro"
                cobros[-1].destroySelf()
            elif len(cobros) <= 0:
                print "No existe ningún cobro"
            else:
                #print "Borrado cobro"
                cobros[0].destroySelf()
        self.rellenar_tabla()

    #def abrir_factura(self, tv, path, col, usuario=None, ventanita=None):
    #    """ Abre la factura seleccionada para ver los cobros por ejemplos. """
    #    print "path", path
    #    model = tv.get_model()
    #    importe = float(model[path][4])
    #    ide = model[path][0]
    #    # Abrir ventana para adjuntar archivo y poner un importe
    #    pclases.Cobro(facturaVenta=ide, importe=importe,
    #            fecha=mx.DateTime.localtime(), observaciones="")
    #    self.rellenar_tabla()

    def add_documento(self, num_factura):
        """ Muestra una ventana donde añadir un documento de pago"""
        importe = utils.dialogo_entrada(titulo="Importe para la factura %s" %
               (num_factura),
               texto="Ponga el fichero de pago en el scanner y acepte. ",
               padre=self.wids['ventana'])
        if not importe:
            return 0.0
        return float(importe)

if __name__ == '__main__':
    t = CobroFacturasVenta()
