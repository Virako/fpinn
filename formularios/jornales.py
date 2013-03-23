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
## jornales.py - Ventana para introducción manual de jornales.
###################################################################
## TODO: 
## 1.- La búsqueda no funciona. Además, buscar por producción es 
##     una patata. Eso no sirve para nada.
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
    import adqprod
except ImportError:
    sys.path.append(os.path.join('..', 'framework'))
    import pclases
    from seeker import VentanaGenerica 
    import adqprod
from utils import _float as float
import adapter
from math import ceil

DEBUG = False

class Jornales(Ventana, VentanaGenerica):
    CLASE = pclases.Jornal
    VENTANA = os.path.join("..", "ui", "jornales.glade")
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
                       'cb_productoID/changed': self.mostrar_envases, 
                       'sp_envases/changed': self.cambiar_produccion, 
                      }
        self.add_connections(connections)
        self.inicializar_ventana()
        if self.objeto == None:
            self.ir_a_primero()
        else:
            self.ir_a(objeto)
        self.wids['ventana'].resize(1, 1)
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
        utils.rellenar_lista(self.wids['cbe_empleadoID'], 
                             [(p.id, "%s (%d)" % (p.nombre, p.id)) for p in 
                                pclases.Empleado.select(orderBy = "nombre")])
        utils.rellenar_lista(self.wids['cb_campannaID'], 
                             [(p.id, p.get_info()) for p in 
                                pclases.Campanna.select(orderBy = "fechaInicio")])
        utils.rellenar_lista(self.wids['cb_parcelaID'], 
                             [(p.id, p.parcela) for p in 
                                pclases.Parcela.select(orderBy = "parcela")])
        utils.rellenar_lista(self.wids['cb_actividadID'], 
                             [(p.id, "%s%s" % (p.descripcion, 
                                    (p.campo and " (campo)") or 
                                    (p.manipulacion and " (manipulación)") or 
                                    "")) 
                                for p in 
                             pclases.Actividad.select(orderBy = "descripcion")])
        utils.rellenar_lista(self.wids['cb_productoID'], 
                             [(p.id, "%s (%s kg/envase)" % (
                                    p.nombre, 
                                    utils.float2str(p.envase 
                                                    and p.envase.kg 
                                                    or "?")))
                              for p in 
                              pclases.ProductoVenta.select(orderBy = "nombre")]
                             )

        self.wids['entry1'].set_property("width-chars", 4)
        self.wids['entry1'].modify_base(gtk.STATE_NORMAL, 
            self.wids['entry1'].get_colormap().alloc_color("light gray"))
        self.wids['entry2'].set_property("width-chars", 4)
        self.wids['entry2'].modify_base(gtk.STATE_NORMAL, 
            self.wids['entry2'].get_colormap().alloc_color("light slate blue"))
        self.wids['entry3'].set_property("width-chars", 4)
        self.wids['entry3'].modify_base(gtk.STATE_NORMAL, 
            self.wids['entry3'].get_colormap().alloc_color("light steel blue"))
        self.wids['entry4'].set_property("width-chars", 12)
        self.wids['entry4'].modify_base(gtk.STATE_NORMAL, 
            self.wids['entry4'].get_colormap().alloc_color("light sea green"))
        self.wids['entry5'].set_property("width-chars", 12)
        self.wids['entry5'].modify_base(gtk.STATE_NORMAL, 
            self.wids['entry5'].get_colormap().alloc_color("light yellow"))
        self.wids['entry6'].set_property("width-chars", 10)
        self.wids['entry6'].modify_base(gtk.STATE_NORMAL, 
            self.wids['entry6'].get_colormap().alloc_color("light coral"))
        self.wids['entry7'].set_property("width-chars", 32)
        self.wids['entry7'].modify_base(gtk.STATE_NORMAL, 
            self.wids['entry7'].get_colormap().alloc_color("light salmon"))

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
            self.check_permisos(nombre_fichero_ventana = "jornales.py")

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
            filas_res.append((r.id, 
                            r.empleado and r.empleado.nombre or "SIN EMPLEADO", 
                            utils.str_fechahora(r.fechahoraInicio), 
                            utils.str_fechahora(r.fechahoraFin)))
        id = utils.dialogo_resultado(filas_res,
                                     titulo = 'SELECCIONE %s' % self.clase.sqlmeta.table.upper(),
                                     cabeceras = ('ID', 
                                                  'Empleado', 
                                                  'Inicio', 
                                                  'Fin'), 
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
        self.objeto.make_swap()
        self.wids['ventana'].set_title(self.objeto.get_info())
        a, b, c, d, e, f, g = adqprod.jornal2chunk(self.objeto)
        self.wids['entry1'].set_text(a)
        self.wids['entry2'].set_text(b)
        self.wids['entry3'].set_text(c)
        self.wids['entry4'].set_text(d)
        self.wids['entry5'].set_text(e)
        self.wids['entry6'].set_text(f)
        self.wids['entry7'].set_text(g)
        self.wids['data'].set_text(adqprod.jornal2data(self.objeto))
        self.mostrar_envases()

    def mostrar_envases(self, *args, **kw):
        """
        Muestra la producción en función del número de envases y el 
        producto del combo.
        """
        idproducto = utils.combo_get_value(self.wids['cb_productoID'])
        if idproducto:
            p = pclases.ProductoVenta.get(idproducto)
            envase = p.envase
            if envase:
                try:
                    envases = int(ceil(self.objeto.produccion / envase.kg))
                except ZeroDivisionError:
                    envases = 0
            else:
                envases = 0
        else:
            envases = 0
        self.wids['sp_envases'].set_value(envases)

    def cambiar_produccion(self, *args, **kw):
        """
        Cambia la producción en función del número de envases y 
        producto seleccionado.
        """
        self.wids['sp_envases'].update()    # Por si está tecleando en lugar 
                            # de usar los botones de incremento y decremento.
        envases = self.wids['sp_envases'].get_value()
        idproducto = utils.combo_get_value(self.wids['cb_productoID'])
        if idproducto:
            p = pclases.ProductoVenta.get(idproducto)
            envase = p.envase
            if envase:
                kg = envase.kg * envases
            else:
                kg = None
        else:
            kg = None
        if not kg is None:
            self.wids['e_produccion'].set_text(utils.float2str(kg))

    def nuevo(self, widget):
        """
        Función callback del botón b_nuevo.
        Pide los datos básicos para crear un nuevo objeto.
        Una vez insertado en la BD hay que hacerlo activo
        en la ventana para que puedan ser editados el resto
        de campos que no se hayan pedido aquí.
        """
        empleados = [(e.id, e.nombre +" "+ e.dni) 
                     for e in pclases.Empleado.select(orderBy = "nombre")]
        empleadoid = utils.dialogo_combo(titulo = "SELECCIONE EMPLEADO", 
                            texto = "Seleccione un empleado del desplegable:", 
                            ops = empleados, 
                            padre = self.wids['ventana'])
        if empleadoid:
            objeto_anterior = self.objeto
            if objeto_anterior != None:
                objeto_anterior.notificador.desactivar()
            self.objeto = self.clase(empleadoID = empleadoid, 
                                     campanna = None, 
                                     parcela = None, 
                                     actividad = None, 
                                     salario = None)
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
                                         texto = "Introduzca producción:", 
                                         padre = self.wids['ventana']) 
        if a_buscar != None:
            try:
                ida_buscar = int(a_buscar)
            except ValueError:
                ida_buscar = -1
            campos_busqueda = (self.clase.q.produccion, )
            subsubcriterios = []
            #sqlower = pclases.sqlbuilder.func.lower
            for cb in campos_busqueda:
                #ssc = [sqlower(cb).contains(t.lower()) 
                ssc = [cb.contains(t.lower()) 
                        for t in a_buscar.split()]
                if ssc:
                    subsubcriterios.append(pclases.AND(*ssc))
                else:
                    subsubcriterios.append(
                        #sqlower(cb).contains(a_buscar.lower()))
                        cb.contains(a_buscar.lower()))
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
            self.logger.error("jornales.py::borrar -> %s ID %d no se pudo eliminar. Excepción: %s." % (self.objeto.sqlmeta.table, self.objeto.id, e))
            utils.dialogo_info(titulo = "%s NO BORRADO" % self.clase.sqlmeta.table.upper(), 
                               texto = "%s no se pudo eliminar.\n\nSe generó un informe de error en el «log» de la aplicación." % self.clase.sqlmeta.table.title(),
                               padre = self.wids['ventana'])
            self.actualizar_ventana()
            return
        self.objeto = None
        self.ir_a_primero()

if __name__ == "__main__":
    p = Jornales()

