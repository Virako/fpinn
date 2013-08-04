#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2005, 2006 Francisco José Rodríguez Bogado,                   #
#                          Diego Muñoz Escalante.                             #
# (pacoqueen@users.sourceforge.net, escalant3@users.sourceforge.net)          #
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

###############################################################################
# BUG localizado: El gc no puede eliminar objetos de memoria (o al menos sus
#                 hilos) por estar las hebras pendientes del "signal" aunque el
#                 objeto persistente ya no se use más en adelante.
###############################################################################

# NOTAS:
#  Ahora mismo todo esto es un batiburrillo. Las notificaciones de cambios remotos, el IPC, la
#  persistencia y todo eso de momento queda en el aire. Lo voy a hacer a la forma "tradicional".
#  El ye olde check: Cada cierto tiempo comprobar si hay cambios entre los atributos del objeto
#  y los de la cache local (que aquí se llama swap por motivos que no vienen a cuento), y si los
#  hay lanzo la función definida en el notificador y puto pelota.
#  ¿Qué es lo que hay que hacer entonces en cada ventana? Pues cada vez que se muestren datos en
#  pantalla se llama al make_swap y con un timeout_add que chequean los cambios de vez en cuando
#  con .chequear_cambios(). Fácil, ¿no? PUES NO ME GUSTA. Prefería las notificaciones y las 
#  señales de la BD, su hilo con su conexión IPC, etc...

"""
    Catálogo de clases persistentes.
"""


DEBUG = False
#DEBUG = True   # Se puede activar desde ipython después de importar con 
                # pclases.DEBUG = True
VERBOSE = False

if DEBUG:
    print "IMPORTANDO PCLASES"

# 14/01/2011: No sé bien qué ha pasado con SQLObject pero ahora 
# sí construye bien las claves ajenas explicitándolas. Si dejo 
# que lo haga solo, le añade ID al final: p. ej: ventanaIDID
# Anulo aquí la variable para que en los "if" de las clases 
# ejecute las ForeignKeys
#sqlobject_version = False
from sqlobject import __doc__ as sqlobject_version
try:
    sqlobject_version = sqlobject_version.replace("\n", "").replace("\t", "")
except AttributeError:  # __doc__ es None. ¿Versión demasiado antigua?
    sqlobject_version = None
sqlobject_autoid = lambda: sqlobject_version > "SQLObject 0.10.4"
# 14/01/2011: Cambio IVA de 16 al 18. 

import os
import threading
from sqlobject import *
from math import ceil
from select import select
import mx, mx.DateTime, datetime

from framework.configuracion import ConfigConexion
from formularios import notificacion
from formularios.utils import parse_fecha
from formularios.utils import str_fecha
from formularios.utils import str_fechahora
from formularios.utils import _float
from formularios.utils import float2str
from formularios.utils import comparar_fechas


# GET FUN !

config = ConfigConexion()

#conn = '%s://%s:%s@%s/%s' % (config.get_tipobd(), 
#                             config.get_user(), 
#                             config.get_pass(), 
#                             config.get_host(), 
#                             config.get_dbname())

# HACK: No reconoce el puerto en el URI y lo toma como parte del host. Lo añado detrás y colará en el dsn cuando lo parsee. 
#conn = '%s://%s:%s@%s/%s port=%s' % (config.get_tipobd(), 
#conn = '%s://%s:%s@%s/%s' % (config.get_tipobd(), 
conn = '%s://%s:%s@%s/%s?autoCommit=True' % (config.get_tipobd(), 
                                     config.get_user(), 
                                     config.get_pass(), 
                                     config.get_host(), 
                                     config.get_dbname(), 
                                     #config.get_puerto()) 
                            )

# HACK:
# Hago todas las consultas case-insensitive machacando la función de 
# sqlbuilder:
_CONTAINSSTRING = sqlbuilder.CONTAINSSTRING
def CONTAINSSTRING(expr, pattern):
    try:
        nombre_clase = SQLObject.sqlmeta.style.dbTableToPythonClass(
                        expr.tableName)
        clase = globals()[nombre_clase]
        columna = clase.sqlmeta.columns[expr.fieldName]
    except (AttributeError, KeyError):
        return _CONTAINSSTRING(expr, pattern)
    if isinstance(columna, (SOStringCol, SOUnicodeCol)):
        op = sqlbuilder.SQLOp("ILIKE", expr, 
                                '%' + sqlbuilder._LikeQuoted(pattern) + '%')
    elif isinstance(columna, (SOFloatCol, SOIntCol, SODecimalCol, 
                              SOMediumIntCol, SOSmallIntCol, SOTinyIntCol)):
        try:
            pattern = str(_float(pattern))
        except ValueError:
            pattern = None
        if not pattern:
            op = sqlbuilder.SQLOp("IS NOT", expr, None)
        else:
            op = sqlbuilder.SQLOp("=", expr, 
                                    sqlbuilder._LikeQuoted(pattern))
    else:
        op = sqlbuilder.SQLOp("LIKE", expr, 
                                '%' + sqlbuilder._LikeQuoted(pattern) + '%')
    return op
sqlbuilder.CONTAINSSTRING = CONTAINSSTRING


class SQLObjectChanged(Exception):
    """ User-defined exception para ampliar la funcionalidad
    de SQLObject y que soporte objetos persistentes."""
    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)

class PRPCTOO:
    """ 
    Clase base para heredar y no repetir código.
    Únicamente implementa los métodos para iniciar un hilo de 
    sincronización y para detenerlo cuando ya no sea necesario.
    Ningún objeto de esta clase tiene utilidad "per se".
    """
    # El nombre viene de todo lo que NO hace pero para lo que es útil:
    # PersistentRemoteProcessComunicatorThreadingObservadorObservado. TOOOOOMA.
    def __init__(self, nombre_clase_derivada = ''):
        """
        El nombre de la clase derivada pasado al 
        constructor es para la metainformación 
        del hilo.
        """
        self.__oderivado = nombre_clase_derivada
        self.swap = {}

    def abrir_conexion(self):
        """
        Abre una conexión con la BD y la asigna al 
        atributo conexión de la clase.
        No sale del método hasta que consigue la
        conexión.
        """
        while 1:
            try:
                self.conexion = self._connection.getConnection()
                if DEBUG: print " --> Conexión abierta."
                return
            except:
                print "ERROR estableciendo conexión secundaria para IPC. Vuelvo a intentar"
    
    def abrir_cursor(self):
        self.cursor = self.conexion.cursor()
        if DEBUG: print [self.cursor!=None and self.cursor or "El cursor devuelto es None."][0], self.conexion, len(self.conexion.cursors)

    def make_swap(self):
        # Antes del sync voy a copiar los datos a un swap temporal, para poder comparar:
        for campo in self.sqlmeta.columns:
            self.swap[campo]=eval('self.%s' % campo)
        
    def comparar_swap(self):
        # Y ahora sincronizo:
        self.sync()
        # y comparo:
        for campo in self.sqlmeta.columns:
            # print self.swap[campo], eval('self.%s' % campo) 
            if self.swap[campo]!=eval('self.%s' % campo): 
                raise SQLObjectChanged(self)

    def cerrar_cursor(self):
        self.cursor.close()

    def cerrar_conexion(self):
        self.conexion.close()
        if DEBUG: print " <-- Conexión cerrada."

    ## Código del hilo:
    def esperarNotificacion(self, nomnot, funcion=lambda: None):
        """
        Código del hilo que vigila la notificación.
        self -> Objeto al que pertenece el hilo.
        nomnot es el nombre de la notificación a esperar.
        funcion es una función opcional que será llamada cuando se
        produzca la notificación.
        """
        if DEBUG: print "Inicia ejecución hilo"
        while self != None and self.continuar_hilo:   # XXX
            if DEBUG: print "Entra en la espera bloqueante: %s" % nomnot
            self.abrir_cursor()
            self.cursor.execute("LISTEN %s;" % nomnot)
            self.conexion.commit()
            if select([self.cursor], [], [])!=([], [], []):
                if DEBUG: print "Notificación recibida"
                try:
                    self.comparar_swap()
                except SQLObjectChanged:
                    if DEBUG: print "Objeto cambiado"
                    funcion()
                except SQLObjectNotFound:
                    if DEBUG: print "Registro borrado"
                    funcion()
                # self.cerrar_cursor()
        else:
            if DEBUG: print "Hilo no se ejecuta"
        if DEBUG: print "Termina ejecución hilo"

    def chequear_cambios(self):
        try:
            self.comparar_swap()
            # print "NO CAMBIA"
        except SQLObjectChanged:
            # print "CAMBIA"
            if DEBUG: print "Objeto cambiado"
            # print self.notificador
            self.notificador.run()
        except SQLObjectNotFound:
            if DEBUG: print "Registro borrado"
            self.notificador.run()

    def ejecutar_hilo(self):
        ## ---- Código para los hilos:
        self.abrir_conexion()
        self.continuar_hilo = True
        nombre_clase = self.__oderivado
        self.th_espera = threading.Thread(target=self.esperarNotificacion, args=("IPC_%s" % nombre_clase, self.notificador.run), name="Hilo-%s" % nombre_clase)
        self.th_espera.setDaemon(1)
        self.th_espera.start()

    def parar_hilo(self):
        self.continuar_hilo = False
        if DEBUG: print "Parando hilo..."
        self.cerrar_conexion()

    def destroy_en_cascada(self):
        """
        Destruye recursivamente los objetos que dependientes y 
        finalmente al objeto en sí.
        OJO: Es potencialmente peligroso y no ha sido probado en profundidad.
             Puede llegar a provocar un RuntimeError por alcanzar la profundidad máxima de recursividad
             intentando eliminarse en cascada a sí mismo por haber ciclos en la BD. 
        """
        for join in self.sqlmeta.joins:
            lista = join.joinMethodName
            for dependiente in getattr(self, lista):
            # for dependiente in eval("self.%s" % (lista)):
                if DEBUG:
                    print "Eliminando %s..." % dependiente
                dependiente.destroy_en_cascada()
        self.destroySelf()

    def copyto(self, obj, eliminar = False):
        """
        Copia en obj los datos del objeto actual que en obj sean 
        nulos.
        Enlaza también las relaciones uno a muchos para evitar 
        violaciones de claves ajenas, ya que antes de terminar, 
        si "eliminar" es True se borra el registro de la BD.
        PRECONDICIÓN: "obj" debe ser del mismo tipo que "self".
        POSTCONDICIÓN: si "eliminar", self debe quedar eliminado.
        """
        DEBUG = False
        assert type(obj) == type(self) and obj != None, "Los objetos deben pertenecer a la misma clase y no ser nulos."
        for nombre_col in self.sqlmeta.columns:
            valor = getattr(obj, nombre_col)
            if valor == None or (isinstance(valor, str) and valor.strip() == ""):
                if DEBUG:
                    print "Cambiando valor de columna %s en objeto destino." % (nombre_col)
                setattr(obj, nombre_col, getattr(self, nombre_col))
        for col in self._SO_joinList:
            atributo_lista = col.joinMethodName
            lista_muchos = getattr(self, atributo_lista)
            nombre_clave_ajena = repr(self.__class__).replace("'", ".").split(".")[-2] + "ID" # HACK (y de los feos)
            nombre_clave_ajena = nombre_clave_ajena[0].lower() + nombre_clave_ajena[1:]       # HACK (y de los feos)
            for propagado in lista_muchos:
                if DEBUG:
                    print "Cambiando valor de columna %s en objeto destino." % (nombre_clave_ajena)
                    print "   >>> Antes: ", getattr(propagado, nombre_clave_ajena)
                setattr(propagado, nombre_clave_ajena, obj.id)
                if DEBUG:
                    print "   >>> Después: ", getattr(propagado, nombre_clave_ajena)
        if eliminar:
            try:
                self.destroySelf()
            except:     # No debería. Pero aún así, me aseguro de que quede eliminado (POSTCONDICIÓN).
                self.destroy_en_cascada()

    def clone(self, *args, **kw):
        """
        Crea y devuelve un objeto idéntico al actual.
        Si se pasa algún parámetro adicional se intentará enviar 
        tal cual al constructor de la clase ignorando los 
        valores del objeto actual para esos parámetros.
        """
        parametros = {}
        for campo in self.sqlmeta.columns:
            valor = getattr(self, campo)
            parametros[campo] = valor
        for campo in kw:
            valor = kw[campo]
            parametros[campo] = valor
        nuevo = self.__class__(**parametros)
        return nuevo

    # PLAN: Hacer un full_clone() que además de los atributos, clone también los registros relacionados.

    def get_info(self):
        """
        Devuelve información básica (str) acerca del objeto. Por ejemplo, 
        si es un pedido de venta, devolverá el número de pedido, fecha y 
        cliente.
        Este método se hereda por todas las clases y debería ser redefinido.
        """
        return "%s ID %d" % (self.sqlmeta.table, self.id)

class ImagenPlano:
    """
    Clase base para las clases que tengan rutas a una imagen con la 
    representación del plano.
    Provee métodos para insertar una imagen, obtenerla, etc.
    """
    def get_ruta_base():
        """
        Devuelve la ruta del directorio que contiene la imagen.
        Se asegura cada vez que es consultada que el directorio existe.
        """
        # Siempre se trabaja en un subdirectorio del raíz del programa. 
        # Normalmente formularios o framework.
        # Por tanto lo primero que hago es salir del subdirectorio para 
        # buscar el de documentos adjuntos.
        RUTA_BASE = os.path.join(config.get_dir_compartido())
        try:
            assert os.path.exists(RUTA_BASE)
        except AssertionError:
            os.mkdir(RUTA_BASE)
        return RUTA_BASE
    
    ruta_base = get_ruta_base = staticmethod(get_ruta_base)

    def get_ruta_completa_plano(self):
        """
        Devuelve la ruta completa al fichero: directorio base + nombre 
        del fichero.
        Si no tiene plano asociado, devuelve la imagen estándar.
        """
        if self.rutaPlano:
            return os.path.join(ImagenPlano.get_ruta_base(), self.rutaPlano)
        return os.path.join("imagenes", "map.png")

    def copiar_a_dircompartido(ruta):
        """
        Copia el fichero de la ruta al directorio compartido.
        """
        import shutil
        try:
            shutil.copy(ruta, ImagenPlano.get_ruta_base())
            res = True
        except Exception, msg:
            print "pclases::ImagenPlano::copiar_a_dircompartido -> Excepción %s" % msg
            res = False
        return res

    copiar_a_dircompartido = staticmethod(copiar_a_dircompartido)

    def guardar(self, ruta):
        """
        Adjunta el fichero del que recibe la ruta con el objeto.
        Si no puede devuelve False.
        """
        nombreFichero = os.path.split(ruta)[-1]
        if ImagenPlano.copiar_a_dircompartido(ruta):
            res = True
            self.rutaPlano = nombreFichero
        else:
            res = False
        return res

    def mostrar_imagen_en(self, w, MAX = None):
        """
        «w» debe ser un gtk.Image
        Si «MAX» es diferente de None se escala la imagen en caso de que 
        alguna de sus dimensiones sea superior.
        """
        import gtk
        pixbuf = gtk.gdk.pixbuf_new_from_file(self.get_ruta_completa_plano())
        if MAX != None and (pixbuf.get_width() > MAX 
                            or pixbuf.get_height() > MAX):
            colorspace = pixbuf.get_property("colorspace")
            has_alpha = pixbuf.get_property("has_alpha")
            bits_per_sample = pixbuf.get_property("bits_per_sample")
            pixbuf2 = gtk.gdk.Pixbuf(colorspace, 
                                     has_alpha, 
                                     bits_per_sample, 
                                     MAX, 
                                     MAX)
            pixbuf.scale(pixbuf2, 
                         0, 0, 
                         MAX, MAX, 
                         0, 0,
                         (1.0 * MAX) / pixbuf.get_width(), 
                         (1.0 * MAX) / pixbuf.get_height(), 
                         gtk.gdk.INTERP_BILINEAR)
            pixbuf = pixbuf2
        w.set_from_pixbuf(pixbuf)

def starter(objeto, *args, **kw):
    """
    Método que se ejecutará en el constructor de todas las 
    clases persistentes.
    Inicializa el hilo y la conexión secundaria para IPC, 
    así como llama al constructor de la clase padre SQLObject.
    """
    objeto.continuar_hilo = False
    objeto.notificador = notificacion.Notificacion(objeto)
    SQLObject._init(objeto, *args, **kw)
    PRPCTOO.__init__(objeto, objeto.sqlmeta.table)
    objeto.make_swap()    # Al crear el objeto hago la primera caché de datos, por si acaso la ventana 
                          # se demora mucho e intenta compararla antes de crearla.

    #objeto._cacheValues = False    # FIXME: Sospecho que tarde o temprano tendré que desactivar las cachés locales de SQLObject. 
                                    # Tengo que probarlo antes de poner en producción porque no sé si va a resultar peor el remedio 
                                    # (por ineficiente) que la enfermedad (que solo da problemas de vez en cuando y se resuelven 
                                    # con un Shift+F5).
                                    # Mala idea. ¡Si desactivo el caché de SQLObject tengo que hacer sync() después de cada operación!

## XXX XXX XXX XXX XXX XXX XXX XXX XXX XXX XXX XXX XXX XXX XXX XXX XXX XXX XXX

class Cliente(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    albaranesSalida = MultipleJoin("AlbaranSalida")
    facturasVenta = MultipleJoin("FacturaVenta")
    if not sqlobject_version or not sqlobject_autoid():
        tarifa = ForeignKey("Tarifa")
        serieFacturasVenta = ForeignKey("SerieFacturasVenta", default = None)

    def get_vencimientos(self, fecha_base = mx.DateTime.localtime()):
        """
        Devuelve una lista con los días naturales de los vencimientos
        del cliente. P. ej.:
        - Si el cliente tiene "30", devuelve [30].
        - Si no tiene, devuelve [].
        - Si tiene "30-60", devuelve [30, 60].
        - Si tiene "90 D.F.F." (90 días a partir de fecha factura), devuelve [90].
        - Si tiene "30-120 D.R.F." (30 y 120 días a partir de fecha de recepción de factura) devuelve [30, 120].
        etc.
        - ¡NUEVO! Si tiene "120 D.U.D.M.F.F." (120 días a contar a partir del último día del mes de la fecha de 
          factura) devuelve 120 + los días que haya entre la fecha «fecha_base» y el fin de mes, con objeto de 
          que sean sumados a la fecha de factura desde la ventana que me invoca."
        En definitiva, filtra todo el texto y devuelve los números que encuentre en cliente.vencimientos.
        """
        res = []
        if self.vencimientos != None:
            
            import re
            regexpcars = re.compile("\w")
            cadena = "".join(regexpcars.findall(self.vencimientos)).upper()
            regexpr = re.compile("\d*")
            lista_vtos = regexpr.findall(self.vencimientos)
            if "UDM" in cadena:
                try:
                    findemes = mx.DateTime.DateTimeFrom(day = -1, month = fecha_base.month, year = fecha_base.year)
                except Exception, msg:
                    print "ERROR: pclases::Cliente::get_vencimientos() -> Exception: %s" % (msg)
                    difafindemes = 0
                else:
                    difafindemes = findemes.day - fecha_base.day
            else:
                difafindemes = 0
            try:
                res = [int(i) + difafindemes for i in lista_vtos if i != '']
            except TypeError, msg:
                print "ERROR: pclases::Cliente::get_vencimientos() -> TypeError: %s" % (msg)
        return res

    def get_dias_de_pago(self):
        """
        Devuelve UNA TUPLA con los días de pago del cliente (vacía si no tiene).
        """
        res = []
        if self.diadepago != None:
            import re
            regexpr = re.compile("\d*")
            lista_dias = regexpr.findall(self.diadepago)
            try:
                res = tuple([int(i) for i in lista_dias if i != ''])
            except TypeError, msg:
                print "ERROR: pclases: cliente.get_dias_de_pago(): %s" % (msg)
        return res

    def es_extranjero(self):
        """
        Devuelve True si el cliente es extranjero.
        Para ello mira si el país (de facturación) del cliente es diferente al 
        de la empresa. Si no se encuentran datos de la empresa
        devuelve True si el país no es España.
        """
        cpf = unicode(self.paisfacturacion.strip())
        try:
            de = DatosDeLaEmpresa.select()[0]
            depf = unicode(de.paisfacturacion.strip())
            if depf.strip() == "":
                raise IndexError, "Empresa encontrada sin país de facturación."
            res = cpf != "" and depf.lower() != cpf.lower()
        except IndexError:
            res = cpf != "" and cpf.lower() != unicode("españa")
        return res

    extranjero = property(es_extranjero)
 
    def get_facturas_por_intervalo(self, inicio, fin, serie = None):
        """
        Devuelve las facturas asociadas con el cliente 
        entre las fechas de inicio y fin. La fecha de inicio puede ser None.
        Si serie no es None, filtrará por la serie numérica de facturas.
        """
        if inicio:
            facturas = FacturaVenta.select(AND(
                                FacturaVenta.q.fecha >= inicio, 
                                FacturaVenta.q.fecha <= fin, 
                                FacturaVenta.q.clienteID == self.id))
        else:
            facturas = FacturaVenta.select(AND(
                                FacturaVenta.q.fecha <= fin, 
                                FacturaVenta.q.clienteID == self.id))
        if serie:
            _facturas = []
            for f in facturas:
                if f.serieFacturasVenta == serie:
                    _facturas.append(f)
        else:
            _facturas = facturas
        return tuple(_facturas)
    
    def calcular_total_facturado_por_intervalo(self, inicio, fin, iva = True, 
                                               serie = None):
        """
        Devuelve el total facturado entre el intervalo de fechas por el 
        cliente. La fecha inicial puede ser None.
        Por defecto incluye el IVA en las facturas.
        OJO: Solo facturado y facturas de terceros. No albaranes.
        """
        t = sum([f.calcular_importe_total(iva) 
                 for f in self.get_facturas_por_intervalo(inicio, fin, serie)])
        return t

    def calcular_total_consumido_por_intervalo(self, inicio, fin, serie):
        """
        Devuelve el total consumido entre el intervalo de fechas por el 
        cliente. La fecha inicial puede ser None.
        Por defecto incluye el IVA en las facturas.
        OJO: Solo facturado y facturas de terceros. No albaranes.
        """
        t = sum([f.calcular_kilos() 
                 for f in self.get_facturas_por_intervalo(inicio, fin)])
        return t

    def get_info(self):
        """
        Devuelve ID y nombre del cliente.
        """
        return "Cliente ID %d: %s" % (self.id, self.nombre)

class Proveedor(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    facturasCompra = MultipleJoin('FacturaCompra')
    facturasVenta = MultipleJoin('FacturaVenta')
    envases = MultipleJoin('Envase')

    def get_info(self):
        """
        Devuelve ID y nombre del cliente.
        """
        return "Proveedor ID %d: %s" % (self.id, self.nombre)

class Imagen(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    if not sqlobject_version or not sqlobject_autoid():
        empleado = ForeignKey('Empleado')
    
    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------


    def get_info(self):
        """
        Devuelve ID, nombre y ruta de la imagen.
        """
        return "Imagen ID %d: %s (%s)" % (self.id, self.nombre, self.ruta)

    def guardar_blob_from_file(self, ruta):
        """
        Guarda en el BLOB la imagen recibida.
        """
        from PIL import Image
        im = Image.open(ruta)
        self.imagen = im.tostring()
        self.ancho, self.alto = im.size
        self.modo = im.mode

    def to_pil(self):
        """
        Devuelve una imagen PIL a partir del BLOB guardado.
        """
        from PIL import Image
        im = Image.new(self.modo, (self.ancho, self.alto))
        im.fromstring(self.imagen)
        return im

class Empleado(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    imagenes = MultipleJoin('Imagen')
    documentos = MultipleJoin('Documento')
    jornales = MultipleJoin("Jornal")
    salarios = MultipleJoin("Salario")
    trabajos = MultipleJoin("Trabajo")
    cuadrillas = MultipleJoin("CuadrillaEmpleado")
    anticipo = MultipleJoin("Anticipo")

    def calcular_edad(self, fecha = mx.DateTime.localtime()):
        """
        Calcula la edad en la fecha recibida.
        """
        annos = fecha.year - self.fechaNacimiento.year
        if (fecha.month < self.fechaNacimiento.month or 
            (fecha.month == self.fechaNacimiento.month and 
             fecha.day < self.fechaNacimiento.day)):
            annos -= 1
        return annos

    def get_info(self):
        """
        Devuelve ID, nombre y DNI del empleado.
        """
        return "Empleado ID %d: %s - %s" % (self.id, self.nombre, self.dni)

    def get_gtkimage(self, maximo = None):
        """
        Devuelve una GtkImage de la foto del empleado o de la foto por 
        defecto si no tiene.
        Si maximo != None reescala la imagen para que ninguna de sus dos 
        dimensiones supere esa cantidad
        """
        import gtk
        from formularios import utils
        if self.imagenes:
            impil = self.imagenes[0].to_pil()
        else:
            from PIL import Image
            impil = Image.open(os.path.join("imagenes", "users.png"))
        ancho, alto = impil.size
        escala = (float(maximo) / max(ancho, alto))
        impil = impil.resize((int(ancho * escala), 
                              int(alto * escala)), 
                              resample = 1)
        pixbuf = utils.image2pixbuf(impil)
        gtkimage = gtk.Image()
        gtkimage.set_from_pixbuf(pixbuf)
        return gtkimage

    def calcular_produccion_personal(self, fecha):
        """
        Devuelve la producción personal en kilos del empleado para 
        la fecha recibida.
        La producción personal es la suma de jornales que hayan empezado
        más tarde de las 00:00 del día recibido y antes de las 00:00 del 
        día siguiente.
        OJO: No se tiene en cuenta la hora de finalización de la jornada.
        """
        fecha_sig = fecha + mx.DateTime.oneDay
        jornales = Jornal.select(AND(Jornal.q.empleadoID == self.id, 
                                     Jornal.q.fechahoraInicio >= fecha, 
                                     Jornal.q.fechahoraInicio < fecha_sig))
        prod = sum([j.produccion for j in jornales])
        return prod

    def calcular_ratio(self):
        """
        Devuelve la media diaria del empleado.
        Para ello suma todas las producciones y divide entre el número de 
        días trabajados (cardinalidad del conjunto de fechas diferentes sin 
        horas).
        OJO: Solo tiene en cuenta las "fechahoras" de inicio.
        """
        from formularios.utils import unificar
        jornales = Jornal.select(Jornal.q.empleadoID == self.id)
        prodtotal = sum([j.produccion for j in jornales])
        dias = [(j.fechahoraInicio.day, 
                 j.fechahoraInicio.month, 
                 j.fechahoraInicio.year) for j in jornales]
        dias = unificar(dias)
        try:
            res = prodtotal / len(dias)
        except ZeroDivisionError:
            res = 0.0
        return res

    def calcular_producciones_por_dia(self, fechainicio=None, fechafin=None):
        """
        Devuelve un diccionario de días y producción total en cada uno 
        de esos días para el empleado.
        Si fechainicio != None, solo cuenta a partir de ese día.
        Si fechafin != None, solo cuenta hasta ese día (incluido hasta las
        23:59, por eso se le suma un día).
        OJO: Solo cuenta fechahoraInicio para el día del jornal.
        """
        if not fechainicio and not fechafin:
            jornales = Jornal.select(Jornal.q.empleadoID == self.id)
        elif fechainicio and not fechafin:
            jornales = Jornal.select(AND(Jornal.q.empleadoID == self.id, 
                                 Jornal.q.fechahoraInicio >= fechainicio))
        elif not fechainicio and fechafin:
            jornales = Jornal.select(AND(Jornal.q.empleadoID == self.id, 
                    Jornal.q.fechahoraInicio < fechafin + mx.DateTime.oneDay))
        else:
            jornales = Jornal.select(AND(Jornal.q.empleadoID == self.id, 
                                    Jornal.q.fechahoraInicio >= fechainicio, 
                    Jornal.q.fechahoraInicio < fechafin + mx.DateTime.oneDay))
        res = {}
        for j in jornales:
            dia = mx.DateTime.DateTimeFrom(day = j.fechahoraInicio.day, 
                                           month = j.fechahoraInicio.month, 
                                           year = j.fechahoraInicio.year)
            if dia not in res:
                res[dia] = j.produccion
            else:
                res[dia] += j.produccion
        return res

    def get_trabajo_mes(self, f1=None, f2=None):
        return Trabajo.select(AND(Trabajo.q.empleadoID == self.id,
                Trabajo.q.fecha >= f1, Trabajo.q.fecha < f2))

    def get_anticipos_mes(self, f1=None, f2=None):
        return Anticipo.select(AND(Anticipo.q.empleadoID == self.id,
                Anticipo.q.fecha >= f1, Anticipo.q.fecha < f2))


class Trabajo(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------


class Cuadrilla(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------


class CuadrillaEmpleado(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    empleado = MultipleJoin('Empleado')


class Anticipo(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------


class Envase(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    if not sqlobject_version or not sqlobject_autoid():
        proveedor = ForeignKey('Proveedor')
    productosVenta = MultipleJoin('ProductoVenta')
    empaquetados = MultipleJoin("Empaquetado")

    def get_info(self):
        return "%s (%s kg)" % (self.nombre, 
                               float2str(self.kg, autodec = True))

class Tarrina(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    if not sqlobject_version or not sqlobject_autoid():
        proveedor = ForeignKey('Proveedor')
    productosVenta = MultipleJoin('ProductoVenta')
    empaquetados = MultipleJoin("Empaquetado")

class Empaquetado(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    if not sqlobject_version or not sqlobject_autoid():
        envase = ForeignKey('Envase')
        tarrina = ForeignKey('Tarrina')

    def calcular_capacidad_total(self):
        """
        Devuelve la capacidad total en kg: cantidad de tarrinas * capacidad de 
        cada una.
        """
        res = self.cantidad * self.tarrina.gr / 1000.0
        return res

class Cobro(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    documentos = MultipleJoin('Documento')
    if not sqlobject_version or not sqlobject_autoid():
        facturaVenta = ForeignKey("FacturaVenta")

class Pago(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    if not sqlobject_version or not sqlobject_autoid():
        facturaCompra = ForeignKey('FacturaCompra')

class VencimientoCobro(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    if not sqlobject_version or not sqlobject_autoid():
        facturaVenta = ForeignKey('FacturaVenta')

class VencimientoPago(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    if not sqlobject_version or not sqlobject_autoid():
        facturaCompra = ForeignKey('FacturaCompra')

class SerieFacturasCompra(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    facturasCompra = MultipleJoin('FacturaCompra')

    def get_next_numfactura(self, commit = False):
        """
        Devuelve el siguiente número de factura del contador.
        Si commit es True, incrementa el contador.
        """
        num = self.contador
        if commit:
            self.contador += 1
        numfactura = self._build_numfactura(num)
        return numfactura

    def get_num_numfactura(self, factura):
        """
        Devuelve, como entero, el número de la factura recibida.
        Acepta el número de factura como cadena, un objeto factura o un ID.
        """
        if isinstance(factura, str):
            numfactura = factura
        elif isinstance(factura, FacturaCompra):
            numfactura = factura.facturaCompra
        elif isinstance(factura, int):
            factura = FacturaCompra.get(factura)
            numfactura = factura.numfactura
        num = numfactura.replace(self.prefijo, "", 1)
        num = num[::-1].replace(self.sufijo[::-1], "", 1)[::-1]
        num = int(num)
        return num

    def _build_numfactura(self, num = None):
        """
        Devueve el número completo de factura, con prefijo y sufijo.
        Si "num" es None, usa el actual del contador.
        """
        if num == None:
            num = self.contador
        formatstrnum = "%%0%dd" % self.posiciones
        strnum = formatstrnum % num
        res = "%s%s%s" % (self.prefijo, strnum, self.sufijo)
        return res

    def get_last_numfactura(self):
        """
        Devuelve el último número (completo, con prefijo y sufijo) de 
        factura asignado o "-" si no se encuentra.
        """
        cont = self.contador - 1
        num = 0
        while (cont > num and 
            FacturaCompra.selectBy(
                numfactura = self._build_numfactura(num)).count() == 0):
            cont -= 1
        return num > 0 and self._build_numfactura(num) or "-"

class SerieFacturasVenta(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    facturasVenta = MultipleJoin('FacturaVenta')
    clientes = MultipleJoin("Cliente")

    def get_next_numfactura(self, commit = False):
        """
        Devuelve el siguiente número de factura del contador.
        Si commit es True, incrementa el contador.
        """
        num = self.contador
        if commit:
            self.contador += 1
        numfactura = self._build_numfactura(num)
        return numfactura

    def get_num_numfactura(self, factura):
        """
        Devuelve, como entero, el número de la factura recibida.
        """
        if isinstance(factura, str):
            numfactura = factura
        elif isinstance(factura, FacturaVenta):
            numfactura = factura.facturaVenta
        elif isinstance(factura, int):
            factura = FacturaVenta.get(factura)
            numfactura = factura.numfactura
        num = numfactura.replace(self.prefijo, "", 1)
        num = num[::-1].replace(self.sufijo[::-1], "", 1)[::-1]
        num = int(num)
        return num

    def _build_numfactura(self, num = None):
        """
        Devueve el número completo de factura, con prefijo y sufijo.
        Si "num" es None, usa el actual del contador.
        """
        if num == None:
            num = self.contador
        formatstrnum = "%%0%dd" % self.posiciones
        strnum = formatstrnum % num
        res = "%s%s%s" % (self.prefijo, strnum, self.sufijo)
        return res

    def get_last_numfactura(self):
        """
        Devuelve el último número (completo, con prefijo y sufijo) de 
        factura asignado o "-" si no se encuentra.
        """
        cont = self.contador - 1
        num = 0
        while (cont > num and 
            FacturaVenta.selectBy(
                numfactura = self._build_numfactura(num)).count() == 0):
            cont -= 1
        return num > 0 and self._build_numfactura(num) or "-"

    def get_info(self):
        res = self._build_numfactura(0)
        if self.b:
            res += " (B)"
        return res

class FacturaCompra(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    if not sqlobject_version or not sqlobject_autoid():
        proveedor = ForeignKey('Proveedor')
        serieFacturasCompra = ForeignKey('SerieFacturasCompra')
    gastos = MultipleJoin('Gasto')
    pago = MultipleJoin('Pago')
    vencimientoPago = MultipleJoin('VencimientoPago')

class Gasto(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    if not sqlobject_version or not sqlobject_autoid():
        cuentaGastos = ForeignKey('CuentaGastos')
        facturaCompra = ForeignKey('FacturaCompra')
        parcela = ForeignKey("Parcela")
    documentos = MultipleJoin('Documento')
    salarios = MultipleJoin("Salario")

    # Por compatibilidad con Empleado (con quien comparte código de adjuntos 
    # en ventana):
    nombre = property(lambda self: self.concepto)

class CuentaGastos(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    gastos = MultipleJoin('Gasto')

    def buscar_cuenta_apertura():
        """
        Devuelve la cuenta de gastos de apertura.
        Si no existe, la crea.
        Si existe más de una con la palabra "apertura" devuelve la primera
        de ellas según el ID.
        """
        CG = CuentaGastos
        try:
            cuenta = CG.select("descripcion ILIKE '%apertura%'", 
                               orderBy = "id")[0]
        except IndexError:
            cuenta = CG(descripcion = "Gastos de apertura")
        return cuenta

    def buscar_cuenta_cierre():
        """
        Devuelve la cuenta de gastos de apertura.
        Si no existe, la crea.
        Si existe más de una con la palabra "apertura" devuelve la primera
        de ellas según el ID.
        """
        CG = CuentaGastos
        try:
            cuenta = CG.select("descripcion ILIKE '%cierre%'", 
                               orderBy = "id")[0]
        except IndexError:
            cuenta = CG(descripcion = "Gastos de cierre")
        return cuenta

    def buscar_cuentas_varios():
        """
        Devuelve una tupla con las cuentas que no son de apertura ni cierre. 
        """
        CG = CuentaGastos
        apertura = CG.buscar_cuenta_apertura()
        cierre = CG.buscar_cuenta_cierre()
        cuentas = [c for c in CG.select() 
                    if c is not apertura and c is not cierre]
        return tuple(cuentas)

    buscar_cuenta_apertura = staticmethod(buscar_cuenta_apertura)
    buscar_cuenta_cierre = staticmethod(buscar_cuenta_cierre)
    buscar_cuentas_varios = staticmethod(buscar_cuentas_varios)
    
class Documento(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    if not sqlobject_version or not sqlobject_autoid():
        empleado = ForeignKey('Empleado', default = None)
        cobro = ForeignKey('Cobro', default = None)
        gasto = ForeignKey('Gasto', default = None)

    def get_info(self):
        """
        Devuelve ID, nombre y ruta del documento.
        """
        return "Documento ID %d: %s (%s)" % (self.id, self.nombre, self.ruta)

    def get_ruta_base():
        """
        Devuelve la ruta del directorio que contiene los documentos adjuntos.
        Se asegura cada vez que es consultada que el directorio existe.
        """
        # Siempre se trabaja en un subdirectorio del raíz del programa. 
        # Normalmente formularios o framework.
        # Por tanto lo primero que hago es salir del subdirectorio para 
        # buscar el de documentos adjuntos.
        RUTA_BASE = os.path.join(config.get_dir_adjuntos())
        try:
            assert os.path.exists(RUTA_BASE)
        except AssertionError:
            os.mkdir(RUTA_BASE)
        return RUTA_BASE
    
    ruta_base = get_ruta_base = staticmethod(get_ruta_base)

    def get_ruta_completa(self):
        """
        Devuelve la ruta completa al fichero: directorio base + nombre 
        del fichero.
        """
        return os.path.join(Documento.get_ruta_base(), self.nombreFichero)

    def copiar_a_diradjuntos(ruta):
        """
        Copia el fichero de la ruta al directorio de adjuntos.
        """
        import shutil
        try:
            shutil.copy(ruta, Documento.get_ruta_base())
            res = True
        except Exception, msg:
            print "pclases::Documento::copiar_a_diradjuntos -> Excepción %s"\
                   % msg
            res = False
        return res

    copiar_a_diradjuntos = staticmethod(copiar_a_diradjuntos)

    def adjuntar(ruta, objeto, nombre = ""):
        """
        Adjunta el fichero del que recibe la ruta con el objeto
        del segundo parámetro.
        Si no puede determinar la clase del objeto o no está 
        soportado en la relación, no crea el registro documento
        y devuelve None.
        En otro caso devuelve el objeto Documento recién creado.
        """
        res = None
        if objeto != None and os.path.exists(ruta):
            objeto_relacionado = None
            if isinstance(objeto, Empleado):
                empleado = objeto
                gasto = None
            elif isinstance(objeto, Gasto):
                empleado = None
                gasto = objeto
            else:
                raise TypeError, "pclases::Documento::adjuntar -> %s no es un tipo válido." % type(objeto)
            nombreFichero = os.path.split(ruta)[-1]
            if Documento.copiar_a_diradjuntos(ruta):
                nuevoDoc = Documento(nombre = nombre, 
                                     nombreFichero = nombreFichero, 
                                     empleado = empleado, 
                                     gasto = gasto) 
                res = nuevoDoc
        return res

    adjuntar = staticmethod(adjuntar)

class Actividad(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    jornales = MultipleJoin("Jornal")
    salarios = MultipleJoin("Salario")
    
    def get_info(self):
        """
        Devuelve ID, código y descripción de la actividad.
        """
        return "Actividad ID %d: %s (%d)" % (self.id, 
                                             self.descripcion, 
                                             self.codigo)

class Campanna(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    jornales = MultipleJoin("Jornal")
    practicasCuturales = MultipleJoin("PracticaCutural")
    cultivos = MultipleJoin("Cultivo")
    fertilizaciones = MultipleJoin("Fertilizacion")
    enmiendas = MultipleJoin("Enmienda")
    fitosanitarios = MultipleJoin("Fitosanitario")
    
    def get_info(self):
        return "Campaña ID %d: %s a %s" % (self.id, 
                                           str_fecha(self.fechaInicio), 
                                           str_fecha(self.fechaFin))

    def _buscar_campanna(fecha):
        """
        Recibe una fecha y devuelve la primera campaña que coincida con ella.
        """
        campanna = None
        campannas = Campanna.select(AND(Campanna.q.fechaInicio <= fecha, 
                            Campanna.q.fechaFin >= fecha - mx.DateTime.oneDay))
            # Siempre que se comparen fechas con fechahoras hay que sumar un 
            # día a la fecha para que 31/12/2007 (00:00) sea mayor o igual a 
            # 31/12/2007 15:30 -por ejemplo-.
        if campannas.count() > 0:
            campanna = campannas[0]
        return campanna

    _buscar_campanna = staticmethod(_buscar_campanna)
    
    def buscar_campanna(campanna_o_fecha):
        """
        Busca la campaña correspondiente a la fecha recibida.
        Acepta también que sea un objeto Campanna, en cuyo caso la
        devuelve tal cual.
        Si no hay campañas coincidentes devuelve None.
        """
        if isinstance(campanna_o_fecha, str):
            fecha = parse_fecha(campanna_o_fecha)
            campanna = Campanna._buscar_campanna(fecha)
        elif isinstance(campanna_o_fecha, (datetime.date, 
                                           type(mx.DateTime.localtime()))):
            campanna = Campanna._buscar_campanna(campanna_o_fecha)
        elif isinstance(campanna_o_fecha, Campanna):
            campanna = campanna_o_fecha
        return campanna
    
    buscar_campanna = staticmethod(buscar_campanna)

class Jornal(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    if not sqlobject_version or not sqlobject_autoid():
        empleado = ForeignKey('Empleado')
        campanna = ForeignKey('Campanna')
        parcela = ForeignKey('Parcela')
        actividad = ForeignKey('Actividad')
        salario = ForeignKey('Salario')
    
    def get_info(self):
        """
        Devuelve ID, fehca de inicio y fecha de fin.
        """
        return "Jornal ID %d: de %s a %s." % (self.id, 
                                        str_fechahora(self.fechahoraInicio), 
                                        str_fechahora(self.fechahoraFin))

    def calcular_media_global(fecha):
        """
        Devuelve la media de producción de los empleados en la fecha recibida.
        """
        from formularios.utils import unificar
        J = Jornal
        try:
            fecha_sig = fecha + mx.DateTime.oneDay
        except TypeError:
            from formularios.utils import parse_fecha, str_fecha
            fecha_sig = (parse_fecha(str_fecha(fecha)) 
                         + mx.DateTime.oneDay)
        jornales = J.select(AND(J.q.fechahoraInicio >= fecha, 
                                J.q.fechahoraInicio < fecha_sig))
        prod = sum([j.produccion for j in jornales])
        empleados = [j.empleado for j in jornales]
        empleados = unificar(empleados)
        try:
            res = prod / len(empleados)
        except ZeroDivisionError:
            res = 0.0
        return res

    calcular_media_global = staticmethod(calcular_media_global)

    def calcular_medias_por_dia(fechainicio = None, fechafin = None):
        """
        Devuelve un diccionario de días y producción media de cada 
        día.
        Si fechainicio != None, cuenta a partir de ese día únicamente.
        OJO: Solo tiene en cuenta la fechahoraInicio para obtener el día.
        """
        from formularios.utils import unificar
        if fechainicio and not fechafin:
            jornales = Jornal.select(Jornal.q.fechahoraInicio >= fechainicio)
        elif fechainicio and fechafin:
            jornales=Jornal.select(AND(Jornal.q.fechahoraInicio >= fechainicio,
                      Jornal.q.fechahoraInicio < fechafin + mx.DateTime.oneDay))
        elif not fechainicio and fechafin:
            jornales = Jornal.select(Jornal.q.fechahoraInicio < fechafin + mx.DateTime.oneDay)
        else:
            jornales = Jornal.select()
        dias = unificar([mx.DateTime.DateTimeFrom(day = j.fechahoraInicio.day, 
                                              month = j.fechahoraInicio.month, 
                                                year = j.fechahoraInicio.year)
                         for j in jornales])
        res = {}
        for dia in dias:
            res[dia] = Jornal.calcular_media_global(dia)
        return res

    calcular_medias_por_dia = staticmethod(calcular_medias_por_dia)

    def get_duracion(self):
        """
        Devuelve la duración en horas como flotante.
        """
        duracion = self.fechahoraFin - self.fechahoraInicio
        horas = duracion.seconds / 3600.0
        return horas

    def get_horas_campo(self):
        """
        Devuelve las horas de campo del jornal.
        Si las horas son de campo o de manipulación lo define la actividad.
        """
        if self.actividad.campo:
            return self.get_duracion()
        return 0.0

    def get_horas_manipulacion(self):
        """
        Devuelve las horas de manipulación del jornal en función de 
        su actividad.
        """
        if self.actividad.manipulacion:
            return self.get_horas_campo()
        return 0.0

    def get_euros_campo(self):
        """
        Devuelve las horas de campo del jornal evaluadas según el precio por 
        hora de campo del emplado.
        """
        return self.get_horas_campo() * self.empleado.precioHoraCampo

    def get_euros_manipulacion(self):
        """
        Devuelve las horas de manipulación del jornal evaluadas según el 
        precio por hora de manipulación del emplado.
        """
        return (self.get_horas_manipulacion() 
                * self.empleado.precioHoraManipulacion)

    horasCampo = property(get_horas_campo)
    horasManipulacion = property(get_horas_manipulacion)
    eurosCampo = property(get_euros_campo)
    eurosManipulacion = property(get_euros_manipulacion)

class PracticaCutural(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    if not sqlobject_version or not sqlobject_autoid():
        campanna = ForeignKey('Campanna')
        parcela = ForeignKey('Parcela')

class Cultivo(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    if not sqlobject_version or not sqlobject_autoid():
        campanna = ForeignKey('Campanna')
        parcela = ForeignKey('Parcela')

class Fertilizacion(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    if not sqlobject_version or not sqlobject_autoid():
        campanna = ForeignKey('Campanna')
        parcela = ForeignKey('Parcela')
        productoVenta = ForeignKey("ProductoVenta", default = None)

class Enmienda(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    if not sqlobject_version or not sqlobject_autoid():
        campanna = ForeignKey('Campanna')
        parcela = ForeignKey('Parcela')
        productoVenta = ForeignKey("ProductoVenta", default = None)

class Fitosanitario(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    if not sqlobject_version or not sqlobject_autoid():
        campanna = ForeignKey('Campanna')
        parcela = ForeignKey('Parcela')
        productoVenta = ForeignKey("ProductoVenta", default = None)

class MateriaActiva(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

class Finca(SQLObject, PRPCTOO, ImagenPlano):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    parcelas = MultipleJoin("Parcela")

class Parcela(SQLObject, PRPCTOO, ImagenPlano):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    if not sqlobject_version or not sqlobject_autoid():
        finca = ForeignKey('Finca')
    practicasCuturales = MultipleJoin("PracticaCutural")
    cultivos = MultipleJoin("Cultivo")
    fertilizaciones = MultipleJoin("Fertilizacion")
    enmiendas = MultipleJoin("Enmienda")
    fitosanitarios = MultipleJoin("Fitosanitario")
    jornales = MultipleJoin("Jornal")
    gastos = MultipleJoin("Gasto")
    lineasDeVenta = MultipleJoin("LineaDeVenta")

    def get_info(self):
        """
        Información básica de la parcela: ID, nombre y finca.
        """
        return "Parcela ID %d. %s (%s)" % (self.id, 
                                           self.parcela, 
                                           self.finca and self.finca.nombre 
                                            or "¡No asignada a finca!")

    def calcular_produccion_por_planta(self, campanna_o_fecha):
        """
        Devuelve la producción por planta de la parcela en la campaña 
        recibida.
        """
        prod = self.calcular_produccion(campanna_o_fecha)
        try:
            prod_planta = prod / self.numeroDePlantas
        except ZeroDivisionError:
            prod_planta = 0
        return prod_planta

    def calcular_produccion_por_planta_e_intervalo(self, inicio, fin):
        """
        Calcula la producción de la parcela entre las fechas inicial y 
        final en kg por planta.
        La fecha de inicio puede omitirse pasándole None.
        """
        prod = self.calcular_produccion_por_intervalo(inicio, fin)
        try:
            prod_planta = prod / self.numeroDePlantas
        except ZeroDivisionError:
            prod_planta = 0
        return prod_planta

    def calcular_produccion(self, campanna_o_fecha):
        """
        Devuelve la producción en kilos de la parcela para la campaña o 
        fecha recibida.
        Si es una fecha, determina la campaña y hace los cálculos.
        Si no hay campaña creada en la fecha recibida se devuelve 0.
        """
        res = 0.0
        campanna = Campanna.buscar_campanna(campanna_o_fecha)
        if campanna != None:
            producciones = Jornal.select(AND(Jornal.q.campannaID == campanna.id,
                                             Jornal.q.parcelaID == self.id))
            res = sum([p.produccion for p in producciones])
        return res

    def calcular_produccion_por_intervalo(self, inicio, fin):
        """
        Devuelve la producción en kilos de la parcela entre las fechas 
        de inicio y fin. La fecha de inicio puede ser None.
        """
        res = 0.0
        if inicio:
            producciones = Jornal.select(AND(
                Jornal.q.fechahoraInicio >= inicio, 
                Jornal.q.fechahoraFin < fin + mx.DateTime.oneDay, 
                Jornal.q.parcelaID == self.id))
        else:
            producciones = Jornal.select(AND(
                Jornal.q.fechahoraFin < fin + mx.DateTime.oneDay, 
                Jornal.q.parcelaID == self.id))
        res = sum([p.produccion for p in producciones])
        return res

    def get_gastos_apertura(self, campanna_o_fecha):
        """
        Devuelve los gastos del tipo apertura asociados con la parcela 
        en el periodo indicado por campanna o la Campaña que contiene 
        la fecha.
        El tipo viene indicado por la cuenta de gastos. La misma debe 
        llamarse "gastos de apertura" (en todo caso se busca por 'apertura').
        """
        apertura = CuentaGastos.buscar_cuenta_apertura()
        campanna = Campanna.buscar_campanna(campanna_o_fecha)
        try:
            fecha_fin_efectiva = campanna.fechaFin + mx.DateTime.oneDay
        except TypeError:
            fecha_fin_efectiva=mx.DateTime.DateTimeFrom(campanna.fechaFin.year, 
                                                       campanna.fechaFin.month, 
                                                          campanna.fechaFin.day)
            fecha_fin_efectiva += mx.DateTime.oneDay
        gastos = Gasto.select(AND(Gasto.q.cuentaGastosID == apertura.id, 
                                  Gasto.q.fecha >= campanna.fechaInicio, 
                                     Gasto.q.fecha < fecha_fin_efectiva, 
                                           Gasto.q.parcelaID == self.id))
        return gastos

    def get_gastos_apertura_por_intervalo(self, inicio, fin):
        """
        Devuelve los gastos del tipo apertura asociados con la parcela 
        entre las fechas de inicio y fin. La fecha de inicio puede ser None.
        El tipo viene indicado por la cuenta de gastos. La misma debe 
        llamarse "gastos de apertura" (en todo caso se busca por 'apertura').
        """
        apertura = CuentaGastos.buscar_cuenta_apertura()
        try:
            fecha_fin_efectiva = fin + mx.DateTime.oneDay
        except TypeError:
            fecha_fin_efectiva=mx.DateTime.DateTimeFrom(fin.year, 
                                                        fin.month, 
                                                        fin.day)
            fecha_fin_efectiva += mx.DateTime.oneDay
        if inicio:
            gastos = Gasto.select(AND(Gasto.q.cuentaGastosID == apertura.id, 
                                      Gasto.q.fecha >= inicio, 
                                      Gasto.q.fecha < fecha_fin_efectiva, 
                                      Gasto.q.parcelaID == self.id))
        else:
            gastos = Gasto.select(AND(Gasto.q.cuentaGastosID == apertura.id, 
                                      Gasto.q.fecha < fecha_fin_efectiva, 
                                      Gasto.q.parcelaID == self.id))
        return gastos
    
    def get_total_gastos_apertura(self, campanna_o_fecha):
        t = sum([g.importe for g in self.get_gastos_apertura(campanna_o_fecha)])
        return t

    def get_total_gastos_apertura_por_intervalo(self, inicio, fin):
        """
        Devuelve el total de gastos de apertura entre las fechas inicio y fin.
        La fecha de inicio puede ser None.
        """
        t = sum([g.importe for g 
                 in self.get_gastos_apertura_por_intervalo(inicio, fin)])
        return t

    def get_gastos_cierre(self, campanna_o_fecha):
        """
        Devuelve los gastos del tipo cierre asociados con la parcela 
        en el periodo indicado por campanna o la Campaña que contiene 
        la fecha.
        El tipo viene indicado por la cuenta de gastos. La misma debe 
        llamarse "gastos de cierre" (en todo caso se busca por 'cierre').
        """
        cierre = CuentaGastos.buscar_cuenta_cierre()
        campanna = Campanna.buscar_campanna(campanna_o_fecha)
        try:
            fecha_fin_efectiva = campanna.fechaFin + mx.DateTime.oneDay
        except TypeError:
            fecha_fin_efectiva=mx.DateTime.DateTimeFrom(campanna.fechaFin.year, 
                                                       campanna.fechaFin.month, 
                                                          campanna.fechaFin.day)
            fecha_fin_efectiva += mx.DateTime.oneDay
        gastos = Gasto.select(AND(Gasto.q.cuentaGastosID == cierre.id, 
                                  Gasto.q.parcelaID == self.id, 
                                  Gasto.q.fecha >= campanna.fechaInicio, 
                                  Gasto.q.fecha < fecha_fin_efectiva))
        return gastos

    def get_gastos_cierre_por_intervalo(self, inicio, fin):
        """
        Devuelve los gastos del tipo cierre asociados con la parcela 
        entre las fechas de inicio y fin. La fecha de inicio puede ser None.
        El tipo viene indicado por la cuenta de gastos. La misma debe 
        llamarse "gastos de cierre" (en todo caso se busca por 'cierre').
        """
        cierre = CuentaGastos.buscar_cuenta_cierre()
        try:
            fecha_fin_efectiva = fin + mx.DateTime.oneDay
        except TypeError:
            fecha_fin_efectiva=mx.DateTime.DateTimeFrom(fin.year, 
                                                        fin.month, 
                                                        fin.day)
            fecha_fin_efectiva += mx.DateTime.oneDay
        if inicio:
            gastos = Gasto.select(AND(Gasto.q.cuentaGastosID == cierre.id, 
                                      Gasto.q.fecha >= inicio, 
                                      Gasto.q.fecha < fecha_fin_efectiva, 
                                      Gasto.q.parcelaID == self.id))
        else:
            gastos = Gasto.select(AND(Gasto.q.cuentaGastosID == cierre.id, 
                                      Gasto.q.fecha < fecha_fin_efectiva, 
                                      Gasto.q.parcelaID == self.id))
        return gastos

    def get_total_gastos_cierre(self, campanna_o_fecha):
        t = sum([g.importe for g in self.get_gastos_cierre(campanna_o_fecha)])
        return t

    def get_total_gastos_cierre_por_intervalo(self, inicio, fin):
        """
        Devuelve el total de gastos de cierre entre las fechas inicio y fin.
        La fecha de inicio puede ser None.
        """
        t = sum([g.importe for g 
                 in self.get_gastos_cierre_por_intervalo(inicio, fin)])
        return t

    def get_gastos_varios(self, campanna_o_fecha):
        """
        Devuelve los gastos varios asociados con la parcela 
        en el periodo indicado por campanna o la Campaña que contiene 
        la fecha.
        Los gastos varios son aquellos que no pertenecen a los de 
        apertura ni cierre.
        """
        varios = CuentaGastos.buscar_cuentas_varios()
        idsvarios = [c.id for c in varios]
        for id in idsvarios:
            en_cuenta_varios = [Gasto.q.cuentaGastosID == id]
        campanna = Campanna.buscar_campanna(campanna_o_fecha)
        try:
            fecha_fin_efectiva = campanna.fechaFin + mx.DateTime.oneDay
        except TypeError:
            fecha_fin_efectiva=mx.DateTime.DateTimeFrom(campanna.fechaFin.year, 
                                                       campanna.fechaFin.month, 
                                                          campanna.fechaFin.day)
            fecha_fin_efectiva += mx.DateTime.oneDay
        gastos = Gasto.select(AND(Gasto.q.fecha >= campanna.fechaInicio, 
                                  Gasto.q.parcelaID == self.id, 
                                  Gasto.q.fecha < fecha_fin_efectiva, 
                                  *en_cuenta_varios))
        return gastos

    def get_gastos_varios_por_intervalo(self, inicio, fin):
        """
        Devuelve los gastos varios asociados con la parcela 
        en el periodo entre inicio y fin. La fecha de inicio puede ser None.
        Los gastos varios son aquellos que no pertenecen a los de 
        apertura ni cierre.
        """
        varios = CuentaGastos.buscar_cuentas_varios()
        idsvarios = [c.id for c in varios]
        for id in idsvarios:
            en_cuenta_varios = [Gasto.q.cuentaGastosID == id]
        try:
            fecha_fin_efectiva = fin + mx.DateTime.oneDay
        except TypeError:
            fecha_fin_efectiva=mx.DateTime.DateTimeFrom(fin.year, 
                                                        fin.month, 
                                                        fin.day)
            fecha_fin_efectiva += mx.DateTime.oneDay
        if inicio:
            gastos = Gasto.select(AND(Gasto.q.fecha >= inicio, 
                                      Gasto.q.parcelaID == self.id, 
                                      Gasto.q.fecha < fecha_fin_efectiva, 
                                      *en_cuenta_varios))
        else:
            gastos = Gasto.select(AND(Gasto.q.parcelaID == self.id, 
                                      Gasto.q.fecha < fecha_fin_efectiva, 
                                      *en_cuenta_varios))
        return gastos

    def get_total_gastos_varios(self, campanna_o_fecha):
        t = sum([g.importe for g in self.get_gastos_varios(campanna_o_fecha)])
        return t
 
    def get_total_gastos_varios_por_intervalo(self, inicio, fin):
        """
        Devuelve el total de gastos entre las fechas inicio (puede ser None) 
        y fin.
        """
        t = sum([g.importe for g 
                 in self.get_gastos_varios_por_intervalo(inicio, fin)])
        return t

    def get_ingresos_por_fecha(self, inicio, fin):
        """
        Devuelve un diccionario de LDVs relacionados con la parcela 
        entre las fechas inicio y fin junto con el total sin IVA de los 
        mismos.
        La fecha de inicio puede omitirse.
        """
        if inicio:
            ldvs = LineaDeVenta.select(AND(
                        LineaDeVenta.q.parcelaID == self.id, 
                        LineaDeVenta.q.albaranSalidaID == AlbaranSalida.q.id, 
                        AlbaranSalida.q.fecha >= inicio, 
                        AlbaranSalida.q.fecha <= fin))
            #albaranes = AlbaranSalida.select(AND(
            #              AlbaranSalida.q.fecha >= inicio, 
            #              AlbaranSalida.q.fecha <= fin, 
            #              AlbaranSalida.q.parcelaID == self.id))
        else:
            ldvs = LineaDeVenta.select(AND(
                        LineaDeVenta.q.parcelaID == self.id, 
                        LineaDeVenta.q.albaranSalidaID == AlbaranSalida.q.id, 
                        AlbaranSalida.q.fecha <= fin))
            #albaranes = AlbaranSalida.select(AND(
            #                AlbaranSalida.q.fecha <= fin, 
            #                AlbaranSalida.q.parcelaID == self.id))
        res = {}
        #for a in albaranes:
        #    res[a] = a.calcular_importe(iva = False)
        for ldv in ldvs:
            res[ldv] = ldv.calcular_importe(iva = False)
        return res

    def get_total_ingresos_por_intervalo(self, inicio, fin):
        """
        Devuelve el total de ingresos procedentes de los albaranes 
        relacionados con la parcela entre las fechas indicadas.
        «inicio» puede ser None.
        """
        res = 0.0
        albaranes = self.get_ingresos_por_fecha(inicio, fin)
        for a in albaranes:
            res += albaranes[a]
        return res

class ProductoVenta(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    if not sqlobject_version or not sqlobject_autoid():
        familia = ForeignKey("Familia")
    lineasDeVenta = MultipleJoin("LineaDeVenta")
    fertilizaciones = MultipleJoin("Fertilizacion")
    enmiendas = MultipleJoin("Enmienda")
    fitosanitarios = MultipleJoin("Fitosanitario")
    if not sqlobject_version or not sqlobject_autoid():
        envase = ForeignKey("Envase")
    precios = RelatedJoin("Precio")
    if not sqlobject_version or not sqlobject_autoid():
        precio = ForeignKey("Precio", default = None)

    def actualizar_existencias_envases(self, cantidad):
        """
        Incrementa o decrementa el envase del producto y de la 
        tarrina si lo llevara. Cantidad es la cantidad en kg de producto que 
        sale o entra. El número de envases a modificar es un entero redondeado 
        por arriba resultado de dividir la cantidad entre la capacidad del 
        envase.
        """
        # NOTA: Esto debería ser atómico
        envase = self.envase
        if envase:
            capacidad = envase.kg
            if cantidad < 0:
                signo = -1
            else:
                signo = 1
            envases = int(ceil(abs(cantidad) / capacidad))
            envases *= signo
            print envases, cantidad
            envase.sync()
            envase.existencias += envases
            envase.syncUpdate()
            # Ahora actualizo las tarrinas y flowpack que lleva.
            for e in envase.empaquetados:
                tarrina = e.tarrina
                cantidad = e.cantidad
                tarrina.sync()
                tarrina.existencias += envases * cantidad
                tarrina.syncUpdate()


class Familia(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    productosVenta = MultipleJoin("ProductoVenta")

class Cmr(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    albaranesSalida = MultipleJoin("AlbaranSalida")

class Transportista(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    albaranesSalida = MultipleJoin("AlbaranSalida")

class AlbaranSalida(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    if not sqlobject_version or not sqlobject_autoid():
        cmr = ForeignKey("Cmr")
        cliente = ForeignKey("Cliente")
        transportista = ForeignKey("Transportista", default = None)
    lineasDeVenta = MultipleJoin("LineaDeVenta")

    def destino_extranjero(self):
        """
        Devuelve True si el país de destino es extranjero.
        Para ello mira si el país es diferente al 
        de la empresa. Si no se encuentran datos de la empresa
        devuelve True si el país no es España.
        """
        cpf = unicode(self.pais.strip())
        try:
            de = DatosDeLaEmpresa.select()[0]
            depf = unicode(de.paisfacturacion.strip())
            if depf.strip() == "":
                raise IndexError, "Empresa encontrada sin país de facturación."
            res = cpf != "" and depf.lower() != cpf.lower()
        except IndexError:
            res = cpf != "" and cpf.lower() != unicode("españa")
        return res

    def get_next_numalbaran():
        """
        Devuelve el siguiente número de albarán mirando el último 
        y sumando 1 al primer número que encuentre empezando por la 
        izquierda. Soporta y respeta, por tanto, los números de albarán 
        alfanuméricos.
        """
    def ultimo_numalbaran(clase):
        """
        Devuelve un ENTERO con el último número de albarán sin letras o 0 si 
        no hay ninguno o los que hay tienen caracteres alfanuméricos y no se 
        pueden pasar a entero.
        Para determinar el último número de albarán no se recorre toda la 
        tabla de albaranes intentando convertir a entero. Lo que se hace es 
        ordenar a la inversa por ID y comenzar a buscar el primer número de 
        albarán convertible a entero. Como hay una restricción para crear 
        albaranes, es de suponer que siempre se va a encontrar el número más 
        alto al principio de la lista orderBy="-id".
        OJO: Aquí los números son secuenciales y no se reinicia en cada año 
        (que es como se está haciendo ahora en facturas).
        """
        # DONE: Además, esto debería ser un método de clase.
        import re
        regexp = re.compile("[0-9]*")
        ultimo = 0
        # albs = AlbaranSalida.select(orderBy = '-numalbaran')       # No, porque A_AJUSTE se colocaría el primero a tratar.
        albs = clase.select(orderBy = '-id')
        for a in albs:
            try:
                numalbaran = a.numalbaran
                ultimo = [int(item) for item in regexp.findall(numalbaran) if item != ''][0]
                # ultimo = int(numalbaran)
                break
            except (IndexError, ValueError), msg:
                print "pclases.py (ultimo_numalbaran): Número de último albarán no se pudo determinar: %s" % (msg)
                # No se encontaron números en la cadena de numalbaran o ¿se encontró un número pero no se pudo parsear (!)?
                ultimo = 0
        return ultimo

    def siguiente_numalbaran(clase):
        """
        Devuelve un ENTERO con el siguiente número de albarán sin letras o 0 
        si no hay ninguno o los que hay tienen caracteres alfanuméricos y no 
        se pueden pasar a entero.
        OJO: Aquí los números son secuenciales y no se reinicia en cada año 
        (que es como se está haciendo ahora en facturas).
        """
        return AlbaranSalida.get_ultimo_numero_numalbaran() + 1

    def siguiente_numalbaran_str(clase):
        """
        Devuelve el siguiente número de albarán libre como cadena intentando 
        respetar el formato del último numalbaran.
        """
        import re
        regexp = re.compile("[0-9]*")
        ultimo = None
        albs = clase.select(orderBy = '-id')
        for a in albs:
            try:
                numalbaran = a.numalbaran
                ultimo = [int(item) 
                          for item in regexp.findall(numalbaran) 
                          if item != ''][-1]
                break
            except (IndexError, ValueError), msg:
                print "pclases.py (siguiente_numalbaran_str): Número de último albarán no se pudo determinar: %s" % (msg)
                # No se encontaron números en la cadena de numalbaran o ¿se encontró un número pero no se pudo parsear (!)?
                ultimo = ""
        if ultimo != "" and ultimo != None:
            head = numalbaran[:numalbaran.rindex(str(ultimo))]
            tail = numalbaran[numalbaran.rindex(str(ultimo)) + len(str(ultimo)):]
            str_ultimo = str(ultimo + 1)
            res = head + str_ultimo + tail
            while AlbaranSalida.select(AlbaranSalida.q.numalbaran == res).count() != 0:
                ultimo += 1
                str_ultimo = str(ultimo + 1)
                res = head + str_ultimo + tail
        else:
            res = 1
        if not isinstance(res, str):
            res = str(res)
        return res

    get_ultimo_numero_numalbaran = classmethod(ultimo_numalbaran)
    get_siguiente_numero_numalbaran = classmethod(siguiente_numalbaran)
    get_siguiente_numero_numalbaran_str = classmethod(siguiente_numalbaran_str)
    get_next_numalbaran = get_siguiente_numero_numalbaran_str

    def calcular_importe(self, iva = False):
        """
        Calcula el importe total del albarán.
        Incluye el IVA del cliente si iva es True.
        """
        # XXX: Transporte y descarga no entra en cálculo de IVA.
        # total = self.transporte + self.descarga + self.comision 
        total = -self.comision 
        # XXX
            # XXX: ¿Comisión en positivo?
        if iva:
            try:
                total *= 1.0 + self.cliente.iva
            except AttributeError:
                total *= 1.18   # No cliente, IVA por defecto = 0.18
        for ldv in self.lineasDeVenta:
            total += ldv.calcular_importe(iva)
        # XXX: Transporte y descarga fuera de IVA y restan.
        total -= self.transporte
        total -= self.descarga 
        # XXX
        return total

    (SIN_CLIENTE, 
     VACIO, 
     INCOMPLETO, 
     PENDIENTE_FACTURAR, 
     PENDIENTE_COBRO, 
     COBRADO) = range(6)

    def get_estado(self):
        """
        Devuelve un entero que se corresponde con una constante que 
        indica el estado del albarán entre:
        * Sin cliente.
        * Vacío (sin líneas de venta).
        * Incompleto (importe total es cero).
        * Pendiente de facturar.
        * Facturado y pendiente de cobro.
        * Facturado y cobrado.
        """
        if not self.cliente:
            return self.SIN_CLIENTE
        if not self.lineasDeVenta:
            return self.VACIO
        if self.calcular_importe(iva = True) == 0:
            return self.INCOMPLETO
        fras = [ldv.facturaVentaID for ldv in self.lineasDeVenta 
                if ldv.facturaVenta]
        if not fras:
            return self.PENDIENTE_FACTURAR
        else:
            from formularios.utils import unificar
            fras = unificar(fras)
            totalpdte = sum(
                [FacturaVenta.get(f).calcular_pendiente_cobro() 
                 for f in fras])
            if totalpdte or not [f for f in fras 
                                 if FacturaVenta.get(f).vencimientosCobro]:
                # Si tienen algo pendiente de cobrar o no tienen vencimientos.
                return self.PENDIENTE_COBRO
            return self.COBRADO

    def get_str_estado(self, estado = None):
        """
        Devuelve el estado del albarán como cadena.
        """
        if estado is None:
            estado = self.get_estado()
        if estado == self.SIN_CLIENTE:
            return "Sin cliente"
        if estado == self.VACIO:
            return "Vacío"
        if estado == self.INCOMPLETO:
            return "Incompleto"
        if estado == self.PENDIENTE_FACTURAR:
            return "Pendiente de facturar"
        if estado == self.PENDIENTE_COBRO:
            return "Pendiente de cobro"
        if estado == self.COBRADO:
            return "Cobrado"

    def get_str_estado_css(self, estado = None):
        """
        Devuelve el estado del albarán como cadena compatible con CSS de Django.
        """
        if estado is None:
            estado = self.get_estado()
        if estado == self.SIN_CLIENTE:
            return "estadonocliente"
        if estado == self.VACIO:
            return "estadovacio"
        if estado == self.INCOMPLETO:
            return "estadoincompleto"
        if estado == self.PENDIENTE_FACTURAR:
            return "estadopendientefacturar"
        if estado == self.PENDIENTE_COBRO:
            return "estadopendientecobro"
        if estado == self.COBRADO:
            return "estadocobrado"

    def get_info(self):
        return "Albarán número %s (%s)" % (self.numalbaran, 
                    self.cliente and self.cliente.nombre or "Sin cliente")

    def get_str_fecha(self):
        from formularios.utils import str_fecha
        return str_fecha(self.fecha)

class FacturaVenta(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    if not sqlobject_version or not sqlobject_autoid():
        cliente = ForeignKey('Cliente')
        serieFacturasVenta = ForeignKey("SerieFacturasVenta")
        proveedor = ForeignKey('Cliente', default = None)
    lineasDeVenta = MultipleJoin("LineaDeVenta")
    cobros = MultipleJoin("Cobro")
    vencimientosCobro = MultipleJoin("VencimientoCobro")
    servicios = MultipleJoin("Servicio")

    def get_albaranes(self):
        """ Devuelve los objetos albarán relacionados.  """
        albs = []
        for ldv in self.lineasDeVenta:
            if ldv.albaranSalida and ldv.albaranSalida not in albs:
                albs.append(ldv.albaranSalida)
        return albs

    def emparejar_vencimientos(self):
        """
        Devuelve un diccionario con los vencimientos y cobros de la factura emparejados.
        El diccionario es de la forma:
        {vencimiento1: [cobro1], 
         vencimiento2: [cobro2], 
         vencimiento3: [], 
         'vtos': [vencimiento1, vencimiento2, vencimiento3...], 
         'cbrs': [cobro1, cobro2]}
        Si tuviese más cobros que vencimientos, entonces se devolvería un 
        diccionario tal que:
        {vencimiento1: [cobro1], 
         vencimiento2: [cobro2],
         None: [cobro3, cobro4...], 
         'vtos': [vencimiento1, vencimiento2], 
         'cbrs': [cobro1, cobro2, cobro3, cobro4...]}
        'vtos' y 'cbrs' son copias ordenadas de las listas de vencimientos y 
        cobros.
        El algoritmo para hacerlo es:
        1.- Construyo el diccionario con todos los vencimientos.
        2.- Construyo una lista auxiliar con los cobros ordenados por fecha.
        3.- Recorro el diccionario de vencimientos por orden de fecha.
            3.1.- Saco y asigno el primer cobro de la lista al vencimiento tratado en la iteración.
            3.2.- Si no quedan vencimientos por asignar, creo una clave None y agrego los cobros restantes.
        """
        res = {}
        cbrs = self.cobros[:]
        cbrs.sort(utils.cmp_fecha_id)
        vtos = self.vencimientosCobro[:]
        vtos.sort(utils.cmp_fecha_id)
        res['vtos'] = vtos[:]
        res['cbrs'] = cbrs[:]
        for vto in vtos:
            try:
                cbr = cbrs.pop()
            except IndexError:
                res[vto] = []
            else:
                res[vto] = [cbr]
        if cbrs != []:
            res[None] = cbrs
        return res

    def calcular_importe_total(self, iva = True, incluir_dto_numerico = True, 
                               # precision = None):
                               precision = 2):
        """
        Calcula el importe total, IVA incluido.
        self.descuento se aplica ANTES del IVA (forma parte de la b. imp.).
        self.descuentoNumerico se aplica DESPUÉS del IVA y se tendrá en 
        cuenta si se indica en el parámetro. Ponerlo a False ayuda a encontrar 
        la base imponible completa cuando iva también es False.
        Si precision es None, no aplica ningún tipo de redondeo. En otro caso, 
        a las cifras que componen el total (IVA, comisión, etc.) se le aplica 
        un redondeo antes de sumarlas.
        """
        b_imponible = 0.0
        for ldv in self.lineasDeVenta:
            b_imponible += ldv.calcular_importe()
        for srv in self.servicios:
            b_imponible += srv.calcular_importe()
        # XXX: Transporte no entra en base imponible. Va fuera de IVA.
        # b_imponible += self.comision + self.transporte
        b_imponible += self.comision 
        # XXX
        b_imponible *= (1 - self.descuento)
        if precision != None:
            b_imponible = round(b_imponible, 2)
        if iva:
            if precision != None:
                total = (b_imponible 
                         + round(b_imponible * self.iva, 2))
            else:
                total = b_imponible * (1 + self.iva)
            if incluir_dto_numerico:
                total += self.descuentoNumerico
        else:
            total = b_imponible
            if incluir_dto_numerico:
                try:
                    descuento_numerico_sin_iva = (self.descuentoNumerico 
                                                    / (1 + self.iva))
                except ZeroDivisionError:   # ¿? Con IVA negativo tal vez...
                    descuento_numerico_sin_iva = self.descuentoNumerico
                total += descuento_numerico_sin_iva
        # XXX: Transporte no entra en IVA
        total += self.transporte
        # XXX
        if precision != None:
            total = round(total, precision)
        return total

    def crear_vencimientos_por_defecto(self, forzar = False):
        """
        Crea e los vencimientos por defecto definidos por el cliente en la 
        factura actual y en función de las LDV que tenga en ese momento 
        (concretamente del valor del total de la ventana calculado a partir
        de las LDV.)
        Devuelve una lista de vencimientos creados o una lista vacía si no se 
        pudieron crear.
        Si forzar = True asegura que crea al menos un vencimiento aunque el 
        cliente no los tenga definidos: efectivo y a 0 D.F.F.
        """
        from formularios.utils import cmp_mxDateTime
        factura = self
        cliente = factura.cliente
        vtos_creados = []
        if ((cliente.vencimientos != None and cliente.vencimientos != '')
            or forzar):
            try:
                vtos = cliente.get_vencimientos(factura.fecha)
            except:
                if forzar:
                    vtos = [0]
                else:
                    txt = "No se pudieron determinar los vencimientos del"\
                          " cliente ID %d" % cliente.id
                    print txt
                    return []
            if forzar and not vtos:
                vtos = [0]
            for vto in factura.vencimientosCobro:
                vto.destroySelf()
            total = factura.calcular_importe_total(iva = True)
            numvtos = len(vtos)
            try:
                cantidad = total/numvtos
            except ZeroDivisionError:
                cantidad = total
            if factura.fecha == None:
                factura.fecha = time.localtime()
                factura.syncUpdate()
            if cliente.diadepago != None and cliente.diadepago != '':
                diaest = cliente.get_dias_de_pago()
            else:
                diaest = False
            for incr in vtos:
                try:
                    fechavto = factura.fecha + (incr * mx.DateTime.oneDay)
                except TypeError:
                    factura_fecha = mx.DateTime.DateTimeFrom(
                        day = factura.fecha.day, 
                        month = factura.fecha.month, 
                        year = factura.fecha.year)
                    fechavto = factura_fecha + (incr * mx.DateTime.oneDay)
                vto = VencimientoCobro(fecha = fechavto,
                                       importe = cantidad,
                                       facturaVenta = factura) 
                vtos_creados.append(vto)
                if diaest:
                    # Esto es más complicado de lo que pueda parecer a simple 
                    # vista. Ante poca inspiración... ¡FUERZA BRUTA!
                    fechas_est = []
                    for dia_estimado in diaest:
                        while True:
                            try:
                                fechaest = mx.DateTime.DateTimeFrom(
                                    day = dia_estimado, 
                                    month = fechavto.month, 
                                    year = fechavto.year)
                                break
                            except:
                                dia_estimado -= 1
                                if dia_estimado <= 0:
                                    dia_estimado = 31
                        # print utils.str_fecha(fechavto), utils.str_fecha(fechaest)
                        if fechaest < fechavto: 
                            # El día estimado cae ANTES del día del 
                            # vencimiento. No es lógico, la estimación debe 
                            # ser posterior.
                            # Cae en el mes siguiente, pues.
                            mes = fechaest.month + 1
                            anno = fechaest.year
                            if mes > 12:
                                mes = 1
                                anno += 1
                            try:
                                fechaest = mx.DateTime.DateTimeFrom(
                                    day = dia_estimado, 
                                    month = mes, 
                                    year = anno)
                            except mx.DateTime.RangeError:
                                fechaest = mx.DateTime.DateTimeFrom(
                                    day = -1, 
                                    month = mes, 
                                    year = anno)
                        fechas_est.append(fechaest)
                    fechas_est.sort(cmp_mxDateTime)
                    fechaest = fechas_est[0]
                    vto.fecha = fechaest 
        else:
            txt = "El cliente ID %d no tiene datos suficientes para crear vto.\
                    por defecto." % cliente.id
            print txt
        return vtos_creados

    def calcular_pendiente_cobro(self):
        """
        Devuelve la cantidad pendiente de cobro de la factura basándose, OJO, 
        en la diferencia entre vencimientos y cobros. Es decir, una factura 
        sin vencimientos _no está pendiente de cobro_.
        """
        totalfra = sum([v.importe for v in self.vencimientosCobro])
        cobrado = sum([c.importe for c in self.cobros])
        return totalfra - cobrado

    def calcular_kilos(self):
        """
        Devuelve la suma de las cantidades de todas las líneas de venta.
        """
        return sum([ldv.cantidad for ldv in self.lineasDeVenta])

    def fecha_vencimiento(self):
        vto = self.crear_vencimientos_por_defecto(True)
        if not vto:
            return ""
        elif len(vto) > 1: # Usar la fecha más antigua
            print "Hay mas de un vencimiento, ponemos el primero por defecto. "
            #for v in xrange(len(vto)):
            #    print vto[v].fecha
            return vto[0].fecha
        else:
            #print "NO: ", vto[0].fecha
            return vto[0].fecha

    def fecha_pago(self):
        cob = self.cobros[:]
        try:
            return cob[0].fecha
        except:
            return "no existe cobro"

    def estado(self):
        if self.calcular_pendiente_cobro() > 0:
            if comparar_fechas(str_fecha(),
                    str_fecha(self.fecha_vencimiento())) >= 0:
                # TODO "CREAR ALARMAS"
                st =  "Vencido"
            elif self.observaciones.count("Correo enviado"):
                st =  "Enviado"
            else:
                st =  "No enviado"
        elif self.calcular_pendiente_cobro() == 0:
            st =  "Cobrado"
        else:
            st =  "ERROR"
        return st

class Pale(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    lineasDeVenta = MultipleJoin("LineaDeVenta")

class Tarifa(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    lineasDeVenta = MultipleJoin("LineaDeVenta")
    precios = MultipleJoin("Precio")
    clientes = MultipleJoin("Cliente")

    def get_info(self):
        return "Tarifa ID %d: %s" % (self.id, self.nombre)

    def get_precio(self, producto):
        """
        Devuelve el precio (el importe total, no el registro) de la tarifa 
        para el producto recibido.
        Si no está definido, lanza un ValueError.
        Si hay más de un precio -creados por error del programa, pues 
        no debería suceder-, devuelve el último creado.
        """
        precio = self.get_precioID(producto)
        importe = precio.get_importe()
        return importe

    def get_precioID(self, producto):
        """
        Devuelve el precio (el ID del registro) de la tarifa 
        para el producto recibido.
        Si no está definido, lanza un ValueError.
        Si hay más de un precio -creados por error del programa, pues 
        no debería suceder-, devuelve el último creado.
        """
        sqlquery = """SELECT precio_id 
                      FROM precio_producto_venta 
                      WHERE producto_venta_id = %d 
                        AND precio_id IN (SELECT id 
                                          FROM precio 
                                          WHERE tarifa_id = %d)
                      ORDER BY precio_id DESC;""" %(
            producto.id, self.id)
        precios = Precio._connection.queryOne(sqlquery)
        try:
            return Precio.get(precios[0]).id
        except (IndexError, TypeError):
            raise ValueError

    def buscar_tarifa(producto, precio, exacto = False):
        """
        Devuelve la tarifa más cercana al precio recibido para el producto 
        recibido.
        Si exacto = True solo tiene en cuenta la tarifa cuyo precio sea 
        exactamente igual al recibido con 2 decimales de precisión.
        """
        tarifa = None
        mas_cercana = None
        diferencia_menor = None
        for p in producto.precios:
            p_importe = p.get_importe()
            if round(p_importe, 2) == precio:
                tarifa = p.tarifa
                mas_cercana = tarifa
                break
            else:
                if mas_cercana == None:
                    mas_cercana = p.tarifa
                else:
                    if (diferencia_menor == None 
                        or diferencia_menor > abs(precio - p_importe)):
                        mas_cercana = p.tarifa
        if not exacto:
            tarifa = mas_cercana
        return tarifa

    buscar_tarifa = staticmethod(buscar_tarifa)

    def add_conceptoLdv_a_ldvs(self, concepto):
        """
        Añade, partiendo del concepto «concepto» un nuevo conceptoLdv a las 
        líneas de venta no facturadas relacionadas con la tarifa (self).
        """
        for ldv in self.lineasDeVenta:
            if not ldv.facturaVenta:
                ConceptoLdv(concepto = concepto, 
                            textoConcepto = concepto.concepto, 
                            importe = concepto.importe, 
                            lineaDeVenta = ldv)

    def get_por_defecto():
        """
        Devuelve la tarifa por defecto (la última) o None si no hay.
        """
        try:
            return Tarifa.select(orderBy = "-id")[0]
        except IndexError:
            return None

    get_por_defecto = staticmethod(get_por_defecto)

class LineaDeVenta(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    if not sqlobject_version or not sqlobject_autoid():
        envase = ForeignKey("Envase")
        productoVenta = ForeignKey("ProductoVenta")
        albaranSalida = ForeignKey("AlbaranSalida")
        facturaVenta = ForeignKey("FacturaVenta")
        pale = ForeignKey("Pale")
        tarifa = ForeignKey("Tarifa")
        parcela = ForeignKey("Parcela", default = None)
    conceptosLdv = MultipleJoin("ConceptoLdv")

    def actualizar_conceptos(self):
        """
        Crea o cambia los conceptos relacionados con la LDV en función 
        de la tarifa de la misma siempre y cuando no esté facturada.
        Si tiene albarán de salida, aplica la tarifa del cliente.
        Si el cliente no tiene tarifa, busca la tarifa más cercana en precio 
        y aplica los conceptos de la misma.
        Si no encuentra ninguna tarifa, elimina los conceptos -si los 
        tuviera- o no los crea.
        """
        if not self.facturaVenta:
            self.tarifa = Tarifa.buscar_tarifa(self.productoVenta, self.precio)
            if self.tarifa:
                for conldv in self.conceptosLdv:
                    conldv.destroySelf()
                try:
                    precio_id = self.tarifa.get_precioID(self.productoVenta)
                    precio = Precio.get(precio_id)
                except ValueError:
                    pass
                else:
                    for con in precio.conceptos:
                        conldv = ConceptoLdv(lineaDeVenta = self, 
                                             textoConcepto = con.concepto, 
                                             concepto = con, 
                                             importe = con.importe)

    def calcular_bultos(self):
        """
        Devuelve el número de bultos correspondiente a la cantidad y 
        envase de la línea de venta.
        Siempre será un número entero. Redondea hacia arriba.
        """
        try:
            return int(ceil(self.cantidad / self.envase.kg)) 
        except:
            return 0

    def calcular_importe(self, iva = False):
        # XXX: Chequeo líneas incoherentes
        if self.precio == None:
            self.precio = 0.0
            self.sync()
        if self.cantidad == None:
            self.cantidad = 0.0
            self.sync()
        # XXX: EOChequeo líneas incoherentes
        res = self.precio * self.cantidad
        if iva:
            try:
                iva = self.facturaVenta.iva
            except AttributeError:
                try:
                    iva = self.albaranSalida.cliente.iva
                except AttributeError:  # Ni factura ni albarán
                    iva = 0.18   # No cliente, IVA por defecto = 0.18
        return res * (1.0 + iva)

class Servicio(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    if not sqlobject_version or not sqlobject_autoid():
        facturaVenta = ForeignKey('FacturaVenta')

    def _init(self, *args, **kw):
        starter(self, *args, **kw)

    def get_subtotal(self, iva = False):
        """
        Devuelve el subtotal del servicio. Con IVA (el IVA de la factura) 
        si se le indica.
        Si no tiene factura e iva es True, se aplica el IVA por defecto = 0.18.
        """
        res = self.cantidad * self.precio * (1 - self.descuento)
        if iva and self.facturaVentaID: 
            res *= (1 + self.facturaVenta.iva)
        return res

    calcular_importe = calcular_subtotal = get_subtotal

class Precio(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    if not sqlobject_version or not sqlobject_autoid():
        tarifa = ForeignKey("Tarifa")
    conceptos = MultipleJoin("Concepto")
    productosVenta = RelatedJoin("ProductoVenta")

    def get_importe(self):
        """
        Devuelve el importe total del precio por unidad, que 
        se compone de la suma de todos los conceptos más la 
        cantidad adicional.
        """
        [c.sync() for c in self.conceptos]
        res = sum([c.importe for c in self.conceptos])
        res += self.importeAdicional
        return res

    def actualizar_a(self, nuevo_importe, actualizar_ldvs_no_facturadas = True):
        """
        Actualiza el precio *total* al nuevo precio. 
        Opcionalmente, cambia el precio también en todos los albaranes 
        no facturados.
        """
        #CWT: Se cambia el precio base y se dejan intactos los conceptos.
        # Esto sí que es un déjà vu, porque juraría que era así hace un par de 
        # versiones y se cambió.
        #divisor = 1.0 * len(self.conceptos) #+ 1
        ##self.importeAdicional = nuevo_importe / divisor
        #for concepto in self.conceptos:
        #    concepto.importe = nuevo_importe / divisor
        #    concepto.sync()
        precio_anterior = self.get_importe()
        diferencia = nuevo_importe - precio_anterior
        self.importeAdicional += diferencia
        self.sync()
        if actualizar_ldvs_no_facturadas:
            #Una vez cambiado el precio, actualizo todas las LDVs no facturadas.
            for ldv in self.tarifa.lineasDeVenta:
                if not ldv.facturaVenta and ldv.albaranSalida:
                    if ldv.productoVenta in self.productosVenta:
                        ldv.precio = self.get_importe() 
                        ldv.sync()

class Concepto(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    if not sqlobject_version or not sqlobject_autoid():
        precio = ForeignKey("Precio")
    conceptosLdv = MultipleJoin("ConceptoLdv")

    def actualizar_conceptosLdv(self):
        """
        Actualiza los conceptosLdv relacionados pendientes de facturar 
        para que sean idénticos al concepto (self).
        """
        for cldv in self.conceptosLdv:
            if not cldv.lineaDeVenta.facturaVenta:
                cldv.textoConcepto = self.concepto
                cldv.importe = self.importe
                cldv.syncUpdate()

class ConceptoLdv(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    if not sqlobject_version or not sqlobject_autoid():
        lineaDeVenta = ForeignKey("LineaDeVenta")
        concepto = ForeignKey("Concepto")

class Salario(SQLObject, PRPCTOO):
    # XXX: Común a todas las clases que heredan de SQLObject.
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    # XXX: --------------------------------------------------

    if not sqlobject_version or not sqlobject_autoid():
        gasto = ForeignKey("Gasto")
        empleado = ForeignKey("Empleado")
        actividad = ForeignKey("Actividad")
    jornales = MultipleJoin("Jornal")

    def update_actividad(self):
        """
        Actualiza la actividad del salario a aquella que tenga más horas 
        acumuladas en los jornales que lo componen.
        """
        horas = {}
        max = 0.0
        clave_max = None
        for j in self.jornales:
            try:
                horas[j] += j.get_duracion()
            except KeyError:
                horas[j] = j.get_duracion()
            if horas[j] > max:
                max = horas[j]
                clave_max = j
        if clave_max:
            self.actividad = clave_max.actividad
        else:
            self.actividad = None
        self.sync()

class Usuario(SQLObject, PRPCTOO):
    _connection = conn
    sqlmeta.fromDatabase = True

    permisos = MultipleJoin('Permiso')
    alertas = MultipleJoin('Alerta')
    estadisticas = MultipleJoin('Estadistica')

    def _init(self, *args, **kw):
        starter(self, *args, **kw)

    def get_permiso(self, ventana):
        """
        Devuelve el registro permiso del usuario sobre 
        la ventana "ventana" o None si no se encuentra.
        """
        try:
            return [p for p in self.permisos if p.ventana == ventana][0]
        except IndexError:
            return None

    def enviar_mensaje(self, texto, permitir_duplicado = False):
        """
        Envía un nuevo mensaje al usuario creando una 
        alerta pendiente para el mismo.
        Si permitir_duplicado es False, se buscan los mensajes 
        con el mismo texto que se intenta enviar. En caso de 
        que exista, solo se actualizará la hora de la alerta 
        y se pondrá el campo "entregado" a False.
        Si es True, se envía el nuevo mensaje aunque pudiera 
        estar duplicado.
        """
        mensajes = Alerta.select(AND(Alerta.q.mensaje == texto, 
                                     Alerta.q.usuarioID == self.id))
        if not permitir_duplicado:
            for m in mensajes:
                m.destroySelf()
        a = Alerta(usuario = self, mensaje = texto, entregado = False)

class Modulo(SQLObject, PRPCTOO):
    _connection = conn
    sqlmeta.fromDatabase = True
    
    ventanas = MultipleJoin('Ventana')

    def _init(self, *args, **kw):
        starter(self, *args, **kw)

class Ventana(SQLObject, PRPCTOO):
    _connection = conn
    sqlmeta.fromDatabase = True
    
    if not sqlobject_version or not sqlobject_autoid():
        modulo = ForeignKey('Modulo')
    permisos = MultipleJoin('Permiso')
    estadisticas = MultipleJoin('Estadistica')

    def _init(self, *args, **kw):
        starter(self, *args, **kw)

class Permiso(SQLObject, PRPCTOO):
    _connection = conn
    sqlmeta.fromDatabase = True
    
    if not sqlobject_version or not sqlobject_autoid():
        usuario = ForeignKey('Usuario')
        ventana = ForeignKey('Ventana')

    def _init(self, *args, **kw):
        starter(self, *args, **kw)

class Alerta(SQLObject, PRPCTOO):
    _connection = conn
    sqlmeta.fromDatabase = True
    
    if not sqlobject_version or not sqlobject_autoid():
        usuario = ForeignKey('Usuario')

    def _init(self, *args, **kw):
        starter(self, *args, **kw)

class DatosDeLaEmpresa(SQLObject, PRPCTOO):
    _connection = conn
    sqlmeta.fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)

    def get_propia_empresa_como_cliente(clase):
        """
        Devuelve el registro cliente de la BD que se corresponde 
        con la empresa atendiendo a los datos del registro DatosDeLaEmpresa
        o None si no se encuentra.
        """
        nombre_propia_empresa = clase.select()[0].nombre
        clientes = Cliente.select(Cliente.q.nombre == nombre_propia_empresa)
        if clientes.count() == 0:
            cliente = None
        elif clientes.count() == 1:
            cliente = clientes[0]
        else:   # >= 2
            print "pclases.py: DatosDeLaEmpresa::get_propia_empresa_como_cliente: Más de un posible cliente encontrado. Selecciono el primero."
            cliente = clientes[0]
        return cliente

    def get_propia_empresa_como_proveedor(clase):
        """
        Devuelve el registro proveedor que se corresponde con la 
        empresa atendiendo a los datos del registro DatosDeLaEmpresa 
        o None si no se encuentra.
        """
        nombre_propia_empresa = clase.select()[0].nombre
        proveedores = Proveedor.select(Proveedor.q.nombre == nombre_propia_empresa)
        if proveedores.count() == 0:
            proveedor = None
        elif proveedores.count() == 1:
            proveedor = proveedores[0]
        else:   # >= 2
            print "pclases.py: DatosDeLaEmpresa::get_propia_empresa_como_proveedor: Más de un posible proveedor encontrado. Selecciono el primero."
            proveedor = proveedores[0]
        return proveedor
    
    get_cliente = classmethod(get_propia_empresa_como_cliente)
    get_proveedor = classmethod(get_propia_empresa_como_proveedor)
  
class Estadistica(SQLObject, PRPCTOO):
    _connection = conn
    sqlmeta.fromDatabase = True
    
    if not sqlobject_version or not sqlobject_autoid():
        usuario = ForeignKey('Usuario')
        ventana = ForeignKey('Ventana')

    def _init(self, *args, **kw):
        starter(self, *args, **kw)

    def incrementar(usuario, ventana):
        if isinstance(usuario, int):
            usuario_id = usuario
        else:
            usuario_id = usuario.id
        if isinstance(ventana, int):
            ventana_id = ventana
        elif isinstance(ventana, str):
            try:
                ventana = Ventana.selectBy(fichero = ventana)[0]
                ventana_id = ventana.id
            except Exception, msg:
                print "pclases::Estadistica::incrementar -> Ventana '%s' no encontrada. Excepción: %s" % (ventana, msg)
                return
        else:
            ventana_id = ventana.id
        st = Estadistica.select(AND(Estadistica.q.usuarioID == usuario_id, Estadistica.q.ventanaID == ventana_id))
        if not st.count():
            st = Estadistica(usuarioID = usuario_id, 
                             ventanaID = ventana_id)
        else:
            if st.count() > 1:
                sts = list(st)
                st = sts[0]
                for s in sts[1:]:
                    st.veces += s.veces
                    s.destroySelf()
            st = st[0]
        st.ultimaVez = mx.DateTime.localtime()
        st.veces += 1
        st.sync()

    incrementar = staticmethod(incrementar)


## XXX XXX XXX XXX XXX XXX XXX XXX XXX XXX XXX XXX XXX XXX XXX XXX XXX XXX XXX

if __name__ == '__main__':
    pass

