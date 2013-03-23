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
## salario.py - Salarios de empleados.
###################################################################
## Changelog:
## 14 de enerio de 2007 -> Inicio
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

class Salarios(Ventana, VentanaGenerica):
    CLASE = pclases.Salario
    VENTANA = os.path.join("..", "ui", "salarios.glade")
    def __init__(self, objeto = None, usuario = None):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        self.usuario = usuario
        self.clase = self.CLASE
        Ventana.__init__(self, self.VENTANA, objeto)
        connections = {'b_salir/clicked': self.salir,
                       'b_nuevo/clicked': self.nuevo,
                       'b_borrar/clicked': self.borrar,
                       'b_actualizar/clicked': self.actualizar_ventana,
                       'b_guardar/clicked': self.guardar,
                       'b_buscar/clicked': self.buscar,
                       'b_add_jornal/clicked': self.add_jornal, 
                       'b_drop_jornal/clicked': self.drop_jornal, 
                       'b_anterior/clicked': self.anterior, 
                       'b_siguiente/clicked': self.siguiente, 
                      }
        self.add_connections(connections)
        self.dic_campos = self.__build_dic_campos()
        self.adaptador = adapter.adaptar_clase(self.clase, self.dic_campos)
        self.inicializar_ventana()
        if self.objeto == None:
            self.ir_a_primero()
        else:
            self.ir_a(objeto)
        gtk.main()

    def anterior(self, boton):
        salarios = pclases.Salario.select(orderBy = "id")
        ids = [e.id for e in salarios]
        try:
            idactual = self.objeto.id
            idanterior = ids[ids.index(idactual) - 1]
        except (IndexError, AttributeError):
            utils.dialogo_info(titulo = "ERROR", 
                               texto = "El salario actual es el primero.", 
                               padre = self.wids['ventana'])
        else:
            self.objeto = pclases.Salario.get(idanterior)
            self.rellenar_widgets()

    def siguiente(self, boton):
        salarios = pclases.Salario.select(orderBy = "id")
        ids = [e.id for e in salarios]
        try:
            idactual = self.objeto.id
            idsiguiente = ids[ids.index(idactual) + 1]
        except (IndexError, AttributeError):
            utils.dialogo_info(titulo = "ERROR", 
                               texto = "El salario actual es el último.", 
                               padre = self.wids['ventana'])
        else:
            self.objeto = pclases.Salario.get(idsiguiente)
            self.rellenar_widgets()

    def drop_jornal(self, b):
        selection = self.wids['tv_jornales'].get_selection()
        model, paths = selection.get_selected_rows()
        for path in paths:
            id = model[path][-1]
            jornal = pclases.Jornal.get(id)
            # jornal.destroySelf()
            jornal.salario.horasCampo -= jornal.horasCampo
            jornal.salario.totalEuros -= (jornal.eurosCampo 
                                          + jornal.eurosManipulacion)
            dia = utils.abs_mxfecha(jornal.fechahoraInicio)
            dias = [utils.abs_mxfecha(j.fechahoraInicio) for j in jornal.salario.jornales]
            if dias.count(dia) == 1:
                jornal.salario.totalEuros -= jornal.empleado.precioDiario
            jornal.salario = None
        self.objeto.update_actividad()
        self.actualizar_ventana()

    def add_jornal(self, b):
        """
        Muestra un diálogo de resultados con los jornales sin salarios 
        relacionados, pertenecientes al empleado del registro salario y 
        su fechahoraInicio esté entre la fecha del salario y el final del 
        mes de esa misma fecha.
        """
        findemes = mx.DateTime.DateTimeFrom(day = -1, 
                                            month = self.objeto.fecha.month, 
                                            year = self.objeto.fecha.year)
        findemes += mx.DateTime.oneDay  # Porque vamos a comparar con fechahora.
        J = pclases.Jornal
        jornales = J.select(pclases.AND(J.q.salarioID == None, 
                                    J.q.empleadoID == self.objeto.empleadoID, 
                                    J.q.fechahoraInicio < findemes, 
                                    J.q.fechahoraInicio >= self.objeto.fecha), 
                            orderBy = "fechahoraInicio")
        cabeceras=("ID", "Inicio", "Fin", "Actividad", "Parcela", "Produccion")
        filas = [(j.id, 
                  utils.str_fechahora(j.fechahoraInicio), 
                  utils.str_fechahora(j.fechahoraFin), 
                  j.actividad and j.actividad.descripcion or "", 
                  j.parcela and j.parcela.parcela or "", 
                  utils.float2str(j.produccion))
                 for j in jornales]
        resjornales = utils.dialogo_resultado(filas, 
                                              "SELECCIONE JORNADAS", 
                                              self.wids['ventana'], 
                                              cabeceras, 
                                              multi = True)
        if resjornales and resjornales[0] > 0:
            for jid in resjornales:
                jornal = pclases.Jornal.get(jid)
                jornal.salario = self.objeto
                jornal.salario.horasCampo += jornal.horasCampo
                jornal.salario.totalEuros += (jornal.eurosCampo 
                                              + jornal.eurosManipulacion)
                dia = utils.abs_mxfecha(jornal.fechahoraInicio)
                dias = [utils.abs_mxfecha(j.fechahoraInicio) for j in jornal.salario.jornales]
                if dia not in dias:
                    jornal.salario.totalEuros += jornal.empleado.precioDiario
            self.objeto.update_actividad()
            self.actualizar_ventana()

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
        #cols = (('Campaña', 'gobject.TYPE_STRING', False, True, False, None),
        cols = (('Actividad', 'gobject.TYPE_STRING', False, True, False,None),
                ('Parcela', 'gobject.TYPE_STRING', False, True, False, None),
                ('Inicio', 'gobject.TYPE_STRING', False, True, False, None),
                ('Fin', 'gobject.TYPE_STRING', False, True, False, None),
                ('Duracion', 'gobject.TYPE_STRING', False, True, False, None), 
                ('Producción', 'gobject.TYPE_STRING', False, True, True,None),
                ('ID', 'gobject.TYPE_INT64', False, False, False, None))
                # La última columna (oculta en la Vista) siempre es el id.
        utils.preparar_listview(self.wids['tv_jornales'], cols, multi = True)
        for numcol in (4, 5):
            col = self.wids['tv_jornales'].get_column(numcol)
            for cell in col.get_cell_renderers():
                cell.set_property("xalign", 1.0)
        utils.rellenar_lista(self.wids['cbe_empleadoID'], 
                             [(p.id, p.nombre) for p in 
                                pclases.Empleado.select(orderBy = "nombre")])
        utils.rellenar_lista(self.wids['cb_actividadID'], 
                        [(p.id, p.descripcion) for p in 
                         pclases.Actividad.select(orderBy = "descripcion")])
        if pclases.Salario.select().count() == 0:
            self.wids['b_anterior'].set_sensitive(False)
            self.wids['b_siguiente'].set_sensitive(False)


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
        ws = ["b_borrar", "frame1"] + \
             [self.adaptador.get_adaptadores()[col]['widget'].name 
              for col in self.adaptador.get_adaptadores().keys()]
            # b_nuevo y b_buscar no se activan/desactivan aquí, sino en el
            # chequeo de permisos.
        ws.remove("gastoID")
        for w in ws:
            try:
                self.wids[w].set_sensitive(s)
            except Exception, msg:
                print "Widget problemático:", w, "Excepción:", msg
                #import traceback
                #traceback.print_last()
        if chequear_permisos:
            self.check_permisos(nombre_fichero_ventana = "salarios.py")

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
                              r.empleado and r.empleado.nombre or "", 
                              utils.str_fecha(r.fecha), 
                              utils.float2str(r.totalEuros)))
        id = utils.dialogo_resultado(filas_res,
                    titulo = 'SELECCIONE %s' % self.clase.sqlmeta.table.upper(),
                    cabeceras = ('ID', 'Empleado', 'Fecha', 'Salario'), 
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
        self.rellenar_tabla_jornales()
        self.objeto.make_swap()
        self.wids['ventana'].set_title(self.objeto.get_info())
        salarios = pclases.Salario.select(orderBy = "id")
        ids = [e.id for e in salarios]
        idactual = self.objeto.id
        self.wids['b_anterior'].set_sensitive(ids[0] != idactual)
        self.wids['b_siguiente'].set_sensitive(ids[-1] != idactual)

    def rellenar_tabla_jornales(self):
        model = self.wids['tv_jornales'].get_model()
        model.clear()
        totalprod = 0.0
        totalhoras = mx.DateTime.DateTimeDelta(0)
        for p in self.objeto.jornales:
            totalprod += p.produccion
            totalhoras += p.fechahoraFin - p.fechahoraInicio
            #model.append((p.campanna 
            #                and utils.str_fecha(p.campanna.fechaInicio) or "", 
            definicion_actividad = p.actividad and p.actividad.descripcion or ""
            if p.actividad:
                if p.actividad.campo:
                    definicion_actividad += " (campo)"
                elif p.actividad.manipulacion:
                    definicion_actividad += " (manipulación)"
            model.append((definicion_actividad, 
                          p.parcela and p.parcela.parcela or "", 
                          utils.str_fechahora(p.fechahoraInicio),
                          utils.str_fechahora(p.fechahoraFin),
                          utils.float2str(p.get_duracion()), 
                          utils.float2str(p.produccion), 
                          p.id))
        #self.wids['XXXe_total_si_lo_hay'].set_text(utils.float2str(total))
        #print totalprod, totalhoras
            
    def nuevo(self, widget):
        """
        Función callback del botón b_nuevo.
        Pide los datos básicos para crear un nuevo objeto.
        Una vez insertado en la BD hay que hacerlo activo
        en la ventana para que puedan ser editados el resto
        de campos que no se hayan pedido aquí.
        """
        gasto, empleado = build_gasto_salario(self.wids['ventana'])
        if gasto != None:
            objeto_anterior = self.objeto
            if objeto_anterior != None:
                objeto_anterior.notificador.desactivar()
            try:
                hoy = mx.DateTime.localtime()
                primeros_de_mes_hoy = mx.DateTime.DateTimeFrom(day = 1, 
                                                            month = hoy.month, 
                                                            year = hoy.year)
                self.objeto = self.clase(gasto = gasto, 
                                         empleado = empleado, 
                                         actividad = None, 
                                         fecha = primeros_de_mes_hoy)
            except Exception, msg:
                gasto.destroy_en_cascada()
                utils.dialogo_info(titulo = "ERROR", 
                                   texto = "Ocurrió un error al crear el nuevo salario.\n\nInformación de depuración:\n%s" % msg, 
                                   padre = self.wids['ventana'])
                print msg
            else:
                col = self.objeto.sqlmeta.columns['gastoID']
                utils.rellenar_lista(
                    self.adaptador.get_adaptadores()[col]['widget'], 
                    [(g.id, getattr(g, g.sqlmeta.columnList[0].name)) 
                        for g in pclases.Gasto.select()])
                    # Recreo el model porque se crea un gasto por cada salario.
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
        a_buscar = utils.dialogo_entrada(
            titulo = "BUSCAR %s" % self.clase.sqlmeta.table.upper(), 
            texto = "Introduzca nombre de empleado o fecha:", 
            padre = self.wids['ventana'])
        if a_buscar != None:
            fecha, empleado = adivinar_fecha_o_empleado(a_buscar)
            try:
                ida_buscar = int(a_buscar)
            except ValueError:
                ida_buscar = -1
            campos_busqueda = (self.clase.q.empleadoID, 
                               self.clase.q.fecha)
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
        if not utils.dialogo('¿Eliminar %s?' % self.clase.sqlmeta.table.lower(), 
                             'BORRAR', 
                             padre = self.wids['ventana']):
            return
        self.objeto.notificador.desactivar()
        try:
            self.objeto.destroySelf()
        except Exception, e:
            self.logger.error("salarios.py::borrar -> %s ID %d no se pudo eliminar. Excepción: %s." % (self.objeto.sqlmeta.table, self.objeto.id, e))
            utils.dialogo_info(titulo = "%s NO BORRADO" % self.clase.sqlmeta.table.upper(), 
                               texto = "%s no se pudo eliminar.\n\nSe generó un informe de error en el «log» de la aplicación." % self.clase.sqlmeta.table.title(),
                               padre = self.wids['ventana'])
            self.actualizar_ventana()
        else:
            self.objeto = None
            self.ir_a_primero()

def build_gasto_salario(padre, empleado = None):
    """
    Verifica que hay una cuenta de gastos para salarios.
    Si no existe, la crea.
    Pregunta por el empleado al que le corresponde el salario si 
    no se recibe como parámetro.
    Si cancela u ocurre un error, devuelve (None, None).
    Si no, devuelve el gasto creado relacionado con el empleado 
    y el empleado en una tupla (gasto, empleado).
    Recibe la ventana padre para el diálogo modal.
    """
    res = [None, None]
    if not empleado:
        empleados = pclases.Empleado.select(orderBy = "nombre")
        empleados = [(e.id, "%s, %s" % (e.nombre, e.dni)) for e in empleados]
        empleadoid = utils.dialogo_combo("SELECCIONE EMPLEADO:", 
                                   "Seleccione un empleado del desplegable:", 
                                   empleados, 
                                   padre = padre)
    else:
        empleadoid = empleado.id
    if empleadoid != None:
        res[1] = pclases.Empleado.get(empleadoid)
        try:
            cuenta = pclases.CuentaGastos.selectBy(descripcion="Salarios")[0]
        except IndexError:
            cuenta = pclases.CuentaGastos(descripcion = "Salarios")
        gasto = pclases.Gasto(cuentaGastos = cuenta, 
                              facturaCompra = None, 
                              parcela = None, 
                              concepto = "Salario %s" % res[1].nombre, 
                              importe = 0.0)
        res[0] = gasto
    return res

def adivinar_fecha_o_empleado(txt):
    """
    Devuelve como texto un ID de empleado o una fecha (o parte de ella) 
    en formato AAAA-MM-DD.
    Si alguna de las dos cosas no se puede determinar la devuelve como 
    cadena vacía.
    """
    empleado = adivinar_empleado(txt)
    fecha = adivinar_fecha(txt)
    return fecha, empleado

def adivinar_empleado(txt):
    """
    Si el texto coincide con el nombre o el cif de un empleado 
    devuelve como texto su ID.
    Si encuentra varios, devuelve todos los ID separados por espacio.
    Devuelve una cadena vacía en otro caso.
    """
    E = pclases.Empleado
    campos_busqueda = (E.q.nombre, 
                       E.q.dni)
    subcriterios = []
    for cb in campos_busqueda:
        ssc = [cb.contains(t) for t in txt.split()]
        if ssc:
            subcriterios.append(pclases.AND(*ssc))
        else:
            subcriterios.append(cb.contains(txt))
    if len(subcriterios) > 1:
        criterios = pclases.OR(*subcriterios)
    else:
        criterios = subcriterios
    resultados = E.select(criterios)
    res = ""
    if resultados.count():
        res = " ".join([`r.id` for r in resultados])
    return res

def adivinar_fecha(txt):
    """
    Intenta determinar una fecha completa a partir de txt. Si son dos
    números los devuelve como AAAA-MM. Si es solo uno, lo devuelve con 
    cuatro dígitos suponiendo que es un año.
    En otro caso devuelve la cadena vacía.
    """
    import re
    rex = re.compile("[\d]+")
    nums = rex.findall(txt)
    res = ""
    if len(nums) == 3:
        if len(nums)[0] > 2:    # Si viene con el año al principio
            fecha = mx.DateTime.DateTimeFrom(day = int(nums[2]), 
                                             month = int(nums[1]), 
                                             year = int(nums[0]))
        else:
            fecha = mx.DateTime.DateTimeFrom(day = int(nums[0]), 
                                             month = int(nums[1]), 
                                             year = int(nums[2]))
        res = "%d-%d-%d" % (fecha.year, fecha.month, fecha.day)
            # OJO: Formato de fecha puede variar en el backend postgresql.
    elif len(nums) == 2:
        if len(nums)[0] > 2:    # Si viene con el año al principio
            res = "%d-%d" % nums
        else:
            res = "%d-%d" % nums[::-1]
    elif len(nums) == 1:
        res = nums[0]
    return res
        

if __name__ == "__main__":
    p = Salarios()

