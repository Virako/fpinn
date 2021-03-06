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
## empleados.py -- Personal.
###################################################################
## NOTAS:
##  
###################################################################
## Changelog:
## 4 de enero de 2007 -> Inicio
## 
###################################################################

import os
from formularios.ventana import Ventana
from formularios import utils
import pygtk
pygtk.require('2.0')
import gtk, gtk.glade, time, mx, mx.DateTime
from framework import pclases
from formularios.seeker import VentanaGenerica
from framework import adapter

DEBUG = False

class Empleados(Ventana, VentanaGenerica):
    CLASE = pclases.Empleado
    VENTANA = os.path.join("ui", "empleados.glade")

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
                       'b_imagen/clicked': self.set_imagen,
                       'b_documentos/clicked': self.add_documento, 
                       'b_prev/clicked': self.prev, 
                       'b_next/clicked': self.next, 
                       'b_get_baja/clicked': self.get_baja, 
                       'b_quit_baja/clicked': self.quit_baja, 
                       'b_precio_a_todos/clicked': self.aplicar_precio_a_todos
                      }
        self.add_connections(connections)
        self.inicializar_ventana()
        if self.objeto == None:
            self.ir_a_primero()
        else:
            self.ir_a(objeto)
        gtk.main()

    def prev(self, b):
        """
        Va al empleado anterior en la lista de empleados 
        ordenada por ID.
        """
        if self.objeto:
            ids = get_lista_ids(self.clase)
            try:
                indice = ids.index(self.objeto.id) - 1
                if indice >= 0:
                    id = ids[indice]
                else:
                    raise ValueError
            except:
                utils.dialogo_info(titulo = "PRIMERO", 
                                   texto = "El empleado en pantalla es el primero.", 
                                   padre = self.wids['ventana'])
            else:
                self.ir_a(pclases.Empleado.get(id))

    def next(self, b):
        """
        Va al empleado siguiente en la lista de empleados 
        ordenada por ID.
        """
        if self.objeto:
            ids = get_lista_ids(self.clase)
            try:
                id = ids[ids.index(self.objeto.id) + 1]
            except:
                utils.dialogo_info(titulo = "ÚLTIMO", 
                                   texto = "El empleado en pantalla es el último.", 
                                   padre = self.wids['ventana'])
            else:
                self.ir_a(pclases.Empleado.get(id))

    def add_documento(self, boton):
        if self.objeto:
            import documentos
            ventanadoc = documentos.Documentos(self.objeto)

    def set_imagen(self, boton):
        nomfich = utils.dialogo_abrir(titulo = "BUSCAR FOTOGRAFÍA EMPLEADO", 
                                      filtro_imagenes = True, 
                                      padre = self.wids['ventana'])
        if nomfich != None:
            if not self.objeto.imagenes:
                imagen = pclases.Imagen(empleado = self.objeto, 
                                        titulo = self.objeto.get_info())
            else:
                imagen = self.objeto.imagenes[0]
            imagen.guardar_blob_from_file(nomfich)
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
            for widname in self.wids.keys():
                if "_" in widname:
                    widname = widname.split("_")[-1]
                if widname == colname:
                    w = self.wids[widname]
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
        return
        # XXX: Aquí generalmente se inicializan los TreeViews y combos.
        cols = (('XXXNombreCol', 'gobject.TYPE_STRING', XXXEditable, XXXOrdenable, XXXBuscable, XXXCallbackEdicion),
                ('ID', 'gobject.TYPE_INT64', False, False, False, None))
                # La última columna (oculta en la Vista) siempre es el id.
        utils.preparar_listview(self.wids['XXXtv_treeview'], cols)
        utils.rellenar_lista(self.wids['XXXcbe_comboboxentry'], 
                             [(p.id, p.XXXcampo) for p in 
                                pclases.XXXClase.select(orderBy = "XXXcampo")])

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
            self.check_permisos(nombre_fichero_ventana = "empleados.py")

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
            filas_res.append((r.id, r.nombre, r.dni, r.telefono))
        id = utils.dialogo_resultado(filas_res,
                                     titulo = 'SELECCIONE EMPLEADO',
                                     cabeceras = ('ID', 
                                                  'Nombre', 
                                                  'D.N.I./Pasaporte', 
                                                  'Teléfono'), 
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
        self.wids['id'].set_text(str(self.objeto.id))
        gtkimage = self.objeto.get_gtkimage(maximo = 125)
        self.wids['b_imagen'].set_image(gtkimage)
        self.wids['b_imagen'].set_label("")
        #self.rellenar_tabla_XXX()
        self.objeto.make_swap()
        self.wids['ventana'].set_title(self.objeto.get_info())
        ids = get_lista_ids(self.clase)
        self.wids['b_next'].set_sensitive(self.objeto.id != ids[-1])
        self.wids['b_prev'].set_sensitive(self.objeto.id != ids[0])
        # WORKAROUND para GTK y PyGTK 2.10 en Windows XP
        self.wids['b_imagen'].get_image().show()

    def rellenar_tabla_XXX(self):
        model = self.wids['XXXtv_treeview'].get_model()
        model.clear()
        total = 0.0
        for p in self.objeto.XXXunoamuchos:
            total += p.XXXcampoacumulable
            model.append((p.XXXcampo1, 
                          utils.float2str(p.XXXcampoacumulable), 
                          p.id))
        self.wids['XXXe_total_si_lo_hay'].set_text(utils.float2str(total))
            
    def nuevo(self, widget):
        """
        Función callback del botón b_nuevo.
        Pide los datos básicos para crear un nuevo objeto.
        Una vez insertado en la BD hay que hacerlo activo
        en la ventana para que puedan ser editados el resto
        de campos que no se hayan pedido aquí.
        """
        nombre = utils.dialogo_entrada(titulo = "NOMBRE", 
                                       texto = "Nombre completo:", 
                                       padre = self.wids['ventana'])
        if nombre is not None:
            objeto_anterior = self.objeto
            if objeto_anterior != None:
                objeto_anterior.notificador.desactivar()
            self.objeto = self.clase(nombre = nombre)
            self.objeto.notificador.activar(self.aviso_actualizacion)
            self._objetoreciencreado = self.objeto
            self.activar_widgets(True)
            self.actualizar_ventana(objeto_anterior = objeto_anterior)
            utils.dialogo_info('NUEVO EMPLEADO CREADO', 
                               'Se ha creado un nuevo empleado.\nA continuación complete la información del misma y guarde los cambios.', 
                               padre = self.wids['ventana'])

    def buscar(self, widget):
        """
        Muestra una ventana de búsqueda y a continuación los
        resultados. El objeto seleccionado se hará activo
        en la ventana a no ser que se pulse en Cancelar en
        la ventana de resultados.
        """
        a_buscar = utils.dialogo_entrada(titulo = "BUSCAR EMPLEADO", 
                                         texto = "Introduzca nombre, d.n.i./pasaporte, código o teléfono:", 
                                         padre = self.wids['ventana']) 
        if a_buscar != None:
            try:
                ida_buscar = int(a_buscar)
            except ValueError:
                ida_buscar = -1
            campos_busqueda = (self.clase.q.nombre, 
                               self.clase.q.dni, 
                               self.clase.q.telefono)
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

    def comprobar_dni(self):
        """
        Comprueba la letra del DNI o la asigna en 
        caso de que el texto del entry tenga formato de 
        DNI y no tenga letra.
        """
        adaptadores = self.adaptador.get_adaptadores()
        col = self.objeto.sqlmeta.columns['dni']
        adaptador = adaptadores[col]
        entry = adaptador['widget']
        valor = entry.get_text()
        import re
        dni = "[0-9][0-9][\.,]?[0-9]{3}[\.,]?[0-9]{3}[-]?[a-z]?"
        rexp = re.compile(dni)
        if rexp.findall(valor):
            dninum = "".join([i for i in valor if i.isdigit()])
            dnivalido = utils.calcularNIF(dninum)
            entry.set_text(utils.int2str("1" + dninum)[1:] + "-" + dnivalido)

    def comprobar_ccc(self):
        adaptadores = self.adaptador.get_adaptadores()
        col = self.objeto.sqlmeta.columns['ccc']
        adaptador = adaptadores[col]
        entry = adaptador['widget']
        valor = entry.get_text()
        if valor:
            if "-" in valor:
                try:
                    nbanco, nsuc, ncc, ncuenta = valor.split("-")
                except:
                    pass
                else:
                    try:
                        valor = "%04d %04d %02d %010d" % (int(nbanco), 
                                                          int(nsuc), 
                                                          int(ncc), 
                                                          int(ncuenta))
                    except:
                        pass
            num = "".join([i for i in valor if i.isdigit()])
            nbanco = num[:4]
            nsuc = num[4:8]
            ncuenta = num[10:20]
            try:
                ncc = utils.calcCC(nbanco, nsuc, ncuenta)
            except:
                entry.set_text("")
            else:
                entry.set_text("%04d-%04d-%02d-%010d" % (int(nbanco), 
                                                         int(nsuc), 
                                                         int(ncc), 
                                                         int(ncuenta)))

    def guardar(self, widget):
        """
        Guarda el contenido de los entry y demás widgets de entrada
        de datos en el objeto y lo sincroniza con la BD.
        """
        # Desactivo el notificador momentáneamente
        self.objeto.notificador.desactivar()
        self.comprobar_dni()
        self.comprobar_ccc()
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
        if not utils.dialogo('¿Eliminar el empleado?', 
                             'BORRAR', 
                             padre = self.wids['ventana']):
            return
        self.objeto.notificador.desactivar()
        try:
            self.objeto.destroySelf()
        except Exception, e:
            self.logger.error("empleados.py::borrar -> Empleado ID %d no se pudo eliminar. Excepción: %s." % (self.objeto.id, e))
            utils.dialogo_info(titulo = "EMPLEADO NO BORRADO", 
                               texto = "El empleado no se pudo eliminar.\n\nSe generó un informe de error en el «log» de la aplicación.",
                               padre = self.wids['ventana'])
            self.actualizar_ventana()
            return
        self.objeto = None
        self.ir_a_primero()

    def get_baja(self, widget):
        self.wids['observaciones'].set_text('de baja')

    def quit_baja(self, widget):
        self.wids['observaciones'].set_text('')

    def aplicar_precio_a_todos(self, boton):
        """
        Aplica el precio diario, de campo y de manipulación a todos los 
        empleados.
        """
        self.guardar(boton) # Guardo por si acaso.
        for e in pclases.Empleado.select():
            e.precioDiario = self.objeto.precioDiario
            e.precioHoraCampo = self.objeto.precioHoraCampo
            e.precioHoraManipulacion = self.objeto.precioHoraManipulacion
            e.sync()
        utils.dialogo_info(titulo = "PRECIOS ACTUALZIADOS", 
                           texto = "Se actualizaron con éxito los precios de todos los empleados.", 
                           padre = self.wids['ventana'])

def get_lista_ids(clase):
    """
    Devuelve una tupla ordenada de identificadores de la clase.
    """
    return [e.id for e in clase.select(orderBy = "id")]

if __name__ == "__main__":
    p = Empleados()

