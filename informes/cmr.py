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
from reportlab.lib.pagesizes import A4

import os
from framework import pclases
from formularios import utils
from informes import geninformes
from tempfile import gettempdir

def go(dde_nombre = "",
       dde_direccion1 = "",
       dde_direccion2 = "",
       cliente_nombre = "",
       cliente_direccion1 = "",
       cliente_direccion2 = "",
       entrega1 = "",
       entrega2 = "",
       transportista_nombre = "",
       transportista_direccion1 = "",
       transportista_direccion2 = "",
       observaciones = "",
       ldvs = [],
       estipulaciones = "",
       ciudad = "",
       mes = "",    # Día y mes o solo nombre del mes. Como se quiera.
       anno = "",   # OJO: Sólo los dos últimos dígitos del año.
       solo_texto = False, 
       porteador = "", 
       sucesivos = "", 
       ciudad_formalizado = ""):
    """
    A partir de los parámetros recibidos construye un PDF con el CMR.
    ldvs es una lista de bultos, embalaje y kgs.
    Si solo_texto es True, no se dibuja la plantilla del albarán, solo los
    datos.
    Devuelve en nombre del fichero generado.
    """
    # Inicialización y medidas:
    nomarchivo = os.path.join(gettempdir(), "cmr_%s.pdf" % (
                                        geninformes.give_me_the_name_baby()))
    c = canvas.Canvas(nomarchivo)
    tampag = A4
    c.setPageSize(tampag)
    tm, bm, lm, rm = 0.3*cm, 0.8*cm, 1*cm, 1*cm
    fuente, tamanno = "Helvetica", 8
    hlin = 0.7*cm
    MAXLINEAS = int(5.5*cm / hlin)
    paginas = int(len(ldvs)/ MAXLINEAS) + 1
        # Dato a imprimir, x1, x2 (o None si no va centrado) e y.
        # Si dato es una lista, se usará hlin para decrementar la y.
        # Si x1 y x2 son listas/tuplas, es porque el dato también se
        # divide en listas/tuplas (columnas) y se corresponden entre sí.
    medidas = {
     "dde_nombre":
        (dde_nombre,                   2*cm, None,      27.50*cm),
     "dde_direccion1":
        (dde_direccion1,               2*cm, None,      27   *cm),
     "dde_direccion2":
        (dde_direccion2,               2*cm, None,      26.5 *cm),
     "cliente_nombre":
        (cliente_nombre,               2*cm, None,      25   *cm),
     "cliente_direccion1":
        (cliente_direccion1,           2*cm, None,      24.50*cm),
     "cliente_direccion2":
        (cliente_direccion2,           2*cm, None,      24   *cm),
     "entrega1":
        (entrega1,                     2*cm, None,      22.25*cm),
     "entrega2":
        (entrega2,                     2*cm, None,      22.65*cm),
     "transportista1_nombre":
        (transportista_nombre,     11.35*cm, None,      25.00*cm),
     "transportista1_direccion1":
        (transportista_direccion1, 11.35*cm, None,      24.50*cm),
     "transportista1_direccion2":
        (transportista_direccion2, 11.35*cm, None,      24.00*cm),
     "transportista2_nombre":
        (transportista_nombre,      7.80*cm, 13.30*cm,   3.5 *cm),
     "transportista2_direccion1":
        (transportista_direccion1,  7.80*cm, 13.30*cm,   2.75*cm),
     "transportista2_direccion2":
        (transportista_direccion2,  7.80*cm, 13.30*cm,   2.00*cm),
     "observaciones":
        (observaciones,            11.10*cm, 19.40*cm,  20.8 *cm),
     "porteador":
        (porteador,                11.10*cm, 19.40*cm,  24.50*cm),
     "sucesivos":
        (sucesivos,                11.10*cm, 19.40*cm,  22.65*cm),
     "ldvs":
        (ldvs,                    ( 4.50*cm,
                                    7.30*cm,
                                   15.20*cm),( 7.00*cm,
                                              10.00*cm,
                                              17.45*cm), 17.25*cm),
     "estipulaciones":
        (estipulaciones,           11.10*cm, 19.40*cm,   10   *cm),
     "ciudad1":
        (ciudad_formalizado,        3.75*cm, None,        4.85 *cm),
     "mes1":
        (mes,                       7.8 *cm, None,        4.85 *cm),
     "anno1":
        (anno,                     10.0 *cm, None,        4.85 *cm),
     "ciudad2":
        (ciudad,                   14.50*cm, None,        3.10*cm),
     "mes2":
        (mes,                      17.75*cm, None,        3.10*cm),
     "anno2":
        (anno,                     19.2 *cm, None,        3.10*cm),
              }
    # Páginas del albarán
    for pag in range(1, paginas + 1):
        # Parte preimpresa:
        if not solo_texto:
            dibujar_imprenta(c, tampag)
        # Datos:
        c.setFont(fuente, tamanno)
        rellenar_datos(c, medidas, fuente, tamanno, hlin)
        rellenar_ldvs(c, ldvs[:MAXLINEAS], medidas, fuente, tamanno, hlin)
        ldvs = ldvs[MAXLINEAS:]
        c.showPage()
    c.save()
    return nomarchivo

def escribir(c, txt, x1, x2, y, inc, fuente, tamanno):
    """
    Escribe el texto «txt» en el canvas «c».
    Si lo recibido es una lista usa inc para decrementar la y hasta que 
    agota los elementos de la lista.
    Si x1 o x2 son listas/tuplas, escribe los subelementos de txt (que debe 
    ser una lista de listas) en esas posiciones.
    """
    if isinstance(txt, (tuple, list)):
        escribir_lista(c, txt, x1, x2, y, inc, fuente, tamanno)
    else:
        escribir_texto(c, txt, x1, x2, y, fuente, tamanno)

def escribir_texto(c, txt, x1, x2, y, fuente, tamanno):
    if x2:
        geninformes.agregarFila(x1, 
                                y, 
                                x2, 
                                geninformes.escribe(txt), 
                                c, 
                                fuente, 
                                tamanno, 
                                centrado = True, 
                                altura_linea = 0.25*cm)
    else:
        c.drawString(x1, y, geninformes.escribe(txt))

def escribir_lista(c, lineas, x1, x2, y, inc, fuente, tamanno):
    for linea in lineas:
        if isinstance(linea, (tuple, list)):
            escribir_linea(c, linea, x1, x2, y, fuente, tamanno)
        else:
            escribir_texto(c, linea, x1, x2, y, fuente, tamanno)
        y -= inc

def escribir_linea(c, elementos, x1, x2, y, fuente, tamanno):
    for txt, sx1, sx2 in zip(elementos, x1, x2):
        escribir_texto(c, txt, sx1, sx2, y, fuente, tamanno)

def rellenar_datos(c, medidas, fuente, tamanno, inc):
    for clave in medidas:
        if clave != "ldvs":
            que, x1, x2, y = medidas[clave]
            escribir(c, que, x1, x2, y, inc, fuente, tamanno)

def rellenar_ldvs(c, ldvs, medidas, fuente, tamanno, inc):
    todas_ldvs, x1, x2, y = medidas["ldvs"]
    escribir(c, ldvs, x1, x2, y, inc, fuente, tamanno)

def dibujar_imprenta(c, tampag):
    """
    Dibuja el "esqueleto" del CMR. Viene de imprenta en las
    hojas reales y es independiente de los datos.
    """
    fondo = os.path.join("imagenes", "cmr.png")
    c.drawImage(fondo, 0, 0, tampag[0], tampag[1])

def go_from_albaranSalida(albaran, solo_texto = False, porteador = "", 
                          sucesivos = ""):
    """
    Construye el PDF del albarán a partir de un objeto AlbaranSalida.
    """
    try:
        dde = pclases.DatosDeLaEmpresa.select()[0]
        dde_nombre = dde.nombre
        dde_direccion1 = dde.direccion
        dde_direccion2 = "%s-%s %s (%s)" % (dde.cp, 
                                            dde.ciudad, 
                                            dde.provincia, 
                                            dde.pais)
        ciudad_formalizado = dde.ciudad
    except IndexError:
        dde_nombre = ""
        dde_direccion1 = ""
        dde_direccion2 = ""
        ciudad_formalizado = ""
    cliente_nombre = albaran.cliente.nombre
    cliente_direccion1 = albaran.cliente.direccion
    cliente_direccion2 = "%s-%s %s (%s)" % (albaran.cliente.cp, 
                                            albaran.cliente.ciudad, 
                                            albaran.cliente.provincia, 
                                            albaran.cliente.pais)
    entrega1 = albaran.direccion
    entrega2 = "%s %s (%s)" % (albaran.cp, 
                               albaran.ciudad, 
                               albaran.pais)
    if albaran.transportista:
        transportista_nombre = albaran.transportista.agencia
        transportista_direccion1 = "%s %s" % (albaran.transportista.dni, 
                                              albaran.transportista.nombre)
        transportista_direccion2 = "%s %s" % (albaran.transportista.telefono, 
                                              albaran.transportista.matricula)
    else:
        transportista_nombre = transportista_direccion1 \
            = transportista_direccion2 = ""
    observaciones = "Serán por cuenta del remitente los daños ocasionados "\
        "en la mercancía transportada por vicio, defecto o mal "\
        "acondicionamiento de la carga mercancía no preenfriada mal "\
        "congelada, motín, huelga o guerra y multas por exceso de peso."\
        "La estiba la realiza el remitente. El porteador no se hace "\
        "responsable de la falta de bultos o deterioro de la mercancía, si "\
        "la reclamación no viene acompañada de un certificado del Comisario "\
        "de Averías."
    estipulaciones = "La duración de este transporte estará sujeto a las "\
        "normas establecidas en cada país en el acuerdo europeo sobre las "\
        "condiciones de tranajo (A.E.T.R.) La mercancía viaja asegurada "\
        "por el remitente o consignatario, salvo pacto en contrario."
    estipulaciones = ""
    ciudad = albaran.ciudad
    MAX_WIDTH = 18
    if " " in ciudad and ciudad.index(" ") <= MAX_WIDTH:
        while len(ciudad) > MAX_WIDTH:
            ciudad = ciudad[:ciudad.rindex(" ")]
    mes = albaran.fecha.strftime("%d/%m")
    anno = albaran.fecha.strftime("%y")
    # Líneas de venta agrupadas por producto
    ldvs = []
    prods = {}
    for ldv in albaran.lineasDeVenta:
        p = ldv.productoVenta
        if p not in prods:
            prods[p] = [ldv.calcular_bultos(), 
                        ldv.cantidad]
        else:
            prods[p][0] += ldv.calcular_bultos()
            prods[p][1] += ldv.cantidad
    ldvs = []
    for p in prods:
        linea = (str(prods[p][0]),
                 #p.nombre,
                 p.envase and p.envase.nombre or "", 
                 utils.float2str(prods[p][1], autodec = True))
        ldvs.append(linea)
    return go(dde_nombre, dde_direccion1, dde_direccion2, cliente_nombre,
              cliente_direccion1, cliente_direccion2, entrega1, entrega2, 
              transportista_nombre, transportista_direccion1, 
              transportista_direccion2, observaciones, ldvs, estipulaciones, 
              ciudad, mes, anno, solo_texto, porteador, sucesivos, 
              ciudad_formalizado)

def prueba_albaran():
    from informes import abrir_pdf
    abrir_pdf(go_from_albaranSalida(pclases.AlbaranSalida.select()[-1]))
    import time
    time.sleep(1)
    abrir_pdf(go_from_albaranSalida(pclases.AlbaranSalida.select()[-1], True))

if __name__=='__main__':
    prueba_albaran()


