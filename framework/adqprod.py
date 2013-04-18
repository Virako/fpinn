#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2005-2007  Francisco José Rodríguez Bogado,                   #
#                          (pacoqueen@users.sourceforge.net)                  #
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


"""
Módulo de adquisición de producciones.
"""

import mx, mx.DateTime
import md5
import sys
from framework import pclases
from formularios import utils


def procesar(data_recibido):
    """
    Recibe una cadena que contiene datos como cadena en el siguiente formato:
    idempleado: 4 caracteres con ceros por la izquierda.
    idactividad: 4 caracteres con ceros por la izquierda.
    idparcela: 4 caracteres con ceros por la izquierda.
    inicio: 12 caracteres en la forma AAAAMMDDHHSS (Año, mes, día, horas 
        y segundos).
    fin: 12 caracteres en la forma AAAAMMDDHHSS.
    producción: 10 caracteres con la producción en kilos, bien de manipulación,
        bien de recolección. Los dos últimos dígitos son décimas y centésimas.
        Completado con ceros por la izquierda.
    MD5: 32 caracteres con la suma MD5 del contenido previo. Si no coincide 
        se lanza una excepción ValueError.
    Devuelve una tupla con cada uno de los datos.
    Si alguno de los valores no es del tipo válido lanza un TypeError.
    """
    data = data_recibido[:]
    # Separo campos
    idempleado, data = data[:4], data[4:]
    idactividad, data = data[:4], data[4:]
    idparcela, data = data[:4], data[4:]
    inicio, data = data[:12], data[12:]
    fin, data = data[:12], data[12:]
    produccion, data = data[:10], data[10:]
    digest = data[:]
    # Comparación de MD5
    digest_data = md5.new(data_recibido[:-32]).hexdigest()
    if digest_data != digest:
        raise ValueError, "MD5 no coincide (recibido, computado): %s != %s" % (
                            digest, digest_data)
    # Proceso datos
    idempleado = int(idempleado)
    idactividad = int(idactividad)
    idparcela = int(idparcela)
    inicio = mx.DateTime.strptime(inicio, "%Y%m%d%H%M")
    fin = mx.DateTime.strptime(fin, "%Y%m%d%H%M")
    fin += (mx.DateTime.oneSecond * 60) - 0.01
        # A la fecha de fin la aproximo lo máximo que deja la resolución 
        # al minuto siguiente, para que la diferencia entre las 00:00 y las 
        # 23:59 del mismo día se aproxime lo más posible a las 24 horas.
    produccion = float(produccion[:-2]) + (float(produccion[-2:]) / 100)
    return idempleado, idactividad, idparcela, inicio, fin, produccion

def build_jornal(data = None, intentos = 5):
    """
    Devuelve un registro jornal con la producción recibida en data.
    Si data es None, pide los datos de nuevo hasta un máximo de «n» intentos.
    Si no consigue recibir o procesar bien los datos, devuelve None.
    """
    n = 0
    while (not data and n < intentos) or n == 0:    
            # La primera vez siempre debe entrar
        if not data:
            data = pedir_datos()
        n += 1
        try:
            ide, ida, idp, inicio, fin, prod = procesar(data)
        except ValueError:
            data = None
    if data != None:    # Los ha procesado correctamente.
        empleado = pclases.Empleado.get(ide)
        actividad = pclases.Actividad.get(ida)
        parcela = pclases.Parcela.get(idp)
        C = pclases.Campanna
        try:
            campanna = C.buscar_campanna(inicio)
            if campanna == None:
                raise IndexError
        except IndexError, msg:  
            # No existe la campaña. Devuelvo error y aviso por stderr.
            jornal = None
            sys.stderr.write("No existe campaña para la fecha %s.\n%s" % (
                utils.str_fechahora(inicio), msg))
        else:
            jornal = pclases.Jornal(empleado = empleado, 
                                    actividad = actividad, 
                                    campanna = campanna, 
                                    parcela = parcela, 
                                    salario = None, 
                                    fechahoraInicio = inicio, 
                                    fechahoraFin = fin, 
                                    produccion = prod)
    else:
        jornal = None
    return jornal

def jornal2data(jornal):
    """
    Proceso inverso: Construye un paquete de datos a partir del jornal.
    """
    idempleado, idactividad, idparcela, inicio, fin, produccion, digest \
        = jornal2chunk(jornal)
    data = idempleado + idactividad + idparcela + inicio + fin + produccion
    paquete = data + digest
    return paquete

def jornal2chunk(jornal):
    """
    Devuelve cada trozo que compone un paquete de datos procedente de un 
    nodo de campo por separado
    """
    idempleado = "%04d" % jornal.empleado.id
    idactividad = "%04d" % jornal.actividad.id
    idparcela = "%04d" % jornal.parcela.id
    fi = jornal.fechahoraInicio
    inicio = fi.strftime("%Y%m%d%H%M")
    ff = jornal.fechahoraFin
    fin = ff.strftime("%Y%m%d%H%M")
    prod = jornal.produccion
    produccion = "%08d%02d" % (int(prod), 
                               int(round((prod - int(prod)) * 100)))
    data = idempleado + idactividad + idparcela + inicio + fin + produccion
    digest = md5.new(data).hexdigest()
    return idempleado, idactividad, idparcela, inicio, fin, produccion, digest

def pedir_datos():
    """
    Pide y devuelve un paquete de datos.
    TODO: De momento lo construye artificialmente para pruebas hasta
    que se defina el protocolo de comunicación a bajo nivel.
    """
    import md5
    datos = "0001000100012008123100002008123123590000001234"
    datos += md5.new(datos).hexdigest()
    return datos

### UnitTests con python-unit (pyunit) [http://pyunit.sourceforge.net/]
if __name__ == "__main__":
    import unittest

    def build_sample():
        idempleado = "%04d" % 1
        idactividad = "%04d" % 1
        idparcela = "%04d" % 1
        fi = mx.DateTime.DateTimeFrom(day = 1, 
                                      month = 2, 
                                      year = 2003, 
                                      hour = 4, 
                                      minute = 5)
        inicio = fi.strftime("%Y%m%d%H%M")
        ff = fi + mx.DateTime.oneHour
        fin = ff.strftime("%Y%m%d%H%M")
        prod = 123.45
        produccion = "%08d%02d" % (int(prod), 
                                   int(round((prod - int(prod)) * 100)))
        data = idempleado + idactividad + idparcela + inicio + fin + produccion
        digest = md5.new(data).hexdigest()
        return data + digest

    class TestReceive(unittest.TestCase):
        def runTest(self):
            data = build_sample()
            resultado = (1, 1, 1, 
                         mx.DateTime.DateTimeFrom(day = 1, 
                                                  month = 2, 
                                                  year = 2003, 
                                                  hour = 4, 
                                                  minute = 5), 
                         mx.DateTime.DateTimeFrom(day = 1, 
                                                  month = 2, 
                                                  year = 2003, 
                                                  hour = 5, 
                                                  minute = 5, 
                                                  second = 59.99), 
                         123.45)
            # print procesar(data)
            # print resultado
            assert procesar(data) == resultado, "Proceso recepción incorrecto."

        def buildTest(self):
            """
            Necesita que haya datos de ejemplo (con datatest.py de ../bd) 
            para pasar este test y el pedir_datos de prueba que devuelve 
            "0001000100012008123100002008123123590000001234".
            """
            ini = mx.DateTime.DateTimeFrom(day = 31, 
                                           month = 12, 
                                           year = 2008, 
                                           hour = 0, 
                                           minute = 0, 
                                           second = 0)
            fin = mx.DateTime.DateTimeFrom(day = 31, 
                                           month = 12, 
                                           year = 2008, 
                                           hour = 23, 
                                           minute = 59, 
                                           second = 59.99)
            jornal1 = pclases.Jornal(empleado = pclases.Empleado.get(1), 
                                     campanna = pclases.Campanna.get(1), 
                                     actividad = pclases.Actividad.get(1), 
                                     parcela = pclases.Parcela.get(1), 
                                     fechahoraInicio = ini, 
                                     fechahoraFin = fin, 
                                     produccion = 12.34)
            jornal2 = build_jornal()
            assert (jornal1.empleado == jornal2.empleado and 
                    jornal1.campanna == jornal2.campanna and 
                    jornal1.parcela == jornal2.parcela and 
                    jornal1.actividad == jornal2.actividad and 
                    jornal1.fechahoraInicio == jornal2.fechahoraInicio and 
                    jornal1.fechahoraFin == jornal2.fechahoraFin and
                    jornal1.produccion == jornal2.produccion), \
                    "Construcción del jornal incorrecta."


    testCase = TestReceive()
    testCase.runTest()
    testCase.buildTest()

