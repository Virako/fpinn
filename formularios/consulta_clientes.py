#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2005-2008  Francisco José Rodríguez Bogado,                   #
#                          (pacoqueen@users.sourceforge.net)                  #
#                                                                             #
# This file is part of fpinn.                                                 #
#                                                                             #
#     FPInn is free software; you can redistribute it and/or modify           #
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
## consulta_clientes.py - Resumen de media de precio por artículo, 
##                        facturación y porcentaje sobre el total  
##                        de clientes.                             
###################################################################
## 
###################################################################

import os
from ventana import Ventana
import utils
import pygtk
pygtk.require('2.0')
import gtk, gtk.glade, time, sqlobject
import sys
try:
    import pclases
except ImportError:
    from os.path import join as pathjoin; sys.path.append(pathjoin("..", "framework"))
    import pclases
import mx, mx.DateTime
sys.path.append('.')
import ventana_progreso
import re
from utils import _float as float

class ConsultaClientes(Ventana):
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
        Ventana.__init__(self, os.path.join("..", "ui", 
            'consulta_clientes.glade'), objeto)
        connections = {'b_salir/clicked': self.salir,
                       'b_buscar/clicked': self.buscar,
                       'b_imprimir/clicked': self.imprimir,
                       'b_fecha_inicio/clicked': self.set_inicio,
                       'b_fecha_fin/clicked': self.set_fin, 
                       'b_exportar/clicked': self.exportar}
        self.add_connections(connections)
        cols = (('Cliente', 'gobject.TYPE_STRING', False, True, True, None),
                ('Producto', 'gobject.TYPE_STRING', False, True, False, None),
                ('Media precio', 'gobject.TYPE_STRING', 
                    False, True, False, None),
                ('Facturación', 'gobject.TYPE_STRING', 
                    False, True, False, None),
                ('% facturación', 'gobject.TYPE_STRING', 
                    False, True, False, None),
                ('kg facturados', 'gobject.TYPE_STRING', 
                    False, True, False, None),
                ('id', 'gobject.TYPE_STRING', False, False, False, None))
        utils.preparar_treeview(self.wids['tv_datos'], cols)
        for i in range(2, 6):
            col = self.wids['tv_datos'].get_column(i)
            for cell in col.get_cell_renderers():
                cell.set_property("xalign", 1)
        col = self.wids['tv_datos'].get_column(1)
        self.wids['tv_datos'].set_expander_column(col)
        temp = mx.DateTime.localtime()
        self.fin = utils.abs_mxfecha(temp)
        self.wids['e_fechafin'].set_text(utils.str_fecha(temp))
        ops = []
        for s in pclases.SerieFacturasVenta.select():
            ops.append((s.id, s.get_info()))
        utils.rellenar_lista(self.wids['cb_serie'], ops)
        gtk.main()

    def exportar(self, boton):
        """
        Exporta el contenido del TreeView a un fichero csv.
        """
        import sys, os
        sys.path.append(os.path.join("..", "informes"))
        from treeview2csv import treeview2csv
        from informes import abrir_csv
        tv = self.wids['tv_datos']
        abrir_csv(treeview2csv(tv))

    def chequear_cambios(self):
        pass

    def rellenar_tabla(self, clientes, total_facturado, total_consumido):
    	"""
        Rellena el model con los items de la consulta.
        Elementos es un diccionario con objetos cuentaClientes y una lista  
        de clientes correspondientes a los meses de consulta.
        """        
    	model = self.wids['tv_datos'].get_model()
    	model.clear()
        self.wids['e_total_importes'].set_text("%s €" 
            % utils.float2str(total_facturado))
        self.wids['e_total_cantidades'].set_text("%s kg" 
            % utils.float2str(total_consumido))
    	for cliente in clientes:
            padre = model.append(None,(cliente.nombre, 
                                       "", 
                                       "", 
                                       utils.float2str(
                                            clientes[cliente]['facturado']), 
                                       utils.float2str(
                                            clientes[cliente]['porcentaje']),
                                       utils.float2str(
                                            clientes[cliente]['consumido']), 
                                       cliente.id))
            for producto in clientes[cliente]['productos']:
                preciomedio = clientes[cliente]['productos'][producto][1]
                kg = clientes[cliente]['productos'][producto][0]
                bultos = clientes[cliente]['productos'][producto][2]
                model.append(padre, ("", 
                                     producto.nombre, 
                                     utils.float2str(preciomedio), 
                                     "", 
                                     "", 
                                     "%s kg (%d bultos)" % (
                                        utils.float2str(kg), bultos), 
                                     producto.id))
        
    def set_inicio(self,boton):
        temp = utils.mostrar_calendario(padre = self.wids['ventana'])
        self.wids['e_fechainicio'].set_text(utils.str_fecha(temp))
        self.inicio = utils.parse_fecha(utils.str_fecha(temp))

    def set_fin(self,boton):
        temp = utils.mostrar_calendario(padre = self.wids['ventana'])
        self.wids['e_fechafin'].set_text(utils.str_fecha(temp))
        self.fin = utils.parse_fecha(utils.str_fecha(temp))

    def buscar(self,boton):
        clientes = pclases.Cliente.select(orderBy = "nombre")
        dic_clientes = {}
        total_facturado = total_consumido = 0.0
        idserie = utils.combo_get_value(self.wids['cb_serie'])
        if not idserie:
            serie = None
        else:
            serie = pclases.SerieFacturasVenta.get(idserie)
        for cliente in clientes:
            facturas_del_cliente = cliente.get_facturas_por_intervalo(
                                    self.inicio, self.fin, serie)
            if not facturas_del_cliente:
                continue
            dic_clientes[cliente] = {}
            facturado = cliente.calcular_total_facturado_por_intervalo(
                            self.inicio, self.fin, serie)
            consumido = cliente.calcular_total_consumido_por_intervalo(
                            self.inicio, self.fin, serie)
            total_facturado += facturado
            total_consumido += consumido
            dic_clientes[cliente]['facturado'] = facturado
            dic_clientes[cliente]['productos'] = {}
            dic_clientes[cliente]['consumido'] = consumido
            for factura in facturas_del_cliente:
                # OJO: Solo facturas (y fras. de terceros). No albaranes.
                for ldv in factura.lineasDeVenta:
                    producto = ldv.productoVenta
                    if producto not in dic_clientes[cliente]['productos']:
                        dic_clientes[cliente]['productos'][producto] = [
                            (ldv.cantidad, ldv.precio, ldv.calcular_bultos())]
                    else:
                        dic_clientes[cliente]['productos'][producto] += [
                            (ldv.cantidad, ldv.precio, ldv.calcular_bultos())]
            for producto in dic_clientes[cliente]['productos']:
                tcantidad = sum([i[0] for i 
                              in dic_clientes[cliente]['productos'][producto]])
                tprecio = sum([i[0] * i[1] for i 
                              in dic_clientes[cliente]['productos'][producto]])
                try:
                    precio_medio = tprecio / tcantidad
                except ZeroDivisionError:
                    precio_medio = 0.0
                tbultos = sum([i[2] for i 
                              in dic_clientes[cliente]['productos'][producto]])
                dic_clientes[cliente]['productos'][producto] = (
                    tcantidad, precio_medio, tbultos)
        for cliente in clientes:
            try:
                porcentaje = dic_clientes[cliente]['facturado']/total_facturado
            except ZeroDivisionError:
                porcentaje = 0.0
            except KeyError:
                continue
            dic_clientes[cliente]['porcentaje'] = porcentaje * 100
        self.rellenar_tabla(dic_clientes, total_facturado, total_consumido)
        

    def imprimir(self,boton):
        """
        Prepara la vista preliminar para la impresión del informe
        """
        import sys, os
        sys.path.append(os.path.join("..", "informes"))
        from treeview2pdf import treeview2pdf
        from informes import abrir_pdf
        if self.inicio == None:
            strfecha = "Hasta el %s" % self.wids['e_fechafin'].get_text()
        else:
            strfecha = "%s - %s" % (self.wids['e_fechainicio'].get_text(), 
                                    self.wids['e_fechafin'].get_text())
        tv = self.wids['tv_datos']
        abrir_pdf(treeview2pdf(tv, 
                               titulo = "Resumen de clientes", 
                               fecha = strfecha))


if __name__ == '__main__':
    t = ConsultaClientes()

