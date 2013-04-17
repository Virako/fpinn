#! /usr/bin/python
# -*- coding:utf-8 -*-

###############################################################################
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

import sane


def select_scan():
    sane.init()
    devices = sane.get_devices()

    if not len(devices):
        print "No existen dispositivos. "
        return 0
    elif len(devices) > 1:
        print "Seleccione el dispositivo deseado: " # TODO
        n = -1
        while n != -1:
            num = 0
            for d in devices:
                print num, ": ", d
                num += 1
            try:
                n = int(raw_input("Seleccione dispositivo para usar: "))
            except:
                n = -1
        return devices[n][0]
    elif len(devices) == 1:
        return devices[0][0]


def scan(factura=None, cmr=None):
    print "scan"
    if factura:
        factura = factura.replace("/", "_")
        filename = "../factura/%s.pdf" % (factura)
    if cmr:
        filename = "../cmr/%s.pdf" % (cmr)
    if not filename:
        return -1

    sel_scan = select_scan()
    if not sel_scan:
        return -1
    scan = sane.open(sel_scan)
    scan.mode = 'color'
    scan.resolution = 150
    print "scannn"
    img = scan.scan()
    img.save(filename)
    return 1
