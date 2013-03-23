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
## consulta_precios.py - Resumen de media de precio por artículo, 
##                        facturación y porcentaje sobre el total  
##                        de precios.                             
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
try:
    from pychart import *
except ImportError:
    utils.dialogo_info(titulo = "ERROR DE IMPORTACIÓN", 
                       texto = 'No se encontró el módulo "pychart".')
    sys.exit(1)
from tempfile import gettempdir

class ConsultaPrecios(Ventana):
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
        Ventana.__init__(self, os.path.join("..", "ui", 'consulta_precios.glade'), objeto)
        connections = {'b_salir/clicked': self.salir,
                       'b_buscar/clicked': self.buscar,
                       'b_imprimir/clicked': self.imprimir,
                       'b_fecha_inicio/clicked': self.set_inicio,
                       'b_fecha_fin/clicked': self.set_fin, 
                       'b_exportar/clicked': self.exportar}
        self.add_connections(connections)
        cols = [('Fecha', 'gobject.TYPE_STRING', False, True, True, None)]
        for p in pclases.ProductoVenta.select(orderBy = "nombre"):
            cols.append((p.nombre, "gobject.TYPE_STRING", 
                         False, False, False, None))
        cols += [('id', 'gobject.TYPE_STRING', False, False, False, None)]
        utils.preparar_listview(self.wids['tv_datos'], cols)
        for i in range(1, len(cols)-1):
            col = self.wids['tv_datos'].get_column(i)
            for cell in col.get_cell_renderers():
                cell.set_property("xalign", 1)
        temp = mx.DateTime.localtime()
        self.fin = utils.abs_mxfecha(temp)
        self.wids['e_fechafin'].set_text(utils.str_fecha(temp))
        self.wids['tv_datos'].set_size_request(700, 200)
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

    def rellenar_tabla(self, precios):
    	"""
        Rellena el model con los items de la consulta.
        Elementos es un diccionario con objetos cuentaPrecios y una lista  
        de precios correspondientes a los meses de consulta.
        """ 
    	model = self.wids['tv_datos'].get_model()
    	model.clear()
        total = 0
        fechas = precios.keys()
        fechas.sort()
    	for fecha in fechas:
            fila = [utils.str_fecha(fecha)]
            for producto in pclases.ProductoVenta.select(orderBy = "nombre"):
                fila.append(utils.float2str(precios[fecha][producto]))
            fila.append(0)
            padre = model.append(fila)
        self.dibujar_grafica(precios)

    def dibujar_grafica(self, precios):
        """
        Construye y muestra la gráfica generada en el widget «grafica».
        """
        datos_por_producto = {}
        for fecha in precios:
            for producto in precios[fecha]:
                if producto not in datos_por_producto:
                    datos_por_producto[producto] = {}
                precio = precios[fecha][producto]
                if utils.str_fecha(fecha) not in datos_por_producto[producto]:
                    datos_por_producto[producto][utils.str_fecha(fecha)] = precio
                else:
                    datos_por_producto[producto][utils.str_fecha(fecha)] += precio
                    datos_por_producto[producto][utils.str_fecha(fecha)] /= 2.0
        theme.get_options()
        theme.use_color = True
        theme.reinitialize()
        tempdir = gettempdir()
        formato = "png"   # NECESITA ghostscript
        nomarchivo = "%s.%s" % (mx.DateTime.localtime().strftime(
            "gprecios_%Y_%m_%d_%H_%M_%S"), formato)
        nombregraph = os.path.join(tempdir, "%s") % (nomarchivo)
        can = canvas.init(fname = nombregraph, format = formato)
        # Máximos y mínimos:
        min_global = 0
        max_global = 1
        data = []
        for producto in datos_por_producto:
            datos = datos_por_producto[producto]
            data = [[d.replace("/","//"), datos[d]] for d in datos]
            def cmp_data(d1, d2):
                f1 = utils.parse_fecha(d1[0].replace("//", "/"))
                f2 = utils.parse_fecha(d2[0].replace("//", "/"))
                if f1 < f2:
                    return -1
                else:
                    return 1
                return 0
            data.sort(cmp_data)
            max_y = max([i[1] for i in data])
            max_y *= 1.1    # Un 10% más, para que quede bonita la gráfica.
            min_y = min([i[1] for i in data])
            min_y *= 1.1
            min_global = min(0, min_y, min_global)   # Para evitar que quede 
                                            # un valor positivo como mínimo.
            max_global = max(1, max_y, max_global)

        if data:
            xaxis = axis.X(label="Fecha")
            yaxis = axis.Y(label="Precio medio", tic_interval=int(max_y) / 10)
            ar = area.T(x_coord = category_coord.T(data, 0), 
                        x_range=(-13, 0), 
                        y_range=(int(min_global), int(max_global)), 
                        x_axis = xaxis, 
                        y_axis = yaxis, 
                        size = (500, 250))

        for producto in datos_por_producto:
            datos = datos_por_producto[producto]
            data = [[d.replace("/","//"), datos[d]] for d in datos]
            def cmp_data(d1, d2):
                f1 = utils.parse_fecha(d1[0].replace("//", "/"))
                f2 = utils.parse_fecha(d2[0].replace("//", "/"))
                if f1 < f2:
                    return -1
                else:
                    return 1
                return 0
            data.sort(cmp_data)

            ar.add_plot(line_plot.T(label = producto.nombre.replace("/", "//")[:30], data = data))

        try:
            ar.draw()
        except UnboundLocalError:
            # No hay gráfica. Pasando.
            return

        try:
            can.close()
            self.wids['grafica'].set_size_request(700, 300)
            self.wids['grafica'].set_from_file(nombregraph)
        except:
            utils.dialogo_info(titulo = "NECESITA GHOSTSCRIPT",
                               texto = "Para ver gráficas en pantalla necesita instalar Ghostscript.\nPuede encontrarlo en el servidor de la aplicación o descargarlo de la web (http://www.cs.wisc.edu/~ghost/).",
                               padre = self.wids['ventana'])


    def set_inicio(self,boton):
        temp = utils.mostrar_calendario(padre = self.wids['ventana'])
        self.wids['e_fechainicio'].set_text(utils.str_fecha(temp))
        self.inicio = utils.parse_fecha(utils.str_fecha(temp))

    def set_fin(self,boton):
        temp = utils.mostrar_calendario(padre = self.wids['ventana'])
        self.wids['e_fechafin'].set_text(utils.str_fecha(temp))
        self.fin = utils.parse_fecha(utils.str_fecha(temp))

    def buscar(self,boton):
        if self.inicio:
            albaranes = pclases.AlbaranSalida.select(pclases.AND(
                pclases.AlbaranSalida.q.fecha >= self.inicio, 
                pclases.AlbaranSalida.q.fecha <= self.fin))
        else:
            albaranes = pclases.AlbaranSalida.select(
                pclases.AlbaranSalida.q.fecha <= self.fin)
        dic_precios = {}
        for albaran in albaranes:
            fecha = albaran.fecha
            if fecha not in dic_precios:
                dic_precios[fecha] = {}
            for ldv in albaran.lineasDeVenta:
                producto = ldv.productoVenta
                if producto not in dic_precios[fecha]:
                    dic_precios[fecha][producto] = []
                dic_precios[fecha][producto].append(ldv.precio)
        for fecha in dic_precios:
            for producto in dic_precios[fecha]:
                precios = dic_precios[fecha][producto]
                try:
                    precio_medio = sum(precios) / len(precios)
                except ZeroDivisionError:
                    precio_medio = None
                dic_precios[fecha][producto] = precio_medio
        fechas = dic_precios.keys()
        fechas.sort()
        productos = pclases.ProductoVenta.select()
        for producto in productos:
            defecto = 0.0
            for fecha in fechas:
                try:
                    dic_prods = dic_precios[fecha]
                except KeyError:
                    dic_precios[fecha] = {}
                try:
                    precio_en_fecha = dic_precios[fecha][producto]
                except KeyError:
                    dic_precios[fecha][producto] = defecto
                else:
                    if precio_en_fecha == None:
                        dic_precios[fecha][producto] = defecto
                    else:
                        defecto = dic_precios[fecha][producto]
        self.rellenar_tabla(dic_precios)

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
                               titulo = "Resumen de precios", 
                               fecha = strfecha))


if __name__ == '__main__':
    t = ConsultaPrecios()

