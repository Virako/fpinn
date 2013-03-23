#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2005-2008 Francisco José Rodríguez Bogado,                    #
#                         (pacoqueen@users.sourceforge.net)                   #
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

import reportlab
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
import mx, mx.DateTime

import sys, os
try:
    import pclases
except ImportError:
    sys.path.append(os.path.join('..', 'framework'))
    import pclases
try:
    import utils
except ImportError:
    sys.path.append(os.path.join('..', 'formularios'))
    import utils
try:
    import geninformes 
except ImportError:
    try:
        sys.path.append(os.path.insert(0, '.'))
        import geninformes
    except ImportError:
        sys.path.append(os.path.join('..', 'informes'))
        import geninformes
from tempfile import gettempdir
import Image, ImageEnhance

def reduce_opacity(im, opacity):
    """Returns a PIL image with reduced opacity.
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/362879
    """
    assert opacity >= 0 and opacity <= 1
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    else:
        im = im.copy()
    alpha = im.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    im.putalpha(alpha)
    return im

def watermark(im, mark, position, opacity=1):
    """Adds a watermark to an image.
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/362879
    """
    if opacity < 1:
        mark = reduce_opacity(mark, opacity)
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    # create a transparent layer the size of the image and draw the
    # watermark in that layer.
    layer = Image.new('RGBA', im.size, (0,0,0,0))
    if position == 'tile':
        for y in range(0, im.size[1], mark.size[1]):
            for x in range(0, im.size[0], mark.size[0]):
                layer.paste(mark, (x, y))
    elif position == 'scale':
        # scale, but preserve the aspect ratio
        ratio = min(
            float(im.size[0]) / mark.size[0], float(im.size[1]) / mark.size[1])
        w = int(mark.size[0] * ratio)
        h = int(mark.size[1] * ratio)
        mark = mark.resize((w, h))
        layer.paste(mark, ((im.size[0] - w) / 2, (im.size[1] - h) / 2))
    else:
        layer.paste(mark, position)
    # composite the watermark with the layer
    return Image.composite(layer, im, layer)


def go(numfactura = "", 
       fecha = "", 
       nombre_cliente = "", 
       direccion = "", 
       ciudad = "", 
       cif = "", 
       ldvs = [], 
       totales = [], 
       solo_texto = False):
    """
    A partir de los parámetros recibidos construye un PDF con el factura 
    completo.
    ldvs es una lista de cantidad (float), concepto, kgs (float), precio 
    (float) e importe (float).
    Si len(ldvs) > MAXLINEAS genera (len(ldvs)/MAXLINEAS) + 1 páginas, con el 
    número de página entre paréntesis tras el número de factura.
    Si solo_texto es True, no se dibuja la plantulla de la factura, solo los 
    datos.
    Devuelve en nombre del fichero generado.
    """
    # Inicialización y medidas:
    nomarchivo = os.path.join(gettempdir(), "factura_%s.pdf" % (
                                        geninformes.give_me_the_name_baby()))
    c = canvas.Canvas(nomarchivo)
    c.setTitle("factura_%s" % numfactura)
    tampag = A4
    c.setPageSize(tampag)
    tm, bm, lm, rm = 1*cm, .6*cm, .6*cm, 1*cm
    fuente, tamanno = "Helvetica", 10
    hlin = 0.7*cm
    MAXLINEAS = 30
    paginas = int((len(ldvs) + len(totales))/ MAXLINEAS) + 1
    medidas = {"cliente": (10*cm, tampag[1]-1*cm, 18.6*cm, tampag[1]-4.95*cm), 
                # x e y para la esquina sup. izq. e inf. der.
               "logo": (2.2*cm, tampag[1] - 1.3*cm, 5.2*cm, 3.4*cm),
                # (x,y) de esquina sup. izq. y ancho y alto 
               "dde": (tampag[1]/2, -0.6*cm),
                # (x,y) sabiendo que va con CenteredString y girado 90º
               "regmercantil": (tampag[0]/2, 0.6*cm),
                # (x,y) sabiendo que va centrado.
               "ldvs": (1*cm, tampag[1] - 6.2*cm, tampag[0]-rm, 2.7*cm),
                # (x,y) de esquinas sup. izq. e inf. der.
               "watermark": (9.5*cm, 13.5*cm, 9.5*cm, 10*cm), 
                # esquina sup. izq., ancho y alto
               "numfactura": (1.5*cm, tampag[1] - 5.8*cm), 
                # (x,y)
               "fecha": (10.5*cm, tampag[1] - 5.8*cm), 
                # (x,y)
              }
    hcab = 0.5*cm   # altura cabecera
    medidas_tabla = {"xnumalb":  1.0*cm,  
                     "xdesc":    1.0*cm+2.7*cm, 
                     "xfecha":   1.0*cm+2.7*cm+7.4*cm, 
                     "xkgs":     1.0*cm+2.7*cm+7.4*cm+2.6*cm, 
                     "xprecio":  1.0*cm+2.7*cm+7.4*cm+2.6*cm+1.7*cm, 
                     "ximporte": 1.0*cm+2.7*cm+7.4*cm+2.6*cm+1.7*cm+2*cm,
                     "xfinal": medidas["ldvs"][2], 
                     "y0": medidas["ldvs"][1] - hcab, 
                     "yfinal": medidas["ldvs"][3], 
                     "y1": medidas["ldvs"][1] - hcab - hlin, 
                     "h": hlin, 
                     "hcab": hcab
                    } 
    # Páginas de la factura
    for pag in range(1, paginas + 1):
        # Parte preimpresa:
        if not solo_texto:
            dibujar_imprenta(c, hlin, tm, bm, lm, rm, tampag, medidas, 
                             fuente, tamanno, MAXLINEAS, medidas_tabla)
        # Datos:
        c.setFont(fuente, tamanno)
        if paginas > 1:
            numalb = numfactura + "(%d)" % pag
            if pag == paginas:
                printot = totales
            else:
                printot = []
        else:
            numalb = numfactura
            printot = totales
        rellenar_datos(c, numalb, fecha, nombre_cliente, direccion, ciudad, 
                       cif, medidas, fuente, tamanno)
        rellenar_ldvs(c, ldvs[:MAXLINEAS], printot, medidas_tabla, hlin)
        ldvs = ldvs[MAXLINEAS:]
        c.showPage()
    c.save()
    return nomarchivo

def rellenar_datos(c, numfactura, fecha, nombre_cliente, direccion, ciudad, 
                   cif, medidas, fuente, tamanno):
    c.saveState()
    c.setFont(fuente, tamanno + 4)
    c.drawString(medidas["numfactura"][0], medidas["numfactura"][1], 
                 geninformes.escribe(numfactura))
    c.drawString(medidas["fecha"][0], medidas["fecha"][1], 
                 geninformes.escribe("Fecha: " + fecha))
    c.drawString(medidas["cliente"][0]+0.7*cm, medidas["cliente"][1]-1.0*cm, 
                 geninformes.escribe(nombre_cliente))
    c.drawString(medidas["cliente"][0]+0.7*cm, medidas["cliente"][1]-1.75*cm, 
                 geninformes.escribe(direccion))
    c.drawString(medidas["cliente"][0]+0.7*cm, medidas["cliente"][1]-2.50*cm, 
                 geninformes.escribe(ciudad))
    c.drawString(medidas["cliente"][0]+0.7*cm, medidas["cliente"][1]-3.25*cm, 
                 geninformes.escribe("CIF/NIF: " + cif))
    c.restoreState()

def rellenar_ldvs(c, ldvs, totales, medidas_tabla, hlin):
    y = medidas_tabla["y1"]
    for ldv in ldvs:
        y -= hlin
        c.drawCentredString(
                          (medidas_tabla["xnumalb"]+medidas_tabla["xdesc"])/2, 
                          y + 0.15*cm, 
                          geninformes.escribe(ldv[0]))
        c.drawString(medidas_tabla["xdesc"] + 0.1*cm, 
                     y + 0.15*cm, 
                     geninformes.escribe(ldv[1]))
        c.drawCentredString(
                          (medidas_tabla["xfecha"]+medidas_tabla["xkgs"])/2, 
                          y + 0.15*cm, 
                          geninformes.escribe(ldv[2]))
        c.drawRightString(medidas_tabla["xprecio"] - 0.1*cm, 
                          y + 0.15*cm, 
                          geninformes.escribe(ldv[3]))
        c.drawRightString(medidas_tabla["ximporte"] - 0.1*cm, 
                          y + 0.15*cm, 
                          geninformes.escribe(ldv[4]))
        c.drawRightString(medidas_tabla["xfinal"] - 0.1*cm, 
                          y + 0.15*cm, 
                          geninformes.escribe(ldv[5]))
    if totales:
        print_totales(c, totales, medidas_tabla, hlin)

def print_totales(c, totales, medidas_tabla, hlin):
    """
    Escribe cada línea de la lista de totales en la parte baja de 
    la tabla.
    Las líneas son a su vez una lista cuyo último elemento es el número 
    que va en la columna Importe y el resto se concatenan y alinean a la 
    derecha en la columna Precio.
    """
    c.saveState()
    c.setFont("Courier-Bold", 14)
    y = medidas_tabla["yfinal"]
    for linea in totales[::-1]:
        txt = " ".join([str(i) for i in linea[:-1]])
        tot = linea[-1]
        if not isinstance(tot, str):
            try:
                tot = utils.float2str(tot)
            except (TypeError, ValueError):
                tot = str(tot)
        c.drawRightString(medidas_tabla["ximporte"] - 0.2*cm, y + 0.2*cm, 
                          geninformes.escribe(txt))
        c.drawRightString(medidas_tabla["xfinal"] - 0.2*cm, y + 0.2*cm, 
                          geninformes.escribe(tot))
        y += medidas_tabla["h"]
    c.restoreState()

def dibujar_imprenta(c, hlin, tm, bm, lm, rm, tampag, medidas, fuente, 
                     tamanno, maxlineas, medidas_tabla):
    """
    Dibuja el "esqueleto" de la factura de venta. Viene de imprenta en las 
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
    print_datos_empresa(c, dde, medidas)
    print_logo(c, os.path.join("..", "imagenes", dde.logo), medidas["logo"])
    print_marca_agua(c, os.path.join("..", "imagenes", dde.logo), 
                     medidas["watermark"])
    print_cabecera(c, medidas["cliente"])
    print_tabla(c, medidas, medidas_tabla)
    c.restoreState()

def print_datos_empresa(c, dde, medidas):
    linea_datos = "%s %s C.P. %s" % (dde.direccion, dde.ciudad, dde.cp)
    if dde.ciudad != dde.provincia:
        linea_datos += " (" + dde.provincia + ")"
    linea_datos += " Teléfono %s" % dde.telefono
    c.saveState()
    c.setFont("Helvetica", 8)
    c.rotate(90)
    c.drawCentredString(medidas["dde"][0], medidas["dde"][1], 
                        geninformes.escribe(linea_datos))
    c.rotate(-90)
    c.drawCentredString(medidas["regmercantil"][0], medidas["regmercantil"][1], 
                        geninformes.escribe(dde.registroMercantil)) 
    c.restoreState()

def print_logo(c, logo, medidas):
    x, y, ancho, alto = medidas
    c.drawImage(logo, x, y - alto, ancho, alto)

def print_marca_agua(c, logo, medidas):
    x, y, ancho, alto = medidas
    i = Image.open(logo)
    color_pagina = (255, 255, 255, 255) # Por defecto blanco inmaculado.
    iwmark = watermark(Image.new("RGBA", i.size, color_pagina), 
                       i,
                       (0, 0), 
                       0.1)
    import tempfile
    ext = logo.split(".")[-1]
    # Se supone que reportlab puede pintar imágenes PIL, pero me ha cascado.
    tmpim = os.path.join(tempfile.gettempdir(), 
                         tempfile.gettempprefix() + "." + ext)
    iwmark.save(tmpim)
    c.drawImage(tmpim, x, y - iwmark.size[1], ancho, alto)

def print_cabecera(c, medidas):
    x1, y1, x2, y2 = medidas
    e1 = x1, y1, +0.5*cm, -0.5*cm
    e2 = x2, y1, -0.5*cm, -0.5*cm
    e3 = x1, y2, +0.5*cm, +0.5*cm
    e4 = x2, y2, -0.5*cm, +0.5*cm
    for e in (e1, e2, e3, e4):
        x, y, incx, incy = e
        c.line(x, y, x+incx, y)
        c.line(x, y, x, y+incy)

def print_tabla(c, medidas, medidas_tabla):
    y0 = medidas["ldvs"][1]
    y1 = y0 - medidas_tabla["hcab"]
    # Cabecera
    c.saveState()
    c.setFillColorRGB(1, 1, 1)
    geninformes.rectangulo(c, 
                           (medidas_tabla["xnumalb"], y0), 
                           (medidas_tabla["xdesc"], y1), 
                           geninformes.escribe("Nº Albarán"), 
                           alinTxtX = "centro", 
                           alinTxtY = "centro", 
                           color_relleno = (0, 0.5, 0))
    geninformes.rectangulo(c, 
                           (medidas_tabla["xdesc"], y0), 
                           (medidas_tabla["xfecha"], y1), 
                           geninformes.escribe("Descripción"), 
                           alinTxtX = "centro", 
                           alinTxtY = "centro", 
                           color_relleno = (0, 0.5, 0))
    geninformes.rectangulo(c, 
                           (medidas_tabla["xfecha"], y0), 
                           (medidas_tabla["xkgs"], y1), 
                           geninformes.escribe("Fecha"), 
                           alinTxtX = "centro", 
                           alinTxtY = "centro", 
                           color_relleno = (0, 0.5, 0))
    geninformes.rectangulo(c, 
                           (medidas_tabla["xkgs"], y0), 
                           (medidas_tabla["ximporte"], y1), 
                           geninformes.escribe("Kg y Precio"), 
                           alinTxtX = "centro", 
                           alinTxtY = "centro", 
                           color_relleno = (0, 0.5, 0))
    geninformes.rectangulo(c, 
                           (medidas_tabla["ximporte"], y0), 
                           (medidas["ldvs"][2], y1), 
                           geninformes.escribe("Importe"), 
                           alinTxtX = "centro", 
                           alinTxtY = "centro", 
                           color_relleno = (0, 0.5, 0))
    c.restoreState()
    # Líneas verticales
    c.line(medidas["ldvs"][0], medidas["ldvs"][1], 
           medidas["ldvs"][0], medidas["ldvs"][3])
    c.line(medidas["ldvs"][2], medidas["ldvs"][1], 
           medidas["ldvs"][2], medidas["ldvs"][3])
    # Líneas horizontales
    c.line(medidas["ldvs"][0], medidas["ldvs"][3], 
           medidas["ldvs"][2], medidas["ldvs"][3])
    # Total
    c.saveState()
    c.setFont("Helvetica-Bold", 12)
    c.restoreState()

def go_from_facturaVenta(factura, solo_texto = False):
    """
    Construye el PDF de la factura a partir de un objeto FacturaVenta.
    """
    numfactura = factura.numfactura
    fecha = utils.str_fecha(factura.fecha)
    nombre_cliente = factura.cliente.nombre
    direccion = factura.cliente.direccionfacturacion
    ciudad = "%s %s %s" % (
                factura.cliente.cpfacturacion, 
                factura.cliente.ciudadfacturacion, 
                factura.cliente.paisfacturacion 
                    and "("+factura.cliente.paisfacturacion+")" 
                    or "")
    cif = factura.cliente.cif
    # Líneas de venta agrupadas por albarán
    albs = {}
    for ldv in factura.lineasDeVenta:
        a = ldv.albaranSalida
        if a not in albs:
            albs[a] = [ldv]
        else:
            albs[a].append(ldv)
    ldvs = []
    albaranes = [a for a in albs.keys() if a != None]
    albaranes.sort(key = lambda a: a.numalbaran)
    if None in albs:
        albaranes.insert(0, None)
    for alb in albaranes:
        linea_albaran = (alb.numalbaran, 
                         "", 
                         utils.str_fecha(alb.fecha), 
                         "", 
                         "", 
                         "")
        ldvs.append(linea_albaran)
        for ldv in albs[alb]:
            linea = ("", 
                     ldv.productoVenta.nombre, 
                     "", 
                     utils.float2str(ldv.cantidad, autodec = True), 
                     utils.float2str(ldv.precio), 
                     utils.float2str(ldv.calcular_importe()))
            ldvs.append(linea)
    totales = []
    total = factura.calcular_importe_total(iva = True)
    comision = factura.comision
    if comision:
        totales.append(("% comisión", comision))
    transporte = factura.transporte
    dto = factura.descuento
    bimponible = factura.calcular_importe_total(iva = False, 
                                                incluir_dto_numerico = False)
    # XXX: Transporte fuera de IVA
    bimponible -= transporte
    # XXX
    if dto:
        totales.append((("Descuento %s%%" 
                            % utils.float2str(dto*100, autodec = True)), 
                         -bimponible * dto   
                            # Descuento, por definición, en negativo.
                       ))
    totales.append(("Base imponible", bimponible))
    if factura.iva != 0:
        # XXX: Transporte fuera de IVA
        # totiva = total - factura.descuentoNumerico - bimponible 
        totiva = total - factura.descuentoNumerico - bimponible - transporte
        # XXX
        totales.append(("%d%% IVA" % (factura.iva * 100), totiva)) 
    dtonum = factura.descuentoNumerico
    if dtonum:
        totales.append((factura.conceptoDescuentoNumerico, dtonum))
    if transporte:
        totales.append(("Transporte", transporte))
    totales.append(("TOTAL FACTURA", total))
    observaciones = factura.observaciones
    if observaciones:
        ldvs.append(("", "", "", "", "", ""))
        ldvs.append(("", "", "", "", "", ""))
        ldvs.append(("", "OBSERVACIONES:", "", "", "", ""))
        ldvs.append(("", "  " + observaciones, "", "", "", ""))
    return go(numfactura, fecha, nombre_cliente, direccion, ciudad, cif, 
              ldvs, totales, solo_texto)

def prueba_factura():
    sys.path.append("../formularios")
    from informes import abrir_pdf
    abrir_pdf(go_from_facturaVenta(pclases.FacturaVenta.select(
                orderBy = "-id")[0]))
    import time
    time.sleep(1)
    abrir_pdf(go_from_facturaVenta(pclases.FacturaVenta.select(
        orderBy = "-id")[0], True))

if __name__=='__main__':
    prueba_factura()


