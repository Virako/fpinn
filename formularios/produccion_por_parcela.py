#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2005-2007  Francisco José Rodríguez Bogado,                   #
#                          (pacoqueen@users.sourceforge.net                   #
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
## produccion_por_parcela.py - Producción por parcela.
###################################################################
## NOTAS:
##  
###################################################################
## Changelog:
## 15 de enero de 2007 -> Inicio
## 
###################################################################
## TODO: Al cambiar la organización de las parcelas de un año para
## otro se "pierden" las consultas de años anteriores. No surgió 
## durante las reuniones de requisitos ni se ha planteado aún la 
## situación. Pero lo ideal sería que cada año pudiera tener una 
## organización diferente de parcelas y fincas.
###################################################################

import sys, os
import utils
import pygtk
pygtk.require('2.0')
import gtk, gtk.glade, time, mx, mx.DateTime
try:
    import pclases
except ImportError:
    sys.path.append(os.path.join('..', 'framework'))
    import pclases
from ventana import Ventana

class ProduccionPorParcela(Ventana):
    VENTANA = os.path.join("..", "ui", "produccion_por_parcela.glade")
    def __init__(self, objeto = None, usuario = None):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        self.usuario = usuario
        Ventana.__init__(self, self.VENTANA, objeto)
        self.add_connections({"b_salir/clicked": self.salir, 
                              "cb_campanna/changed": self.mostrar_fincas})
        self.inicializar_ventana()
        gtk.main()

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
        camps = [(c.id, "%s - %s" % (utils.str_fecha(c.fechaInicio), 
                                     utils.str_fecha(c.fechaFin)))
                 for c in pclases.Campanna.select(orderBy = "fechaInicio")]
        utils.rellenar_lista(self.wids['cb_campanna'], camps)
        self.wids['b_guardar'] = gtk.Button("N/A")
        self.wids['b_guardar'].set_property("visible", False)
        self.wids['b_guardar'].set_sensitive(False)
        i = -1
        anno_actual = mx.DateTime.localtime().year
        model = self.wids['cb_campanna'].get_model()
        for i in range(len(model)):
            if str(anno_actual) in model[i][1]:
                break
            # Y si el año no está, se queda en la última campaña.
        self.wids['cb_campanna'].set_active(i)

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
            self.check_permisos(nombre_fichero_ventana = "produccion_por_parcela.py")

    def rellenar_widgets(self):
        """
        Introduce la información de la cuenta actual
        en los widgets.
        No se chequea que sea != None, así que
        hay que tener cuidado de no llamar a 
        esta función en ese caso.
        """
        self.limpiar_tabla()
        self.mostrar_fincas()

    def limpiar_tabla():
        for child in self.wids['tabla'].get_children():
            self.wids['tabla'].remove(child)
            child.destroy

    def mostrar_fincas(self, cb = None):
        from math import ceil
        numfincas = pclases.Finca.select().count()
        ancho = alto = int(ceil(numfincas ** 0.5))
        self.wids['tabla'].resize((ancho * 2) - 1, 
                                  (alto * 2) - 1)
            # Entre cada finca habrá un separator. De ahí el (x2)-1.
        columna = fila = 0
        numcolumnas = self.wids['tabla'].get_property("n-columns")
        numfilas = self.wids['tabla'].get_property("n-rows")
        for finca in pclases.Finca.select(orderBy = "nombre"):
            self.insert_finca(finca, fila, columna)
            columna += 1
            if columna < numcolumnas:
                self.wids['tabla'].attach(gtk.VSeparator(), 
                                          columna, columna +1, 
                                          fila, fila +1)
                columna += 1
            elif columna >= numcolumnas:
                columna = 0
                fila += 1
                if fila < numfilas:
                    for col in range(numcolumnas):
                        self.wids['tabla'].attach(gtk.HSeparator(), 
                                                  col, col +1, 
                                                  fila, fila +1, 
                                                  yoptions = 0)
                    fila += 1
        self.wids['tabla'].show_all()


    def insert_finca(self, finca, fila, columna):
        """
        Inserta en self.wids['tabla'] -en (fila, columna)- la información de 
        la finca a través de un gtk.Image y un label dentro de un VBox que a 
        su vez está dentro de un HBox de dos columnas y con la información de 
        la finca como ToolTip.
        """
        #MAX = 50    # Máximo ancho y alto de píxeles para el mapa de la finca.
        MAX = 100   # Máximo ancho y alto de píxeles para el mapa de la finca.
        vbox = gtk.VBox()
        image = gtk.Image()
        #image.set_from_file(finca.get_ruta_completa_plano())
        finca.mostrar_imagen_en(image, MAX)
        label = gtk.Label(' <span foreground="Gray"><big><i>' 
                            + finca.nombre 
                            + '</i></big></span> ')
        label.set_use_markup(True)
        label.set_angle(90)
        idcampanna = utils.combo_get_value(self.wids['cb_campanna'])
        campanna = pclases.Campanna.get(idcampanna)
        prod = sum([parcela.calcular_produccion(campanna)
                    for parcela in finca.parcelas])
        plantas = sum([p.numeroDePlantas for p in finca.parcelas])
        if plantas != 0:
            kgplanta = sum([parcela.calcular_produccion(campanna)
                            for parcela in finca.parcelas]) / plantas
        else:
            kgplanta = 0.0
        apertura = sum([parcela.get_total_gastos_apertura(campanna)
                        for parcela in finca.parcelas])
        varios = sum([parcela.get_total_gastos_varios(campanna)
                      for parcela in finca.parcelas])
        cierre = sum([parcela.get_total_gastos_cierre(campanna)
                      for parcela in finca.parcelas])
        texto_tip = "<big><big>%s</big>\nProducción: <b>%s kg</b>\n<b>%s kg/planta</b>\nGastos apertura: %s €\nGastos varios: %s €\nGastos de cierre: %s €</big>" % (
                                finca.nombre, 
                                utils.float2str(prod),
                                utils.float2str(kgplanta), 
                                utils.float2str(apertura), 
                                utils.float2str(varios), 
                                utils.float2str(cierre))
        #image.set_tooltip_text(texto_tip)
        try:
            image.set_tooltip_markup(texto_tip)
        except:
            pass    # No tiene este método en GTK/PyGTK 2.10 de WXP
        vbox.pack_start(image)
        vbox.pack_start(label)
        hbox = gtk.HBox()
        hbox.pack_start(vbox)
        widparcelas = self.insert_parcelas(finca)
        hbox.pack_start(widparcelas)
        self.wids['tabla'].attach(hbox, columna, columna+1, fila, fila+1)

    def insert_parcelas(self, finca):
        """
        Devuelve una tabla con las parcelas de la finca en sus celdas.
        Cada parcela estará dentro de un VBox con el plano y un label con 
        el nombre de la parcela.
        Se añadirá también un ToolTip con los datos de la parcela.
        """
        tabla = gtk.Table()
        from math import ceil
        PARCELA = pclases.Parcela
        _parcelas = PARCELA.select(PARCELA.q.fincaID == finca.id, 
                                   #orderBy = "parcela")
                                   #orderBy = "ruta_plano")
                                   #orderBy = "repr_orden, ruta_plano")
                                   orderBy = "repr_orden")  # Dependiendo 
        # de la versión de sqlobject, permite ordenar por una sola o por 
        # dos o más columnas pasadas como cadena.
        # Me voy al peor caso (ordena solo por repr_orden) y ordeno por 
        # la otra columna: ruta_plano.
        _parcelas = [p for p in _parcelas]  # Parece que [:] también va según 
        # qué versiones de sqlobject para copiar la lista entera.
        def ordenar_por_orden_y_ruta_plano(p1, p2):
            if p1.reprOrden == p2.reprOrden:
                if p1.rutaPlano < p2.rutaPlano:
                    return -1
                elif p1.rutaPlano > p2.rutaPlano:
                    return 1
                else:
                    return 0
            elif p1.reprOrden < p2.reprOrden:
                return -1
            else:
                return 1
        _parcelas.sort(ordenar_por_orden_y_ruta_plano)
        ordenadas = []
        no_importa = []
        for p in _parcelas: # _parcelas ya está ordenada
            if p.reprOrden >= 0:
                ordenadas.append(p)
            else:
                no_importa.append(p)
        parcelas = ordenadas + no_importa
        #numparcelas = parcelas.count()
        numparcelas = sum(p.reprAncho for p in parcelas)
        # El algoritmo para ir colocando parcelas es: de izquerda a derecha 
        # por orden de reprOrden. Si no está definido, por orden de rutaPlano.
        # El alto de las parcelas siempre se considerará 1 (se ignora el valor
        # real por el momento) y se distribuyen de manera que la finca siempre 
        # tenga una forma rectangular más ancha que alta.
        ancho = alto = int(ceil(numparcelas ** 0.5))
        # Caso especial para un determinado tipo de finca rectangular que 
        # no encaja bien en una tabla cuadrada. EXPERIMENTAL.
        if (ancho+1) * (alto-1) == numparcelas:
            ancho += 1
            alto -= 1
        #print finca.nombre, ancho, alto 
        tabla.resize(alto, ancho)
        columna = fila = 0
        numcolumnas = tabla.get_property("n-columns")
        numfilas = tabla.get_property("n-rows")
        celdas_ocupadas = []
        for parcela in parcelas:
            #if parcelas.count() > 6:
            if len(parcelas) > 6:
                celdas_ocupadas += self.insert_parcela(tabla, parcela, fila, 
                                                       columna, 
                                                       celdas_ocupadas, 
                                                       numcolumnas, 100)
            else:
                celdas_ocupadas += self.insert_parcela(tabla, parcela, fila, 
                                                       columna, 
                                                       celdas_ocupadas, 
                                                       numcolumnas)
            #columna += 1
            columna += parcela.reprAncho
            if columna >= numcolumnas:
                columna = 0
                fila += 1
        return tabla

    def insert_parcela(self, tabla, parcela, fila, columna, 
                       celdas_ocupadas, ancho_max, tammax = 150):
        """
        Inserta en tabla -en (fila, columna)- la información de 
        la parcela a través de un gtk.Image y un label dentro de un VBox que a 
        su vez está dentro de un HBox de dos columnas y con la información de 
        la parcela como ToolTip.
        Recibe una lista de tuplas de coordenadas con las celdas ocupadas y 
        el ancho máximo para controlar la inserción de parcelas más altas 
        que una casilla.
        Devuelve los pares de coordenadas de las celdas ocupadas por la 
        parcela insertada.
        """
        #MAX = 25  # Máximo ancho y alto de píxeles para el mapa de la parcela.
        #MAX = 150 # Máximo ancho y alto de píxeles para el mapa de la parcela.
        MAXX = MAXY = tammax
        MAXX *= parcela.reprAncho
        MAXY *= parcela.reprAlto
        hbox = gtk.HBox()
        image = gtk.Image()
        pixbuf = gtk.gdk.pixbuf_new_from_file(parcela.get_ruta_completa_plano())
        if (pixbuf.get_width() != MAXX 
            or pixbuf.get_height() != MAXY):
            colorspace = pixbuf.get_property("colorspace")
            has_alpha = pixbuf.get_property("has_alpha")
            bits_per_sample = pixbuf.get_property("bits_per_sample")
            pixbuf2 = gtk.gdk.Pixbuf(colorspace, 
                                     has_alpha, 
                                     bits_per_sample, 
                                     MAXX, 
                                     MAXY)
            pixbuf.scale(pixbuf2, 
                         0, 0, 
                         MAXX, MAXY, 
                         0, 0,
                         (1.0 * MAXX) / pixbuf.get_width(), 
                         (1.0 * MAXY) / pixbuf.get_height(), 
                         gtk.gdk.INTERP_BILINEAR)
            pixbuf = pixbuf2
        image.set_from_pixbuf(pixbuf)
        idcampanna = utils.combo_get_value(self.wids['cb_campanna'])
        campanna = pclases.Campanna.get(idcampanna)
        prod = parcela.calcular_produccion(campanna)
        kgplanta = parcela.calcular_produccion_por_planta(campanna)
        apertura = parcela.get_total_gastos_apertura(campanna)
        varios = parcela.get_total_gastos_varios(campanna)
        cierre = parcela.get_total_gastos_cierre(campanna)
        texto_tip = "<big><big>%s</big>\nProducción: <b>%s kg</b>\n<b>%s kg/"\
                    "planta</b>\nGastos apertura: %s €\nGastos varios: %s €"\
                    "\nGastos de cierre: %s €</big>" % (
                        parcela.parcela, 
                        utils.float2str(prod),
                        utils.float2str(kgplanta), 
                        utils.float2str(apertura), 
                        utils.float2str(varios), 
                        utils.float2str(cierre))
        try:
            image.set_tooltip_markup(texto_tip)
        except:
            pass    # No tiene este método en GTK/PyGTK 2.10 de WXP
        #label = gtk.Label(' <span foreground="Gray"><small><i>' + parcela.parcela + '</i></small></span> ')
        #label.set_use_markup(True)
        #label.set_angle(90)
        #hbox.pack_start(label)
        hbox.pack_start(image)
        hbox_ext = gtk.HBox()
        hbox_ext.pack_start(hbox)
        #tabla.attach(hbox_ext, columna, columna+1, fila, fila+1)
        # Si la celda ya está ocupada, paso a la columna siguiente.
        while (columna, fila) in celdas_ocupadas:
            columna += 1
            if columna + parcela.reprAncho - 1 >= ancho_max:
                columna = 0
                fila += 1
        tabla.attach(hbox_ext, columna, columna + parcela.reprAncho, 
                               fila, fila + parcela.reprAlto)
        res = []
        for x in range(columna, columna + parcela.reprAncho):
            for y in range(fila, fila + parcela.reprAlto):
                res.append((x, y))
        # OJO: Ignoro el alto por el momento por la forma que tiene el 
        # algoritmo de ir rellenando parcelas de izquierda a derecha. Si una 
        # parcela pudiera invadir la fila inferior, tendría que guardar 
        # entonces las "semifilas" ocupadas e ir cuadrando las parcelas 
        # lateralmente con el riesgo de que una tenga un ancho superior al 
        # espacio dispnible en la fila, teniéndola que pasar a la siguiente.
        # Acabaría casi con un algoritmo de la mochila con restricciones de 
        # orden y pesos por elemento. Y de momento meter IA no está entre mis 
        # planes, y menos por un antojo CWT.
        # OJO 2: Ignoro el alto... parcialmente. Estoy de experimentos. De 
        # momento no dejo que el usuario lo menta en la ventana de parcelas, 
        # pero atacando directamente los datos y preparándolos un poco me 
        # puede valer.
        #print parcela.parcela, parcela.reprOrden, ":", parcela.reprAncho, "x", parcela.reprAlto, "->", columna, "a", columna+parcela.reprAncho, ";" , fila, "a", fila + parcela.reprAlto
        return res


if __name__ == "__main__":
    p = ProduccionPorParcela()

