#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2005-2008  Francisco José Rodríguez Bogado,                   #
#                          Diego Muñoz Escalante.                             #
# (pacoqueen@users.sourceforge.net, escalant3@users.sourceforge.net)          #
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
from formularios.ventana import Ventana
from formularios import utils
import pygtk
pygtk.require('2.0')
import gtk, gtk.glade, time, sqlobject
import sys
from framework import pclases
import mx, mx.DateTime
sys.path.append('.')
import ventana_progreso
import re
from formularios.utils import _float as float

class FacturarAlbaranes(Ventana):
    inicio = None
    fin = None
    resultado = []
        
    def __init__(self, objeto = None, usuario = None):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        self.usuario = usuario
        global fin
        Ventana.__init__(self, os.path.join("ui", 'facturar_albaranes.glade'), objeto)
        connections = {'b_salir/clicked': self.salir,
                       'b_doit/clicked': self.generar}
        self.add_connections(connections)
        cols = (('Número', 'gobject.TYPE_STRING', False, True, True, None),
                ('Cliente','gobject.TYPE_STRING', False, True, False, None),
                ('Fecha', 'gobject.TYPE_STRING', False, True, False, None), 
                ('Importe', 'gobject.TYPE_STRING', False, True, False, None), 
                ('Estado', 'gobject.TYPE_STRING', False, True, False, None), 
                ('Facturar', 'gobject.TYPE_BOOLEAN', True, True, False, 
                    self.cambiar_generar),
                ('id','gobject.TYPE_STRING', False, False, False, None))
        utils.preparar_listview(self.wids['tv_datos'], cols)
        self.wids['tv_datos'].connect("row-activated", 
                                      abrir_albaran, 
                                      self.usuario, 
                                      self)
        col = self.wids['tv_datos'].get_column(3)
        for cell in col.get_cell_renderers():
            cell.set_property("xalign", 1.0)
        col = self.wids['tv_datos'].get_column(4)
        for cell in col.get_cell_renderers():
            cell.set_property("xalign", 0.5)
        self.rellenar_widgets()
        self.wids['ventana'].resize(800, 600)
        gtk.main()

    def cambiar_generar(self, cell, path):
        model = self.wids['tv_datos'].get_model()
        model[path][5] = not cell.get_active()

    def generar(self, boton):
        """
        Genera una factura por cada cliente de los albaranes seleccionados con 
        las líneas de venta de los mismos pendientes de facturar.
        Finalmente recarga la información de esta ventana con los albaranes 
        que han quedado pendientes.
        """
        idserie = utils.combo_get_value(self.wids['cb_serie'])
        if not idserie or idserie == -1:
            # CWT: NEW! 29/07/2008.
            #utils.dialogo_info(titulo = "SELECCIONE SERIE", 
            #                   texto = "Debe seleccionar una serie numérica de facturas.", 
            #                   padre = self.wids['ventana'])
            usar_serie_cliente = True
        else:
            usar_serie_cliente = False
        albaranes = []
        model = self.wids['tv_datos'].get_model()
        for fila in range(len(model)):
            if model[fila][5] and model[fila][4] != "Incompleto":
                albaran = pclases.AlbaranSalida.get(model[fila][-1])
                albaranes.append(albaran)
        facturas_creadas = []
        for albaran in albaranes:
            try:
                facturas = [f for f in facturas_creadas 
                            if f.cliente == albaran.cliente]
                factura = facturas.pop()
            except IndexError:
                if not usar_serie_cliente:
                    serie = pclases.SerieFacturasVenta.get(idserie)
                else:
                    serie = albaran.cliente.serieFacturasVenta
                    if serie == None:
                        utils.dialogo_info(
                            titulo = "CLIENTE SIN SERIE DE FACTURAS", 
                            texto = "Para usar la serie numérica del cliente"\
                             "\n debe asignarle previamente una en la ventana"\
                             "\n de clientes. En otro caso seleccione una ser"\
                             "ie\n del desplegable inferior.", 
                             padre = self.wids['ventana'])
                        continue
                numfactura = serie.get_next_numfactura(commit = False)
                # Por si salta una excepción y no se pudo crear.
                factura = pclases.FacturaVenta(bloqueada = False, 
                                               cliente = albaran.cliente, 
                                               serieFacturasVenta = serie, 
                                               numfactura = numfactura, 
                                               iva = albaran.cliente.iva)
                numfactura = serie.get_next_numfactura(commit = True)
            # XXX: Comisión, descarga y transporte restan
            #factura.comision += albaran.comision
            factura.comision -= albaran.comision
            # factura.transporte += albaran.transporte
            factura.transporte -= albaran.transporte
            if  albaran.descarga:
                factura.descuentoNumerico = -albaran.descarga
                factura.conceptoDescuentoNumerico = "Descarga"
            for ldv in albaran.lineasDeVenta:
                if ldv.facturaVenta == None:
                    ldv.facturaVenta = factura
                    ldv.sync()
            vtos = factura.crear_vencimientos_por_defecto(forzar = True)
            if vtos:
                factura.bloqueada = True
                # TODO: E imprimir la factura.
            facturas_creadas.append(factura)
        self.rellenar_widgets()
        return  # TODO: No sé si realmente mostrar la factura creada. 
                # Si ya se ha generado el PDF y todo, ¿para qué abrirla?
        import facturas_venta
        #for factura in facturas_creadas:
        #    ventana = facturas_venta.FacturasVenta(factura, self.usuario)
        #No puedo abrir varias ventanas a la vez. Abro la última factura creada.
        try:
            ventana = facturas_venta.FacturasVenta(facturas_creadas[-1], 
                                                   self.usuario)
        except IndexError:
            pass

    def activar_widgets(self, activar):
        pass

    def chequear_cambios(self):
        pass

    def rellenar_widgets(self):
        series = [(s.id, s.get_next_numfactura(commit = False)) 
                  for s in pclases.SerieFacturasVenta.select()]
        series.insert(0, (-1, "Usar el predefinido de cada cliente"))
        utils.rellenar_lista(self.wids['cb_serie'], series)
        self.rellenar_tabla()

    def rellenar_tabla(self):
    	"""
        Rellena el model con los items de la consulta.
        Elementos es un diccionario con objetos cuentaGastos y una lista  
        de gastos correspondientes a los meses de consulta.
        """        
    	model = self.wids['tv_datos'].get_model()
    	model.clear()
        LDV = pclases.LineaDeVenta
        ldvs_no_facturadas = LDV.select(pclases.AND(
            LDV.q.albaranSalidaID != None, 
            LDV.q.facturaVentaID == None))
        albaranes = []
        for ldv in ldvs_no_facturadas:
            albaran = ldv.albaranSalida
            if albaran not in albaranes:
                albaranes.append(albaran)
    	for albaran in albaranes:
            model.append((albaran.numalbaran, 
                          albaran.cliente.nombre, 
                          utils.str_fecha(albaran.fecha), 
                          utils.float2str(albaran.calcular_importe(iva = True)),
                          albaran.get_str_estado(), 
                          False, 
                          albaran.id))

def abrir_albaran(tv, path, col, usuario = None, ventana_invocadora = None):
    """
    Abre el albarán seleccionado.
    """
    model = tv.get_model()
    id = model[path][-1]
    albaran = pclases.AlbaranSalida.get(id)
    from albaranes_de_salida import AlbaranesDeSalida
    v = AlbaranesDeSalida(albaran, usuario)
    if ventana_invocadora:
        try:
            ventana_invocadora.rellenar_widgets()
        except AttributeError:  # La ventana ya ha sido cerrada.
            pass


if __name__ == '__main__':
    t = FacturarAlbaranes()

