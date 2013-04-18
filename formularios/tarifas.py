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
## tarifas.py 
###################################################################
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
from formularios.utils import _float as float
from framework import adapter

DEBUG = False

class Tarifas(Ventana, VentanaGenerica):
    CLASE = pclases.Tarifa
    VENTANA = os.path.join("ui", "tarifas.glade")
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
                       # XXX: Más widgets y señales si se necesitan.
                       'b_add/clicked': self.add_producto, 
                       'b_add_concepto/clicked': self.add_concepto, 
                       'b_drop/clicked': self.drop
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
        cols = (('Cliente', 'gobject.TYPE_STRING', False, True, True, None),
                ('CIF', 'gobject.TYPE_STRING', False, True, False, None),
                ('Código Postal','gobject.TYPE_STRING',False,True,False,None),
                ('Ciudad', 'gobject.TYPE_STRING', False, True, False, None),
                ('Provincia', 'gobject.TYPE_STRING', False, True, False, None),
                ('País', 'gobject.TYPE_STRING', False, True, False, None),
                ('ID', 'gobject.TYPE_INT64', False, False, False, None))
                # La última columna (oculta en la Vista) siempre es el id.
        utils.preparar_listview(self.wids['tv_clientes'], cols)
        cols = (('Producto', 'gobject.TYPE_STRING', True, True, True, 
                    self.editar_descripcion),
                ('Precio','gobject.TYPE_STRING', True, True, False,
                    self.editar_precio),
                ('ID', 'gobject.TYPE_STRING', False, False, False, None))
                # La última columna (oculta en la Vista) siempre es el id.
        utils.preparar_treeview(self.wids['tv_productos'], cols, multi = True)

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
            self.check_permisos(nombre_fichero_ventana = "tarifas.py")

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
            filas_res.append((r.id, r.nombre))
        id = utils.dialogo_resultado(filas_res,
                                     titulo = 'SELECCIONE %s' % self.clase.sqlmeta.table.upper(),
                                     cabeceras = ('ID', 'Tarifa'), 
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
        self.rellenar_tabla_precios()
        self.rellenar_tabla_clientes()
        self.objeto.make_swap()
        self.wids['ventana'].set_title(self.objeto.get_info())

    def rellenar_tabla_clientes(self):
        model = self.wids['tv_clientes'].get_model()
        model.clear()
        for p in self.objeto.clientes:
            model.append((p.nombre, 
                          p.cif, 
                          p.cp, 
                          p.ciudad, 
                          p.provincia, 
                          p.pais, 
                          p.id))
            
    def rellenar_tabla_precios(self):
        model = self.wids['tv_productos'].get_model()
        model.clear()
        for p in self.objeto.precios:
            p.sync()
            for pv in p.productosVenta:
                padre = model.append(None, (pv.nombre, 
                                            utils.float2str(p.get_importe()), 
                                            "PV:%d" % pv.id))
                #if p.importeAdicional: # CWT: Ignoro precio base cuando es 0.
                #    model.append(padre, (p.descripcion, 
                #                         utils.float2str(p.importeAdicional), 
                #                         "P:%d" % p.id))
                # CWT: Que sí. Que sí hay que mostrarlo.
                model.append(padre, (p.descripcion, 
                                     utils.float2str(p.importeAdicional), 
                                     "P:%d" % p.id))
                for c in p.conceptos:
                    model.append(padre, (c.concepto, 
                                         utils.float2str(c.importe), 
                                         "C:%d" % c.id))

    def drop(self, boton):
        """
        Elimina un precio, un producto de la tarifa, o un concepto.
        """
        sel = self.wids['tv_productos'].get_selection()
        model, paths = sel.get_selected_rows()
        for path in paths:
            tipo, id = model[path][-1].split(":")
            if tipo == "C":
                concepto = pclases.Concepto.get(int(id))
                concepto.destroy_en_cascada()
            elif tipo == "P":
                precio = pclases.Precio.get(int(id))
                for concepto in precio.conceptos:
                    #concepto.destroySelf()
                    concepto.destroy_en_cascada()
                precio.destroySelf()
            elif tipo == "PV":
                pv = pclases.ProductoVenta.get(int(id))
                for precio in pv.precios:
                    if precio.tarifa == self.objeto:
                        for concepto in precio.conceptos:
                            #concepto.destroySelf()
                            concepto.destroy_en_cascada()
                        precio.destroySelf()
        if paths:
            self.rellenar_tabla_precios()

    def add_concepto(self, b):
        """
        Añade un detalle a un precio.
        Si se han marcado varias filas, añade el mismo concepto a todos 
        los precios marcados.
        """
        sel = self.wids['tv_productos'].get_selection()
        model, paths = sel.get_selected_rows()
        ids = []
        tratados = []
        while paths:
            path = paths.pop()
            tratados.append(path)
            tipo, id = model[path][-1].split(":")
            if tipo == "PV":
                paths += [hijo.path for hijo in model[path].iterchildren()
                          if hijo.path not in tratados]
            elif tipo == "C":
                #pathpadre = model[path].parent.path
                #if pathpadre not in tratados:
                #    paths.append(pathpadre)
                id = pclases.Concepto.get(int(id)).precioID
                if not id in ids:
                    ids.append(id)
            elif tipo == "P":
                id = int(id)
                if id not in ids:
                    ids.append(id)
        if ids:
            concepto = utils.dialogo_entrada(titulo = "CONCEPTO", 
                                             texto = "Introduzca detalle:", 
                                             padre = self.wids['ventana'])
            if concepto:
                precio = utils.dialogo_entrada(titulo = "IMPORTE", 
                                               texto = "Importe del detalle:", 
                                               padre = self.wids['ventana'])
                if precio:
                    try:
                        precio = utils._float(precio)
                    except (ValueError, TypeError):
                        utils.dialogo_info(titulo = "ERROR DE FORMATO", 
                            texto = "El texto %s no es un número." % precio, 
                            padre = self.wids['ventana'])
                    else:
                        for id in ids:
                            pre = pclases.Precio.get(id)
                            con = pclases.Concepto(importe = precio, 
                                                   concepto = concepto, 
                                                   precio = pre)
                            pre.tarifa.add_conceptoLdv_a_ldvs(con)
                        self.rellenar_tabla_precios()

    def add_producto(self, b):
        """
        Añade un precio a la tarifa, y a éste el producto seleccionado.
        En principio estaba contemplado que a un mismo precio (y sus detalles) 
        se le asociara uno o varios productos. Esto es muy difícil de 
        representar en un GUI y que resulte intuitivo, así que por cada 
        producto añadido a la tarifa se creará un precio al que se le 
        añadirán detalles independientemente o a la vez si se seleccionan 
        varias líneas en el TreeView al darle al botón de añadir detalle.
        """
        productos_no_en_tarifa = []
        for p in pclases.ProductoVenta.select():
            esta = False
            for precio in p.precios:
                if precio.tarifa == self.objeto:
                    esta = True
            if not esta:
                productos_no_en_tarifa.append((p.id, p.nombre))
        productos = utils.dialogo_resultado(productos_no_en_tarifa, 
                                            "SELECCIONE UNO O VARIOS PRODUCTOS",
                                            padre = self.wids['ventana'], 
                                            cabeceras = ("ID", "Producto"), 
                                            multi = True)
        if productos[0] > 0:
            for idp in productos:
                producto = pclases.ProductoVenta.get(idp)
                precio = pclases.Precio(tarifa = self.objeto, 
                                        descripcion = "Precio neto base")
                #Creo conceptos por defecto según la configuración del producto:
                if producto.envasep:
                    pclases.Concepto(precio = precio, 
                                     concepto = "Envase", 
                                     importe = 0.0)
                if producto.manipulacion:
                    pclases.Concepto(precio = precio, 
                                     concepto = "Manipulación", 
                                     importe = 0.0)
                if producto.transporte:
                    pclases.Concepto(precio = precio, 
                                     concepto = "Transporte", 
                                     importe = 0.0)
                if producto.tarifa:
                    pclases.Concepto(precio = precio, 
                                     concepto = "Tarrina", 
                                     importe = 0.0)
                precio.addProductoVenta(producto)
        self.rellenar_tabla_precios()

    def editar_precio(self, cell, path, text):
        """
        Cambia el precio base o del concepto marcado.
        Se diferencian de los productos porque su model[path].parent no 
        es None.
        Se diferencian entre sí porque la última columna contiene una letra, 
        dos puntos, y el identificador. La letra será P si es un precio o 
        C si es un concepto. Para los productos de venta será PV.
        """
        try:
            nuevo_importe = utils._float(text)
        except (ValueError, TypeError):
            utils.dialogo_info(titulo = "ERROR DE FORMATO", 
                               texto = "El texto %s no es un número." % text, 
                               padre = self.wids['ventana'])
        else:
            model = self.wids['tv_productos'].get_model()
            tipo, id = model[path][-1].split(":")
            if tipo == "C":
                concepto = pclases.Concepto.get(int(id))
                concepto.importe = nuevo_importe
                concepto.sync()
                precio = concepto.precio
                precio.sync()
                model[path][1] = utils.float2str(concepto.importe)
                model[path].parent[1] = utils.float2str(precio.get_importe())
                concepto.actualizar_conceptosLdv()
            elif tipo == "P":
                precio = pclases.Precio.get(int(id))
                precio.importeAdicional = nuevo_importe
                precio.sync()
                model[path][1] = utils.float2str(precio.importeAdicional)
                model[path].parent[1] = utils.float2str(precio.get_importe())
            elif tipo == "PV":
                hijo = model.iter_children(model.get_iter(path))
                if hijo:
                    tipo, id = model[hijo][-1].split(":")
                    if tipo == "P":
                        precio = pclases.Precio.get(int(id))
                    elif tipo == "C":
                        precio = pclases.Concepto.get(int(id)).precio
                    else:
                        precio = None
                    if precio:
                        precio.actualizar_a(nuevo_importe, 
                                            actualizar_ldvs_no_facturadas=True)
                        # Actualizo model en vez de recargarlo completo:
                        model[path][1] = utils.float2str(precio.get_importe())
                        hijos = []
                        iter = model.iter_children(model.get_iter(path))
                        if iter:
                            while iter != None:
                                hijos.append(model[iter])
                                iter = model.iter_next(iter)
                        for fila in hijos:
                            tipo, id = fila[-1].split(":")
                            if tipo == "P":
                                precio = pclases.Precio.get(int(id))
                                fila[1] = utils.float2str(
                                    precio.importeAdicional)
                            elif tipo == "C":
                                concepto = pclases.Concepto.get(int(id))
                                fila[1] = utils.float2str(
                                    concepto.importe)
            # Y paso al siguiente precio.
            iter = model.get_iter(path)
            iter = model.iter_next(iter)
            if iter:
                tv = self.wids['tv_productos']
                col = tv.get_column(1)
                cell = col.get_cell_renderers()[0]
                tv.set_cursor_on_cell(model.get_path(iter), 
                                      col, 
                                      cell, 
                                      start_editing = True)


    def editar_descripcion(self, cell, path, text):
        """
        Cambia la descripción de un precio o de un concepto.
        """
        model = self.wids['tv_productos'].get_model()
        tipo, id = model[path][-1].split(":")
        if tipo == "C":
            concepto = pclases.Concepto.get(int(id))
            concepto.concepto = text
            concepto.sync()
            model[path][0] = concepto.concepto
            concepto.actualizar_conceptosLdv()
        elif tipo == "P":
            precio = pclases.Precio.get(int(id))
            precio.descripcion = text
            precio.sync()
            model[path][0] = precio.descripcion

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
                                         texto="Introduzca nombre de tarifa:", 
                                         padre = self.wids['ventana']) 
        if a_buscar != None:
            try:
                ida_buscar = int(a_buscar)
            except ValueError:
                ida_buscar = -1
            campos_busqueda = (self.clase.q.nombre, )
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
        if not utils.dialogo('¿Eliminar %s?'%self.clase.sqlmeta.table.lower(), 
                             'BORRAR', 
                             padre = self.wids['ventana']):
            return
        self.objeto.notificador.desactivar()
        try:
            for cliente in self.objeto.clientes:
                cliente.tarifa = None
            for precio in self.objeto.precios:
                for concepto in precio.conceptos:
                    concepto.destroySelf()
                precio.destroySelf()
            self.objeto.destroySelf()
            #self.objeto.destroy_en_cascada()
        except Exception, e:
            self.logger.error("tarifas.py::borrar -> %s ID %d no se pudo eliminar. Excepción: %s." % (self.objeto.sqlmeta.table, self.objeto.id, e))
            utils.dialogo_info(titulo = "%s NO BORRADO" % self.clase.sqlmeta.table.upper(), 
                               texto = "%s no se pudo eliminar completamente.\n\nSe generó un informe de error en el «log» de la aplicación." % self.clase.sqlmeta.table.title(),
                               padre = self.wids['ventana'])
            self.actualizar_ventana()
            return
        self.objeto = None
        self.ir_a_primero()

if __name__ == "__main__":
    p = Tarifas()

