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
## build_salarios.py - Genera salarios "en batería".
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
from salarios import build_gasto_salario

class SalariosPorLote(Ventana):
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
        Ventana.__init__(self, os.path.join("..", "ui", 'build_salarios.glade'), objeto)
        connections = {'b_salir/clicked': self.salir,
                       'b_fecha/clicked': self.set_fecha, 
                       'b_doit/clicked': self.generar}
        self.add_connections(connections)
        cols = (('Emeplado', 'gobject.TYPE_STRING', False, True, True, None),
                ('Jornal','gobject.TYPE_STRING', False, True, False, None),
                ('Generar', 'gobject.TYPE_BOOLEAN', True, True, False, 
                    self.cambiar_generar),
                ('id','gobject.TYPE_STRING',False,False,False,None))
        utils.preparar_listview(self.wids['tv_datos'], cols)
        col = self.wids['tv_datos'].get_column(2)
        for cell in col.get_cell_renderers():
            cell.set_property("xalign", 0.5)
        temp = time.localtime()
        self.fin = str(temp[0])+'/'+str(temp[1])+'/'+str(temp[2])
        self.wids['e_fecha'].set_text(utils.str_fecha(temp))
        self.rellenar_widgets()
        self.wids['ventana'].resize(800, 600)
        gtk.main()

    def cambiar_generar(self, cell, path):
        model = self.wids['tv_datos'].get_model()
        model[path][2] = not cell.get_active()

    def generar(self, boton):
        """
        Genera un salario por empleado con todos los jornales que tenga a 
        True.
        Después abre una ventana Salarios con cada uno de los salarios 
        generados.
        Finalmente recarga la información de esta ventana con los jornales 
        que han quedado pendientes.
        """
        horas = self.wids['e_horas'].get_text()
        try:
            horas = utils._float(horas)
        except ValueError:
            utils.dialogo_info(titulo = "ERROR", 
                               texto = "El texto «%s» no es un número."%horas, 
                               padre = self.wids['ventana'])
        else:
            jornales = {}
            model = self.wids['tv_datos'].get_model()
            for fila in range(len(model)):
                if model[fila][2]:
                    jornal = pclases.Jornal.get(model[fila][-1])
                    try:
                        jornales[jornal.empleado].append(jornal)
                    except KeyError:
                        jornales[jornal.empleado] = [jornal]
            txtfecha = self.wids['e_fecha'].get_text()
            fecha = utils.parse_fecha(txtfecha)
            salarios_creados = []
            for empleado in jornales:
                gasto, empleado = build_gasto_salario(self.wids['ventana'], 
                                                      empleado)
                salario = pclases.Salario(horasCampo = 0.0, 
                                          fecha = fecha, 
                                          horasManipulacion = horas, 
                                          totalEuros = 0.0, 
                                          empleado = empleado, 
                                          gasto = gasto, 
                                          actividad = None)
                for jornal in jornales[empleado]:
                    jornal.salario = salario
                    salario.horasCampo += jornal.horasCampo
                    # OJO: CWT: No actualizo las horas de manipulación. Eran 
                    # las mismas para todos los salarios creados según 
                    # documento de requisitos v2 (cuaderno).
                    salario.totalEuros += (jornal.eurosCampo 
                                           + jornal.eurosManipulacion)
                dias = []
                for jornal in salario.jornales:
                    dia = utils.abs_mxfecha(jornal.fechahoraInicio)
                    if dia not in dias:
                        dias.append(dia)
                        # NOTA: OJO: Si echa "dos peonás" en el mismo día, se 
                        # le cuenta como un día (aparte de las horas que eche 
                        # y demás. Hablo del precio por día del empleado). Lo 
                        # mismo digo si viene y echa tres días seguidos en el 
                        # mismo jornal. Cuenta como uno. O lo parte el nodo de 
                        # campo o se le cuenta como uno.
                salario.totalEuros += len(dias) * empleado.precioDiario
                salario.update_actividad()
                salarios_creados.append(salario)
            self.rellenar_widgets()
            import salarios
            #for salario in salarios_creados:
            #    ventana = salarios.Salarios(salario, self.usuario)
            #No puedo abrir varias ventanas a la vez. Abro el último salario creado.
            try:
                ventana = salarios.Salarios(salarios_creados[-1], self.usuario)
            except IndexError:
                pass

    def activar_widgets(self, activar):
        pass

    def chequear_cambios(self):
        pass

    def rellenar_widgets(self):
        self.rellenar_tabla()

    def rellenar_tabla(self):
    	"""
        Rellena el model con los items de la consulta.
        Elementos es un diccionario con objetos cuentaGastos y una lista  
        de gastos correspondientes a los meses de consulta.
        """        
    	model = self.wids['tv_datos'].get_model()
    	model.clear()
        jornales = pclases.Jornal.select(pclases.Jornal.q.salarioID == None, 
                                         orderBy = "fechahoraInicio")
    	for jornal in jornales:
            try:
                nombre_completo_empleado = jornal.empleado.nombre
            except AttributeError:
                nombre_completo_empleado = "¡SIN EMPLEADO!"
            info_jornal = "%s. De %s a %s. Producción: %s." % (
                utils.str_fecha(jornal.fechahoraInicio), 
                utils.str_hora_corta(jornal.fechahoraInicio), 
                utils.str_hora_corta(jornal.fechahoraFin), 
                utils.float2str(jornal.produccion))
            model.append((nombre_completo_empleado, 
                          info_jornal, 
                          False, 
                          jornal.id))

    def set_fecha(self,boton):
        temp = utils.mostrar_calendario(padre = self.wids['ventana'])
        self.wids['e_fecha'].set_text(utils.str_fecha(temp))
        self.inicio = str(temp[2])+'/'+str(temp[1])+'/'+str(temp[0])


if __name__ == '__main__':
    t = SalariosPorLote()

