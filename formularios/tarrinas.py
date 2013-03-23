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
## tarrinas.py - Tarrinas para fruta no a granel.
###################################################################
## NOTAS:
##  Usar ESTA ventana a partir de ahora para crear nuevas.
##  Hereda de ventana y ventana genérica, y la mayoría de funciones
##  están automatizadas partiendo tan solo de la clase y un 
##  diccionario que empareje widgets y atributos.
## ----------------------------------------------------------------
##  
###################################################################
## Changelog:
## 17 de diciembre de 2007 -> Inicio
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

class Tarrinas(Ventana, VentanaGenerica):
    CLASE = pclases.Tarrina
    VENTANA = os.path.join("..", "ui", "tarrinas.ui")
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
                       'b_add_empaquetado/clicked': self.add_empaquetado, 
                       'b_drop_empaquetado/clicked': self.drop_empaquetado
                      }
        self.add_connections(connections)
        self.inicializar_ventana()
        if self.objeto == None:
            self.ir_a_primero()
        else:
            self.ir_a(objeto)
        gtk.main()

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
        cols = (('Envase', 'gobject.TYPE_STRING', False, True, True, None),
                ('Cantidad', 'gobject.TYPE_INT', True, True, True, 
                    self.cambiar_cantidad_envase),
                ('Capacidad total (kg)', 'gobject.TYPE_STRING', 
                    False, True, False, None), 
                ('ID', 'gobject.TYPE_INT64', False, False, False, None))
                # La última columna (oculta en la Vista) siempre es el id.
        utils.preparar_listview(self.wids['tv_empaquetado'], cols, multi=True)
        self.wids['tv_empaquetado'].connect("row-activated", self.abrir_envase)

    def abrir_envase(self, tv, path, col):
        id = tv.get_model()[path][-1]
        empaquetado = pclases.Empaquetado.get(id)
        envase = empaquetado.envase
        import envases
        w = envases.Envases(objeto = envase, usuario = self.usuario)

    def cambiar_cantidad_envase(self, cell, path, text):
        """
        Cambia la cantidad de tarrinas contenidas en la configuración de 
        envase.
        """
        try:
            cantidad = int(utils._float(text))
        except (ValueError, TypeError):
            utils.dialogo_info(titulo = "ERROR DE FORMATO", 
                               texto = "El texto %s no es un número." % text, 
                               padre = self.wids['ventana'])
        else:
            model = self.wids['tv_empaquetado'].get_model()
            id = model[path][-1]
            try:
                empaquetado = pclases.Empaquetado.get(id)
            except:
                utils.dialogo_info(titulo = "ERROR EMPAQUIETADO", 
                                   texto = "La configuración de empaquetado "
                                           "no existe. Recargue la ventana.", 
                                   padre = self.wids['ventana'])
            else:
                empaquetado.cantidad = cantidad
                empaquetado.syncUpdate()
                model[path][1] = empaquetado.cantidad
                model[path][2] = utils.float2str(
                    empaquetado.calcular_capacidad_total())

    def add_empaquetado(self, boton):
        # 1.- Pedir envase.
        envases = [(e.id, "%s (%s kg)" % (e.nombre, utils.float2str(e.kg)))
                   for e in pclases.Envase.select(orderBy = "nombre")]
        idenvase = utils.dialogo_combo("ENVASE", 
            "Seleccione un envase:", 
            envases, 
            padre = self.wids['ventana'])
        # 2.- Crear registro.
        if idenvase:
            envase = pclases.Envase.get(idenvase)
            tarrina = self.objeto
            empaquetado = pclases.Empaquetado(envase = envase, 
                                              tarrina = tarrina, 
                                              cantidad = 1)
        # 3.- Actualizar treeview.
            self.rellenar_tabla_empaquetado()
        
    def drop_empaquetado(self, boton):
        sel = self.wids['tv_empaquetado'].get_selection()
        model, paths = sel.get_selected_rows()
        errores = []
        for p in paths:
            id = model[p][-1]
            e = pclases.Empaquetado.get(id)
            try:
                e.destroySelf()
            except: 
                errores.append(e)
        self.rellenar_tabla_empaquetado()
        if errores:
            utils.dialogo_info(titulo = "ERRORES AL ELIMINAR", 
                texto = "Ocurrieron errores al eliminar las configuraciones "
                        "de envasado.", 
                padre = self.wids['ventana'])

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
        #ws = tuple(["XXXWidgets_que_no_tengan_«adaptador»_en_el_diccionario_del_constructor", "XXXtv_treeview", "b_borrar"] + [self.dic_campos[k] for k in self.dic_campos.keys()])
        ws = tuple(["b_borrar"] + 
                   [self.adaptador.get_adaptadores()[col]['widget'].name 
                    for col in self.adaptador.get_adaptadores().keys()])
            # b_nuevo y b_buscar no se activan/desactivan aquí, sino en el
            # chequeo de permisos.
        for w in ws:
            try:
                self.wids[w].set_sensitive(s)
            except Exception, msg:
                print "Widget problemático:", w, "Excepción:", msg
                #import traceback
                #traceback.print_last()
        if chequear_permisos:
            self.check_permisos(nombre_fichero_ventana = "tarrinas.py")

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
            filas_res.append((r.id, r.nombre, r.gr, r.existencias))
        id = utils.dialogo_resultado(filas_res,
                titulo = 'SELECCIONE %s' % self.clase.sqlmeta.table.upper(),
                cabeceras = ('ID', 'Nombre', 'Gramos', 'Existencias'), 
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
        self.rellenar_tabla_empaquetado()
        self.objeto.make_swap()
        self.wids['ventana'].set_title(self.objeto.get_info())

    def rellenar_tabla_empaquetado(self):
        model = self.wids['tv_empaquetado'].get_model()
        model.clear()
        for p in self.objeto.empaquetados:
            model.append((p.envase and p.envase.nombre 
                            or "Pendiente de definir", 
                          p.cantidad, 
                          utils.float2str(p.calcular_capacidad_total()), 
                          p.id))
            
    def nuevo(self, widget):
        """
        Función callback del botón b_nuevo.
        Pide los datos básicos para crear un nuevo objeto.
        Una vez insertado en la BD hay que hacerlo activo
        en la ventana para que puedan ser editados el resto
        de campos que no se hayan pedido aquí.
        """
        objeto_anterior = self.objeto
        if objeto_anterior != None:
            objeto_anterior.notificador.desactivar()
        self.objeto = self.clase()  
        # XXX: Probablemente pete si no tiene suficientes valores por defecto.
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
        a_buscar = utils.dialogo_entrada(titulo = "BUSCAR %s" 
                            % self.clase.sqlmeta.table.upper(), 
                         texto = "Introduzca nombre o capacidad en gramos:", 
                         padre = self.wids['ventana']) 
        if a_buscar != None:
            try:
                ida_buscar = int(a_buscar)
            except ValueError:
                ida_buscar = -1
            campos_busqueda = (self.clase.q.nombre, self.clase.q.gr)
            subsubcriterios = []
            sqlower = pclases.sqlbuilder.func.lower
            for cb in campos_busqueda:
                ssc = [sqlower(cb).contains(t.lower()) 
                        for t in a_buscar.split()]
                if ssc:
                    subsubcriterios.append(pclases.AND(*ssc))
                else:
                    subsubcriterios.append(
                        sqlower(cb).contains(a_buscar.lower()))
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
        if not utils.dialogo('¿Eliminar %s?' % self.clase.sqlmeta.table.lower(), 
                             'BORRAR', 
                             padre = self.wids['ventana']):
            return
        self.objeto.notificador.desactivar()
        try:
            self.objeto.destroySelf()
        except Exception, e:
            self.logger.error("tarrinas.py::borrar -> %s ID %d no se pudo eliminar. Excepción: %s." % (self.objeto.sqlmeta.table, self.objeto.id, e))
            utils.dialogo_info(titulo = "%s NO BORRADO" % self.clase.sqlmeta.table.upper(), 
                               texto = "%s no se pudo eliminar.\n\nSe generó un informe de error en el «log» de la aplicación." % self.clase.sqlmeta.table.title(),
                               padre = self.wids['ventana'])
            self.actualizar_ventana()
            return
        self.objeto = None
        self.ir_a_primero()

if __name__ == "__main__":
    p = Tarrinas()

