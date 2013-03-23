#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2005-2008  Francisco José Rodríguez Bogado,                   #
#                          Diego Muñoz Escalante.                             #
# (pacoqueen@users.sourceforge.net, escalant3@users.sourceforge.net)          #
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
## consulta_gastos.py - Gastos por fecha.
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

class ConsultaGastos(Ventana):
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
        Ventana.__init__(self, os.path.join("..", "ui", 'consulta_gastos.glade'), objeto)
        connections = {'b_salir/clicked': self.salir,
                       'b_buscar/clicked': self.buscar,
                       'b_imprimir/clicked': self.imprimir,
                       'b_fecha_inicio/clicked': self.set_inicio,
                       'b_fecha_fin/clicked': self.set_fin, 
                       'b_exportar/clicked': self.exportar}
        self.add_connections(connections)
        cols = (('Código','gobject.TYPE_STRING',False,True, True, None),
                ('Concepto','gobject.TYPE_STRING',False,False,False,None),
                ('Fecha', 'gobject.TYPE_STRING',False,True, False,None),
                ('Factura','gobject.TYPE_STRING',False,True,False,None),
                ('Parcela','gobject.TYPE_STRING',False,True,False,None),
                ('Importe','gobject.TYPE_STRING',False,True,False,None),
                ('id','gobject.TYPE_STRING',False,False,False,None))
        utils.preparar_treeview(self.wids['tv_datos'], cols)
        col = self.wids['tv_datos'].get_column(5)
        for cell in col.get_cell_renderers():
            cell.set_property("xalign", 1)
        temp = time.localtime()
        self.fin = str(temp[0])+'/'+str(temp[1])+'/'+str(temp[2])
        self.wids['e_fechafin'].set_text(utils.str_fecha(temp))
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

    def rellenar_tabla(self, cuentas):
    	"""
        Rellena el model con los items de la consulta.
        Elementos es un diccionario con objetos cuentaGastos y una lista  
        de gastos correspondientes a los meses de consulta.
        """        
    	model = self.wids['tv_datos'].get_model()
    	model.clear()
        total = 0
    	for cuenta in cuentas:
            padre = model.append(None, (cuenta.descripcion, 
                                        "", 
                                        "", 
                                        "", 
                                        "", 
                                        utils.float2str(0.0), 
                                        cuenta.id))
            for gasto in cuentas[cuenta]:
                model.append(padre, (gasto.codigo, 
                                     gasto.concepto, 
                                     utils.str_fecha(gasto.fecha), 
                                     gasto.facturaCompra
                                        and gasto.facturaCompra.numfactura
                                        or "", 
                                     gasto.parcela 
                                        and gasto.parcela.parcela 
                                        or "", 
                                     utils.float2str(gasto.importe), 
                                     gasto.id))
                model[padre][5] = utils.float2str(
                    utils._float(model[padre][5]) + gasto.importe)
                total += gasto.importe
        self.wids['e_total'].set_text("%s €" % utils.float2str(total))
        
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
            gastos = pclases.Gasto.select(pclases.Gasto.q.fecha <= self.fin, 
                                          orderBy = 'fecha')
        else:
            gastos = pclases.Gasto.select(
                        pclases.AND(pclases.Gasto.q.fecha >= self.inicio,
                                    pclases.Gasto.q.fecha <= self.fin), 
                        orderBy = 'fecha')
        cuentas = {}
        for item in gastos:
            if item.cuentaGastos not in cuentas:
                cuentas[item.cuentaGastos] = [item]
            else:
                cuentas[item.cuentaGastos].append(item)
        self.rellenar_tabla(cuentas)
        

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
                               titulo = "Gastos", 
                               fecha = strfecha))


if __name__ == '__main__':
    t = ConsultaGastos()    
