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
## consulta_facturacion_pendiente.py - Albaranes sin facturar.
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

class ConsultaFacturacionPendiente(Ventana):
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
        self.usuario = usuario
        Ventana.__init__(self, 
                         os.path.join("..","ui",'consulta_facturacion.glade'), 
                         objeto)
        connections = {'b_salir/clicked': self.salir,
                       'b_buscar/clicked': self.buscar,
                       'b_imprimir/clicked': self.imprimir,
                       'b_fecha_inicio/clicked': self.set_inicio,
                       'b_fecha_fin/clicked': self.set_fin, 
                       'b_exportar/clicked': self.exportar}
        self.add_connections(connections)
        cols = (('Albarán','gobject.TYPE_STRING', False, True, True, None),
                ('Fecha','gobject.TYPE_STRING', False, False, False, None),
                ('Cliente', 'gobject.TYPE_STRING', False, True, False, None),
                ('Importe','gobject.TYPE_STRING', False, True, False, None),
                ('id','gobject.TYPE_STRING', False, False, False, None))
        utils.preparar_listview(self.wids['tv_datos'], cols)
        col = self.wids['tv_datos'].get_column(3)
        for cell in col.get_cell_renderers():
            cell.set_property("xalign", 1)
        self.wids['tv_datos'].connect("row-activated", self.abrir_albaran)
        temp = time.localtime()
        self.fin = str(temp[0])+'/'+str(temp[1])+'/'+str(temp[2])
        self.wids['e_fechafin'].set_text(utils.str_fecha(temp))
        self.wids['e_total_cantidades'].set_property("visible", False)
        self.wids['label7'].set_property("visible", False)
        gtk.main()

    def abrir_albaran(self, tv, path, col):
        """
        Abre el albarán al que se le ha hecho doble clic en el TreeView.
        """
        from facturar_albaranes import abrir_albaran
        abrir_albaran(tv, path, col, self.usuario, self)

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

    def rellenar_tabla(self, albaranes):
    	"""
        Rellena el model con los items de la consulta.
        Elementos es un diccionario con objetos albarán.
        """        
    	model = self.wids['tv_datos'].get_model()
    	model.clear()
        total = 0
    	for albaran in albaranes:
            importe = albaran.calcular_importe(iva = True)
            padre = model.append((albaran.numalbaran, 
                                  utils.str_fecha(albaran.fecha), 
                                  albaran.cliente.nombre, 
                                  utils.float2str(importe), 
                                  albaran.id))
            total += importe
        self.wids['e_total_importes'].set_text("%s €" % utils.float2str(total))
        
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
            ldvs = pclases.LineaDeVenta.select(pclases.AND(
                pclases.LineaDeVenta.q.facturaVentaID == None, 
                pclases.LineaDeVenta.q.albaranSalidaID 
                    == pclases.AlbaranSalida.q.id, 
                pclases.AlbaranSalida.q.fecha <= self.fin))
        else:
            ldvs = pclases.LineaDeVenta.select(pclases.AND(
                pclases.LineaDeVenta.q.facturaVentaID == None, 
                pclases.LineaDeVenta.q.albaranSalidaID 
                    == pclases.AlbaranSalida.q.id, 
                pclases.AlbaranSalida.q.fecha >= self.inicio, 
                pclases.AlbaranSalida.q.fecha <= self.fin))
        albaranes = []
        for ldv in ldvs:
            a = ldv.albaranSalida
            if a not in albaranes:
                albaranes.append(a)
        self.rellenar_tabla(albaranes)

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
                               titulo = "Albaranes pendientes de facturar", 
                               fecha = strfecha))


if __name__ == '__main__':
    t = ConsultaFacturacionPendiente()

