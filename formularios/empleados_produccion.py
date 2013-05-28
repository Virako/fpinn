#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2005-2007  Francisco José Rodríguez Bogado,                   #
#                          (pacoqueen@users.sourceforge.net                   #
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
## empleados_produccion.py - Producción por empleado.
###################################################################
## NOTAS:
##  
###################################################################
## Changelog:
## 6 de enero de 2007 -> Inicio
## 
###################################################################

import os
from formularios import utils
import pygtk
pygtk.require('2.0')
import gtk, gtk.glade, time, mx, mx.DateTime
from framework import pclases
from formularios.ventana import Ventana
try:
    from pychart import *
except ImportError:
    utils.dialogo_info(titulo = "ERROR DE IMPORTACIÓN", 
                       texto = 'No se encontró el módulo "pychart".')
    sys.exit(1)
from tempfile import gettempdir


class EmpleadosProduccion(Ventana):
    VENTANA = os.path.join("ui", "empleados_produccion.glade")
    def __init__(self, objeto = None, usuario = None):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        self.usuario = usuario
        Ventana.__init__(self, self.VENTANA, objeto)
        try:
            self.empleado = pclases.Empleado.select(orderBy = "-id")[0]
        except IndexError:
            self.empleado = None
        self.add_connections({"b_salir/clicked": self.salir, 
                              "b_actualizar/clicked": self.rellenar_widgets, 
                              "b_buscar/clicked": self.buscar, 
                              'b_prod_diaria/clicked': self.abrir_prod_diaria, 
                              "b_atras/clicked": self.anterior, 
                              "b_adelante/clicked": self.siguiente, 
                              "cal_trabajo/day_selected":self.rellenar_widgets})
        # TODO: De momento:
        self.wids['b_imprimir'].set_property("visible", False)
        self.inicializar_ventana()
        gtk.main()

    def anterior(self, boton):
        empleados = pclases.Empleado.select(orderBy = "nombre")
        ids = [e.id for e in empleados]
        try:
            idactual = self.empleado.id
            idanterior = ids[ids.index(idactual) - 1]
        except (IndexError, AttributeError):
            utils.dialogo_info(titulo = "ERROR", 
                               texto = "El empleado actual es el primero.", 
                               padre = self.wids['ventana'])
        else:
            self.empleado = pclases.Empleado.get(idanterior)
            self.rellenar_widgets()

    def siguiente(self, boton):
        empleados = pclases.Empleado.select(orderBy = "nombre")
        ids = [e.id for e in empleados]
        try:
            idactual = self.empleado.id
            idsiguiente = ids[ids.index(idactual) + 1]
        except (IndexError, AttributeError):
            utils.dialogo_info(titulo = "ERROR", 
                               texto = "El empleado actual es el último.", 
                               padre = self.wids['ventana'])
        else:
            self.empleado = pclases.Empleado.get(idsiguiente)
            self.rellenar_widgets()

    def abrir_prod_diaria(self, boton):
        """
        Abre la ventana de producción diaria.
        """
        import produccion_por_empleado
        ventana = produccion_por_empleado.ProduccionPorEmpleado(
            objeto = self.empleado, 
            usuario = self.usuario)

    def inicializar_ventana(self):
        """
        Inicializa los controles de la ventana, estableciendo sus
        valores por defecto, deshabilitando los innecesarios,
        rellenando los combos, formateando el TreeView -si lo hay-...
        """
        # Inicialmente no se muestra NADA. Sólo se le deja al
        # usuario la opción de buscar o crear nuevo.
        self.activar_widgets(False)
        # Inicialización del resto de widgets:
        #self.wids['ventana'].resize(640, 480)
        hoy = mx.DateTime.localtime()
        self.wids['cal_trabajo'].select_month(hoy.month - 1, hoy.year)
        self.wids['cal_trabajo'].select_day(hoy.day)
        self.wids['ventana'].set_title("Producción por empleado")
        if pclases.Empleado.select().count() == 0:
            self.wids['b_atras'].set_sensitive(False)
            self.wids['b_adelante'].set_sensitive(False)

    def es_diferente(self):
        return False

    def activar_widgets(self, s, chequear_permisos = True):
        """
        Activa o desactiva (sensitive=True/False) todos 
        los widgets de la ventana que dependan del 
        objeto mostrado.
        Entrada: s debe ser True o False. En todo caso
        se evaluará como boolean.
        """
        ws = self.wids.keys()
        for w in ws:
            try:
                self.wids[w].set_sensitive(s)
            except Exception, msg:
                print "Widget problemático:", w, "Excepción:", msg
                #import traceback
                #traceback.print_last()
        if chequear_permisos:
            self.check_permisos(nombre_fichero_ventana = "empleados_produccion.py")
        self.wids['b_guardar'].set_sensitive(False)
        self.wids['b_actualizar'].set_sensitive(True)

    def rellenar_widgets(self, boton = None):
        """
        Introduce la información de la cuenta actual
        en los widgets.
        No se chequea que sea != None, así que
        hay que tener cuidado de no llamar a 
        esta función en ese caso.
        """
        if self.empleado != None:
            gtkimage = self.empleado.get_gtkimage(125)
            self.wids['im_foto'].set_from_pixbuf(gtkimage.get_pixbuf())
            self.wids['e_codigo'].set_text(str(self.empleado.id))
            self.wids['e_nombre'].set_text(self.empleado.nombre)
            anno, mes, dia = self.wids['cal_trabajo'].get_date()
            fecha = mx.DateTime.DateTimeFrom(day = dia, 
                                             month = mes + 1, 
                                             year = anno)
            prod = self.empleado.calcular_produccion_personal(fecha)
            self.wids['e_prod_personal'].set_text(utils.float2str(prod))
            mediaglobal = pclases.Jornal.calcular_media_global(fecha)
            self.wids['e_media_global'].set_text(utils.float2str(mediaglobal))
            ratio = self.empleado.calcular_ratio()
            self.wids['e_ratio'].set_text(utils.float2str(ratio))
            dibujar_grafico(self.wids['grafico'], self.empleado)
            empleados = pclases.Empleado.select(orderBy = "nombre")
            ids = [e.id for e in empleados]
            idactual = self.empleado.id
            self.wids['b_atras'].set_sensitive(ids[0] != idactual)
            self.wids['b_adelante'].set_sensitive(ids[-1] != idactual)
        else:
            self.activar_widgets(False)
    
    def buscar(self, boton):
        a_buscar = utils.dialogo_entrada(titulo = "BUSCAR EMPLEADO", 
                                         texto = "Introduzca nombre, código o DNI:", 
                                         padre = self.wids['ventana'])
        if a_buscar != None:
            if a_buscar.isdigit():
                subcriterios = [pclases.Empleado.q.id == int(a_buscar)]
            else:
                subcriterios = []
            if a_buscar:
                subnombre = pclases.AND(*[pclases.Empleado.q.nombre.contains(
                                    subtext) for subtext in a_buscar.split()])
                subcriterios.append(subnombre)
                subdni = pclases.AND(*[pclases.Empleado.q.dni.contains(subtext)
                                       for subtext in a_buscar.split()])
                subcriterios.append(subdni)
                resultados = pclases.Empleado.select(pclases.OR(*subcriterios), 
                                                     orderBy = "nombre")
            else:
                resultados = pclases.Empleado.select(orderBy = "nombre")
            resultados = [(r.id, r.nombre, r.dni) for r in resultados]
            idempleado = utils.dialogo_resultado(resultados, 
                                                 "SELECCIONE EMPLEADO", 
                                                 padre = self.wids['ventana'], 
                                                 cabeceras=("ID", "Nombre", "DNI"))
            if idempleado and idempleado > 0:
                self.empleado = pclases.Empleado.get(idempleado)
                self.rellenar_widgets()


def dibujar_grafico(widim, empleado):
    """
    Dibuja un gráfico de barras en widim. 
    Empleado es el empleado de la ventana, sus datos se verán en las 
    barras.
    La media global se mostrará en puntos unidos con líneas en la misma 
    gráfica.
    Para no tardar mucho en las consultas y que la gráfica quede más o 
    menos "limpia", se reducen los datos mostrados en ella a los últimos 
    90 días (que no significa 90 valores. Los días sin producción no se 
    muestran).
    """
    nombregraph = generar_grafica(empleado)
    try:
        widim.set_size_request(200*2, 170*2)
        widim.set_from_file(nombregraph)
    except:
        utils.dialogo_info(titulo = "NECESITA GHOSTSCRIPT",
                           texto = "Para ver gráficas en pantalla necesita instalar Ghostscript.\nPuede encontrarlo en el servidor de la aplicación o descargarlo de la web (http://www.cs.wisc.edu/~ghost/).")

def generar_grafica(empleado):
    ffin = mx.DateTime.localtime()
    fini = ffin - (mx.DateTime.oneDay * 90)
    prodsempleado = empleado.calcular_producciones_por_dia(fechainicio = fini, 
                                                           fechafin = ffin)
    dias = prodsempleado.keys()
    medias = pclases.Jornal.calcular_medias_por_dia(fechainicio = fini, 
                                                    fechafin = ffin)
    for dia in medias:
        if dia not in dias:
            dias.append(dia)
    dias.sort()
    data = []
    for dia in dias:
        try:
            pe = prodsempleado[dia]
        except KeyError:
            pe = 0.0
        try:
            pt = medias[dia]
        except KeyError:
            pt = 0.0
        data.append((dias.index(dia), pe, pt))

    theme.get_options()
    theme.use_color = True
    theme.reinitialize()
    tempdir = gettempdir()
    formato = "png"   # NECESITA ghostscript
    nomarchivo = "%s.%s" % (
        mx.DateTime.localtime().strftime("prodemp_%Y_%m_%d_%H_%M_%S"), 
        formato)
    nombregraph = os.path.join(tempdir, "%s") % (nomarchivo)
    can = canvas.init(fname = nombregraph, format = formato)
    try:
        max_y = max([i[1] for i in data])
    except ValueError:
        max_y = 1
    max_y *= 1.1    # Un 10% más, para que quede bonita la gráfica.
    max_y = max(1, max_y)   # Para evitar que quede 0 como máximo.

    ar = area.T(size = (150*2, 120*2), 
                x_axis = None, 
                y_axis = axis.Y(label = "Producción (kg)"), 
                legend = None) 
    ar.add_plot(bar_plot.T(label = "empleado", data = data, 
                           fill_style = fill_style.blue), 
                line_plot.T(label = "media", data = data, ycol = 2, 
                            line_style = line_style.T(color = color.gray)))
    try:
        ar.draw()
    except ValueError:  # data está vacío, fijo
        nombregraph = os.path.join("imagenes", "bars.png")

    try:
        can.close()
    except: 
        nombregraph = os.path.join("imagenes", "bars.png")
    return nombregraph



if __name__ == "__main__":
    p = EmpleadosProduccion()

