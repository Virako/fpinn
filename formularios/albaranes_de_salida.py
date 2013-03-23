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
## albaranes de salida.py 
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

class AlbaranesDeSalida(Ventana, VentanaGenerica):
    CLASE = pclases.AlbaranSalida
    VENTANA = os.path.join("..", "ui", "albaranes_de_salida.glade")
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
                       'b_drop_ldv/clicked': self.drop_ldv, 
                       'b_add_ldv/clicked': self.add_ldv, 
                       'b_agrupar/clicked': self.agrupar_ldvs,
                       'b_guardar_transp/clicked': self.guardar_transportista, 
                       'b_imprimir/clicked': self.imprimir, 
                       'b_fecha/clicked': self.cambiar_fecha, 
                       'e_nombre_transp/insert-text': 
                                self.activar_guardar_transp, 
                       'e_agencia_transp/insert-text': 
                                self.activar_guardar_transp, 
                       'e_telefono_transp/insert-text': 
                                self.activar_guardar_transp, 
                       'e_matricula_transp/insert-text': 
                                self.activar_guardar_transp, 
                       'cbe_transportistaID/changed': 
                                self.cambiar_transportista, 
                       'b_calcularcomision/clicked': self.calcular_comision
                      }
        self.add_connections(connections)
        self.inicializar_ventana()
        if self.objeto == None:
            self.ir_a_primero()
        else:
            self.ir_a(objeto)
        gtk.main()

    def calcular_comision(self, boton):
        """
        Sobreescribe el valor de la comisión del albarán con el cálculo 
        del total del mismo por la comisión en porcentaje por defecto 
        del cliente.
        """
        if self.objeto:
            try:
                porcentaje_comision = self.objeto.cliente.comision
            except AttributeError:
                porcentaje_comision = 1.0   # No cliente. No comisión.
            else:
                importe_mercancia = (self.objeto.calcular_importe() 
                                     - self.objeto.transporte 
                                     - self.objeto.comision 
                                     - self.objeto.descarga)
                comision = importe_mercancia * porcentaje_comision
                self.objeto.comision = comision
                self.actualizar_ventana()

    def cambiar_fecha(self, boton):
        try:
            temp = utils.mostrar_calendario(
                utils.parse_fecha(self.wids['e_fecha'].get_text()), 
                padre = self.wids['ventana'])
        except:
            temp = utils.mostrar_calendario(padre = self.wids['ventana'])
        self.wids['e_fecha'].set_text(utils.str_fecha(temp))
        self.objeto.fecha = mx.DateTime.DateTimeFrom(day = temp[0], 
                                                     month = temp[1], 
                                                     year = temp[2])
        self.objeto.make_swap()

    def activar_guardar_transp(self, entry, nuevotexto, longnuevotexto, pos):
        """
        Activa el botón de guardar transportista.
        Este callback está asociado al cambio de texto de los entries del 
        transportista por el usuario, por tanto se supone que ha cambiado 
        los datos del transportista y querrá guardarlos.
        Verifica antes que haya un transportista seleccionado al que 
        modificar los datos.
        Si no hay transportista y va a crear uno nuevo, no es esta función 
        el que controla el botón de guardar, sino el del propio combobox.
        """
        cbe = self.wids['cbe_transportistaID']
        id = utils.combo_get_value(cbe)
        self.wids['b_guardar_transp'].set_sensitive(id != None)

    def cambiar_transportista(self, cbe):
        """
        Callback para la señal "changed" del combo de transportista.
        Si el transportista escrito no está en la tabla de transportistas, 
        habilita el botón guardar para que escriba la información del mismo.
        Si el transportista ya existe, rellena los campos con los datos 
        del mismo.
        """
        texto = cbe.child.get_text()
        id = utils.combo_get_value(cbe)
        if id != None:
            self.rellenar_datos_transp(id)
        self.wids['b_guardar_transp'].set_sensitive(texto != "" and id == None)

    def rellenar_datos_transp(self, id):
        t = pclases.Transportista.get(id)
        self.wids['e_nombre_transp'].set_text(t.nombre)
        self.wids['e_agencia_transp'].set_text(t.agencia)
        self.wids['e_telefono_transp'].set_text(t.telefono)
        self.wids['e_matricula_transp'].set_text(t.matricula)

    def guardar_transportista(self, boton):
        """
        Guarda los datos de los "entries" del transportista en un nuevo 
        registro y deshabilita el botón.
        """
        entry_dni = self.wids['cbe_transportistaID'].child
        dni = entry_dni.get_text()
        nombre = self.wids['e_nombre_transp'].get_text()
        agencia = self.wids['e_agencia_transp'].get_text()
        telefono = self.wids['e_telefono_transp'].get_text()
        matricula = self.wids['e_matricula_transp'].get_text()
        id = utils.combo_get_value(self.wids['cbe_transportistaID'])
        if id == None:  # Creo nuevo.
            transp = pclases.Transportista(dni = dni, 
                                           nombre = nombre, 
                                           agencia = agencia, 
                                           telefono = telefono, 
                                           matricula = matricula)
            self.objeto.transportista = transp
        else:           # Actualizo existente.
            t = pclases.Transportista.get(id)
            t.nombre = nombre
            t.agencia = agencia
            t.telefono = telefono
            t.matricula = matricula
        boton.set_sensitive(False)

    def agrupar_ldvs(self, b):
        """
        Agrupa las líneas de venta seleccionadas en un palé.
        Si una o varias de ellas ya es un palé, se usará el primero como  
        palé destino en lugar de crear uno.
        """
        selection = self.wids['tv_ldvs'].get_selection()
        model, paths = selection.get_selected_rows()
        try:
            idpale = [model[path][-1].split(":")[1] 
                      for path in paths
                      if model[path][-1].split(":")[0] == "P"][0]
            pale = pclases.Pale.get(idpale)
        except IndexError:
            pale = pclases.Pale()
        cambio = False
        for path in paths:
            tipo, ldvid = model[path][-1].split(":")
            if tipo == "LDV":
                ldv = pclases.LineaDeVenta.get(ldvid)
                ldv.pale = pale
                cambio = True
        if cambio:
            self.rellenar_ldvs()

    def add_ldv(self, b):
        """
        Añade una línea de venta de un producto al albarán.
        El precio del producto para la tarifa del cliente tiene 
        preferencia sobre el precio por defecto del producto configurado 
        en la ventana de productos de venta.
        """
        producto, cantidad = buscar_producto(self.wids['ventana'])
        if producto and cantidad != None:
            if not producto.envase:
                utils.dialogo_info(titulo = "PRODUCTO SIN ENVASE", 
                                   texto = "Debe especificar un envase por de"\
                                           "fecto en la configuración del pro"\
                                           "ducto.", 
                                   padre = self.wids['ventana'])
            else:
                #try:
                #    tarifa = self.objeto.cliente.tarifa
                #except AttributeError:
                #    tarifa = None
                #try:
                #    precio_defecto = tarifa.get_precio(producto)
                #except (AttributeError, ValueError):
                #    if producto.precio:
                #        precio_defecto = producto.precio.get_importe()
                #    else:
                #        precio_defecto = 0.0
                #    tarifa = None
                # CWT:
                precio_defecto = 0.0
                tarifa = None
                ldv = pclases.LineaDeVenta(envase = producto.envase, 
                                           productoVenta = producto, 
                                           albaranSalida = self.objeto, 
                                           facturaVenta = None, 
                                           pale = None, 
                                           tarifa = tarifa, 
                                           cantidad = cantidad, 
                                           precio = precio_defecto)
                producto.actualizar_existencias_envases(-cantidad)
                self.rellenar_ldvs()

    def drop_ldv(self, boton):
        selection = self.wids['tv_ldvs'].get_selection()
        model, paths = selection.get_selected_rows()
        errors = 0
        for path in paths:
            tipo, ldvid = model[path][-1].split(":")
            if tipo == "LDV":
                ldv = pclases.LineaDeVenta.get(ldvid)
                for cldv in ldv.conceptosLdv:
                    cldv.destroySelf()
                try:
                    ldv.destroySelf()
                except Exception, msg:
                    errors += 1
            elif tipo == "P":
                pale = pclases.Pale.get(ldvid)
                ldvs = pale.lineasDeVenta[:]
                for ldv in ldvs:
                    ldv.pale = None
                try:
                    pale.destroySelf()
                except:
                    errors += 1
                    for ldv in ldvs:
                        ldv.pale = pale
            cantidad = ldv.cantidad 
            producto = ldv.productoVenta
            producto.actualizar_existencias_envases(+cantidad)
        if errors:
            utils.dialogo_info(titulo = "ERROR", 
                               texto = "Se produjeron errores al eliminar las"\
                                       " líneas seleccionadas.\nTal vez estén"\
                                       " implicadas en facturas que impiden s"\
                                       "u borrado.\n\nTexto de depuración del"\
                                       " último error:\n%s" % msg, 
                               padre = self.wids['ventana'])
        if paths:
            self.rellenar_ldvs()

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
                if widname_glade == "b_fecha":
                    continue    # No es el entry de la fecha, es el botón.
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
        cols = (('Producto', 'gobject.TYPE_STRING', True, True, True, 
                    self.cambiar_cod_pale),
                ('Cantidad', 'gobject.TYPE_STRING', True, True, False, 
                    self.cambiar_cantidad), 
                ('Precio', 'gobject.TYPE_STRING', True, True, False, 
                    self.cambiar_precio), 
                #CWT: No mostrar envase en albarán. Nobody expects the spanish 
                #     inquisition!
                # ('Envase', 'gobject.TYPE_STRING', False, True, False, None), 
                ('Bultos', 'gobject.TYPE_INT', True, True, False, 
                    self.cambiar_bultos), 
                ('Parcela', 'gobject.TYPE_STRING', True, True, True, None),  
                ('ID', 'gobject.TYPE_STRING', False, False, False, None))
        utils.preparar_treeview(self.wids['tv_ldvs'], cols, multi = True)
        #CWT: self.cambiar_por_combo(self.wids['tv_ldvs'], 3)
        self.cambiar_por_combo(self.wids['tv_ldvs'], 4)
        self.wids['tv_ldvs'].get_column(1).get_cell_renderers()[0]\
            .set_property("xalign", 0.9)
        self.wids['tv_ldvs'].get_column(2).get_cell_renderers()[0]\
            .set_property("xalign", 0.9)
        self.wids['tv_ldvs'].get_column(3).get_cell_renderers()[0]\
            .set_property("xalign", 0.9)
        utils.rellenar_lista(self.wids['cbe_clienteID'], 
                             [(p.id, p.nombre) for p in 
                                pclases.Cliente.select(orderBy = "nombre")])
        self.wids['b_guardar_transp'].set_sensitive(False)
        if pclases.Envase.select().count() == 0:
            utils.dialogo_info(titulo = "NO DATOS ENVASE", 
                               texto = "Necesita dar de alta al menos un tipo"\
                                       " de envase antes de crear albaranes d"\
                                       "e salida.", 
                               padre = self.wids['ventana'])
            #sys.exit()
            self.wids['b_buscar'].set_property("visible", False)
            self.wids['b_nuevo'].set_property("visible", False)
            self.wids['b_imprimir'].set_property("visible", False)

    def cambiar_cod_pale(self, cell, path, text):
        """
        Si la línea seleccionada corresponde a un palé, se cambia el 
        código (que aparece en la columna "Producto") por el texto 
        tecleado.
        """
        model = self.wids['tv_ldvs'].get_model()
        tipo, id = model[path][-1].split(":")
        if tipo == "P":
            pale = pclases.Pale.get(id)
            pale.codigo = text
            model[path][0] = pale.codigo

    def cambiar_cantidad(self, cell, path, text): 
        """
        Si la línea editada corresponde a una línea de venta, parsea el texto
        introducido y cambia la cantidad por el número obtenido.
        También recalcula los bultos en función de esta nueva cantidad y la 
        capacidad del envase.
        Si el resultado no es un número entero, redondea la cantidad de bultos 
        al entero superior. 
        Actualiza también los bultos y cantidades de la línea padre.
        """
        model = self.wids['tv_ldvs'].get_model()
        tipo, id = model[path][-1].split(":")
        if tipo == "LDV":
            try:
                num = utils._float(text)
            except:
                utils.dialogo_info(titulo = "ERROR DE FORMATO", 
                                   texto = "El texto %s no es un número."%text,
                                   padre = self.wids['ventana'])
            else:
                ldv = pclases.LineaDeVenta.get(id)
                cantidad = ldv.cantidad - num
                ldv.cantidad = num
                bultos = ldv.calcular_bultos()
                model[path][1] = utils.float2str(ldv.cantidad, autodec = True)
                #CWT: model[path][4] = bultos
                model[path][3] = bultos
                linea_pale = model[path].parent
                if linea_pale:
                    #CWT: bultos = [model[p.path][4] 
                    bultos = [model[p.path][3] 
                              for p in linea_pale.iterchildren()]
                    #linea_pale[4] = sum(bultos)
                    linea_pale[3] = sum(bultos)
                    cantidades = [utils._float(model[p.path][1]) 
                                  for p in linea_pale.iterchildren()]
                    linea_pale[1] = utils.float2str(sum(cantidades), 
                                                    autodec = True)
                producto = ldv.productoVenta
                producto.actualizar_existencias_envases(cantidad)

    def cambiar_bultos(self, cell, path, text): 
        """
        Si la línea editada corresponde a una línea de venta, parsea el texto
        introducido y cambia la cantidad por el resultado de multiplicar 
        la capacidad del envase por los bultos escritos.
        También recalcula los bultos en función de esta nueva cantidad y la 
        capacidad del envase en lugar de conservar el valor escrito (aunque 
        deben coincidir).
        Si el resultado no es un número entero, redondea la cantidad de bultos 
        al entero superior. 
        Actualiza también los bultos y cantidades de la línea padre.
        """
        model = self.wids['tv_ldvs'].get_model()
        tipo, id = model[path][-1].split(":")
        if tipo == "LDV":
            try:
                num = utils._float(text)
            except:
                utils.dialogo_info(titulo = "ERROR DE FORMATO", 
                                   texto = "El texto %s no es un número."%text,
                                   padre = self.wids['ventana'])
            else:
                ldv = pclases.LineaDeVenta.get(id)
                bultos = num
                num = ldv.envase.kg * bultos
                cantidad = ldv.cantidad - num
                ldv.cantidad = num
                bultos = ldv.calcular_bultos()
                model[path][1] = utils.float2str(ldv.cantidad, autodec = True)
                #CWT: model[path][4] = bultos
                model[path][3] = bultos
                linea_pale = model[path].parent
                if linea_pale:
                    # CWT: bultos = [model[p.path][4] 
                    bultos = [model[p.path][3] 
                              for p in linea_pale.iterchildren()]
                    #linea_pale[4] = sum(bultos)
                    linea_pale[3] = sum(bultos)
                    cantidades = [utils._float(model[p.path][1]) 
                                  for p in linea_pale.iterchildren()]
                    linea_pale[1] = utils.float2str(sum(cantidades), 
                                                    autodec = True)
                producto = ldv.productoVenta
                producto.actualizar_existencias_envases(cantidad)

    def cambiar_precio(self, cell, path, text):
        """
        Cambia el precio de la LDV. 
        """
        model = self.wids['tv_ldvs'].get_model()
        tipo, id = model[path][-1].split(":")
        if tipo == "LDV":
            try:
                num = utils._float(text)
            except:
                utils.dialogo_info(titulo = "ERROR DE FORMATO", 
                                   texto = "El texto %s no es un número."%text,
                                   padre = self.wids['ventana'])
            else:
                ldv = pclases.LineaDeVenta.get(id)
                if ldv.facturaVenta and ldv.facturaVenta.bloqueada:
                    utils.dialogo_info(titulo = "OPERACIÓN NO PERMITIDA", 
                        texto = "La línea se encuentra facturada en %s, que "
                                "no permite cambios. Corrija allí el precio "\
                                "si fuera necesario." % (
                                    ldv.facturaVenta.numfactura), 
                        padre = self.wids['ventana'])
                else:
                    ldv.precio = num
                    model[path][2] = utils.float2str(ldv.precio)
                    # CWT: ¡Cambio en los requisitos! Ya no se relacionan 
                    # LDVs con tarifas. ¿Y cómo vamos a calcular los gastos 
                    # entonces? ¿A qué tarifa pertenece un precio? ¿Solo 
                    # habrá una en toda la historia de la aplicación? Mmm...
                    #precio_correcto = False
                    #if num == 0:
                    #    ldv.precio = num
                    #    model[path][2] = utils.float2str(ldv.precio)
                    #    precio_correcto = True
                    #    ldv.tarifa = None
                    #else:
                    #    for precio in ldv.productoVenta.precios:
                    #        if round(precio.get_importe(), 2) == num:
                    #            ldv.precio = num
                    #            ldv.tarifa = precio.tarifa
                    #            model[path][2] = utils.float2str(ldv.precio)
                    #            precio_correcto = True
                    #            break
                    #if not precio_correcto:
                    #    self.preguntar_si_cambiar_tarifa(ldv, num)
                    #    ldv.sync()
                    #    model[path][2] = utils.float2str(ldv.precio)
                    #    # Si hay más líneas del mismo producto, también debo 
                    #    # actualizarlas.
                    #    if len([l for l in self.objeto.lineasDeVenta
                    #            if l.precio == ldv.precio]) > 1:
                    #        self.rellenar_ldvs()
                    ldv.actualizar_conceptos()

    def preguntar_si_cambiar_tarifa(self, ldv, nuevo_precio):
        """
        Muestra los precios disponibles según las tarifas y ofrece la 
        opción de cambiar alguna de ellas para ajustarla al precio 
        introducido.
        """
        precios_producto = ldv.productoVenta.precios[:]
        precios_producto.sort(key = lambda p: p.get_importe())
        precios = [(p.id, "%s (%s)" % (
                        p.get_importe(), 
                        p.tarifa and p.tarifa.nombre or "SIN TARIFA"))
                    for p in precios_producto]
        txtprecios = "\n".join([" - %s" % p[1] for p in precios])
        idprecio = utils.dialogo_combo(titulo = "PRECIO INCORRECTO", 
                    texto = "El precio tecleado no se corresponde con ninguna"\
                            " tarifa.\nLos precios válidos son:\n%s\n\nSelecc"\
                            "ione una tarifa si desea cambiarla por el precio"\
                            " tecleado." % txtprecios, 
                    ops = precios,  
                    padre = self.wids['ventana'])
        if idprecio:
            precio = pclases.Precio.get(idprecio)
            if utils.dialogo(titulo = "¿CAMBIAR TARIFA?", 
                             texto = "Ha elegido cambiar en la tarifa %s el p"\
                                     "recio %s por %s.\nSimultáneamente se ca"\
                                     "mbiará el precio para todos los albaran"\
                                     "es no facturados.\n\n¿Está seguro de qu"\
                                     "erer actualizar el precio?" % (
                                precio.tarifa and precio.tarifa.nombre or "", 
                                 utils.float2str(precio.get_importe()), 
                                 utils.float2str(nuevo_precio)), 
                             padre = self.wids['ventana']):
                precio.actualizar_a(nuevo_precio, 
                                    actualizar_ldvs_no_facturadas = True)
                ldv.tarifa = precio.tarifa

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
        ws = (["b_borrar", "vbox1", "vbox3"] + 
              [self.adaptador.get_adaptadores()[col]['widget'].name 
              for col in self.adaptador.get_adaptadores().keys()]) 
            # b_nuevo y b_buscar no se activan/desactivan aquí, sino en el
            # chequeo de permisos.
        for w in ("cmrID", ): 
            ws.remove(w)
        for w in ws:
            try:
                self.wids[w].set_sensitive(s)
            except Exception, msg:
                print "Widget problemático:", w, "Excepción:", msg
                #import traceback
                #traceback.print_last()
        if chequear_permisos:
            self.check_permisos(
                nombre_fichero_ventana = "albaranes_de_salida.py")

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
                              r.numalbaran, 
                              r.cliente and r.cliente.nombre or "", 
                              utils.str_fecha(r.fecha)))
        id = utils.dialogo_resultado(filas_res,
                                     titulo = 'SELECCIONE %s' % (
                                        self.clase.sqlmeta.table.upper()),
                                     cabeceras = ('ID', 
                                                  'Número', 
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
        if self.objeto.cliente and (self.objeto.nombreEnvio == 
            self.objeto.direccion == self.objeto.cp == self.objeto.ciudad ==
            self.objeto.telefono == self.objeto.pais == ""):
            self.objeto.nombreEnvio = self.objeto.cliente.nombre
            self.objeto.direccion = self.objeto.cliente.direccion
            self.objeto.cp = self.objeto.cliente.cp
            self.objeto.ciudad = self.objeto.cliente.ciudad
            self.objeto.telefono = self.objeto.cliente.telefono
            self.objeto.pais = self.objeto.cliente.pais
        adaptadores = self.adaptador.get_adaptadores()
        for col in adaptadores.keys():
            if col.name == "comision":
                # UGLY AND DIRTY HACK: Es para no tocar la clase Adapter. Aquí la comisión es en ninerito, no en porcentaje.
                self.wids['e_comision'].set_text(utils.float2str(self.objeto.comision, autodec = True, precision = 2))
            else:
                adaptadores[col]['mostrar'](self.objeto)
        self.rellenar_ldvs()
        self.objeto.make_swap()
        self.wids['ventana'].set_title(self.objeto.get_info())
        numfacturas = utils.unificar([ldv.facturaVenta.numfactura 
                                      for ldv in self.objeto.lineasDeVenta 
                                      if ldv.facturaVenta])
        numfacturas = ", ".join(numfacturas)
        self.wids['e_facturas'].set_text(numfacturas)

    def rellenar_ldvs(self):
        """
        Limpia e introduce en el model las líneas de venta del albarán.
        Si una LDV pertenece a un palé, inserta como nodo padre la información 
        del palé y a continuación la LDV como nodo hijo.
        """
        model = self.wids['tv_ldvs'].get_model()
        model.clear()
        pales = {}
        for ldv in self.objeto.lineasDeVenta:
            pale = ldv.pale
            if pale:
                if pale not in pales:
                    nodo_padre = model.append(None, 
                                   (pale.codigo, 
                                    utils.float2str(ldv.cantidad, 
                                                    autodec = True),
                                    "", 
                                    #CWT: "", 
                                    ldv.calcular_bultos(), 
                                    "", 
                                    "P:%d" % pale.id))
                    pales[pale] = nodo_padre
                else:
                    nodo_padre = pales[pale]
                    model[nodo_padre][1] = utils.float2str(
                        utils._float(model[nodo_padre][1]) + 
                        ldv.cantidad)
                    #model[nodo_padre][4] += ldv.calcular_bultos()
                    model[nodo_padre][3] += ldv.calcular_bultos()
            else:
                nodo_padre = None
            model.append(nodo_padre, 
                            (ldv.productoVenta 
                                and ldv.productoVenta.nombre or "", 
                             utils.float2str(ldv.cantidad, autodec = True), 
                             utils.float2str(ldv.precio), 
                             #CWT: ldv.envase.nombre, 
                             ldv.calcular_bultos(), 
                             ldv.parcela and ldv.parcela.parcela or "", 
                             "LDV:%d" % ldv.id))
            
    def nuevo(self, widget):
        """
        Función callback del botón b_nuevo.
        Pide los datos básicos para crear un nuevo objeto.
        Una vez insertado en la BD hay que hacerlo activo
        en la ventana para que puedan ser editados el resto
        de campos que no se hayan pedido aquí.
        """
        clientes = [(c.id, c.nombre) 
                    for c in pclases.Cliente.select(
                        pclases.Cliente.q.inhabilitado == False, 
                        orderBy = "nombre")]
        idcliente = utils.dialogo_combo("CLIENTE", 
                                        "Seleccione cliente:", 
                                        clientes, 
                                        self.wids['ventana'])
        if idcliente != None:
            objeto_anterior = self.objeto
            if objeto_anterior != None:
                objeto_anterior.notificador.desactivar()
            numalbaran = self.clase.get_next_numalbaran()
            numalbaran = utils.dialogo_entrada(titulo = "NÚMERO DE ALBARÁN", 
                texto = "Introduzca número de albarán:", 
                valor_por_defecto = numalbaran, 
                padre = self.wids['ventana'])
            if not numalbaran:
                return
            if pclases.AlbaranSalida.select(
                    pclases.AlbaranSalida.q.numalbaran == numalbaran).count():
                utils.dialogo(titulo = "ALBARÁN DUPLICADO", 
                              texto = "El número de albarán %s ya existe." % (
                                numalbaran), 
                              padre = self.wids['ventana'])
                return
            try:
                self.objeto = self.clase(clienteID = idcliente, 
                                         numalbaran = numalbaran, 
                                         cmrID = None, 
                                         bloqueado = False)
            except Exception, msgerror:
                # Probablemente número de albarán duplicado.
                utils.dialogo_info(titulo = "ERROR", 
                    texto = "Se produjo un error al crear el albarán.\nVue"\
                            "lva a intentarlo.\n\nInformación de depuració"\
                            "n:\n%s" % msgerror, 
                    padre = self.wids['ventana'])
            else:
                self.objeto.notificador.activar(self.aviso_actualizacion)
                self._objetoreciencreado = self.objeto
                self.activar_widgets(True)
                self.actualizar_ventana(objeto_anterior = objeto_anterior)
                utils.dialogo_info('NUEVO %s CREADO' % (
                                        self.clase.sqlmeta.table.upper()), 
                    'Se ha creado un nuevo %s.\nA continuación complete la in'\
                    'formación del misma y guarde los cambios.' % (
                        self.clase.sqlmeta.table.lower()), 
                    padre = self.wids['ventana'])

    def buscar(self, widget):
        """
        Muestra una ventana de búsqueda y a continuación los
        resultados. El objeto seleccionado se hará activo
        en la ventana a no ser que se pulse en Cancelar en
        la ventana de resultados.
        """
        a_buscar = utils.dialogo_entrada(titulo = "BUSCAR %s" % (
                                            self.clase.sqlmeta.table.upper()), 
                                         texto="Introduzca número de albarán:",
                                         padre = self.wids['ventana']) 
        if a_buscar != None:
            try:
                ida_buscar = int(a_buscar)
            except ValueError:
                ida_buscar = -1
            campos_busqueda = (self.clase.q.numalbaran, )
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
                    texto = 'La búsqueda no produjo resultados.\nPruebe a cam'\
                            'biar el texto buscado o déjelo en blanco para ve'\
                            'r una lista completa.\n(Atención: Ver la lista c'\
                            'ompleta puede resultar lento si el número de ele'\
                            'mentos es muy alto)',
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
                    texto = "Se produjo un error al recuperar la información."\
                            "\nCierre y vuelva a abrir la ventana antes de vo"\
                            "lver a intentarlo.", 
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
                self.objeto.comision = utils._float(self.wids['e_comision'].get_text())
                continue
            try:
                setattr(self.objeto, col.name, adaptadores[col]['leer']())
            except Exception, e:
                utils.dialogo_info(titulo = "ERROR", 
                    texto = "Ocurrió un error al guardar el albarán.\n"
                            "Verifique que el número no está duplicado."
                            "\n\n\nInformación de depuración: %s" % (e), 
                    padre = self.wids['ventana'])
                return
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
            self.objeto.destroySelf()
        except Exception, e:
            self.logger.error("albaranes_de_salida.py::borrar -> %s ID %d no"\
                              " se pudo eliminar. Excepción: %s." % (
                                self.objeto.sqlmeta.table, self.objeto.id, e))
            utils.dialogo_info(titulo = "%s NO BORRADO" % (
                                    self.clase.sqlmeta.table.upper()), 
                               texto = "%s no se pudo eliminar.\n\nSe generó"\
                                       " un informe de error en el «log» de "\
                                       "la aplicación." % (
                                            self.clase.sqlmeta.table.title()),
                               padre = self.wids['ventana'])
            self.actualizar_ventana()
            return
        self.objeto = None
        self.ir_a_primero()

    def cambiar_por_combo(self, tv, numcol):
        import gobject
        # Elimino columna actual
        column = tv.get_column(numcol)
        tv.remove_column(column)
        # Creo model para el CellCombo
        model = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_INT64)
        for parcela in pclases.Parcela.select(orderBy = "parcela"):
            model.append(("%s (%s)" % (parcela.parcela, 
                                       parcela.finca and parcela.finca.nombre
                                        or ""), 
                          parcela.id))
        # Creo CellCombo
        cellcombo = gtk.CellRendererCombo()
        cellcombo.set_property("model", model)
        cellcombo.set_property("text-column", 0)
        cellcombo.set_property("editable", True)
        cellcombo.set_property("has-entry", False)
        # Función callback para la señal "editado"
        def guardar_combo(cell, path, text, model_tv, numcol, model_combo):
            if model_tv[path][-1].split(":")[0] == "LDV":
                # Es lento, pero no encuentro otra cosa:
                idparcela = None
                if text == None:
                    # Ocurre si le da muy muy pero que muy rápido al combo 
                    # abriéndolo y cerrándolo sin parar
                    text = model_combo[0][0]
                for i in xrange(len(model_combo)):
                    texto, id = model_combo[i]
                    if texto == text:
                        idparcela = id
                        break
                if idparcela == None:
                    utils.dialogo_info(titulo = "ERROR PARCELA", 
                        texto = "Ocurrió un error inesperado guardando parce"\
                                "la.\n\nContacte con los desarrolladores de "\
                                "la aplicación\n(Vea el diálogo «Acerca de.."\
                                ".» en el menú principal.)", 
                        padre = self.wids['ventana'])
                else:
                    parcela = pclases.Parcela.get(idparcela)
                    model_tv[path][numcol] = text
                    tipo, idldv = model_tv[path][-1].split(":")
                    assert tipo == "LDV", "No se puede cambiar/guardar una pa"\
                                          "rcela en un objeto palé. Debe ser "\
                                          "una línea de venta."
                    ldv = pclases.LineaDeVenta.get(idldv)
                    ldv.parcela = parcela
                self.actualizar_ventana()
        # Y agrego al TreeView
        cellcombo.connect("edited", 
                          guardar_combo, 
                          tv.get_model(), 
                          numcol, 
                          model)
        #column.pack_start(cellcombo)
        #column.set_attributes(cellcombo, text = numcol)
        tv.insert_column_with_attributes(numcol, 
                                         "Parcela", 
                                         cellcombo, 
                                         text = numcol)

    def imprimir(self, boton):
        """
        Imprime el albarán y el CMR si el cliente es extranjero.
        """
        r = utils.dialogo(titulo = "¿IMPRIMIR SOLO DATOS?", 
                          texto = "Presione «Sí» para imprimir el albarán en "\
                                  "una hoja preimpresa.", 
                          cancelar = True, 
                          defecto = gtk.RESPONSE_YES, 
                          tiempo = 20, 
                          padre = self.wids['ventana'])
        if r != gtk.RESPONSE_CANCEL:
            try:
                import albaran
                from informes import abrir_pdf
            except ImportError:
                sys.path.append(os.path.join("..", "informes"))
                import albaran
                from informes import abrir_pdf
            fpdf = albaran.go_from_albaranSalida(self.objeto, solo_texto = r)
            if fpdf:
                abrir_pdf(fpdf)
            if (self.objeto.cliente.es_extranjero() or 
                self.objeto.destino_extranjero()):
                porteador = utils.dialogo_entrada(titulo = "CMR - PORTEADOR", 
                    texto = "Introduzca porteador:", 
                    valor_por_defecto = "", 
                    padre = self.wids['ventana'])
                if porteador == None:
                    return
                sucesivos = utils.dialogo_entrada(
                    titulo = "CMR - PORTEADORES SUCESIVOS", 
                    texto = "Introduzca porteadores sucesivos:", 
                    valor_por_defecto = "", 
                    padre = self.wids['ventana'])
                if sucesivos == None:
                    return
                import cmr
                fpdf2 = cmr.go_from_albaranSalida(self.objeto, solo_texto = r, 
                                                  porteador = porteador, 
                                                  sucesivos = sucesivos)
                if fpdf2:
                    abrir_pdf(fpdf2)



def refinar_busqueda(prods, padre = None):
    """
    Muestra un diálogo con todos los productos recibidos y devuelve el 
    producto seleccionado por el usuario, o None si cancela.
    """
    filas = [(p.id, p.nombre, p.familia and p.familia.nombre or "")
             for p in prods]
    id = utils.dialogo_resultado(filas, 
                                 titulo = "SELECCIONE PRODUCTO", 
                                 padre = padre, 
                                 cabeceras = ("ID", "Producto", "Familia"))
    if id > 0:
        producto = pclases.ProductoVenta.get(id)
    else:
        producto = None
    return producto

def _buscar_producto(padre = None):
    """
    Pide un texto y busca un producto que lo contenga en la descripción.
    Si se encuentran varios muestra un diálogo con todos los resultados para 
    que el usuario seleccione uno.
    Si no encuentra ninguno, o se cancela, devuelve None.
    """
    producto = None
    a_buscar = utils.dialogo_entrada(titulo = "BUSCAR PRODUCTO", 
                                     texto = "Introduzca una descripción:", 
                                     padre = padre)
    if a_buscar != None:
        lower = pclases.sqlbuilder.func.lower
        if len((a_buscar).split()) <= 1:
            prods = pclases.ProductoVenta.select(
              lower(pclases.ProductoVenta.q.nombre).contains(a_buscar.lower()))
        else:
            terminos = a_buscar.split()
            subcrits=[lower(pclases.ProductoVenta.q.nombre).contains(t.lower())
                        for t in terminos]
            prods = pclases.ProductoVenta.select(pclases.AND(*subcrits))
        if prods.count() > 1:
            producto = refinar_busqueda(prods, padre)
        elif prods.count() == 1:
            producto = prods[0]
        else:
            utils.dialogo_info(titulo = "SIN RESULTADOS", 
                               texto = "No se encontraron productos con el "\
                                       "texto buscado «%s» en el nombre." % (
                                            a_buscar), 
                               padre = padre)
    return producto

def buscar_producto(padre = None):
    """
    Muestra una ventana donde buscar productos por código. Devuelve 
    una tupla con producto y cantidad o None en ambas posiciones si 
    se cancela.
    """
    res = [None, None]
    gladewids = gtk.glade.XML(os.path.join("..","ui","buscar_producto.glade"))
    ventana = gladewids.get_widget("ventana")
    b_aceptar = gladewids.get_widget("b_aceptar")
    b_cancelar = gladewids.get_widget("b_cancelar")
    b_buscar = gladewids.get_widget("b_buscar")
    e_codigo = gladewids.get_widget("e_codigo")
    e_descripcion = gladewids.get_widget("e_descripcion")
    e_cantidad = gladewids.get_widget("e_cantidad")
    def ok(w, res):
        try:
            res[1] = utils._float(e_cantidad.get_text())
        except (TypeError, ValueError):
            res[1] = 0
        ventana.destroy()
    def ko(w, res):
        res = [None, None]
        ventana.destroy()
    def buscar(w, res):
        codigo = e_codigo.get_text()
        p = pclases.ProductoVenta.select(
            pclases.ProductoVenta.q.codigo.contains(codigo))
        if p.count() == 1:
            res[0] = p[0]
        elif p.count() > 1:
            res[0] = refinar_busqueda(p, ventana)
        if res[0]:
            producto = res[0]
            e_codigo.set_text(producto.codigo)
            e_descripcion.set_text(producto.nombre)
            e_cantidad.grab_focus()
    def intentar_determinar_producto(e, res):
        texto = e.get_text()
        ps = pclases.ProductoVenta.select(
                pclases.ProductoVenta.q.codigo.contains(texto))
        if ps.count() == 1:
            res[0] = ps[0]
            e_codigo.set_text(res[0].codigo)
            e_descripcion.set_text(res[0].nombre)
            e_cantidad.grab_focus()
    b_aceptar.connect("clicked", ok, res)
    b_cancelar.connect("clicked", ko, res)
    b_buscar.connect("clicked", buscar, res)
    ventana.connect("destroy", lambda *args, **kw: gtk.main_quit())
    e_cantidad.connect("activate", ok, res)
    e_codigo.connect("changed", intentar_determinar_producto, res)
    ventana.set_transient_for(padre)
    ventana.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    ventana.set_modal(True)
    e_cantidad.set_text("0")
    e_codigo.grab_focus()
    ventana.show()
    gtk.main()
    return res

if __name__ == "__main__":
    p = AlbaranesDeSalida()

