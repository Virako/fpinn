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
## consulta_parcelas.py - Resumen de producción, gastos e ingresos 
##                        de parcelas por intervalo de fechas.
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

class ConsultaParcelas(Ventana):
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
        Ventana.__init__(self, os.path.join("ui", 'consulta_parcelas.glade'), objeto)
        connections = {'b_salir/clicked': self.salir,
                       'b_buscar/clicked': self.buscar,
                       'b_imprimir/clicked': self.imprimir,
                       'b_fecha_inicio/clicked': self.set_inicio,
                       'b_fecha_fin/clicked': self.set_fin, 
                       'b_exportar/clicked': self.exportar}
        self.add_connections(connections)
        cols = (('Parcela', 'gobject.TYPE_STRING', False, True, True, None),
                ('Kg/planta', 'gobject.TYPE_STRING', False, True, False, None),
                ('Kg totales', 'gobject.TYPE_STRING', False, True, False, None),
                ('Gastos apertura', 'gobject.TYPE_STRING', 
                    False, True, False, None),
                ('Gastos cierre', 'gobject.TYPE_STRING', 
                    False, True, False, None),
                ('Gastos generales', 'gobject.TYPE_STRING', 
                    False, True, False, None),
                ('Ingresos', 'gobject.TYPE_STRING', 
                    False, True, False, None),
                ('id', 'gobject.TYPE_STRING', False, False, False, None))
        utils.preparar_listview(self.wids['tv_datos'], cols)
        for i in range(1, 7):
            col = self.wids['tv_datos'].get_column(i)
            for cell in col.get_cell_renderers():
                cell.set_property("xalign", 1)
        temp = mx.DateTime.localtime()
        self.fin = utils.abs_mxfecha(temp)
        self.wids['e_fechafin'].set_text(utils.str_fecha(temp))
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

    def rellenar_tabla(self, parcelas):
    	"""
        Rellena el model con los items de la consulta.
        Elementos es un diccionario con objetos cuentaParcelas y una lista  
        de parcelas correspondientes a los meses de consulta.
        """        
    	model = self.wids['tv_datos'].get_model()
    	model.clear()
        total = 0
    	for parcela in parcelas:
            padre = model.append((parcela.parcela, 
                            utils.float2str(parcelas[parcela]['prodplanta']), 
                            utils.float2str(parcelas[parcela]['prodtotal']), 
                            utils.float2str(parcelas[parcela]['gapertura']), 
                            utils.float2str(parcelas[parcela]['gcierre']), 
                            utils.float2str(parcelas[parcela]['ggenerales']),
                            utils.float2str(parcelas[parcela]['ingresos']), 
                            parcela.id))
        
    def set_inicio(self,boton):
        temp = utils.mostrar_calendario(padre = self.wids['ventana'])
        self.wids['e_fechainicio'].set_text(utils.str_fecha(temp))
        self.inicio = utils.parse_fecha(utils.str_fecha(temp))

    def set_fin(self,boton):
        temp = utils.mostrar_calendario(padre = self.wids['ventana'])
        self.wids['e_fechafin'].set_text(utils.str_fecha(temp))
        self.fin = utils.parse_fecha(utils.str_fecha(temp))

    def buscar(self,boton):
        dic_parcelas = _buscar(self.inicio, self.fin)
        self.rellenar_tabla(dic_parcelas)
        
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
                               titulo = "Resumen de parcelas", 
                               fecha = strfecha))

def _buscar(inicio, fin):
    parcelas = pclases.Parcela.select(orderBy = "parcela")
    dic_parcelas = {}
    for parcela in parcelas:
        dic_parcelas[parcela] = {}
        prodplanta = parcela.calcular_produccion_por_planta_e_intervalo(
                        inicio, fin)
        dic_parcelas[parcela]['prodplanta'] = prodplanta 
        prodtotal = parcela.calcular_produccion_por_intervalo(
                        inicio, fin)
        dic_parcelas[parcela]['prodtotal'] = prodtotal
        gapertura = parcela.get_total_gastos_apertura_por_intervalo(
                        inicio, fin)
        dic_parcelas[parcela]['gapertura'] = gapertura
        gcierre = parcela.get_total_gastos_cierre_por_intervalo(
                        inicio, fin)
        dic_parcelas[parcela]['gcierre'] = gcierre
        ggenerales = parcela.get_total_gastos_varios_por_intervalo(
                        inicio, fin)
        dic_parcelas[parcela]['ggenerales'] = ggenerales
        ingresos = parcela.get_total_ingresos_por_intervalo(
                        inicio, fin)
        dic_parcelas[parcela]['ingresos'] = ingresos
    return dic_parcelas

if __name__ == '__main__':
    t = ConsultaParcelas()

