#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2013    Victor Ramirez de la Corte, (virako.9@gmail.com)      #
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


import pygtk
pygtk.require('2.0')
import sys
from optparse import OptionParser

from framework.configuracion import ConfigConexion
from formularios.menu import MetaF
from formularios.menu import Menu
from formularios.menu import enviar_correo


def main():
    user = None
    passwd = None
    if len(sys.argv) > 1:
        usage = "uso: %prog [opciones] usuario contraseña"
        parser = OptionParser(usage=usage)
        parser.add_option("-c", "--config", dest="fichconfig",
                help="Usa la configuración alternativa almacenada en FICHERO",
                metavar="FICHERO")
        (options, args) = parser.parse_args()
        fconfig = options.fichconfig
        if len(args) >= 1:
            user = args[0]
        if len(args) >= 2:
            passwd = args[1]
        # HACK
        if fconfig:
            config = ConfigConexion()
            config.set_file(fconfig)

    errores = MetaF()
    sys.stderr = errores

    m = Menu(user, passwd)
    m.mostrar()

    if not errores.vacio():
        print "Detectado errores en segundo plano durante la ejecución."
        enviar_correo('Errores en segundo plano. La stderr contiene:\n%s'
                % (errores), m.get_usuario())


if __name__ == '__main__':
    main()
