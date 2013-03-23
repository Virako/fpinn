#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2005, 2006 Francisco José Rodríguez Bogado,                   #
#                          Diego Muñoz Escalante.                             #
# (pacoqueen@users.sourceforge.net, escalant3@users.sourceforge.net)          #
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


import os

class Singleton(type):
    """
    Patrón Singleton para evitar que una misma instancia del programa trabaje 
    con varias configuraciones:
    """
    def __init__(self, *args):
        type.__init__(self, *args)
        self._instances = {}
    def __call__(self, *args):
        if not args in self._instances:
            self._instances[args] = type.__call__(self, *args)
        return self._instances[args]

class ConfigConexion:
    """
    Clase que recoge los parámetros de configuración
    a partir de un archivo.
    """
    __metaclass__ = Singleton

    def __init__(self, fileconf = 'ginn.conf'):
        if fileconf == None:
            fileconf = "ginn.conf"
        if os.sep in fileconf:
            fileconf = os.path.split(fileconf)[-1]
        self.__set_conf(fileconf)

    def __set_conf(self, fileconf):
        """
        Abre el fichero de configuración y parsea la información del mismo.
        """
        self.__fileconf = fileconf
        if not os.path.exists(self.__fileconf):
            self.__fileconf = os.path.join('framework', fileconf)
        if not os.path.exists(self.__fileconf):
            self.__fileconf = os.path.join('..', 'framework', fileconf)
        if not os.path.exists(self.__fileconf):
            # Es posible que estemos en un directorio más interno. Como por 
            # ejemplo, cuando se genera la documentación.
            self.__fileconf = os.path.join('..', '..', 'framework', fileconf)
        try:
            self.__fileconf = open(self.__fileconf)
        except IOError:
            self.__fileconf = None
            self.__conf = {}
            print "ERROR: configuracion::__set_conf -> Fichero de configuración %s no encontrado." % (fileconf)
        else:
            self.__conf = self.__parse()

    def set_file(self, fileconf):
        """
        Cambia el fichero de configuración y la configuración en sí por el recibido.
        """
        self.__set_conf(fileconf)

    def __parse(self):
        conf = {}
        l = self.__fileconf.readline()
        while l != '':
            l = l.replace('\t', ' ').replace('\n', '').split()
            if l and not l[0].startswith("#"):   
                # Ignoro líneas en blanco y las que comienzan con #
                conf[l[0]] = " ".join([p for p in l[1:] if p.strip() != ""])
            l = self.__fileconf.readline()
        return conf

    def get_tipobd(self):
        return self.__conf['tipobd']
        
    def get_user(self):
        return self.__conf['user']
    
    def get_pass(self):
        return self.__conf['pass']

    def get_dbname(self):
        return self.__conf['dbname']
        
    def get_host(self):
        return self.__conf['host']

    def get_logo(self):
        try:
            logo = self.__conf['logo']
        except KeyError:
            logo = "logo_gtx.jpg"       # Logo genérico
        return logo

    def get_title(self):
        """
        Título de la aplicación que se mostrará en el menú principal.
        """
        try:
            title = self.__conf['title']
        except KeyError:
            title = "FPINN"
        return title
    
    def get_puerto(self):
        """
        Devuelve el puerto de la configuración o el puerto por defecto 5432 
        si no se encuentra.
        """
        try:
            puerto = self.__conf['port']
        except KeyError:
            puerto = '5432'
        return puerto

    def get_dir_adjuntos(self):
        """
        Devuelve el directorio donde se guardarán los adjuntos. Por defecto 
        "adjuntos". La ruta debe ser un único nombre de directorio y se 
        alojará como subdirectorio del "raíz" de la aplicación. Al mismo 
        nivel que "framework", "formularios", etc.
        """
        try:
            ruta = self.__conf['diradjuntos']
        except KeyError:
            ruta = "adjuntos"
        return ruta

    def get_dir_compartido(self):
        """
        Devuelve el directorio donde se guardarán los adjuntos. Por defecto 
        "compartido".
        La ruta debe ser un único nombre de directorio y se alojará como 
        subdirectorio del "raíz" de la aplicación. Al mismo nivel que 
        "framework", "formularios", etc.
        """
        try:
            ruta = self.__conf['dircompartido']
        except KeyError:
            ruta = "compartido"
        return ruta

    def get_kiosco(self):
        try:
            return bool(int(self.__conf["kiosco"]))
        except:
            return False

def unittest():
    """
    Pruebas unitarias del patrón Singleton.
    """
    class Test:
        __metaclass__=Singleton
        def __init__(self, *args): pass
            
    ta1, ta2 = Test(), Test()
    assert ta1 is ta2
    tb1, tb2 = Test(5), Test(5)
    assert tb1 is tb2
    assert ta1 is not tb1

 
