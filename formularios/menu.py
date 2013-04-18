#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2005-2008  Francisco José Rodríguez Bogado,                   #
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


###################################################################
## menu.py - Menú de acceso a módulos y ventanas.
###################################################################
## NOTAS:
##  
###################################################################
## Changelog:
## 27 de abril de 2006 -> Inicio.
## 5 de mayo -> It's alive! Alive! 
## 27 de mayo de 2006 -> Tenemos log.
###################################################################
## NOTAS:
## Si una ventana no pertenece a ningún módulo no aparecerá en los
## permisos ni en el menú. A efectos prácticos, no existirá para 
## los usuarios aunque esté en la BD y tenga relación con alguno 
## a través de la tabla "permisos".
###################################################################
## + Cambiar todos los print "WARNING... " de todos los .py por un 
## mensaje en el LOG.
## - PLAN: Crear una ventana para copias de seguridad.
## - PLAN: Mostrar ventana en tiempo real cuando cambie la salida 
##   del programa (señal de que algo ha pasado, probablemente una 
##   excepción no capturada de la que no se mostrará la ventana 
##   de enviar bugreport hasta cerrar el programa).
###################################################################

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade, gobject

import os, sys, traceback
os.environ['LANG'] = "es_ES"
os.environ['LANGUAGE'] = 'es_ES'
#print os.environ
os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))
#print os.getcwd()
#print os.path.realpath(sys.argv[0])

from formularios import utils
import mx, mx.DateTime
from framework.configuracion import ConfigConexion

_VERSION = '1.9'


class MetaF:
    """
    "Metafichero" para almacenar la salida de errores y poder 
    enviar informes de error.
    """
    def __init__(self):
        self.t = ''
    def write(self, t):
        if ("GtkWarning" not in t and 
            "with become" not in t and 
            "PangoWarning" not in t and 
            "main loop already active" not in t):
            self.t += t
        sys.__stdout__.write(t)
        sys.__stdout__.flush()

    def __repr__(self):
        return self.t

    def __str__(self):
        return self.t

    def __get__(self):
        return self.t

    def vacio(self):
        return len(self.t) == 0


def import_pclases():
    """
    Importa y devuelve el módulo pclases.
    """
    ############################################################
    # Importo pclases. No lo hago directamente en la cabecera 
    # para esperar a ver si se ha pasado al main un fichero de 
    # configuración diferente.
    from framework import pclases
    ############################################################
    return pclases

def apagar_equipo():
    """
    CWT: Apaga el ordenador con el comando de Gnome gnome-power-cmd.
    """
    config = ConfigConexion()
    if config.get_kiosco():
        print "Apagando desde menú de FPINN..."
        # Comentar/descomentar la siguiente línea para pruebas/producción:
        os.system("#gnome-power-cmd.sh shutdown")
        # También puede valer algo como esto:
        # gnome-session-save --kill --gui
        # Si gnome-session no está ejecutado, usar esto, pero antes en sudoers:
        # %users ALL=NOPASSWD: /sbin/halt
        # %wheel ALL=(ALL) SETENV: ALL
        # Si el sistema no usa Gnome, descomentar/comentar la siguiente línea 
        # en pruebas/producción para el apagado del equipo en modo kiosco.
        #os.system("xterm -e sudo halt")
        # PASO chmod +s a halt y shutdown y a puirla:
        os.system("shutdown -h now")

class Menu:
    def __init__(self, user = None, passwd = None):
        """
        user: Usuario. Si es None se solicitará en la ventana de 
        autentificación.
        passwd: Contraseña. Si es None, se solicitaré en la ventana de 
        autentificación.
        Si user y passwd son distintos a None, no se mostrará la ventana de 
        autentificación a no ser que sean incorrectos.
        """
        import gestor_mensajes, autenticacion
        login = autenticacion.Autenticacion(user, passwd)
        pclases = import_pclases()
        if pclases.VERBOSE:
            print "Cargando gestor de mensajes..."
        self.logger = login.logger
        if not login.loginvalido():
            sys.exit(1)
        self.usuario = login.loginvalido()
        self.__gm = gestor_mensajes.GestorMensajes(self.usuario)
        config = ConfigConexion()
        if config.get_kiosco():
            os.system("openbox --replace &")
        self.construir_ventana()
        utils.escribir_barra_estado(self.statusbar, 
                                    "Menú iniciado", 
                                    self.logger, 
                                    self.usuario.usuario)

    def get_usuario(self):
        return self.usuario

    def salir(self, 
              boton, 
              event = None, 
              mostrar_ventana = True, 
              ventana = None):
        """
        Muestra una ventana de confirmación y 
        sale de la ventana cerrando el bucle
        local de gtk_main.
        Si mostrar_ventana es False, sale directamente
        sin preguntar al usuario.
        """
        res = False
        if event == None:
            # Me ha invocado el botón
            if (not mostrar_ventana 
                or utils.dialogo('¿Desea cerrar el menú principal?', 
                                 'SALIR', 
                                 padre = ventana, 
                                 icono = gtk.STOCK_QUIT)):
                if ventana:
                    ventana.destroy()
                else:
                    try:
                        self.ventana.destroy()
                    except:
                        pass
                self.logger.warning("LOGOUT: %s" % (self.usuario.usuario))
                apagar_equipo()
                res = False
            else:
                res = True
        else:
            res = (not mostrar_ventana 
                   or not utils.dialogo('¿Desea cerrar el menú principal?', 
                                        'SALIR', 
                                        padre = ventana, 
                                        icono = gtk.STOCK_QUIT))
            if not res: 
                self.logger.warning("LOGOUT: %s" % (self.usuario.usuario))
                apagar_equipo()
        return res

    def construir_ventana(self):
        self.statusbar = gtk.Statusbar()
        self.ventana = gtk.Window()
        self.ventana.set_position(gtk.WIN_POS_CENTER)
        self.ventana.resize(800, 600)
        self.ventana.set_title('Menú principal')
        ruta_logo = os.path.join("imagenes", 'logo.xpm')
        self.ventana.set_icon(gtk.gdk.pixbuf_new_from_file(ruta_logo))
        self.ventana.set_border_width(10)
        self.ventana.connect("delete_event", self.salir, True, self.ventana)
        self.caja = gtk.VBox()
        self.caja.set_spacing(5)
        self.ventana.add(self.caja)
        self.cabecera = gtk.HBox()
        imagen = gtk.Image()
        config = ConfigConexion()
        pixbuf_logo = gtk.gdk.pixbuf_new_from_file(
            os.path.join('imagenes', config.get_logo()))
        pixbuf_logo = escalar_a(300, 200, pixbuf_logo)
        imagen.set_from_pixbuf(pixbuf_logo)
        self.cabecera.pack_start(imagen, fill=True, expand=False)
        texto = gtk.Label("""
        <big><big><big><b>%s</b></big>        

        <u>Menú de acceso a módulos de la aplicación</u></big>        

        <i>v.%s</i></big>        
        """ % (config.get_title(), _VERSION))
        texto.set_justify(gtk.JUSTIFY_CENTER)
        texto.set_use_markup(True)
        event_box = gtk.EventBox()
            # Porque el gtk.Label no permite cambiar el background.
        event_box.add(texto)
        # CWT: Ahora que le quite el fondo rojo...
        #event_box.modify_bg(gtk.STATE_NORMAL, 
        #                    event_box.get_colormap().alloc_color("#c00000"))
        #texto.modify_fg(gtk.STATE_NORMAL, 
        #                event_box.get_colormap().alloc_color("#ffffff"))
        self.cabecera.pack_start(event_box)
        b_salir = gtk.Button(stock = gtk.STOCK_QUIT)
        b_salir.connect("clicked", lambda boton: self.salir(boton,\
                ventana=self.ventana, mostrar_ventana=True))
        boxsalir = gtk.VBox()
        boxsalir.pack_end(gtk.VBox(), expand = True)
        boxsalir.pack_end(b_salir, expand = False, fill = True)
        boxsalir.pack_end(gtk.VBox(), expand = True)
        self.cabecera.pack_start(boxsalir, fill=False)
        self.caja.pack_start(self.cabecera, fill=True, expand=False)
        self.current_frame = None
        cuerpo_central = self.create_menu()
        self.caja.pack_start(cuerpo_central)
        self.caja.pack_start(self.statusbar, False, True)
        
    def create_menu(self):
        pclases = import_pclases()
        model = gtk.ListStore(str, gtk.gdk.Pixbuf)
        for modulo in [m for m in pclases.Modulo.select(orderBy = "nombre") \
                       if len([p.ventana for p in self.get_usuario().permisos if p.permiso and p.ventana.modulo == m]) > 0]: 
            pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join('imagenes', modulo.icono))
            model.append([modulo.nombre, pixbuf])
        # XXX: Módulo favoritos
        # CWT: No quiere favoritos. :(
        #pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join('imagenes', "favoritos.png"))
        #model.append(("Favoritos", pixbuf))
        # XXX:
        
        contenedor = gtk.ScrolledWindow()
        contenedor.set_property("hscrollbar-policy", gtk.POLICY_AUTOMATIC)
        contenedor.set_property("vscrollbar-policy", gtk.POLICY_AUTOMATIC)
        icon_view = gtk.IconView(model)
        icon_view.set_text_column(0)
        icon_view.set_pixbuf_column(1)
        icon_view.set_orientation(gtk.ORIENTATION_VERTICAL)
        icon_view.set_selection_mode(gtk.SELECTION_SINGLE)
        icon_view.connect('selection-changed', self.on_select, model)
        icon_view.set_columns(1)
        icon_view.set_item_width(110)
        icon_view.set_size_request(150, -1)
        
        contenedor.add(icon_view)
        self.content_box = gtk.HBox(False)
        self.content_box.pack_start(contenedor, fill=True, expand=False)
        icon_view.select_path((0,)) # Al seleccionar una categoría se creará el frame 
        return self.content_box 
 
    def on_select(self, icon_view, model=None):
        pclases = import_pclases()
        selected = icon_view.get_selected_items()
        if len(selected) == 0: return
        i = selected[0][0]
        category = model[i][0]
        if self.current_frame is not None:
            self.content_box.remove(self.current_frame)
            self.current_frame.destroy()
            self.current_frame = None
        if category != "Favoritos":
            modulo = pclases.Modulo.select(
                pclases.Modulo.q.nombre == category)[0]
        else:
            modulo = "Favoritos"
        self.current_frame = self.create_frame(modulo)
        utils.escribir_barra_estado(self.statusbar, category, self.logger, self.usuario.usuario)
        self.content_box.pack_end(self.current_frame, fill=True, expand=True)
        self.ventana.show_all()
        
    def create_frame(self, modulo):
        if modulo != "Favoritos":
            frame = gtk.Frame(modulo.descripcion)
            frame.add(self.construir_modulo(modulo.descripcion, 
                            [p.ventana for p in self.get_usuario().permisos 
                             if p.permiso and p.ventana.modulo == modulo]))
        else:
            frame = gtk.Frame("Ventanas más usadas")
            pclases = import_pclases()
            usuario = self.get_usuario()
            stats = pclases.Estadistica.select(
             pclases.Estadistica.q.usuarioID == usuario.id, orderBy = "-veces")
            # Se filtran las ventanas en las que ya no tiene permisos aunque 
            # estén en favoritos.
            stats = [s for s in stats 
                     if usuario.get_permiso(s.ventana) 
                         and usuario.get_permiso(s.ventana).permiso][:6]
            stats.sort(lambda s1, s2: (s1.ultimaVez > s2.ultimaVez and -1) 
                                      or (s1.ultimaVez < s2.ultimaVez and 1) 
                                      or 0)
            ventanas = [s.ventana for s in stats]
            frame.add(self.construir_modulo("Ventanas más usadas", 
                                            ventanas, 
                                            False))
        return frame        
        
    def cutmaister(self, texto, MAX = 20):
        """
        Si el texto tiene una longitud superior a 20 caracteres de ancho lo
        corta en varias líneas.
        """
        if len(texto) > MAX:
            palabras = texto.split(' ')
            t = ''
            l = ''
            for p in palabras:
                if len(l) + len(p) + 1 < MAX:
                    l += "%s " % p
                else:
                    t += "%s\n" % l
                    l = "%s " % p
                if len(l) > MAX:    # Se ha colado una palabra de más del MAX
                    tmp = l
                    while len(tmp) > MAX:
                        t += "%s-\n" % tmp[:MAX]
                        tmp = tmp[MAX:]
                    l = tmp
                # print t.replace("\n", "|"), "--", l, "--", p
            t += l
            res = t
        else:
            res = texto
        res = "\n".join([s.center(MAX) for s in res.split("\n")])
        return res
    
    def construir_modulo(self, nombre, ventanas, ordenar = True):
        """
        Crea un IconView con las
        ventanas que contiene el módulo.
        Recibe una lista de objetos ventana de pclases.
        Si «ordenar» es False usa el orden de la lista de ventanas 
        recibidas. En otro caso las organiza por orden alfabético.
        """
        model = gtk.ListStore(str, gtk.gdk.Pixbuf, str, str)
        # ventanas.sort(key=lambda v: v.descripcion)
        # En Python2.3 parece ser que no estaba la opción de especificar 
        # la clave de ordenación.
        if ordenar:
            ventanas.sort(lambda s1, s2: (s1.descripcion>s2.descripcion and 1) or \
                                         (s1.descripcion<s2.descripcion and -1) or 0)
        for ventana in ventanas:
            try:
                pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join('imagenes', ventana.icono))
            except (gobject.GError, AttributeError, TypeError):  # Icono es "" o None (NULL en la tabla).
                pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join('imagenes', 'dorsia.png'))
            model.append((self.cutmaister(ventana.descripcion), pixbuf, ventana.fichero, ventana.clase))
            # El model tiene: nombre (descripción), icono, archivo, clase, descripción detallada (hint)
            # NOTA: No se pueden mostrar hints en el IconView (al menos yo no sé cómo), así que ahora 
            #       lo que tiene es el icono.
        contenedor = gtk.ScrolledWindow()
        contenedor.set_property("hscrollbar-policy", gtk.POLICY_AUTOMATIC)
        contenedor.set_property("vscrollbar-policy", gtk.POLICY_AUTOMATIC)
        iview = gtk.IconView(model)
        iview.set_text_column(0)
        iview.set_pixbuf_column(1)
        iview.set_item_width(180)
        iview.connect('item-activated', self.abrir, model)
        iview.connect('selection-changed', self.mostrar_item_seleccionado, model)
        contenedor.add(iview)
        return contenedor

    def mostrar_item_seleccionado(self, icon_view, model):
        selected = icon_view.get_selected_items()
        if len(selected) == 0: return
        i = selected[0][0]
        descripcion_icono_seleccionado = model[i][0]
        descripcion_icono_seleccionado = descripcion_icono_seleccionado.replace('\n', ' ')
        utils.escribir_barra_estado(self.statusbar, descripcion_icono_seleccionado, self.logger, self.usuario.usuario)

    def volver_a_cursor_original(self):
        # print "Patrick Bateman sabe que es una chapuza y que no hay que hacer suposiciones de tiempo."
        self.ventana.window.set_cursor(None)
        return False

    def abrir(self, iview, path, model):
        clase = model[path][3]
        archivo = model[path][2]
        pclases = import_pclases()
        pclases.Estadistica.incrementar(self.usuario, archivo)
        if archivo.endswith('.py'):    
            # Al importar no hay que indicar extensión
            archivo = archivo[:archivo.rfind('.py')]
        if clase == 'acerca_de' and archivo == 'acerca_de':
            utils.escribir_barra_estado(self.statusbar, 'Abrir: "acerca de..."', self.logger, self.usuario.usuario)
            self.acerca_de()
        elif clase == "web":
            utils.escribir_barra_estado(self.statusbar, "Abrir navegador web", 
                                        self.logger, 
                                        self.usuario.usuario)
            # TODO: Mirar si hay alguna instancia ejecutándose y matarla, que 
            # el usuario es propenso a cambiar de ventana sin querer, y como 
            # esté en modo kiosco no hay manera de devolver el foco con el 
            # ratón al que ya está abierto.
            os.system(archivo + " &")
        elif clase == "extapp": # Aplicación externa
            utils.escribir_barra_estado(self.statusbar, "Abrir %s" % archivo, 
                                        self.logger, 
                                        self.usuario.usuario)
            os.system(archivo + " &")
        elif 'usuario' in archivo:
            self.ventana.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
            utils.escribir_barra_estado(self.statusbar, "Cargar: %s.py" % archivo, self.logger, self.usuario.usuario)
            exec "import %s" % archivo
            v = None 
            gobject.timeout_add(100, self.volver_a_cursor_original)
            if archivo == "usuarios": 
                v = usuarios.Usuarios(self.get_usuario())
            elif archivo == "ventana_usuario":
                v = ventana_usuario.Usuarios(self.get_usuario())
        else:
            try:
                self.ventana.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
                utils.escribir_barra_estado(self.statusbar, "Cargar: %s.py" % archivo, self.logger, self.usuario.usuario)
                while gtk.events_pending(): gtk.main_iteration(False)
                try:
                    exec "reload(%s)" % archivo
                    # PLAN: Esto no funciona como esperaba debido a que aunque 
                    # se cierre la ventana, hay referncias por ahí rulando y 
                    # el reload no recompila y vuelve a cargar el módulo.
                    # Ver: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/160164 o 
                    # http://aspn.activestate.com/ASPN/Mail/Message/python-list/907876 
                    # y usar cuando lo tenga suficientemente testeado.
                except NameError:
                    exec "import %s" % archivo
                # HACK: Debe haber una forma mejor de hacerlo. De momento me 
                #       aprovecho de que el mainloop no va a atender al 
                #       timeout aunque se cumpla el tiempo, ya que está 
                #       ocupado en abrir la ventana, con lo que el cursor sale 
                #       del "busy" justo cuando debe, al abrirse la ventana.
                v = None 
                gobject.timeout_add(100, self.volver_a_cursor_original)
                v = eval('%s.%s' % (archivo, clase))
                v(usuario = self.get_usuario())
                # Podría incluso guardar los objetos ventana que se van 
                # abriendo para controlar... no sé, algo, contar las ventanas 
                # abiertas o algo.
            except:
                self.ventana.window.set_cursor(None)
                utils.escribir_barra_estado(self.statusbar, "Error detectado. Iniciando informe por correo.", self.logger, self.usuario.usuario)
                print "Se ha detectado un error"
                texto = ''
                for e in sys.exc_info():
                    texto += "%s\n" % e
                tb = sys.exc_info()[2]
                texto += "Línea %s\n" % tb.tb_lineno
                info = MetaF() 
                traceback.print_tb(tb, file = info)
                texto += "%s\n" % info
                enviar_correo(texto, self.get_usuario())

    def mostrar(self):
        self.ventana.show_all()
        self.ventana.connect('destroy', gtk.main_quit)
        config = ConfigConexion()
        if config.get_kiosco():
            self.ventana.fullscreen()
        gtk.main()

    def launch_browser_mailer(self, dialogo, uri, tipo):
        # FIXME: De momento sólo funciona para NT-compatibles. Usar el 
        # nuevo multi_open.
        if tipo == 'email':
            if os.name == 'nt':
                try:
                    os.startfile('mailto:%s' % uri) # if pywin32 is installed we open
                except:
                    pass
            else:
                utils.dialogo_info('NO IMPLEMENTADO', 
                                   'Funcionalidad no implementada.\nDebe lanzar manualmente su cliente de correo.\nCorreo-e seleccionado: %s' % uri,
                                   padre = self.ventana)
        elif tipo == 'web':
            if os.name == 'nt':
                try:
                    os.startfile(uri)
                except:
                    pass
            else:
                utils.dialogo_info('NO IMPLEMENTADO', 
                                   'Funcionalidad no implementada.\nDebe lanzar manualmente su navegador web.\nURL seleccionada: %s' % uri, 
                                   self.ventana)

    def acerca_de(self):
        gtk.about_dialog_set_email_hook(self.launch_browser_mailer, 'email')
        gtk.about_dialog_set_url_hook(self.launch_browser_mailer, 'web')
        vacerca = gtk.AboutDialog()
        vacerca.set_name('FP-INN')
        vacerca.set_version(_VERSION)
        vacerca.set_comments('Software de gestión para FresParaíso')
        vacerca.set_authors(['Francisco José Rodríguez Bogado <rodriguez.bogado@gmail.com>', 'Diego Muñoz Escalante <escalant3@gmail.com>'])
        config = ConfigConexion()
        logo = gtk.gdk.pixbuf_new_from_file(os.path.join('imagenes', config.get_logo()))
        vacerca.set_logo(logo)
        vacerca.set_license(open(os.path.join('gpl.txt')).read())
        vacerca.set_website('http://fpinn.sf.net')
        vacerca.set_artists(['Iconos gartoon por Kuswanto (a.k.a. Zeus) <zeussama@gmail.com>'])
        vacerca.set_copyright('Copyright 2005-2008  Francisco José Rodríguez Bogado.')
        vacerca.run()
        vacerca.destroy()


def construir_y_enviar(w, ventana, remitente, observaciones, texto, usuario):
    import ventana_progreso, sys, os
    try:
        import libgmail
    except:
        sys.path.insert(0, os.path.join('libgmail-0.1.3.3'))
        import libgmail
    rte = remitente.get_text()
    buffer = observaciones.get_buffer()
    obs = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter()) 
    if usuario == None:
        contra = ''
    else:
        contra = usuario.cpass
    pwd = utils.dialogo_entrada(titulo = 'CONTRASEÑA', texto = """ 
    Introduzca la contraseña de su cuenta de correo en gmail.       
    No se almacenará.
    
    """, pwd = True, valor_por_defecto = contra)
    if pwd != None and pwd != "":
        vpro = ventana_progreso.VentanaProgreso()
        vpro.tiempo = 25
        vpro.mostrar()
        vpro.set_valor(0.0, "Intentando login en %s..." % rte)
        import time 
        for nada in xrange(50):
            vpro.set_valor(nada/100.0, "Intentando login en %s..." % rte)
            time.sleep(0.05)     # Es que si no no da tiempo a ver el mensajito.
        con = libgmail.GmailAccount(rte, pwd)
        try:
            con.login()
        except:
            utils.dialogo_info(titulo = "ERROR",
                               texto = "Login erróneo. No se introdujo una cuenta de gmail o contraseña válida.\n\nVuelva a intentarlo.")
            guardar_error_a_disco(rte, obs, texto)
            vpro.ocultar()
            return
        texto = "OBSERVACIONES: " + obs + "\n\n\n" + texto 
        tos = ('rodriguez.bogado@gmail.com', )
        i = 0
        for to in tos:
            vpro.set_valor((i/len(tos)*0.5) + 0.5, "Enviando a %s..." % to)
            msg = libgmail.GmailComposedMessage(to, "ERROR GINN. Capturada excepción no contemplada.", texto)
            try:
                con.sendMessage(msg)
            except Exception, msg:
                utils.dialogo_info(titulo = "ERROR",
                                   texto = "Ocurrió un error al enviar el correo electrónico.\n\n\n%s" % msg)
                guardar_error_a_disco(rte, obs, texto)
                vpro.ocultar()
                return
        vpro.ocultar()
        utils.dialogo_info(titulo = 'CORREO ENVIADO', texto = 'Informe de error enviado por correo electrónico.')
        ventana.destroy()

def mostrar_dialogo_y_guardar(txt):
    dialog = gtk.FileChooserDialog("GUARDAR TRAZA/DEBUG",
                                   None,
                                   gtk.FILE_CHOOSER_ACTION_SAVE,
                                   (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                    gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))
    dialog.set_default_response(gtk.RESPONSE_OK)
    try:
        home = os.environ['HOME']
    except KeyError:
        try:
            home = os.environ['HOMEPATH']
        except KeyError:
            home = "."
            print "WARNING: No se pudo obtener el «home» del usuario"
    if os.path.exists(os.path.join(home, 'tmp')):
        dialog.set_current_folder(os.path.join(home, 'tmp'))
    else:
        dialog.set_current_folder(home)
    filter = gtk.FileFilter()
    filter.set_name("Archivos de traza-depuración texto plano ginn")
    filter.add_pattern("*.qdg")
    filter.add_pattern("*.QDG")
    filter.add_pattern("*.Qdg")

    dialog.add_filter(filter)
    filter = gtk.FileFilter()
    filter.set_name("Todos")
    filter.add_pattern("*")
    dialog.add_filter(filter)

    dialog.set_current_name("%s.qdg" % (mx.DateTime.localtime().strftime("%d_%m_%Y")))

    if dialog.run() == gtk.RESPONSE_ACCEPT:
        nomarchivo = dialog.get_filename()
        try:
            if nomarchivo[:nomarchivo.rindex(".")] not in ("qdg", "QDG", "Qdg"):
                nomarchivo = nomarchivo + ".qdg"
        except:
            nomarchivo = nomarchivo + ".qdg"
        save_to_file(nomarchivo, txt)
    dialog.destroy()

def save_to_file(nombre, texto):
    """
    Abre el archivo "nombre" y guarda el texto en él. Si ya existe, lo añade.
    """
    try:
        f = open(nombre, 'a')
        f.write(texto)
        f.close()
        utils.dialogo_info(titulo = "TRAZA GUARDADA",
            texto = "La información de depuración se ha guardado correctament"\
                    "e en %s.\nCierre la ventana y reinicie el programa compl"\
                    "eto." % (nombre))
    except IOError:
        utils.dialogo_info(titulo = "NO TIENE PERMISO", 
            texto = "No tiene permiso para guardar el archivo. Pruebe en otro"\
                    " directorio.")

def guardar_error_a_disco(remitente, observaciones, texto):
    """
    Pregunta si guardar el error en disco como archivo de texto.
    """
    if utils.dialogo(titulo = "¿GUARDAR A DISCO?",
        texto = "Si no puede enviar el informe de error o no tiene conexión a"\
                " internet\npuede guardar la información en un fichero de tex"\
                "to para que sea revisada más tarde.\n\n¿Quiere guardar la tr"\
                "aza de depuración en disco ahora?"):
        txt = "REMITENTE: %s\n\nOBSERVACIONES: %s\n\nTEXTO: \n%s\n" % (
            remitente, observaciones, texto)
        mostrar_dialogo_y_guardar(txt)
 
def crear_ventana(titulo, texto, usuario):
    # PLAN: ¿Meto un "recordar contraseña"?
    ventana = gtk.Window()
    ventana.set_title(titulo)
    ventana.set_modal(True)
    ventana.set_position(gtk.WIN_POS_CENTER_ALWAYS)
    tabla = gtk.Table(5, 2)
    imagen = gtk.Image()
    imagen.set_from_file(os.path.join('imagenes', 'emblem-mail.png'))
    info = gtk.Label('Se produjo un error mientras usaba la aplicación\nEs recomendable enviar un informe a los desarrolladores.\nDebe contar con una cuenta de correo gmail para poder hacerlo.')
    tabla.attach(imagen, 0, 1, 0, 1, xpadding = 5, ypadding = 5)
    tabla.attach(info, 1, 2, 0, 1, xpadding = 5, ypadding = 5)
    tabla.attach(gtk.Label('cuenta Gmail: '), 0, 1, 1, 2, xpadding = 5, ypadding = 5)
    remitente = gtk.Entry()
    if usuario != None:
        remitente.set_text(usuario.cuenta)
    tabla.attach(remitente, 1, 2, 1, 2, xpadding = 5, ypadding = 5)
    tabla.attach(gtk.Label('Observaciones: '), 0, 1, 2, 3, xpadding = 5, ypadding = 5)
    observaciones = gtk.TextView()
    tabla.attach(observaciones, 1, 2, 2, 3, xpadding = 5, ypadding = 5)
    tabla.attach(gtk.Label('Error capturado: '), 0, 1, 4, 5, xpadding = 5, ypadding = 5)
    tabla.attach(gtk.Label(texto), 1, 2, 4, 5, xpadding = 5, ypadding = 5)
    boton = gtk.Button(stock = gtk.STOCK_OK)
    tabla.attach(boton, 1, 2, 3, 4, xpadding = 5, ypadding = 5)
    ventana.add(tabla)
    ventana.show_all()
    return ventana, boton, remitente, observaciones


def enviar_correo(texto, usuario = None):
    import os
    ventana, boton, remitente, observaciones = crear_ventana('ENVIAR INFORME DE ERROR', texto, usuario)
    ventana.connect('destroy', gtk.main_quit)
    boton.connect('clicked', construir_y_enviar, ventana, remitente, observaciones, texto, usuario)
    gtk.main()

def escalar_a(ancho, alto, pixbuf):
    """
    Devuelve un pixbuf escalado en proporción para que como máximo tenga 
    de ancho y alto las medidas recibidas.
    """
    if pixbuf.get_width() > ancho:
        nuevo_ancho = ancho
        nuevo_alto = int(pixbuf.get_height() 
                         * ((1.0 * ancho) / pixbuf.get_width()))
        colorspace = pixbuf.get_property("colorspace")
        has_alpha = pixbuf.get_property("has_alpha")
        bits_per_sample = pixbuf.get_property("bits_per_sample")
        pixbuf2 = gtk.gdk.Pixbuf(colorspace, 
                                 has_alpha, 
                                 bits_per_sample, 
                                 nuevo_ancho, 
                                 nuevo_alto)
        pixbuf.scale(pixbuf2, 
                     0, 0, 
                     nuevo_ancho, nuevo_alto, 
                     0, 0,
                     (1.0 * nuevo_ancho) / pixbuf.get_width(), 
                     (1.0 * nuevo_alto) / pixbuf.get_height(), 
                     gtk.gdk.INTERP_BILINEAR)
        pixbuf = pixbuf2
    if pixbuf.get_height() > alto:
        nuevo_alto = alto
        nuevo_ancho = int(pixbuf.get_width() 
                          * ((1.0 * alto) / pixbuf.get_height()))
        colorspace = pixbuf.get_property("colorspace")
        has_alpha = pixbuf.get_property("has_alpha")
        bits_per_sample = pixbuf.get_property("bits_per_sample")
        pixbuf2 = gtk.gdk.Pixbuf(colorspace, 
                                 has_alpha, 
                                 bits_per_sample, 
                                 nuevo_ancho, 
                                 nuevo_alto)
        pixbuf.scale(pixbuf2, 
                     0, 0, 
                     nuevo_ancho, nuevo_alto, 
                     0, 0,
                     (1.0 * nuevo_ancho) / pixbuf.get_width(), 
                     (1.0 * nuevo_alto) / pixbuf.get_height(), 
                     gtk.gdk.INTERP_BILINEAR)
        pixbuf = pixbuf2
    return pixbuf
