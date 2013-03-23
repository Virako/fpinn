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
## facturas_venta.py - Facturas de venta.
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

class FacturasVenta(Ventana, VentanaGenerica):
    CLASE = pclases.FacturaVenta
    VENTANA = os.path.join("..", "ui", "facturas_venta.glade")
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
                       'b_add_src/clicked': self.add_from_src,
                       'b_drop_ldv/clicked': self.drop_ldv, 
                       'b_vtos_defecto/clicked': self.crear_vtos_defecto, 
                       'b_add_vto/clicked': self.add_vto,
                       'b_drop_vto/clicked': self.drop_vto,
                       'b_add_cobro/clicked': self.add_cobro, 
                       'b_drop_cobro/clicked': self.drop_cobro, 
                       'b_imprimir/clicked': self.imprimir}
        self.add_connections(connections)
        self.inicializar_ventana()
        if self.objeto == None:
            self.ir_a_primero()
        else:
            self.ir_a(objeto)
        gtk.main()

    def ir_a_primero(self):
        try:
            fra = pclases.FacturaVenta.select(
                    pclases.FacturaVenta.q.proveedorID == None, 
                    orderBy = "-id")[0]
            self.ir_a(fra)
        except IndexError:
            self.objeto = None
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
                if widname_glade == "e_total_iva":
                    continue    # El total se rellena por otra parte y no 
                                # tiene atributo en el objeto.
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
                if col.name == "comision":
                    igual = igual and self.wids['e_comision'].get_text() == utils.float2str(self.objeto.comision, autodec = True, precision = 2)
                else:
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
        cols = (('Producto', 'gobject.TYPE_STRING', False, True, False, None),
                ('Cantidad', 'gobject.TYPE_STRING', False, True, False, None), 
                ('Precio', 'gobject.TYPE_STRING', False, True, False, None), 
                ('Bultos', 'gobject.TYPE_INT', False, True, False, None), 
                ('Importe s/IVA', 'gobject.TYPE_STRING', False, True, False, None), 
                ('Albarán', 'gobject.TYPE_STRING', False, True, False, None), 
                ('ID', 'gobject.TYPE_INT64', False, False, False, None))
                # La última columna (oculta en la Vista) siempre es el id.
        utils.preparar_listview(self.wids['tv_srcs'], cols, multi = True)
        cols = (('Producto', 'gobject.TYPE_STRING', False, True, False, None),
                ('Cantidad', 'gobject.TYPE_STRING', True, True, False, 
                    self.editar_cantidad), 
                ('Precio', 'gobject.TYPE_STRING', True, True, False, 
                    self.editar_precio), 
                ('Importe s/IVA', 'gobject.TYPE_STRING', False, True, False, None), 
                ('ID', 'gobject.TYPE_INT64', False, False, False, None))
        utils.preparar_listview(self.wids['tv_ldvs'], cols, multi = True)
        for i in range(1, 4):
            col = self.wids['tv_ldvs'].get_column(i)
            for cell in col.get_cell_renderers():
                cell.set_property("xalign", 1)
        clientes = [(c.id, "%s (%s)" % (c.nombre, c.cif))
                     for c in pclases.Cliente.select(orderBy = "nombre")]
        utils.rellenar_lista(self.wids['cb_clienteID'], clientes)
        cols = (("Fecha", "gobject.TYPE_STRING", True, True, True, 
                    self.cambiar_fecha_vto), 
                ("Cantidad", "gobject.TYPE_STRING", True, True, False, 
                    self.cambiar_importe_vto), 
                ("ID", "gobject.TYPE_INT64", False, False, False, None))
        utils.preparar_listview(self.wids['tv_vencimientos'], cols)
        cols = (("Fecha", "gobject.TYPE_STRING", True, True, True, 
                    self.cambiar_fecha_cobro), 
                ("Cantidad", "gobject.TYPE_STRING", True, True, False, 
                    self.cambiar_importe_cobro), 
                ("Observaciones", "gobject.TYPE_STRING", True, True, False, 
                    self.cambiar_observaciones_cobro), 
                ("ID", "gobject.TYPE_INT64", False, False, False, None))
        utils.preparar_listview(self.wids['tv_cobros'], cols)
        #---------------------------------------------------------------#
        def comprobar_que_no_me_hace_el_gato(paned,                     #
                        scrolltype_or_allocation_or_requisition = None):#
            MIN = 109                                                   #
            MAX = 720                                                   #
            posactual = paned.get_position()                            #
            if posactual < MIN:                                         #
                paned.set_position(MIN)                                 #
            elif posactual > MAX:                                       #
                paned.set_position(MAX)                                 #
        #---------------------------------------------------------------#
        self.wids['hpaned1'].connect("size_request", 
                                     comprobar_que_no_me_hace_el_gato)
        #CWT: Poder modificar números de factura por haberse emitido algunas 
        #     con la seride del 2010 estando en el 2011.
        # TODO: PORASQUI: Mirar por qué ha pasado eso.
        self.wids['e_numfactura'].set_property("editable", True)

    def editar_cantidad(self, cell, path, text):
        if self.objeto.bloqueada:
            utils.dialogo_info(titulo = "FACTURA BLOQUEADA", 
                texto = "No puede editar cantidades en una factura bloqueada.",
                padre = self.wids['ventana'])
            return
        model = self.wids['tv_ldvs'].get_model()
        id = model[path][-1]
        try:
            num = utils._float(text)
        except:
            utils.dialogo_info(titulo = "ERROR DE FORMATO", 
                               texto = "El texto %s no es un número." % text,
                               padre = self.wids['ventana'])
        else:
            ldv = pclases.LineaDeVenta.get(id)
            ldv.cantidad = num
            model[path][1] = utils.float2str(ldv.cantidad)
            model[path][3] = utils.float2str(ldv.calcular_importe())

    def editar_precio(self, cell, path, text):
        if self.objeto.bloqueada:
            utils.dialogo_info(titulo = "FACTURA BLOQUEADA", 
                texto = "No puede editar precios en una factura bloqueada.",
                padre = self.wids['ventana'])
            return
        model = self.wids['tv_ldvs'].get_model()
        id = model[path][-1]
        try:
            num = utils._float(text)
        except:
            utils.dialogo_info(titulo = "ERROR DE FORMATO", 
                               texto = "El texto %s no es un número." % text,
                               padre = self.wids['ventana'])
        else:
            ldv = pclases.LineaDeVenta.get(id)
            ldv.precio = num
            model[path][2] = utils.float2str(ldv.cantidad)
            model[path][3] = utils.float2str(ldv.calcular_importe())

    def add_from_src(self, b):
        """
        Añade las LDV seleccionadas en el TreeView de orígenes.
        """
        model, paths = self.wids['tv_srcs'].get_selection().get_selected_rows()
        for path in paths:
            ldv = pclases.LineaDeVenta.get(model[path][-1])
            if ldv.albaranSalida not in self.objeto.get_albaranes():
                # La primera vez que añado un albarán, incluyo sus gastos 
                # de transporte y demás.
                self.objeto.transporte -= ldv.albaranSalida.transporte
                self.objeto.descuentoNumerico -= ldv.albaranSalida.descarga
                if ldv.albaranSalida.descarga:
                    self.objeto.conceptoDescuentoNumerico += " Descarga"
                self.objeto.comision -= ldv.albaranSalida.comision
            ldv.facturaVenta = self.objeto
        if paths:
            self.actualizar_ventana()

    def drop_ldv(self, b):
        """
        Desvincula las LDVs marcadas de la factura.
        """
        model, paths = self.wids['tv_ldvs'].get_selection().get_selected_rows()
        for path in paths:
            ldv = pclases.LineaDeVenta.get(model[path][-1])
            ldv.facturaVenta = None
            if ldv.albaranSalida not in self.objeto.get_albaranes():
                # Si quito la última línea de un albarán, retiro también 
                # sus gastos de transporte y demás.
                self.objeto.transporte += ldv.albaranSalida.transporte
                self.objeto.descuentoNumerico += ldv.albaranSalida.descarga
                self.objeto.conceptoDescuentoNumerico = self.objeto.conceptoDescuentoNumerico.replace(" Descarga", "")
                self.objeto.comision += ldv.albaranSalida.comision
        if paths:
            self.actualizar_ventana()

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
        ws = (["b_borrar", "vbox2"] + 
              [self.adaptador.get_adaptadores()[col]['widget'].name 
               for col in self.adaptador.get_adaptadores().keys()])
            # b_nuevo y b_buscar no se activan/desactivan aquí, sino en el
            # chequeo de permisos.
        ws.remove("proveedorID")
        ws.remove("serieFacturasVentaID")
        for w in ws:
            try:
                self.wids[w].set_sensitive(s)
            except Exception, msg:
                print "Widget problemático:", w, "Excepción:", msg
                #import traceback
                #traceback.print_last()
        if chequear_permisos:
            self.check_permisos(nombre_fichero_ventana = "facturas_venta.py")
        # Si ya tiene líneas de venta, evito que cambie el cliente.
        puede_cambiar_cliente = self.objeto and not self.objeto.lineasDeVenta
        try:
            puede_cambiar_cliente = int(puede_cambiar_cliente)
        except TypeError:
            puede_cambiar_cliente = False
        puede_cambiar_cliente = (puede_cambiar_cliente 
                    and self.wids['cb_clienteID'].get_property("sensitive"))
        self.wids['cb_clienteID'].set_sensitive(puede_cambiar_cliente)
        self.wids['b_imprimir'].set_sensitive(self.objeto != None)

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
            filas_res.append((r.id, r.numfactura, 
                                    r.cliente and r.cliente.nombre or "", 
                                    utils.str_fecha(r.fecha)))
        id = utils.dialogo_resultado(filas_res,
                                     titulo = 'SELECCIONE %s' % self.clase.sqlmeta.table.upper(),
                                     cabeceras = ('ID', 
                                                  'Número de factura', 
                                                  'Cliente', 
                                                  'Fecha'), 
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
            if col.name == "comision":
                # UGLY AND DIRTY HACK: Es para no tocar la clase Adapter. Aquí la comisión es en ninerito, no en porcentaje.
                self.wids['e_comision'].set_text(utils.float2str(self.objeto.comision, autodec = True, precision = 2))
            else:
                adaptadores[col]['mostrar'](self.objeto)
        self.rellenar_tabla_origenes()
        subtotal = self.rellenar_tabla_ldvs()
        self.objeto.make_swap()
        self.wids['ventana'].set_title(self.objeto.get_info())
        numsalbs = utils.unificar([ldv.albaranSalida.numalbaran for ldv in 
                                   self.objeto.lineasDeVenta])
        numsalbs = ", ".join(numsalbs)
        self.wids['e_peds_albs'].set_text(numsalbs)
        self.rellenar_totales(subtotal)
        self.rellenar_vencimientos()

    def rellenar_totales(self, subtotal = None, servicios = None):
        if subtotal != None:
            b_imponible = subtotal 
        else:
            b_imponible = sum([ldv.calcular_importe(iva = False)
                               for ldv in self.objeto.lineasDeVenta])
        # XXX: Transporte va fuera de IVA. Comisión, no.
        # servicios = self.objeto.transporte + self.objeto.comision
        servicios = self.objeto.comision
        # XXX
        b_imponible += servicios
        self.wids['e_subtotal'].set_text(utils.float2str(b_imponible))
        descuento = b_imponible * self.objeto.descuento
        self.wids['e_tot_dto'].set_text(utils.float2str(descuento))
        tras_dto = b_imponible - descuento
        totiva = tras_dto * self.objeto.iva
        self.wids['e_total_iva'].set_text(utils.float2str(totiva))
        total = tras_dto + totiva + self.objeto.descuentoNumerico
        # XXX: Transporte va fuera de IVA
        total += self.objeto.transporte 
        # XXX
        self.wids['e_total'].set_text(utils.float2str(total))

    def rellenar_tabla_ldvs(self):
        model = self.wids['tv_ldvs'].get_model()
        model.clear()
        total = 0.0
        for ldv in self.objeto.lineasDeVenta:
            importe = ldv.calcular_importe(iva = False)
            total += importe 
            model.append((ldv.productoVenta.nombre, 
                          utils.float2str(ldv.cantidad), 
                          utils.float2str(ldv.precio), 
                          utils.float2str(importe), 
                          ldv.id))
        return total
            
    def rellenar_tabla_origenes(self):
        model = self.wids['tv_srcs'].get_model()
        model.clear()
        for ldv in pclases.LineaDeVenta.select(pclases.AND(
                pclases.LineaDeVenta.q.albaranSalidaID 
                    == pclases.AlbaranSalida.q.id, 
                pclases.AlbaranSalida.q.clienteID == self.objeto.cliente.id, 
                pclases.LineaDeVenta.q.facturaVentaID == None)):
            ldv.sync()
            model.append((ldv.productoVenta.nombre, 
                          utils.float2str(ldv.cantidad), 
                          utils.float2str(ldv.precio), 
                          ldv.calcular_bultos(), 
                          utils.float2str(ldv.calcular_importe(iva = False)), 
                          ldv.albaranSalida.numalbaran, 
                          ldv.id))

    def nuevo(self, widget):
        """
        Función callback del botón b_nuevo.
        Pide los datos básicos para crear un nuevo objeto.
        Una vez insertado en la BD hay que hacerlo activo
        en la ventana para que puedan ser editados el resto
        de campos que no se hayan pedido aquí.
        """
        clientes = [(c.id, "%s (%s)" % (c.nombre, c.cif)) 
                    for c in pclases.Cliente.select(
                        pclases.Cliente.q.inhabilitado == False, 
                        orderBy = "nombre")]
        idcliente = utils.dialogo_combo("CLIENTE NUEVA FACTURA", 
                                        "Seleccione un cliente de la lista", 
                                        clientes, 
                                        padre = self.wids['ventana'])
        if idcliente != None:
            ivadefecto = pclases.Cliente.get(idcliente).iva
            series = [(s.id, s.get_next_numfactura()) for s in 
                        pclases.SerieFacturasVenta.select(orderBy = "prefijo")]
            idserie = utils.dialogo_combo("SERIE DE FACTURAS", 
                                          "Seleccione una serie:", 
                                          series, 
                                          self.wids['ventana'])
            if idserie != None:
                objeto_anterior = self.objeto
                if objeto_anterior != None:
                    objeto_anterior.notificador.desactivar()
                serie = pclases.SerieFacturasVenta.get(idserie)
                numfactura = serie.get_next_numfactura()
                self.objeto = self.clase(bloqueada = False, 
                                         clienteID = idcliente, 
                                         serieFacturasVentaID = idserie, 
                                         numfactura = numfactura, 
                                         iva = ivadefecto)  
                numfactura = serie.get_next_numfactura(commit = True)
                assert numfactura == self.objeto.numfactura
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
                                         texto="Introduzca número de factura:", 
                                         padre = self.wids['ventana']) 
        if a_buscar != None:
            try:
                ida_buscar = int(a_buscar)
            except ValueError:
                ida_buscar = -1
            campos_busqueda = (self.clase.q.numfactura, ) 
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
            resultados = self.clase.select(pclases.AND(criterio, 
                                            self.clase.q.proveedorID == None))
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
            if col.name ==  "comision":
                try:
                    self.objeto.comision = utils._float(self.wids['e_comision'].get_text())
                except ValueError:
                    self.objeto.comision = 0
                    self.wids['e_comision'].set_text('0')
                continue
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
        # USABILIDAD: Si al intentar borrar, falla por tener cobros o algo, 
        # podría preguntar al usuario si continuar (usando destroy_en_casdcada)
        # o cancelar el resto del borrado (dejando la factura como está o 
        # restaurando los valores anteriores). Seguramente el usuario está tan 
        # acojonado por borrar algo, que si falla acabará respondiendo que 
        # «No» en el segundo diálogo por miedo a empeorar las cosas, dejando 
        # el sistema en la peor situación posible: ni está la factura como 
        # al principio (cosa que desearía el usuario deseando que se lo 
        # trague la tierra por intentar borrar nada) ni se ha eliminado com-
        # pletamente, que era lo que quería al principio, y sin rastro de 
        # cobros de facturas vacías ni datos parciales en registros 
        # relacionados.
        # ¿Qué hacer? Supongo que si quiere borrar será por algo, y ya hay 
        # un diálogo bastante claro como para evitar borrados accidentales. 
        # Así que destroy en cascada y a huir.
        self.objeto.notificador.desactivar()
        for ldv in self.objeto.lineasDeVenta:
            ldv.facturaVenta = None
        for vto in self.objeto.vencimientosCobro:
            vto.destroySelf()
        contador = self.objeto.serieFacturasVenta
        numfactura = self.objeto.numfactura
        try:
            #self.objeto.destroySelf()
            self.objeto.destroy_en_cascada()
        except Exception, e:
            self.logger.error("facturas_venta.py::borrar -> %s ID %d no se pudo eliminar. Excepción: %s." % (self.objeto.sqlmeta.table, self.objeto.id, e))
            utils.dialogo_info(titulo = "%s NO BORRADO" % self.clase.sqlmeta.table.upper(), 
                               texto = "%s no se pudo eliminar.\n\nSe generó un informe de error en el «log» de la aplicación." % self.clase.sqlmeta.table.title(),
                               padre = self.wids['ventana'])
            self.actualizar_ventana()
            return
        else:
    		# DONE: Decrementar contador
            contador.sync()
            intnumfactura = contador.get_num_numfactura(numfactura)
            if contador.contador - 1 == intnumfactura:
                # El contador guarda siempre el siguiente entero para el 
                # número de factura.
                # OJO: Solo decremento en 1 si era la última factura. Si hay 
                # huecos anteriores, no es resposabilidad de esta ventana el 
                # corregirlos. Que lo haga el administrador desde la ventana 
                # de contadores.
                contador.contador -= 1
                contador.syncUpdate()
        self.objeto = None
        self.ir_a_primero()

    def cambiar_cantidad(self, cell, path, texto):
        model = self.wids['tv_ldvs'].get_model()
        idldv = model[path][-1]
        ldv = pclases.LineaDeVenta.get(idldv)
        try:
            ldv.cantidad = utils._float(texto)
            ldv.syncUpdate()
            # self.rellenar_servicios()
            model[path][1] = ldv.cantidad
            model[path][3] = ldv.calcular_importe(iva = False)
            self.rellenar_totales()
            self.rellenar_vencimientos()    
                # Para que verifique si los totales coinciden
        except:
            utils.dialogo_info(titulo = "ERROR DE FORMATO", 
                               texto = 'Formato numérico incorrecto', 
                               padre = self.wids['ventana'])

    def cambiar_precio(self, cell, path, texto):
        model = self.wids['tv_ldvs'].get_model()
        idldv = model[path][-1]
        ldv = pclases.LineaDeVenta.get(idldv)
        try:
            ldv.precio = utils._float(texto)
            ldv.syncUpdate()
            model[path][2] = ldv.precio
            model[path][3] = ldv.calcular_importe(iva = False)
            self.rellenar_totales()
            self.rellenar_vencimientos()
                # Para que verifique si los totales coinciden
        except:
            utils.dialogo_info(titulo = "ERROR DE FORMATO", 
                               texto = 'Formato numérico incorrecto', 
                               padre = self.wids['ventana'])

    def crear_servicio(self):
        # Datos a pedir: Concepto, descuento y precio... Bah, el descuento 
        # que lo cambie en el TreeView.
        concepto = utils.dialogo_entrada(titulo = "CONCEPTO",
                    texto = 'Introduzca el concepto del servicio facturable:', 
                    padre = self.wids['ventana'])
        if concepto != None:
            precio = utils.dialogo_entrada(titulo = "PRECIO", 
                    texto = 'Introduzca el precio unitario sin IVA:', 
                    padre = self.wids['ventana'])
            if precio != None:
                try:
                    precio = utils._float(precio)
                    servicio = pclases.Servicio(facturaVenta = self.objeto,
                                                concepto = concepto,
                                                precio = precio,
                                                descuento = 0)
                    # Cantidad es 1 por defecto.
                except Exception, e:
                    utils.dialogo_info(texto = """
                    Ocurrió un error al crear el servicio.                   
                    Asegúrese de haber introducido correctamente los datos,  
                    especialmente el precio (que no debe incluir símbolos    
                    monetarios), y vuelva a intentarlo.

                    DEBUG:
                    %s
                    """ %(e), 
                                       titulo = "ERROR", 
                                       padre = self.wids['ventana'])
                    return
                self.rellenar_servicios()
                self.rellenar_vencimientos()    
                    # Para que verifique si los totales coinciden

    def cambiar_concepto_srv(self, cell, path, texto):
        model = self.wids['tv_servicios'].get_model()
        idsrv = model[path][-1]
        srv = pclases.Servicio.get(idsrv)
        srv.concepto = texto
        self.rellenar_servicios()

    def cambiar_cantidad_srv(self, cell, path, texto):
        model = self.wids['tv_servicios'].get_model()
        idsrv = model[path][-1]
        srv = pclases.Servicio.get(idsrv)
        try:
            srv.cantidad = utils._float(texto)
            srv.syncUpdate()
            # self.rellenar_servicios()
            model[path][0] = srv.cantidad
            model[path][4] = srv.precio * (1.0 - srv.descuento) * srv.cantidad
            self.rellenar_totales()
            self.rellenar_vencimientos()    
                # Para que verifique si los totales coinciden
        except:
            utils.dialogo_info(titulo = "ERROR DE FORMATO", 
                               texto = 'Formato numérico incorrecto', 
                               padre = self.wids['ventana'])

    def cambiar_precio_srv(self, cell, path, texto):
        model = self.wids['tv_servicios'].get_model()
        idsrv = model[path][-1]
        srv = pclases.Servicio.get(idsrv)
        try:
            srv.precio = utils._float(texto)
            # print srv.precio, utils._float(texto), texto
            self.rellenar_servicios()
            self.rellenar_vencimientos()
                # Para que verifique si los totales coinciden
        except:
            utils.dialogo_info(titulo = "ERROR DE FORMATO", 
                               texto = 'Formato numérico incorrecto', 
                               padre = self.wids['ventana'])

    def cambiar_descuento_srv(self, cell, path, texto):
        model = self.wids['tv_servicios'].get_model()
        idsrv = model[path][-1]
        srv = pclases.Servicio.get(idsrv)
        try:
            try:
                srv.descuento = utils.parse_porcentaje(texto)
            except ValueError:
                srv.descuento = 0
            if srv.descuento > 1.0:
                srv.descuento /= 100.0
            self.rellenar_servicios()
            self.rellenar_vencimientos()
                # Para que verifique si los totales coinciden
        except:
            utils.dialogo_info(titulo = "ERROR DE FORMATO", 
                               texto = 'Formato numérico incorrecto', 
                               padre = self.wids['ventana'])

    def rellenar_servicios(self):
        model = self.wids['tv_servicios'].get_model()
        model.clear()
        for servicio in self.objeto.servicios:
            # print servicio.precio, utils._float(servicio.precio)
            model.append((servicio.cantidad,
                          servicio.concepto, 
                          servicio.precio, 
                          servicio.descuento, 
                          servicio.calcular_importe(),
                          servicio.id))
        self.rellenar_totales()

    def add_srv(self, boton):
        self.crear_servicio()

    def clon_srv(self, boton):
        """
        Busca un servicio existente en la BD (previamente facturado, 
        por tanto) y crea un nuevo servicio idéntico pero asociado a
        la factura actual.
        """
        a_buscar = utils.dialogo_entrada(titulo = 'BUSCAR SERVICIO FACTURADO',
                                         texto = 'Introduzca un concepto (o parte) ya facturado:', 
                                         padre = self.wids['ventana'])
        servicios = pclases.Servicio.select(pclases.Servicio.q.concepto.contains(a_buscar), orderBy = "concepto")
        filas = [(s.id,
                  s.concepto, 
                  s.precio, 
                  (s.facturaVenta and s.facturaVenta.numfactura) or (s.prefactura and s.prefactura.numfactura) or '', 
                  (s.facturaVenta and s.facturaVenta.cliente and s.facturaVenta.cliente.nombre) or 
                    (s.prefactura and s.prefactura.cliente and s.prefactura.cliente.nombre) or '')
                  for s in servicios]
        res = utils.dialogo_resultado(filas,
                                      "SELECCIONE SERVICIO",
                                      cabeceras = ('ID', 'Concepto', 'Precio', 'Facturado en', 'Cliente'),
                                      multi = True, 
                                      padre = self.wids['ventana'])
        if res[0] > 0:
            for idservicio in res:
                servicio = pclases.Servicio.get(idservicio)
                nuevo_servicio = pclases.Servicio(facturaVenta = self.objeto,
                                                  concepto = servicio.concepto,
                                                  precio = servicio.precio,
                                                  descuento = servicio.descuento)
            self.rellenar_servicios()
            self.rellenar_vencimientos()    # Para que verifique si los totales coinciden
        
    def drop_srv(self, boton):
        if self.wids['tv_servicios'].get_selection().count_selected_rows()!=0:
            model,iter=self.wids['tv_servicios'].get_selection().get_selected()
            idservicio = model[iter][-1]
            servicio = pclases.Servicio.get(idservicio)
            servicio.facturaVenta = None
            if servicio.albaranSalida == None:
                servicio.destroySelf()  # No debería saltar ninguna excepción. 
            self.rellenar_servicios()

    def rellenar_vencimientos(self):
        if self.objeto:
            model = self.wids['tv_vencimientos'].get_model()
            model.clear()
            total_vtos = 0.0
            total_cobros = 0.0
            vencido = 0.0
            vtos = self.objeto.vencimientosCobro[:]
            vtos.sort(utils.cmp_fecha_id)
            for vto in vtos:
                model.append((utils.str_fecha(vto.fecha), 
                              utils.float2str(vto.importe), 
                              vto.id))
                total_vtos += vto.importe
                if vto.fecha >= mx.DateTime.localtime():
                    vencido += vto.importe
            model = self.wids['tv_cobros'].get_model()
            model.clear()
            cobros = self.objeto.cobros[:]
            cobros.sort(utils.cmp_fecha_id)
            for cobro in cobros:
                model.append((utils.str_fecha(cobro.fecha), 
                              utils.float2str(cobro.importe), 
                              cobro.observaciones, 
                              cobro.id))
                total_cobros += cobro.importe
            self.wids['e_total_vtos'].set_text(utils.float2str(total_vtos))
            self.wids['e_total_pagado'].set_text(utils.float2str(total_cobros))
            self.wids['e_total_vencido'].set_text(utils.float2str(vencido))
            self.wids['e_pendiente'].set_text(utils.float2str(total_vtos - total_cobros))
            if (self.objeto.vencimientosCobro and 
                (int(round(total_vtos * 100)) != 
                    int(round(self.objeto.calcular_importe_total(iva = True)*100)))):
                utils.dialogo_info(titulo = "VERIFIQUE LOS VENCIMIENTOS", 
                                   texto = "El importe total de los vencimientos no coincide con el importe total de la factura.", 
                                   padre = self.wids['ventana'])

    def crear_vtos_defecto(self, boton):
        if self.objeto:
            vtos_creados = self.objeto.crear_vencimientos_por_defecto()
            if not vtos_creados:
                utils.dialogo_info(
                    titulo = "CLIENTE SIN VENCIMIENTOS DEFINIDOS", 
                    texto = "El cliente no tiene definidos vencimientos por\n"
                            "defecto. Se creará un vencimiento genérico, \n"
                            "pero asegúrese de completar la información del\n"
                            "cliente si quiere usar esta funcionalidad.", 
                    padre = self.wids['ventana'])
                self.objeto.crear_vencimientos_por_defecto(forzar = True)
            self.rellenar_vencimientos()

    def cambiar_fecha_vto(self, cell, path, texto):
        model = self.wids['tv_vencimientos'].get_model()
        id = model[path][-1]
        vto = pclases.VencimientoCobro.get(id)
        try:
            fecha = utils.parse_fecha(texto)
        except:
            utils.dialogo_info(titulo = "ERROR DE FORMATO", 
                               texto = "El texto %s no es una fecha válida." % (
                                texto), 
                               padre = self.wids['ventana'])
        else:
            vto.fecha = fecha
            self.rellenar_vencimientos()

    def cambiar_importe_vto(self, cell, path, texto):
        model = self.wids['tv_vencimientos'].get_model()
        id = model[path][-1]
        vto = pclases.VencimientoCobro.get(id)
        try:
            importe = utils._float(texto)
        except:
            utils.dialogo_info(titulo = "ERROR DE FORMATO", 
                               texto = "El texto %s no es un importe válido."%(
                                texto), 
                               padre = self.wids['ventana'])
        else:
            vto.importe = importe
            self.rellenar_vencimientos()

    def cambiar_fecha_cobro(self, cell, path, texto):
        model = self.wids['tv_cobros'].get_model()
        id = model[path][-1]
        cobro = pclases.Cobro.get(id)
        try:
            fecha = utils.parse_fecha(texto)
        except:
            utils.dialogo_info(titulo = "ERROR DE FORMATO", 
                               texto = "El texto %s no es una fecha válida." % (
                                texto), 
                               padre = self.wids['ventana'])
        else:
            cobro.fecha = fecha
            self.rellenar_vencimientos()

    def cambiar_importe_cobro(self, cell, path, texto):
        model = self.wids['tv_cobros'].get_model()
        id = model[path][-1]
        cobro = pclases.Cobro.get(id)
        try:
            importe = utils._float(texto)
        except:
            utils.dialogo_info(titulo = "ERROR DE FORMATO", 
                               texto = "El texto %s no es un importe válido."%(
                                texto), 
                               padre = self.wids['ventana'])
        else:
            cobro.importe = importe
            self.rellenar_vencimientos()

    def cambiar_observaciones_cobro(self, cell, path, texto):
        model = self.wids['tv_cobros'].get_model()
        id = model[path][-1]
        cobro = pclases.Cobro.get(id)
        cobro.observaciones = texto
        self.rellenar_vencimientos()

    def add_vto(self, boton):
        totalfra = self.objeto.calcular_importe_total(iva = True)
        totalvto = sum([v.importe for v in self.objeto.vencimientosCobro])
        importe_restante = totalfra - totalvto
        pclases.VencimientoCobro(facturaVenta = self.objeto, 
                                 importe = importe_restante, 
                                 fecha = mx.DateTime.localtime())
        self.rellenar_vencimientos()

    def drop_vto(self, boton):
        model, iter=self.wids['tv_vencimientos'].get_selection().get_selected()
        if iter:
            idvto = model[iter][-1]
            vto = pclases.VencimientoCobro.get(idvto)
            vto.destroySelf()
            self.rellenar_vencimientos()

    def add_cobro(self, boton):
        pclases.Cobro(facturaVenta = self.objeto, 
                      importe = 0.0, 
                      fecha = mx.DateTime.localtime(), 
                      observaciones = "")
        self.rellenar_vencimientos()

    def drop_cobro(self, boton):
        model, iter=self.wids['tv_cobros'].get_selection().get_selected()
        if iter:
            idcobro = model[iter][-1]
            cobro = pclases.Cobro.get(idcobro)
            cobro.destroySelf()
        self.rellenar_vencimientos()

    def imprimir(self, boton):
        """
        Imprime la factura.
        """
        r = utils.dialogo(titulo = "¿IMPRIMIR SOLO DATOS?", 
                texto = "Presione «Sí» para imprimir la factura en una hoja "
                        "preimpresa.", 
                cancelar = True, 
                defecto = gtk.RESPONSE_YES, 
                tiempo = 10, 
                padre = self.wids['ventana'])
        if r != gtk.RESPONSE_CANCEL:
            try:
                import factura
                from informes import abrir_pdf
            except ImportError:
                sys.path.append(os.path.join("..", "informes"))
                import factura
                from informes import abrir_pdf
            fpdf = factura.go_from_facturaVenta(self.objeto, solo_texto = r)
            if fpdf:
                abrir_pdf(fpdf)


if __name__ == "__main__":
    p = FacturasVenta()

