#!/usr/bin/env python
# -*- coding: utf-8 -*-

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


import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.MIMEBase import MIMEBase
from email import Encoders


def enviar_correo(subject, destino, text, pdfs=[]):
    # Datos de cuenta para envío
    usuario_gmail = '' # TODO añadir nombre de usuario aqui
    password = '' # TODO añadir contraseña aqui

    # Correos de remitente y destinatario
    origen = usuario_gmail + '@gmail.com'

    # Creación del mensaje
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = origen
    msg['To'] = destino

    # Contenido del mensaje
    msg.attach(MIMEText(text))

    # Adjuntamos pdfs
    for pdf in pdfs:
        try:
            file = open("factura/" + pdf, "rb")
        except:
            print "Archivo %s no encontrado. " % pdf
            continue
        attach_pdf = MIMEBase('application', 'pdf')
        attach_pdf.set_payload(file.read())
        Encoders.encode_base64(attach_pdf)
        attach_pdf.add_header('Content-Disposition',
                'attachment; filename="%s"' % pdf)
        msg.attach(attach_pdf)

    # Conexión con servidor smtp
    sender = smtplib.SMTP('smtp.gmail.com')
    sender.ehlo()
    sender.starttls()

    # Autenticación
    try:
        sender.login(usuario_gmail, password)
    except smtplib.SMTPAuthenticationError:
        print "Password errónea. "
        return 0

    # # Autenticación
    # enviado = False
    # while not enviado:
    #     pwd = raw_input("Password: ")
    #     try:
    #         sender.login(usuario_gmail, pwd)
    #         enviado = True
    #     except smtplib.SMTPAuthenticationError:
    #         print "Password errónea, inténtelo de nuevo. "
    #         enviado = False

    sender.sendmail(origen, destino, msg.as_string())
    sender.close()
    return 1
