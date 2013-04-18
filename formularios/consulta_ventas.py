#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2005-2008  Francisco José Rodríguez Bogado,                   #
#                          (pacoqueen@users.sourceforge.net)                  #
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
## consulta_ventas.py - Ventas por producto entre fechas.
###################################################################
## DONE: Faltaría repartir el resto de gatos entre los productos, pero ¿cómo? 
## ¿Por kilos? ¿Por porcentaje del importe total? ¿Sólo los de manipulación? 
## ¿Todos los gastos? ¿Descuento también el transporte y demás servicios del 
## albarán?  Al final por kilos.
## DONE: Se hace a partir de albaranes como me comentó María del Mar. El 
## problema es que los albaranes con precio cero también entran. ¿Qué hago? 
## ¿Tengo en cuenta solo precios no nulos, o lo hago en base a facturas? Al 
## final a partir de facturas. 
###################################################################

import os
from formularios.ventana import Ventana
from formularios import utils
import pygtk
pygtk.require('2.0')
import gtk, gtk.glade, time, sqlobject
import sys
try:
    from framework import pclases
except ImportError:
    from os.path import join as pathjoin
    sys.path.append(pathjoin("framework"))
    from framework import pclases
import mx, mx.DateTime
sys.path.append('.')
import ventana_progreso
import re
from formularios.utils import _float as float

class ConsultaVentas(Ventana):
    inicio = None
    fin = None
    resultado = []
        
    def __init__(self, objeto = None, usuario = None):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        global fin
        Ventana.__init__(self, 
                         os.path.join("ui", 'consulta_gastos.glade'), 
                         objeto)
        connections = {'b_salir/clicked': self.salir,
                       'b_buscar/clicked': self.buscar,
                       'b_imprimir/clicked': self.imprimir,
                       'b_fecha_inicio/clicked': self.set_inicio,
                       'b_fecha_fin/clicked': self.set_fin, 
                       'b_exportar/clicked': self.exportar}
        self.add_connections(connections)
        cols = (('Código','gobject.TYPE_STRING',False,True, True, None),
                ('Producto','gobject.TYPE_STRING',False,False,False,None),
                ('Kgs', 'gobject.TYPE_STRING',False,True, False,None),
                ('Importe','gobject.TYPE_STRING',False,True,False,None),
                ('Importe s/IVA','gobject.TYPE_STRING',False,True,False,None),
                ('Importe menos gastos', 'gobject.TYPE_STRING', False, True,
                    False, None),
                ('Gastos generales', 'gobject.TYPE_STRING', False, True, 
                    False, None), 
                ('id','gobject.TYPE_STRING',False,False,False,None))
        utils.preparar_listview(self.wids['tv_datos'], cols)
        for ncol in range(2, 6):
            col = self.wids['tv_datos'].get_column(ncol)
            for cell in col.get_cell_renderers():
                cell.set_property("xalign", 1)
        temp = time.localtime()
        self.fin = str(temp[0])+'/'+str(temp[1])+'/'+str(temp[2])
        self.wids['e_fechafin'].set_text(utils.str_fecha(temp))
        self.wids['ventana'].set_title("Consulta de ventas por producto")
        gtk.main()

    def exportar(self, boton):
        """
        Exporta el contenido del TreeView a un fichero csv.
        """
        import os
        sys.path.append(os.path.join("informes"))
        from treeview2csv import treeview2csv
        from informes import abrir_csv
        tv = self.wids['tv_datos']
        abrir_csv(treeview2csv(tv))

    def chequear_cambios(self):
        pass

    def corregir_nombres_fecha(self, s):
        """
        Porque todo hombre debe enfrentarse al menos una 
        vez en su vida a dos tipos de sistemas operativos: 
        los que se no se pasan por el forro las locales, 
        y MS-Windows.
        """
        trans = {'Monday': 'lunes',
                 'Tuesday': 'martes',
                 'Wednesday': 'miércoles',
                 'Thursday': 'jueves',
                 'Friday': 'viernes',
                 'Saturday': 'sábado',
                 'Sunday': 'domingo',
                 'January': 'enero',
                 'February': 'febrero',
                 'March': 'marzo',
                 'April': 'abril',
                 'May': 'mayo',
                 'June': 'junio',
                 'July': 'julio',
                 'August': 'agosto',
                 'September': 'septiembre',
                 'October': 'octubre',
                 'November': 'noviembre',
                 'December': 'diciembre'}
        for in_english in trans:
            s = s.replace(in_english, trans[in_english])
        return s

    def rellenar_tabla(self, productos):
    	"""
        Rellena el model con los items de la consulta.
        """        
    	model = self.wids['tv_datos'].get_model()
    	model.clear()
        total = 0
    	for producto in productos:
            model.append((
                producto.codigo, 
                producto.nombre, 
                utils.float2str(productos[producto]["kgs"]), 
                utils.float2str(productos[producto]["importe"]), 
                utils.float2str(productos[producto]["importe sin iva"]), 
                utils.float2str(productos[producto]["importe menos gastos"]), 
                utils.float2str(productos[producto]["gastos generales"]), 
                producto.id
                ))
            total += productos[producto]["kgs"]
        self.wids['e_total'].set_text("%s kgs" % utils.float2str(total))
        
    def set_inicio(self,boton):
        temp = utils.mostrar_calendario(padre = self.wids['ventana'])
        self.wids['e_fechainicio'].set_text(utils.str_fecha(temp))
        self.inicio = str(temp[2])+'/'+str(temp[1])+'/'+str(temp[0])


    def set_fin(self,boton):
        temp = utils.mostrar_calendario(padre = self.wids['ventana'])
        self.wids['e_fechafin'].set_text(utils.str_fecha(temp))
        self.fin = str(temp[2])+'/'+str(temp[1])+'/'+str(temp[0])

    def buscar(self,boton):
        if self.inicio == None:
            facturas = pclases.FacturaVenta.select(
                            pclases.FacturaVenta.q.fecha <= self.fin)
        else:
            facturas = pclases.FacturaVenta.select(pclases.AND(
                                pclases.FacturaVenta.q.fecha >= self.inicio,
                                pclases.FacturaVenta.q.fecha <= self.fin))
        # Total de gastos generales entre fechas a partir de facturas de compra
        if self.inicio == None:
            frascompra = pclases.FacturaCompra.select(
                            pclases.FacturaCompra.q.fecha <= self.fin)
        else:
            frascompra = pclases.FacturaCompra.select(pclases.AND(
                                pclases.FacturaCompra.q.fecha >= self.inicio,
                                pclases.FacturaCompra.q.fecha <= self.fin))
        gastos = 0.0
        for f in frascompra:
            for g in f.gastos:
                txtcuenta = g.cuentaGastos.descripcion.lower()
                if "generales" in txtcuenta:
                    gastos += g.importe
        # Construyo diccionaro de productos.
        productos = {}
        for a in facturas:
            for ldv in a.lineasDeVenta:
                p = ldv.productoVenta
                if p not in productos:
                    productos[p] = {"kgs": 0.0, 
                                    "importe": 0.0, 
                                    "importe sin iva": 0.0, 
                                    "importe menos gastos": 0.0,
                                    "gastos generales": 0.0}
                productos[p]["kgs"] += ldv.cantidad
                productos[p]["importe"] += ldv.calcular_importe(True)
                productos[p]["importe sin iva"] += ldv.calcular_importe(False)
                tarifa = pclases.Tarifa.buscar_tarifa(p, ldv.precio)
                imenosg = ldv.precio    # Precio unitario sin IVA.
                if tarifa:
                    try:
                        precioid = tarifa.get_precioID(p)
                        precio = pclases.Precio.get(precioid)
                        # imenosg = precio.importeAdicional
                        # Es en base al precio de venta real sin IVA, no al de 
                        # la tarifa.
                        imenosg -= (sum([c.importe for c in precio.conceptos]) 
                            * ldv.cantidad)
                    except ValueError:
                        # No se encuentra el precio. No tengo información 
                        # acerca del precio limpio sin gastos.
                        pass
                productos[p]["importe menos gastos"] += imenosg
        # Gastos generales por kilo de producto.
        kgtotal = sum([productos[p]['kgs'] for p in productos])
        try:
            ggporkg = gastos / kgtotal
        except ZeroDivisionError:
            try:
                ggporkg = gastos / len(productos)
            except ZeroDivisionError:
                ggporkg = 0.0
        for p in productos:
            productos[p]['gastos generales'] = productos[p]['kgs'] * ggporkg
        self.rellenar_tabla(productos)
        

    def imprimir(self,boton):
        """
        Prepara la vista preliminar para la impresión del informe
        """
        import os
        sys.path.append(os.path.join("informes"))
        from treeview2pdf import treeview2pdf
        from informes import abrir_pdf
        if self.inicio == None:
            strfecha = "Hasta el %s" % self.wids['e_fechafin'].get_text()
        else:
            strfecha = "%s - %s" % (self.wids['e_fechainicio'].get_text(), 
                                    self.wids['e_fechafin'].get_text())
        tv = self.wids['tv_datos']
        abrir_pdf(treeview2pdf(tv, 
                               titulo = "Ventas por producto entre fechas", 
                               fecha = strfecha))


if __name__ == '__main__':
    t = ConsultaVentas()

