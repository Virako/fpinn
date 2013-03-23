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
## parcelas.py
###################################################################
## 
###################################################################

import sys, os
from ventana import Ventana
import utils
import pygtk
pygtk.require('2.0')
import gtk, gtk.glade, time, mx, mx.DateTime
try:
    import pclases
    from seeker import VentanaGenerica 
except ImportError:
    sys.path.append(os.path.join('..', 'framework'))
    import pclases
    from seeker import VentanaGenerica 
from utils import _float as float
import adapter

DEBUG = False

class Parcelas(Ventana, VentanaGenerica):
    CLASE = pclases.Parcela
    VENTANA = os.path.join("..", "ui", "parcelas.glade")
    def __init__(self, objeto = None, usuario = None):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        self.usuario = usuario
        self.clase = self.CLASE
        Ventana.__init__(self, self.VENTANA, objeto)
        self.dic_campos = self.__build_dic_campos()
        self.adaptador = adapter.adaptar_clase(self.clase, self.dic_campos)
        connections = {'b_salir/clicked': self.salir,
                       'b_nuevo/clicked': self.nuevo,
                       'b_borrar/clicked': self.borrar,
                       'b_actualizar/clicked': self.actualizar_ventana,
                       'b_guardar/clicked': self.guardar,
                       'b_buscar/clicked': self.buscar,
                       "cb_campanna/changed": self.rellenar_tablas, 
                       "b_add_practica_cutural/clicked": 
                            self.add_practica_cutural, 
                       "b_drop_practica_cutural/clicked": 
                            self.drop_practica_cutural, 
                       "b_add_cultivo/clicked": self.add_cultivo, 
                       "b_drop_cultivo/clicked": self.drop_cultivo, 
                       "b_add_fertilizacion/clicked": self.add_fertilizacion, 
                       "b_drop_fertilizacion/clicked": self.drop_fertilizacion, 
                       "b_add_enmienda/clicked": self.add_enmienda, 
                       "b_drop_enmienda/clicked": self.drop_enmienda, 
                       "b_add_fitosanitario/clicked": self.add_fitosanitario, 
                       "b_drop_fitosanitario/clicked": self.drop_fitosanitario, 
                       "b_plano/clicked": self.cambiar_plano
                      }
        self.add_connections(connections)
        self.inicializar_ventana()
        if self.objeto == None:
            self.ir_a_primero()
        else:
            self.ir_a(objeto)
        gtk.main()

    def cambiar_por_combo(self, tv, numcol):
        import gobject
        # Elimino columna actual
        column = tv.get_column(numcol)
        tv.remove_column(column)
        # Creo model para el CellCombo
        model = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_INT64)
        for materia in pclases.MateriaActiva.select(orderBy = "nombre"):
            model.append((materia.nombre, materia.id))
        # Creo CellCombo
        cellcombo = gtk.CellRendererCombo()
        cellcombo.set_property("model", model)
        cellcombo.set_property("text-column", 0)
        cellcombo.set_property("editable", True)
        cellcombo.set_property("has-entry", False)
        # Función callback para la señal "editado"
        def guardar_combo(cell, 
                          path, 
                          text, 
                          model_tv, 
                          numcol, 
                          model_combo, 
                          nombre_tv):
            # Es lento, pero no encuentro otra cosa:
            idmateria = None
            if text == None:
                # Ocurre si le da muy muy pero que muy rápido al combo 
                # abriéndolo y cerrándolo sin parar
                text = model_combo[0][0]
            for i in xrange(len(model_combo)):
                texto, id = model_combo[i]
                if texto == text:
                    idmateria = id
                    break
            if idmateria == None:
                utils.dialogo_info(titulo = "ERROR EN COMBO MATERIA ACTIVA", 
                                   texto = "Ocurrió un error inesperado seleccionando la materia activa.\n\nContacte con los desarrolladores de la aplicación\n(Vea el diálogo «Acerca de...» en el menú principal.)", 
                                   padre = self.wids['ventana'])
            else:
                materia = pclases.MateriaActiva.get(idmateria)
                model_tv[path][0] = materia.nombre
                model_tv[path][1] = materia.nombreComercial
                model_tv[path][2] = materia.listado
                model_tv[path][3] = materia.otros
                model_tv[path][5] = materia.plazoSeguridad
                model_tv[path][6] = materia.dosis
                if nombre_tv == "tv_fertilizaciones":
                    clase = pclases.Fertilizacion
                elif nombre_tv == "tv_enmiendas":
                    clase = pclases.Enmienda
                elif nombre_tv == "tv_fitosanitarios":
                    clase = pclases.Fitosanitario
                else:
                    clase = None
                if clase:
                    id = model_tv[path][-1]
                    objeto = clase.get(id)
                    objeto.materiaActiva = materia.nombre
                    objeto.nombre = materia.nombreComercial
                    objeto.listado = materia.listado
                    objeto.otros = materia.otros
                    objeto.plazoSeguridad = materia.plazoSeguridad
                    objeto.dosis = materia.dosis
        # Y agrego al TreeView
        cellcombo.connect("edited", 
                          guardar_combo, 
                          tv.get_model(), 
                          numcol, 
                          model, 
                          tv.name)
        #column.pack_start(cellcombo)
        #column.set_attributes(cellcombo, text = numcol)
        tv.insert_column_with_attributes(numcol, 
                                         "Materia activa", 
                                         cellcombo, 
                                         text = numcol)

    def cambiar_plano(self, boton):
        nomfich = utils.dialogo_abrir(titulo = "BUSCAR PLANO PARCELA", 
                                      filtro_imagenes = True, 
                                      padre = self.wids['ventana'])
        if nomfich != None:
            self.objeto.guardar(nomfich)
            self.actualizar_ventana()

    def add_practica_cutural(self, boton):
        campid = utils.combo_get_value(self.wids['cb_campanna'])
        if campid != None:
            pc = pclases.PracticaCutural(campannaID = campid, 
                                         parcela = self.objeto, 
                                         fecha = mx.DateTime.localtime(), 
                                         practica = "", 
                                         maquinaria = "", 
                                         observaciones = "")
            self.wids['tv_cuturales'].get_model().append((
                utils.str_fecha(pc.fecha), 
                pc.practica, 
                pc.maquinaria, 
                pc.observaciones, 
                pc.id))
        else:
            utils.dialogo_info(titulo = "SELECCIONE CAMPAÑA", 
                               texto = "Seleccione la campaña activa.", 
                               padre = self.wids['ventana'])

    def drop_practica_cutural(self, boton):
        selection = self.wids['tv_cuturales'].get_selection()
        model, paths = selection.get_selected_rows()
        for path in paths:
            pcid = model[path][-1]
            pc = pclases.PracticaCutural.get(pcid)
            try:
                pc.destroySelf()
            except Exception, msg:
                utils.dialogo_info(titulo = "ERROR", 
                                   texto = "No se pudo eliminar. Verifique que no esté implicado en otras operaciones.\n\nTexto de depuración:\n%s" % msg, 
                                   padre = self.wids['ventana'])
        if paths:
            self.rellenar_practicas_cuturales()

    def add_cultivo(self, boton): 
        campid = utils.combo_get_value(self.wids['cb_campanna'])
        if campid != None:
            c = pclases.Cultivo(campannaID = campid, 
                                parcela = self.objeto)
            self.wids['tv_cultivos'].get_model().append((
                c.cultivo, 
                c.variedad, 
                utils.str_fecha(c.siembra), 
                utils.str_fecha(c.recoleccionInicio), 
                utils.str_fecha(c.recoleccionFin), 
                c.hidroponico, 
                c.tradicional, 
                c.id))
        else:
            utils.dialogo_info(titulo = "SELECCIONE CAMPAÑA", 
                               texto = "Seleccione la campaña activa.", 
                               padre = self.wids['ventana'])

    def drop_cultivo(self, boton): 
        selection = self.wids['tv_cultivos'].get_selection()
        model, paths = selection.get_selected_rows()
        for path in paths:
            cid = model[path][-1]
            c = pclases.Cultivo.get(cid)
            try:
                c.destroySelf()
            except Exception, msg:
                utils.dialogo_info(titulo = "ERROR", 
                                   texto = "No se pudo eliminar. Verifique que no esté implicado en otras operaciones.\n\nTexto de depuración:\n%s" % msg, 
                                   padre = self.wids['ventana'])
        if paths:
            self.rellenar_cultivos()

    def add_fertilizacion(self, boton):
        campid = utils.combo_get_value(self.wids['cb_campanna'])
        if campid != None:
            c = pclases.Fertilizacion(campannaID = campid, 
                                      parcela = self.objeto)
            self.wids['tv_fertilizaciones'].get_model().append((
                c.materiaActiva, 
                c.nombre, 
                c.listado, 
                c.otros, 
                utils.str_fecha(c.fecha), 
                c.plazoSeguridad, 
                utils.float2str(c.dosis), 
                c.observaciones, 
                c.id))
        else:
            utils.dialogo_info(titulo = "SELECCIONE CAMPAÑA", 
                               texto = "Seleccione la campaña activa.", 
                               padre = self.wids['ventana'])

    def add_enmienda(self, boton):
        campid = utils.combo_get_value(self.wids['cb_campanna'])
        if campid != None:
            c = pclases.Enmienda(campannaID = campid, 
                                 parcela = self.objeto)
            self.wids['tv_enmiendas'].get_model().append((
                c.materiaActiva, 
                c.nombre, 
                c.listado, 
                c.otros, 
                utils.str_fecha(c.fecha), 
                c.plazoSeguridad, 
                utils.float2str(c.dosis), 
                c.observaciones, 
                c.id))
        else:
            utils.dialogo_info(titulo = "SELECCIONE CAMPAÑA", 
                               texto = "Seleccione la campaña activa.", 
                               padre = self.wids['ventana'])

    def add_fitosanitario(self, boton):
        campid = utils.combo_get_value(self.wids['cb_campanna'])
        if campid != None:
            c = pclases.Fitosanitario(campannaID = campid, 
                                      parcela = self.objeto)
            self.wids['tv_fitosanitarios'].get_model().append((
                c.materiaActiva, 
                c.nombre, 
                c.listado, 
                c.otros, 
                utils.str_fecha(c.fecha), 
                c.plazoSeguridad, 
                utils.float2str(c.dosis), 
                c.observaciones, 
                c.id))
        else:
            utils.dialogo_info(titulo = "SELECCIONE CAMPAÑA", 
                               texto = "Seleccione la campaña activa.", 
                               padre = self.wids['ventana'])

    def drop_fertilizacion(self, boton):
        selection = self.wids['tv_fertilizaciones'].get_selection()
        model, paths = selection.get_selected_rows()
        for path in paths:
            pcid = model[path][-1]
            pc = pclases.Fertilizacion.get(pcid)
            try:
                pc.destroySelf()
            except Exception, msg:
                utils.dialogo_info(titulo = "ERROR", 
                                   texto = "No se pudo eliminar. Verifique que no esté implicado en otras operaciones.\n\nTexto de depuración:\n%s" % msg, 
                                   padre = self.wids['ventana'])
        if paths:
            self.rellenar_fertilizaciones()

    def drop_enmienda(self, boton):
        selection = self.wids['tv_enmiendas'].get_selection()
        model, paths = selection.get_selected_rows()
        for path in paths:
            pcid = model[path][-1]
            pc = pclases.Enmienda.get(pcid)
            try:
                pc.destroySelf()
            except Exception, msg:
                utils.dialogo_info(titulo = "ERROR", 
                                   texto = "No se pudo eliminar. Verifique que no esté implicado en otras operaciones.\n\nTexto de depuración:\n%s" % msg, 
                                   padre = self.wids['ventana'])
        if paths:
            self.rellenar_enmiendas()

    def drop_fitosanitario(self, boton):
        selection = self.wids['tv_fitosanitarios'].get_selection()
        model, paths = selection.get_selected_rows()
        for path in paths:
            pcid = model[path][-1]
            pc = pclases.Fitosanitario.get(pcid)
            try:
                pc.destroySelf()
            except Exception, msg:
                utils.dialogo_info(titulo = "ERROR", 
                                   texto = "No se pudo eliminar. Verifique que no esté implicado en otras operaciones.\n\nTexto de depuración:\n%s" % msg, 
                                   padre = self.wids['ventana'])
        if paths:
            self.rellenar_fitosanitarios()

    def __build_dic_campos(self):
        """
        Devuelve un diccionario de campos de la clase de pclases y 
        su widget relacionado.
        El widget y el atributo deben llamarse igual, o en todo caso
        ser del tipo "e_nombre", "cb_nombre", etc.
        Los atributos para los que no se encuentre widget en el glade
        se ignorarán (cuando se adapten mediante el módulo adapter se
        les creará un widget apropiado a estas columnas ignoradas aquí).
        """
        res = {}
        for colname in self.clase.sqlmeta.columns:
            col = self.clase.sqlmeta.columns[colname]
            for widname_glade in self.wids.keys():
                if "_" in widname_glade:
                    widname = widname_glade.split("_")[-1]
                else:
                    widname = widname_glade
                if widname == colname:
                    w = self.wids[widname_glade]
                    res[col] = w
        return res

    def es_diferente(self):
        """
        Devuelve True si algún valor en ventana difiere de 
        los del objeto.
        """
        if self.objeto == None:
            igual = True
        else:
            adaptadores = self.adaptador.get_adaptadores()
            igual = self.objeto != None
            for col in adaptadores:
                fcomp = adaptadores[col]['comparar']
                igual = igual and fcomp(self.objeto)
                if not igual:
                    if DEBUG:
                        print col.name, 
                        en_pantalla = adaptadores[col]['leer']()
                        en_objeto = getattr(self.objeto, col.name)
                        print "En pantalla:", en_pantalla, type(en_pantalla),
                        print "En objeto:", en_objeto, type(en_objeto), 
                        print fcomp(self.objeto)
                    break
        return not igual
    
    def inicializar_ventana(self):
        """
        Inicializa los controles de la ventana, estableciendo sus
        valores por defecto, deshabilitando los innecesarios,
        rellenando los combos, formateando el TreeView -si lo hay-...
        """
        # Inicialmente no se muestra NADA. Sólo se le deja al
        # usuario la opción de buscar o crear nuevo.
        self.activar_widgets(False)
        self.wids['b_actualizar'].set_sensitive(False)
        self.wids['b_guardar'].set_sensitive(False)
        self.wids['b_nuevo'].set_sensitive(True)
        self.wids['b_buscar'].set_sensitive(True)
        self.wids['ventana'].set_title(self.clase.sqlmeta.table.upper())
        # Inicialización del resto de widgets:
        camps = [(c.id, "%s - %s" % (utils.str_fecha(c.fechaInicio),
                                     utils.str_fecha(c.fechaFin)))
                 for c in pclases.Campanna.select(orderBy = "fechaInicio")]
        utils.rellenar_lista(self.wids['cb_campanna'], camps)
        cols = (('Fecha', 'gobject.TYPE_STRING', True, True, True, 
                    self.editar_fecha_practica_cutural),
                ('Práctica', 'gobject.TYPE_STRING', True, True, False, 
                    self.editar_practica_practica_cutural), 
                ('Maquinaria', 'gobject.TYPE_STRING', True, True, False, 
                    self.editar_maquinaria_practica_cutural), 
                ('Observaciones', 'gobject.TYPE_STRING', True, True, False, 
                    self.editar_observaciones_practica_cutural), 
                ('ID', 'gobject.TYPE_INT64', False, False, False, None))
                # La última columna (oculta en la Vista) siempre es el id.
        utils.preparar_listview(self.wids['tv_cuturales'], cols, True)
        cols = (('Cultivo', 'gobject.TYPE_STRING', True, True, True, 
                    self.editar_cultivo_cultivo),
                ('Variedad', 'gobject.TYPE_STRING', True, True, False, 
                    self.editar_variedad_cultivo), 
                ('Siembra', 'gobject.TYPE_STRING', True, True, False, 
                    self.editar_siembra_cultivo), 
                ('Inicio recolección','gobject.TYPE_STRING', True, True, False, 
                    self.editar_recoleccion_ini_cultivo), 
                ('Fin recolección', 'gobject.TYPE_STRING', True, True, False, 
                    self.editar_recoleccion_fin_cultivo), 
                ('Hidropónico', 'gobject.TYPE_BOOLEAN', True, True, False, 
                    self.editar_hidroponico_cultivo), 
                ('Tradicional', 'gobject.TYPE_BOOLEAN', True, True, False, 
                    self.editar_tradicional_cultivo), 
                ('ID', 'gobject.TYPE_INT64', False, False, False, None))
                # La última columna (oculta en la Vista) siempre es el id.
        utils.preparar_listview(self.wids['tv_cultivos'], cols, True)
        cols = (("Materia activa", "gobject.TYPE_STRING", True, True, True, 
                    self.editar_materia_activa_fert), 
                ("Nombre", "gobject.TYPE_STRING", True, True, False, 
                    self.editar_nombre_fert), 
                ("Listado", "gobject.TYPE_BOOLEAN", True, True, False, 
                    self.editar_listado_fert), 
                ("Otros", "gobject.TYPE_BOOLEAN", True, True, False, 
                    self.editar_otros_fert), 
                ("Fecha", "gobject.TYPE_STRING", True, True, False, 
                    self.editar_fecha_fert), 
                ("Plazo seguridad", "gobject.TYPE_INT", True, True, False, 
                    self.editar_plazo_fert), 
                ("Dosis", "gobject.TYPE_STRING", True, True, False, 
                    self.editar_dosis_fert), 
                ("Observaciones", "gobject.TYPE_STRING", True, True, False, 
                    self.editar_observaciones_fert), 
                ('ID', 'gobject.TYPE_INT64', False, False, False, None))
        utils.preparar_listview(self.wids['tv_fertilizaciones'], cols, True)
        self.cambiar_por_combo(self.wids['tv_fertilizaciones'], 0)
        cols = (("Materia activa", "gobject.TYPE_STRING", True, True, True, 
                    self.editar_materia_activa_enmi), 
                ("Nombre", "gobject.TYPE_STRING", True, True, False, 
                    self.editar_nombre_enmi), 
                ("Listado", "gobject.TYPE_BOOLEAN", True, True, False, 
                    self.editar_listado_enmi), 
                ("Otros", "gobject.TYPE_BOOLEAN", True, True, False, 
                    self.editar_otros_enmi), 
                ("Fecha", "gobject.TYPE_STRING", True, True, False, 
                    self.editar_fecha_enmi), 
                ("Plazo seguridad", "gobject.TYPE_INT", True, True, False, 
                    self.editar_plazo_enmi), 
                ("Dosis", "gobject.TYPE_STRING", True, True, False, 
                    self.editar_dosis_enmi), 
                ("Observaciones", "gobject.TYPE_STRING", True, True, False, 
                    self.editar_observaciones_enmi), 
                ('ID', 'gobject.TYPE_INT64', False, False, False, None))
        utils.preparar_listview(self.wids['tv_enmiendas'], cols, True)
        self.cambiar_por_combo(self.wids['tv_enmiendas'], 0)
        cols = (("Materia activa", "gobject.TYPE_STRING", True, True, True, 
                    self.editar_materia_activa_fito), 
                ("Nombre", "gobject.TYPE_STRING", True, True, False, 
                    self.editar_nombre_fito), 
                ("Listado", "gobject.TYPE_BOOLEAN", True, True, False, 
                    self.editar_listado_fito), 
                ("Otros", "gobject.TYPE_BOOLEAN", True, True, False, 
                    self.editar_otros_fito), 
                ("Fecha", "gobject.TYPE_STRING", True, True, False, 
                    self.editar_fecha_fito), 
                ("Plazo seguridad", "gobject.TYPE_INT", True, True, False, 
                    self.editar_plazo_fito), 
                ("Dosis", "gobject.TYPE_STRING", True, True, False, 
                    self.editar_dosis_fito), 
                ("Observaciones", "gobject.TYPE_STRING", True, True, False, 
                    self.editar_observaciones_fito), 
                ('ID', 'gobject.TYPE_INT64', False, False, False, None))
        utils.preparar_listview(self.wids['tv_fitosanitarios'], cols, True)
        self.cambiar_por_combo(self.wids['tv_fitosanitarios'], 0)

    def editar_materia_activa_fert(self, cell, path, text):
        editar_texto_tv(self.wids['tv_fertilizaciones'], 
                        pclases.Fertilizacion, 
                        "materiaActiva", 
                        text, 
                        path, 
                        0)

    def editar_nombre_fert(self, cell, path, text):
        editar_texto_tv(self.wids['tv_fertilizaciones'], 
                        pclases.Fertilizacion, 
                        "nombre", 
                        text, 
                        path, 
                        1)

    def editar_listado_fert(self, cell, path):
        editar_bool_tv(self.wids['tv_fertilizaciones'], 
                       pclases.Fertilizacion, 
                       "listado", 
                       cell, 
                       path, 
                       2)

    def editar_otros_fert(self, cell, path):
        editar_bool_tv(self.wids['tv_fertilizaciones'], 
                       pclases.Fertilizacion, 
                       "otros", 
                       cell, 
                       path, 
                       3)

    def editar_fecha_fert(self, cell, path, text):
        editar_fecha_tv(self.wids['tv_fertilizaciones'], 
                        pclases.Fertilizacion, 
                        "fecha", 
                        text, 
                        path, 
                        4)

    def editar_plazo_fert(self, cell, path, text):
        editar_entero_tv(self.wids['tv_fertilizaciones'], 
                         pclases.Fertilizacion, 
                         "plazo", 
                         text, 
                         path, 
                         5)

    def editar_dosis_fert(self, cell, path, text):
        editar_float_tv(self.wids['tv_fertilizaciones'], 
                        pclases.Fertilizacion, 
                        "dosis", 
                        text, 
                        path, 
                        6)

    def editar_observaciones_fert(self, cell, path, text):
        editar_texto_tv(self.wids['tv_fertilizaciones'], 
                        pclases.Fertilizacion, 
                        "observaciones", 
                        text, 
                        path, 
                        7)

    def editar_materia_activa_enmi(self, cell, path, text):
        editar_texto_tv(self.wids['tv_enmiendas'], 
                        pclases.Enmienda, 
                        "materiaActiva", 
                        text, 
                        path, 
                        0)

    def editar_nombre_enmi(self, cell, path, text):
        editar_texto_tv(self.wids['tv_enmiendas'], 
                        pclases.Enmienda, 
                        "nombre", 
                        text, 
                        path, 
                        1)

    def editar_listado_enmi(self, cell, path):
        editar_bool_tv(self.wids['tv_enmiendas'], 
                       pclases.Enmienda, 
                       "listado", 
                       cell, 
                       path, 
                       2)

    def editar_otros_enmi(self, cell, path):
        editar_bool_tv(self.wids['tv_enmiendas'], 
                       pclases.Enmienda, 
                       "otros", 
                       cell, 
                       path, 
                       3)

    def editar_fecha_enmi(self, cell, path, text):
        editar_fecha_tv(self.wids['tv_enmiendas'], 
                        pclases.Enmienda, 
                        "fecha", 
                        text, 
                        path, 
                        4)

    def editar_plazo_enmi(self, cell, path, text):
        editar_entero_tv(self.wids['tv_enmiendas'], 
                         pclases.Enmienda, 
                         "plazo", 
                         text, 
                         path, 
                         5)

    def editar_dosis_enmi(self, cell, path, text):
        editar_float_tv(self.wids['tv_enmiendas'], 
                        pclases.Enmienda, 
                        "dosis", 
                        text, 
                        path, 
                        6)

    def editar_observaciones_enmi(self, cell, path, text):
        editar_texto_tv(self.wids['tv_enmiendas'], 
                        pclases.Enmienda, 
                        "observaciones", 
                        text, 
                        path, 
                        7)

    def editar_materia_activa_fito(self, cell, path, text):
        editar_texto_tv(self.wids['tv_fitosanitarios'], 
                        pclases.Fitosanitario, 
                        "materiaActiva", 
                        text, 
                        path, 
                        0)

    def editar_nombre_fito(self, cell, path, text):
        editar_texto_tv(self.wids['tv_fitosanitarios'], 
                        pclases.Fitosanitario, 
                        "nombre", 
                        text, 
                        path, 
                        1)

    def editar_listado_fito(self, cell, path):
        editar_bool_tv(self.wids['tv_fitosanitarios'], 
                       pclases.Fitosanitario, 
                       "listado", 
                       cell, 
                       path, 
                       2)

    def editar_otros_fito(self, cell, path):
        editar_bool_tv(self.wids['tv_fitosanitarios'], 
                       pclases.Fitosanitario, 
                       "otros", 
                       cell, 
                       path, 
                       3)

    def editar_fecha_fito(self, cell, path, text):
        editar_fecha_tv(self.wids['tv_fitosanitarios'], 
                        pclases.Fitosanitario, 
                        "fecha", 
                        text, 
                        path, 
                        4)

    def editar_plazo_fito(self, cell, path, text):
        editar_entero_tv(self.wids['tv_fitosanitarios'], 
                         pclases.Fitosanitario, 
                         "plazo", 
                         text, 
                         path, 
                         5)

    def editar_dosis_fito(self, cell, path, text):
        editar_float_tv(self.wids['tv_fitosanitarios'], 
                        pclases.Fitosanitario, 
                        "dosis", 
                        text, 
                        path, 
                        6)

    def editar_observaciones_fito(self, cell, path, text):
        editar_texto_tv(self.wids['tv_fitosanitarios'], 
                        pclases.Fitosanitario, 
                        "observaciones", 
                        text, 
                        path, 
                        7)

    def editar_fecha_practica_cutural(self, cell, path, text):
        try:
            nueva_fecha = utils.parse_fecha(text)
        except (ValueError, TypeError):
            utils.dialogo_info(titulo = "ERROR DE FORMATO", 
                               texto = "El texto %s no es una fecha correcta." % text, 
                               padre = self.wids['ventana'])
        else:
            model = self.wids['tv_cuturales'].get_model()
            pc = pclases.PracticaCutural.get(model[path][-1])
            pc.fecha = nueva_fecha
            model[path][0] = utils.str_fecha(pc.fecha)

    def editar_practica_practica_cutural(self, cell, path, text):
        model = self.wids['tv_cuturales'].get_model()
        pc = pclases.PracticaCutural.get(model[path][-1])
        pc.practica = text
        model[path][1] = pc.practica

    def editar_maquinaria_practica_cutural(self, cell, path, text):
        model = self.wids['tv_cuturales'].get_model()
        pc = pclases.PracticaCutural.get(model[path][-1])
        pc.maquinaria = text
        model[path][2] = pc.maquinaria

    def editar_observaciones_practica_cutural(self, cell, path, text):
        model = self.wids['tv_cuturales'].get_model()
        pc = pclases.PracticaCutural.get(model[path][-1])
        pc.observaciones = text
        model[path][3] = pc.observaciones

    def editar_cultivo_cultivo(self, cell, path, text):
        model = self.wids['tv_cultivos'].get_model()
        c = pclases.Cultivo.get(model[path][-1])
        c.cultivo = text
        model[path][0] = c.cultivo

    def editar_variedad_cultivo(self, cell, path, text):
        model = self.wids['tv_cultivos'].get_model()
        c = pclases.Cultivo.get(model[path][-1])
        c.variedad = text
        model[path][1] = c.variedad

    def editar_siembra_cultivo(self, cell, path, text):
        try:
            nueva_fecha = utils.parse_fecha(text)
        except (ValueError, TypeError):
            utils.dialogo_info(titulo = "ERROR DE FORMATO", 
                               texto = "El texto %s no es una fecha correcta." % text, 
                               padre = self.wids['ventana'])
        else:
            model = self.wids['tv_cultivos'].get_model()
            c = pclases.Cultivo.get(model[path][-1])
            c.siembra = nueva_fecha
            model[path][2] = utils.str_fecha(c.siembra)

    def editar_recoleccion_ini_cultivo(self, cell, path, text):
        try:
            nueva_fecha = utils.parse_fecha(text)
        except (ValueError, TypeError):
            utils.dialogo_info(titulo = "ERROR DE FORMATO", 
                               texto = "El texto %s no es una fecha correcta." % text, 
                               padre = self.wids['ventana'])
        else:
            model = self.wids['tv_cultivos'].get_model()
            c = pclases.Cultivo.get(model[path][-1])
            c.recoleccionInicio = nueva_fecha
            model[path][3] = utils.str_fecha(c.recoleccionInicio)

    def editar_recoleccion_fin_cultivo(self, cell, path, text):
        try:
            nueva_fecha = utils.parse_fecha(text)
        except (ValueError, TypeError):
            utils.dialogo_info(titulo = "ERROR DE FORMATO", 
                               texto = "El texto %s no es una fecha correcta." % text, 
                               padre = self.wids['ventana'])
        else:
            model = self.wids['tv_cultivos'].get_model()
            c = pclases.Cultivo.get(model[path][-1])
            c.recoleccionFin = nueva_fecha
            model[path][4] = utils.str_fecha(c.recoleccionFin)

    def editar_hidroponico_cultivo(self, cell, path):
        model = self.wids['tv_cultivos'].get_model()
        c = pclases.Cultivo.get(model[path][-1])
        c.hidroponico = not cell.get_active()
        model[path][5] = c.hidroponico

    def editar_tradicional_cultivo(self, cell, path):
        model = self.wids['tv_cultivos'].get_model()
        c = pclases.Cultivo.get(model[path][-1])
        c.tradicional = not cell.get_active()
        model[path][6] = c.tradicional

    def rellenar_tablas(self, cb):
        """
        Rellena las tablas de cultivos y prácticas cuturales; que son 
        los únicos datos de la ventana que dependen de la campaña seleccionada 
        además de de la parcela en sí.
        """
        self.rellenar_practicas_cuturales()
        self.rellenar_cultivos()
        self.rellenar_fertilizaciones()
        self.rellenar_enmiendas()
        self.rellenar_fitosanitarios()

    def rellenar_practicas_cuturales(self):
        model = self.wids['tv_cuturales'].get_model()
        model.clear()
        for p in self.objeto.practicasCuturales:
            model.append((utils.str_fecha(p.fecha), 
                          p.practica, 
                          p.maquinaria, 
                          p.observaciones, 
                          p.id))
    
    def rellenar_fertilizaciones(self):
        model = self.wids['tv_fertilizaciones'].get_model()
        model.clear()
        for c in self.objeto.fertilizaciones:
            model.append((
                c.materiaActiva, 
                c.nombre, 
                c.listado, 
                c.otros, 
                utils.str_fecha(c.fecha), 
                c.plazoSeguridad, 
                utils.float2str(c.dosis), 
                c.observaciones, 
                c.id))
 
    def rellenar_enmiendas(self):
        model = self.wids['tv_enmiendas'].get_model()
        model.clear()
        for c in self.objeto.enmiendas:
            model.append((
                c.materiaActiva, 
                c.nombre, 
                c.listado, 
                c.otros, 
                utils.str_fecha(c.fecha), 
                c.plazoSeguridad, 
                utils.float2str(c.dosis), 
                c.observaciones, 
                c.id))

    def rellenar_fitosanitarios(self):
        model = self.wids['tv_fitosanitarios'].get_model()
        model.clear()
        for c in self.objeto.fitosanitarios:
            model.append((
                c.materiaActiva, 
                c.nombre, 
                c.listado, 
                c.otros, 
                utils.str_fecha(c.fecha), 
                c.plazoSeguridad, 
                utils.float2str(c.dosis), 
                c.observaciones, 
                c.id))
    
    def rellenar_cultivos(self):
        model = self.wids['tv_cultivos'].get_model()
        model.clear()
        for p in self.objeto.cultivos:
            model.append((p.cultivo, 
                          p.variedad, 
                          utils.str_fecha(p.siembra), 
                          utils.str_fecha(p.recoleccionInicio), 
                          utils.str_fecha(p.recoleccionFin), 
                          p.hidroponico, 
                          p.tradicional, 
                          p.id))

    def activar_widgets(self, s, chequear_permisos = True):
        """
        Activa o desactiva (sensitive=True/False) todos 
        los widgets de la ventana que dependan del 
        objeto mostrado.
        Entrada: s debe ser True o False. En todo caso
        se evaluará como boolean.
        """
        if self.objeto == None:
            s = False
        ws = (["b_borrar"] + 
              [self.adaptador.get_adaptadores()[col]['widget'].name 
               for col in self.adaptador.get_adaptadores().keys()])
            # b_nuevo y b_buscar no se activan/desactivan aquí, sino en el
            # chequeo de permisos.
        ws.remove("rutaPlano")
        for w in ws:
            try:
                self.wids[w].set_sensitive(s)
            except Exception, msg:
                print "Widget problemático:", w, "Excepción:", msg
                #import traceback
                #traceback.print_last()
        if chequear_permisos:
            self.check_permisos(nombre_fichero_ventana = "parcelas.py")
        # OJO: De momento el alto no se usa. Ver produccion_por_parcela.py
        self.wids['reprAlto'].set_sensitive(False)

    def refinar_resultados_busqueda(self, resultados):
        """
        Muestra en una ventana de resultados todos los
        registros de "resultados".
        Devuelve el id (primera columna de la ventana
        de resultados) de la fila seleccionada o None
        si se canceló.
        """
        filas_res = []
        for r in resultados:
            filas_res.append((r.id, r.parcela, r.sectorDeRiego, r.superficie, 
                        r.finca and r.finca.nombre or "¡Sin finca asignada!"))
        id = utils.dialogo_resultado(filas_res,
                                     titulo = 'SELECCIONE %s' % (
                                        self.clase.sqlmeta.table.upper()),
                                     cabeceras = ('ID', 
                                                  'Parcela', 
                                                  'Sector de riego', 
                                                  'Superficie', 
                                                  'Finca'), 
                                     padre = self.wids['ventana'])
        if id < 0:
            return None
        else:
            return id

    def rellenar_widgets(self):
        """
        Introduce la información de la cuenta actual
        en los widgets.
        No se chequea que sea != None, así que
        hay que tener cuidado de no llamar a 
        esta función en ese caso.
        """
        adaptadores = self.adaptador.get_adaptadores()
        for col in adaptadores.keys():
            adaptadores[col]['mostrar'](self.objeto)
        self.objeto.mostrar_imagen_en(self.wids['plano'], MAX = 200)
        self.objeto.make_swap()
        self.wids['ventana'].set_title(self.objeto.get_info())
        # Por defecto pongo la campaña que coincida con la fecha actual (si 
        # la hay, la primera que encuentre) como campaña activa.
        hoy = mx.DateTime.localtime()
        campannas = pclases.Campanna.select(pclases.AND(
            pclases.Campanna.q.fechaInicio <= hoy, 
            pclases.Campanna.q.fechaFin >= hoy))
        if campannas.count():
            campanna = campannas[0]
            utils.combo_set_from_db(self.wids['cb_campanna'], campanna.id)
            # HACK: WORKAROUND: Debería lanzarse él solito con el changed 
            #                   del combo...
            self.rellenar_tablas(self.wids['cb_campanna'])

    def nuevo(self, widget):
        """
        Función callback del botón b_nuevo.
        Pide los datos básicos para crear un nuevo objeto.
        Una vez insertado en la BD hay que hacerlo activo
        en la ventana para que puedan ser editados el resto
        de campos que no se hayan pedido aquí.
        """
        fincas = [(f.id, f.nombre) 
                  for f in pclases.Finca.select(orderBy = "nombre")]
        idfinca = utils.dialogo_combo(titulo = "SELECCIONE FINCA",
                                      texto = "Seleccione la finca a la que pertenece la nueva parcela:", 
                                      ops = fincas, 
                                      padre = self.wids['ventana'])
        if idfinca != None:
            objeto_anterior = self.objeto
            if objeto_anterior != None:
                objeto_anterior.notificador.desactivar()
            self.objeto = self.clase(fincaID = idfinca) 
            self.objeto.notificador.activar(self.aviso_actualizacion)
            self._objetoreciencreado = self.objeto
            self.activar_widgets(True)
            self.actualizar_ventana(objeto_anterior = objeto_anterior)
            utils.dialogo_info('NUEVO %s CREADO' % self.clase.sqlmeta.table.upper(), 
                               'Se ha creado un nuevo %s.\nA continuación complete la información del misma y guarde los cambios.' % self.clase.sqlmeta.table.lower(), 
                               padre = self.wids['ventana'])

    def buscar(self, widget):
        """
        Muestra una ventana de búsqueda y a continuación los
        resultados. El objeto seleccionado se hará activo
        en la ventana a no ser que se pulse en Cancelar en
        la ventana de resultados.
        """
        a_buscar = utils.dialogo_entrada(titulo = "BUSCAR %s" % self.clase.sqlmeta.table.upper(), 
                                         texto = "Introduzca parcela o sector de riego:", 
                                         padre = self.wids['ventana']) 
        if a_buscar != None:
            try:
                ida_buscar = int(a_buscar)
            except ValueError:
                ida_buscar = -1
            campos_busqueda = (self.clase.q.parcela, self.clase.q.sectorDeRiego)
            subsubcriterios = []
            for cb in campos_busqueda:
                ssc = [cb.contains(t) for t in a_buscar.split()]
                if ssc:
                    subsubcriterios.append(pclases.AND(*ssc))
                else:
                    subsubcriterios.append(cb.contains(a_buscar))
            if len(subsubcriterios) > 1:
                subcriterios = pclases.OR(*subsubcriterios)
            else:
                subcriterios = subsubcriterios
            criterio = pclases.OR(subcriterios, 
                                  self.clase.q.id == ida_buscar)
            resultados = self.clase.select(criterio)
            if resultados.count() > 1:
                ## Refinar los resultados
                id = self.refinar_resultados_busqueda(resultados)
                if id == None:
                    return
                resultados = [self.clase.get(id)]
                # Me quedo con una lista de resultados de un único objeto 
                # ocupando la primera posición.
                # (Más abajo será cuando se cambie realmente el objeto actual 
                # por este resultado.)
            elif resultados.count() < 1:
                ## Sin resultados de búsqueda
                utils.dialogo_info(titulo = 'SIN RESULTADOS', 
                                   texto = 'La búsqueda no produjo resultados.\nPruebe a cambiar el texto buscado o déjelo en blanco para ver una lista completa.\n(Atención: Ver la lista completa puede resultar lento si el número de elementos es muy alto)',
                                   padre = self.wids['ventana'])
                return
            ## Un único resultado
            # Primero anulo la función de actualización
            if self.objeto != None:
                self.objeto.notificador.desactivar()
            # Pongo el objeto como actual
            try:
                self.objeto = resultados[0]
            except IndexError:
                utils.dialogo_info(titulo = "ERROR", 
                                   texto = "Se produjo un error al recuperar la información.\nCierre y vuelva a abrir la ventana antes de volver a intentarlo.", 
                                   padre = self.wids['texto'])
                return
            # Y activo la función de notificación:
            self.objeto.notificador.activar(self.aviso_actualizacion)
            self.activar_widgets(True)
        self.actualizar_ventana()

    def guardar(self, widget):
        """
        Guarda el contenido de los entry y demás widgets de entrada
        de datos en el objeto y lo sincroniza con la BD.
        """
        # Desactivo el notificador momentáneamente
        self.objeto.notificador.desactivar()
        # Actualizo los datos del objeto
        adaptadores = self.adaptador.get_adaptadores()
        for col in adaptadores:
            setattr(self.objeto, col.name, adaptadores[col]['leer']())
        # Fuerzo la actualización de la BD y no espero a que SQLObject 
        # lo haga por mí:
        self.objeto.syncUpdate()
        self.objeto.sync()
        # Vuelvo a activar el notificador
        self.objeto.notificador.activar(self.aviso_actualizacion)
        self.actualizar_ventana()
        self.wids['b_guardar'].set_sensitive(False)

    def borrar(self, widget):
        """
        Elimina la cuenta de la tabla pero NO
        intenta eliminar ninguna de sus relaciones,
        de forma que si se incumple alguna 
        restricción de la BD, cancelará la eliminación
        y avisará al usuario.
        """
        if not utils.dialogo('¿Está completamente seguro de querer eliminar %s?' % self.clase.sqlmeta.table.lower(), 
                             'BORRAR', 
                             padre = self.wids['ventana']):
            return
        self.objeto.notificador.desactivar()
        try:
            #self.objeto.destroySelf()
            self.objeto.destroy_en_cascada()
        except Exception, e:
            self.logger.error("pacelas.py::borrar -> %s ID %d no se pudo eliminar. Excepción: %s." % (self.objeto.sqlmeta.table, self.objeto.id, e))
            utils.dialogo_info(titulo = "%s NO BORRADO" % self.clase.sqlmeta.table.upper(), 
                               texto = "%s no se pudo eliminar.\n\nSe generó un informe de error en el «log» de la aplicación." % self.clase.sqlmeta.table.title(),
                               padre = self.wids['ventana'])
            self.actualizar_ventana()
            return
        self.objeto = None
        self.ir_a_primero()


def editar_fecha_tv(w, clase, campo, text, path, col):
    """
    Parsea la fecha y cambia el valor del objeto de la fila del treeview y 
    muestra el cambio en la capa vista del mismo.
    """
    try:
        nueva_fecha = utils.parse_fecha(text)
    except (ValueError, TypeError):
        utils.dialogo_info(titulo = "ERROR DE FORMATO", 
                           texto = "El texto %s no es una fecha correcta." % text) 
    else:
        model = w.get_model()
        o = clase.get(model[path][-1])
        setattr(o, campo, nueva_fecha)
        model[path][col] = utils.str_fecha(getattr(o, campo))

def editar_texto_tv(w, clase, campo, text, path, col):
    """
    Cambia el texto del campo del objeto de la fila y lo 
    muestra de nuevo en la columna del treeview.
    """
    model = w.get_model()
    o = clase.get(model[path][-1])
    setattr(o, campo, text)
    model[path][col] = getattr(o, campo)

def editar_bool_tv(w, clase, campo, cell, path, col):
    """
    Cambia de valor el cell y del objeto de la fila del path del TreeView.
    """
    model = w.get_model()
    c = clase.get(model[path][-1])
    setattr(c, campo, not cell.get_active())
    model[path][col] = getattr(c, campo)

def editar_entero_tv(w, clase, campo, text, path, col):
    try:
        numero = utils.parse_numero(text)
        if numero == None:
            raise ValueError
    except (ValueError, TypeError):
        utils.dialogo_info(titulo = "ERROR DE FORMATO", 
                           texto = "El texto %s no es un número entero." % text)
    else:
        model = w.get_model()
        o = clase.get(model[path][-1])
        setattr(o, campo, numero)
        model[path][col] = getattr(o, campo)

def editar_float_tv(w, clase, campo, text, path, col):
    try:
        numero = utils._float(text)
    except (ValueError, TypeError):
        utils.dialogo_info(titulo = "ERROR DE FORMATO", 
                           texto = "El texto %s no es un número." % text) 
    else:
        model = w.get_model()
        o = clase.get(model[path][-1])
        setattr(o, campo, numero)
        model[path][col] = utils.float2str(getattr(o, campo))


if __name__ == "__main__":
    p = Parcelas()

