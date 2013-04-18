#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2005-2008 Francisco José Rodríguez Bogado,                    #
#                         (pacoqueen@users.sourceforge.net)                   #
# Copyright (C) 2013  Victor Ramirez de la Corte, virako.9@gmail.com          #
#                                                                             #
# This file is part of FPINN.                                                 #
#                                                                             #
# FPINN is free software; you can redistribute it and/or modify               #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation; either version 2 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# FPINN is distributed in the hope that it will be useful,                    #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with FPINN; if not, write to the Free Software                        #
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA  #
###############################################################################

from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import os
from framework import pclases
from formularios import utils
from informes import geninformes 
from tempfile import gettempdir


def go(numalbaran = "XXXXXX", 
       fecha = "", 
       nombre_cliente = "", 
       direccion = "", 
       ciudad = "", 
       cif = "", 
       matricula = "", 
       ldvs = [], 
       total = 0.0, 
       solo_texto = False):
    """
    A partir de los parámetros recibidos construye un PDF con el albarán 
    completo.
    ldvs es una lista de cantidad (float), concepto, kgs (float), precio 
    (float) e importe (float).
    Si len(ldvs) > 12 genera (len(ldvs)/12) + 1 páginas, con el número 
    de página entre paréntesis tras el número de albarán.
    Si solo_texto es True, no se dibuja la plantulla del albarán, solo los 
    datos.
    Devuelve en nombre del fichero generado.
    """
    # Inicialización y medidas:
    nomarchivo = os.path.join(gettempdir(), "albaran_%s.pdf" % (
                                        geninformes.give_me_the_name_baby()))
    c = canvas.Canvas(nomarchivo)
    tampag = (19*cm, 14.8*cm)
    c.setPageSize(tampag)
    tm, bm, lm, rm = 1*cm, 1*cm, .7*cm, 1*cm
    fuente, tamanno = "Helvetica", 10
    hlin = 0.7*cm
    MAXLINEAS = 12
    paginas = int(len(ldvs) / MAXLINEAS) + 1
    medidas = {"Albarán": (9*cm, tampag[1] - 1.4*cm), 
               "N.º": (15.3*cm, tampag[1] - 1.3*cm),
               "Fecha": (14.3*cm, tampag[1] - 1.9*cm),
               "Cliente": (7.7*cm, tampag[1] - 2.5*cm),
               "Domicilio": (8*cm, tampag[1] - 3.1*cm),
               "Población": (2.7*cm, tampag[1] - 3.9*cm),
               "N.I.F.": (8.8*cm, tampag[1] - 3.9*cm),
               "Matrícula": (14.5*cm, tampag[1] - 3.9*cm),
              }
    xcantidad = 1.2*cm
    xconcepto = 3.4*cm
    xcateg = 9.4*cm
    xkgs = 11.25*cm
    xprecio = 13.05*cm
    ximporte = 15.7*cm
    y0 = tampag[1] - 4.2*cm
    yfinal = 1.75*cm
    y1 = yfinal + (MAXLINEAS * hlin)
    medidas_tabla = {"xcantidad": xcantidad, 
                     "xconcepto": xconcepto, 
                     "xcateg": xcateg, 
                     "xkgs": xkgs, 
                     "xprecio": xprecio, 
                     "ximporte": ximporte, 
                     "y0": y0, 
                     "yfinal": yfinal, 
                     "y1": y1, 
                     "ytotal": bm, 
                     "xfinal": tampag[0] - rm, 
                    } 
    # Páginas del albarán
    for pag in range(1, paginas + 1):
        # Parte preimpresa:
        if not solo_texto:
            dibujar_imprenta(c, hlin, tm, bm, lm, rm, tampag, medidas, 
                             fuente, tamanno, MAXLINEAS, medidas_tabla)
        # Datos:
        c.setFont(fuente, tamanno)
        if paginas > 1:
            numalb = numalbaran + "(%d)" % pag
            if pag == paginas:
                strtot = utils.float2str(total)
            else:
                strtot = ""
        else:
            numalb = numalbaran
            strtot = utils.float2str(total)
        rellenar_datos(c, numalb, fecha, nombre_cliente, direccion, ciudad, 
                       cif, matricula, medidas, fuente, tamanno)
        rellenar_ldvs(c, ldvs[:MAXLINEAS], strtot, medidas_tabla, hlin)
        ldvs = ldvs[MAXLINEAS:]
        c.showPage()
    c.save()
    return nomarchivo

def rellenar_datos(c, numalbaran, fecha, nombre_cliente, direccion, ciudad, 
                   cif, matricula, medidas, fuente, tamanno):
    c.drawString(medidas["N.º"][0] + 0.1*cm, medidas["N.º"][1] + 0.1*cm, 
                 geninformes.escribe(numalbaran))
    c.drawString(medidas["Fecha"][0] + 0.1*cm, medidas["Fecha"][1] + 0.1*cm, 
                 geninformes.escribe(fecha))
    c.drawString(medidas["Cliente"][0] + 0.1*cm, 
                 medidas["Cliente"][1] + 0.1*cm, 
                 geninformes.escribe(nombre_cliente))
    c.drawString(medidas["Domicilio"][0] + 0.1*cm, 
                 medidas["Domicilio"][1] + 0.1*cm, 
                 geninformes.escribe(direccion))
    c.drawString(medidas["Población"][0] + 0.1*cm, 
                 medidas["Población"][1] + 0.1*cm, 
                 geninformes.escribe(ciudad))
    c.drawString(medidas["N.I.F."][0] + 0.1*cm, medidas["N.I.F."][1] + 0.1*cm, 
                 geninformes.escribe(cif))
    c.drawString(medidas["Matrícula"][0] + 0.1*cm, 
                 medidas["Matrícula"][1] + 0.1*cm, 
                 geninformes.escribe(matricula))
    c.saveState()
    c.setFillColorRGB(0.8, 0, 0)
    c.setFont(fuente, tamanno + 4)
    numalbaran = ("%5s" % numalbaran).replace(" ", "0")
    c.drawString(medidas["Albarán"][0] 
                    + c.stringWidth(geninformes.escribe("Albarán"), fuente, tamanno)
                    + 0.5 * cm, 
                 medidas["Albarán"][1], 
                 geninformes.escribe(numalbaran))
    c.restoreState()

def rellenar_ldvs(c, ldvs, total, medidas_tabla, hlin):
    y = medidas_tabla["y1"]
    for ldv in ldvs:
        y -= hlin
        c.drawRightString(medidas_tabla["xconcepto"] - 0.1*cm, 
                          y + 0.15 *cm, 
                          geninformes.escribe(ldv[0]))
        c.drawString(medidas_tabla["xconcepto"] + 0.1*cm, 
                     y + 0.15 *cm, 
                     geninformes.escribe(ldv[1]))
        c.drawCentredString(
                     (medidas_tabla["xcateg"] + medidas_tabla["xkgs"])/2, 
                     y + 0.15 *cm, 
                     geninformes.escribe(ldv[2]))
        c.drawRightString(medidas_tabla["xprecio"] - 0.1*cm, 
                          y + 0.15 *cm, 
                          geninformes.escribe(ldv[3]))
        c.drawRightString(medidas_tabla["ximporte"] - 0.1*cm, 
                          y + 0.15 *cm, 
                          geninformes.escribe(ldv[4]))
        c.drawRightString(medidas_tabla["xfinal"] - 0.1*cm, 
                          y + 0.15 *cm, 
                          geninformes.escribe(ldv[5]))
    c.drawRightString(medidas_tabla["xfinal"] - 0.1*cm, 
                      medidas_tabla["ytotal"] + 0.15 *cm, 
                      geninformes.escribe(total))

def dibujar_imprenta(c, hlin, tm, bm, lm, rm, tampag, medidas, fuente, 
                     tamanno, maxlineas, medidas_tabla):
    """
    Dibuja el "esqueleto" del albarán de salida. Viene de imprenta en las 
    hojas reales y es independiente de los datos.
    """
    try:
        dde = pclases.DatosDeLaEmpresa.select()[0]
    except IndexError:
        class FakeDDE:
            logo = "logo.xpm"
            direccion = "C/ Tal y pan, 5"
            ciudad = "New York, New York"
            provincia = "Estado de Nueva York"
            cp = "01234"
            telefono = "012 34 56 78"
        dde = FakeDDE()
    c.saveState()
    c.setFillColorRGB(0, .5, 0)
    c.setStrokeColorRGB(0, .5, 0)
    print_datos_empresa(c, dde, tm, lm, tampag)
    print_logo(c, os.path.join("imagenes", dde.logo), tampag)
    print_cabecera(c, tampag, rm, medidas, fuente, tamanno)
    print_tabla(c, hlin, tampag, rm, maxlineas, medidas_tabla)
    print_firmas(c, tampag, fuente, tamanno)
    c.restoreState()

def print_datos_empresa(c, dde, tm, lm, tampag):
    linea_datos = "%s %s C.P. %s" % (dde.direccion, dde.ciudad, dde.cp)
    if dde.ciudad != dde.provincia:
        linea_datos += " (" + dde.provincia + ")"
    linea_datos += " Teléfono %s" % dde.telefono
    c.saveState()
    c.setFont("Helvetica", 8)
    c.rotate(90)
    c.drawString(tm, -lm, 
                 geninformes.escribe(linea_datos))
    c.rotate(-90)
    c.restoreState()

def print_logo(c, logo, tampag):
    c.drawImage(logo, 1.2*cm, tampag[1] - 3*cm, 3.5*cm, 2*cm)

def print_cabecera(c, tampag, rm, medidas, fuente, tamanno):
    c.saveState()
    c.setFont("Helvetica", 12)
    c.drawString(medidas["Albarán"][0], 
                 medidas["Albarán"][1], 
                 geninformes.escribe("Albarán"))
    #c.setFillColorRGB(0.8, 0, 0)
    #c.setFont(fuente, tamanno + 4)
    #c.drawString(medidas["Albarán"][0] 
    #                + c.stringWidth(geninformes.escribe("Albarán"), fuente, tamanno)
    #                + 0.5 * cm, 
    #             medidas["Albarán"][1], 
    #             geninformes.escribe("XXXXX"))
    c.restoreState()
    c.drawRightString(medidas["N.º"][0], 
                      medidas["N.º"][1], 
                      geninformes.escribe("N.º"))
    c.line(medidas["N.º"][0] + 0.1*cm, 
           medidas["N.º"][1], 
           tampag[0] - rm, 
           medidas["N.º"][1])
    c.drawRightString(medidas["Fecha"][0], 
                      medidas["Fecha"][1], 
                      geninformes.escribe("Fecha"))
    c.line(medidas["Fecha"][0] + 0.1*cm, 
           medidas["Fecha"][1], 
           tampag[0] - rm, 
           medidas["Fecha"][1])
    c.drawRightString(medidas["Cliente"][0], 
                      medidas["Cliente"][1], 
                      geninformes.escribe("Cliente"))
    c.line(medidas["Cliente"][0] + 0.1*cm, 
           medidas["Cliente"][1], 
           tampag[0] - rm, 
           medidas["Cliente"][1])
    c.drawRightString(medidas["Domicilio"][0], 
                      medidas["Domicilio"][1], 
                      geninformes.escribe("Domicilio"))
    c.line(medidas["Domicilio"][0] + 0.1*cm, 
           medidas["Domicilio"][1], 
           tampag[0] - rm, 
           medidas["Domicilio"][1])
    c.drawRightString(medidas["Matrícula"][0], 
                      medidas["Matrícula"][1], 
                      geninformes.escribe("Matrícula"))
    c.line(medidas["Matrícula"][0] + 0.1*cm, 
           medidas["Matrícula"][1], 
           tampag[0] - rm, 
           medidas["Matrícula"][1])
    c.drawRightString(medidas["N.I.F."][0], 
                      medidas["N.I.F."][1], 
                      geninformes.escribe("N.I.F."))
    c.line(medidas["N.I.F."][0] + 0.1*cm, 
           medidas["N.I.F."][1], 
           medidas["Matrícula"][0] 
            - c.stringWidth(geninformes.escribe("Matrícula"), fuente, tamanno) 
            - 0.2*cm,
           medidas["N.I.F."][1])
    c.drawRightString(medidas["Población"][0], 
                      medidas["Población"][1], 
                      geninformes.escribe("Población"))
    c.line(medidas["Población"][0] + 0.1*cm, 
           medidas["Población"][1], 
           medidas["N.I.F."][0] 
            - c.stringWidth(geninformes.escribe("N.I.F."), fuente, tamanno) 
            - 0.2*cm,
           medidas["Población"][1])

def print_tabla(c, hlin, tampag,rm, maxlineas, medidas_tabla):
    xcantidad = medidas_tabla["xcantidad"]
    xconcepto = medidas_tabla["xconcepto"]
    xcateg = medidas_tabla["xcateg"]
    xkgs = medidas_tabla["xkgs"]
    xprecio = medidas_tabla["xprecio"]
    ximporte = medidas_tabla["ximporte"]
    y0 = medidas_tabla["y0"]
    yfinal = medidas_tabla["yfinal"]
    y1 = medidas_tabla["y1"]
    # Cabecera
    c.saveState()
    c.setFillColorRGB(1, 1, 1)
    geninformes.rectangulo(c, 
                           (xcantidad, y0), 
                           (xconcepto, y1), 
                           geninformes.escribe("Cantidad"), 
                           alinTxtX = "centro", 
                           alinTxtY = "centro", 
                           color_relleno = (0, 0.5, 0))
    geninformes.rectangulo(c, 
                           (xconcepto, y0), 
                           (xcateg, y1), 
                           geninformes.escribe("Concepto"), 
                           alinTxtX = "centro", 
                           alinTxtY = "centro", 
                           color_relleno = (0, 0.5, 0))
    geninformes.rectangulo(c, 
                           (xcateg, y0), 
                           (xkgs, y1), 
                           geninformes.escribe("Categ."), 
                           alinTxtX = "centro", 
                           alinTxtY = "centro", 
                           color_relleno = (0, 0.5, 0))
    geninformes.rectangulo(c, 
                           (xkgs, y0), 
                           (xprecio, y1), 
                           geninformes.escribe("Kgs"), 
                           alinTxtX = "centro", 
                           alinTxtY = "centro", 
                           color_relleno = (0, 0.5, 0))
    geninformes.rectangulo(c, 
                           (xprecio, y0), 
                           (ximporte, y1), 
                           geninformes.escribe("Precio"), 
                           alinTxtX = "centro", 
                           alinTxtY = "centro", 
                           color_relleno = (0, 0.5, 0))
    geninformes.rectangulo(c, 
                           (ximporte, y0), 
                           (tampag[0] - rm, y1), 
                           geninformes.escribe("Importe"), 
                           alinTxtX = "centro", 
                           alinTxtY = "centro", 
                           color_relleno = (0, 0.5, 0))
    c.restoreState()
    # Relleno
    c.saveState()
    c.setFillColorRGB(0.9, 1, 0.9)
    c.rect(xcantidad, 1.75*cm, tampag[0] - rm - xcantidad, y1 - 1.75*cm, 
           stroke = 0, fill=1)
    c.restoreState()
    # Líneas verticales
    c.line(xcantidad, y1, xcantidad, yfinal)
    c.line(xconcepto, y1, xconcepto, yfinal)
    c.line(xcateg, y1, xcateg, yfinal)
    c.line(xkgs, y1, xkgs, yfinal)
    c.line(xprecio, y1, xprecio, yfinal)
    c.line(ximporte, y1, ximporte, yfinal)
    c.line(tampag[0] - rm, y1, tampag[0] - rm, yfinal)
    c.saveState()
    c.setStrokeColorRGB(1, 1, 1)
    c.line(xconcepto, y0, xconcepto, y1)
    c.line(xcateg, y0, xcateg, y1)
    c.line(xkgs, y0, xkgs, y1)
    c.line(xprecio, y0, xprecio, y1)
    c.line(ximporte, y0, ximporte, y1)
    c.restoreState()
    # Líneas horizontales
    for i in range(maxlineas):
        y1 -= hlin
        c.line(xcantidad, y1, tampag[0] - rm, y1)
    # Total
    c.saveState()
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(ximporte - 0.15*cm, medidas_tabla["ytotal"] + 0.2*cm, 
                      geninformes.escribe("Total"))
    c.restoreState()
    geninformes.rectangulo(c, 
                           (ximporte, y1), 
                           (tampag[0] - rm, medidas_tabla["ytotal"]), 
                           color_relleno = (0.9, 1, 0.9))

def print_firmas(c, tampag, fuente, tamanno):
    c.saveState()
    c.setFont(fuente, tamanno - 2)
    c.drawString(2.9*cm, 1.4*cm, geninformes.escribe("Firma del conductor,"))
    c.drawString(8.9*cm, 1.4*cm, geninformes.escribe("Firma del cliente,"))
    c.restoreState()

def go_from_albaranSalida(albaran, solo_texto = False):
    """
    Construye el PDF del albarán a partir de un objeto AlbaranSalida.
    """
    numalbaran = albaran.numalbaran
    fecha = utils.str_fecha(albaran.fecha)
    nombre_cliente = albaran.cliente.nombre
    direccion = albaran.direccion 
    ciudad = albaran.ciudad
    cif = albaran.cliente.cif
    matricula = albaran.transportista and albaran.transportista.matricula or ""
    ldvs = []
    for ldv in albaran.lineasDeVenta:
        linea = (utils.float2str(ldv.calcular_bultos(), autodec = True), 
                 ldv.productoVenta.nombre, 
                 ldv.productoVenta.categoria, 
                 utils.float2str(ldv.cantidad), 
                 utils.float2str(ldv.precio), 
                 utils.float2str(ldv.calcular_importe()))
        ldvs.append(linea)
    total = albaran.calcular_importe()
    return go(numalbaran, fecha, nombre_cliente, direccion, ciudad, cif, 
              matricula, ldvs, total, solo_texto)

def prueba_albaran():
    from informes import abrir_pdf
    abrir_pdf(go_from_albaranSalida(pclases.AlbaranSalida.select()[0]))
    import time
    time.sleep(1)
    abrir_pdf(go_from_albaranSalida(pclases.AlbaranSalida.select()[0], True))

if __name__=='__main__':
    prueba_albaran()


