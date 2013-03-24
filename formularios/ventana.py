#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2005-2008  Francisco José Rodríguez Bogado,                   #
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


###################################################################
## ventana.py - Clase base para todas las ventanas. 
###################################################################
## 
###################################################################
import pygtk
#pygtk.require('2.0')
import gtk, gtk.glade, gobject, utils, pango
import sys, os
sys.path.insert(0, os.path.join('..', 'SQLObject', 'SQLObject-0.6.1'))
import sqlobject
from widgets import Widgets

path_framework = os.path.join("..", "framework")
if path_framework not in sys.path:
    sys.path.append(path_framework)
from configuracion import ConfigConexion
import pclases

def refrescar_cache_sqlobject():
    """
    Recorre toda la lista de objetos en memoria y sincroniza 
    los que sean del módulo "pclases" con su correspondiente 
    en la base de datos.
    """
    import gc
    # XXX
    # import time
    # t1 = time.time()
    # oks = 0
    # XXX
    for objeto in gc.get_objects():
        if (hasattr(objeto, "__module__") and objeto.__module__ == "pclases" 
            and hasattr(objeto, "sync")):
            try:
                objeto.sync()
                # oks += 1
            except Exception, e:
                # print "Objeto %s no se pudo actualizar:\n%s" % (objeto, e)
                # raise e
                pass
    # XXX
    # print "%d objetos actualizados con éxito. Tiempo: " % (oks), time.time() - t1


class Ventana:
    def __init__(self, glade, objeto = None, usuario = None):
        """
        Constructor.
        glade es una cadena con el nombre del fichero .glade a cargar.
        objeto es el objeto principal de la ventana.
        Si usuario se recibe, se guarda en un atributo privado de la 
        clase que servirá únicamente para crear un menú superior en 
        la ventana con las opciones de menú disponibles para el usuario.
        Si el usuario es None, no se crea ningún menú.
        """
        if isinstance(usuario, int):
            usuario = pclases.Usuario.get(usuario)
        self.__usuario = usuario
        self._is_fullscreen = False
        import logging
        self.logger = logging.getLogger('GINN')
        hdlr = logging.FileHandler('ginn.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        # self.logger.setLevel(logging.INFO)
        self.wids = Widgets(glade)
        self.handlers_id = dict([(w, {}) for w in self.wids.keys()])
        for w in self.wids.keys():
            if isinstance(self.wids[w], gtk.Entry):
                h_id = self.wids[w].connect("activate", self.refocus_entry)
                try:
                    self.handlers_id[w]["activate"].append(h_id)
                except KeyError:
                    self.handlers_id[w]["activate"] = [h_id]
        config = ConfigConexion()
        try:
            self.wids['ventana'].set_border_width(5)
            # TODO:Cambiar por uno correspondiente al logo de la configuración. 
            logo_xpm = gtk.gdk.pixbuf_new_from_file('logo_w.xpm')
            self.wids['ventana'].set_icon(logo_xpm)
            self.wids['barra_estado'] = gtk.Statusbar()
            label_statusbar = self.wids['barra_estado'].get_children()[0].child
            font = pango.FontDescription("Monospace oblique 7")
            label_statusbar.modify_font(font)
            label_statusbar.modify_fg(gtk.STATE_NORMAL, 
                label_statusbar.get_colormap().alloc_color("darkgray"))
            contenido_anterior = self.wids['ventana'].get_child()
            self.wids['ventana'].remove(contenido_anterior)
            self.wids['contenedor_exterior'] = gtk.VBox()
            self.wids['ventana'].add(self.wids['contenedor_exterior'])
            self.wids['menu_superior'] = self.build_menu_superior()
            self.wids['contenedor_exterior'].pack_start(
                self.wids['menu_superior'], False)
            self.wids['contenedor_exterior'].add(contenido_anterior)
            self.wids['contenedor_exterior'].pack_end(
                self.wids['barra_estado'], False)
            self.wids['contenedor_exterior'].show()
            self.wids['barra_estado'].show()
            info_conexion = "%s://%s:xxxxxxxx@%s:%s/%s" % (config.get_tipobd(), 
                                                           config.get_user(), 
                                                           config.get_host(), 
                                                           config.get_puerto(), 
                                                           config.get_dbname())
            info_usuario = ""
            if hasattr(self, "usuario") and self.usuario != None:
                info_usuario = " usuario: %s." % (self.usuario.usuario)
            if self.__usuario != None:
                info_usuario = " __usuario: %s." % (self.__usuario.usuario)
            utils.escribir_barra_estado(self.wids['barra_estado'], "Conectado a %s.%s" % (info_conexion, info_usuario))
        except Exception, msg:
            txt = "ventana.py::__init__ -> No se pudo establecer ancho de borde, icono de ventana o barra de estado. Excepción: %s." % (msg)
            self.logger.warning(txt)
        self.objeto = objeto
        self.make_connections()
        self.make_funciones_ociosas()
        try:
            if "tpv.glade" in glade:
                tecla_fullscreen = "F10"
                # Es la de abrir el cajón en el TPV, grrrr...
                # Lo suyo sería mirar en los accelerators si ya está pillado
                # el F11, pero no sé cómo hacerlo si lo ha hecho libglade por 
                # mí y no manualmente con add_accelerator*
            else:
                tecla_fullscreen = "F11"
            def view_key_press(widget, event):
                if event.keyval == gtk.gdk.keyval_from_name("F5"):
                    if event.state == gtk.gdk.SHIFT_MASK:
                        refrescar_cache_sqlobject()
                    # print "Shift+F5"
                    self.actualizar_objeto_y_enlaces()
                    try:
                        self.actualizar_ventana()
                    except AttributeError:
                        # No tiene actualizar_ventana
                        pass
                elif event.keyval == gtk.gdk.keyval_from_name('q') \
                        and event.state & gtk.gdk.CONTROL_MASK \
                        and event.state & gtk.gdk.MOD1_MASK:
                    # print "CONTROL+ALT+q"
                    import trazabilidad
                    t = trazabilidad.Trazabilidad(self.objeto, ventana_padre = self)
                elif event.keyval == gtk.gdk.keyval_from_name(tecla_fullscreen):
                    self._full_unfull()
                else:
                    # DONE: Aquí debería hacer algo para propagar el evento, 
                    #       porque si no la barra de menú superior no 
                    #       es capaz de interceptar el Ctrl+Q que lanzaría 
                    #       el "Cerrar ventana".
                    #       Ya se propaga, el motivo de por qué no funciona 
                    #       el Ctrl+Q no es no propagar el evento.
                    #widget.propagate_key_event(event)
                    #print event.keyval, event.state, event.string
                    pass
            h_id=self.wids['ventana'].connect("key_press_event",view_key_press)
            try:
                self.handlers_id['ventana']["key_press_event"].append(h_id)
            except KeyError:
                self.handlers_id['ventana']["key_press_event"] = [h_id]
        except Exception, msg:
            txtexcp = "ventana.py::__init__ -> Mnemonics no añadidos. %s"%msg
            print txtexcp
            self.logger.warning(txtexcp)
        if config.get_kiosco():
            self._full_unfull()
        # CWT: Todos los fondos rojos. Mmmppfffff...
        #gtk.rc_parse_string("""
        #    style 'rojo' { bg[NORMAL] = '#c00000'} 
        #    class '*' style 'rojo'
        #""")
        # CWT: Por fin entró en razón y me pide que lo quite.

    def _full_unfull(self):
        """
        Si la ventana está en estado normal, la pone a pantalla completa.
        Si está ya a pantalla completa, la restaura.
        """
        try:
            if self._is_fullscreen:
                self.wids['ventana'].unfullscreen()
            else:
                self.wids['ventana'].fullscreen()
            self._is_fullscreen = not self._is_fullscreen
        except (KeyError, AttributeError):
            pass    # No hay ventana, no se llama así o no es un gtk.Window.

    def __add_ventanas(self, modulo):
        """
        Devuelve una cadena con la estructura XML uimanager 
        correspondiente a las vetnanas del módulo a las que tiene
        acceso el usuario.
        PRECONDICION: self.__usuario debe ser un objeto usuario.
        """
        res = ""
        ventanas = [p.ventana for p in self.__usuario.permisos if p.permiso and p.ventana.modulo == modulo]
        ventanas.sort(lambda s1, s2: (s1.descripcion>s2.descripcion and 1) or (s1.descripcion<s2.descripcion and -1) or 0)
        for ventana in ventanas:
            res += """<menuitem name="%s" action="V%d"/>""" % (ventana.descripcion, ventana.id)
        return res

    def __add_modulos(self):
        """
        Devuelve una cadena con la estructura XML uimanager 
        correspondiente a los módulos del usuario.
        PRECONDICION: self.__usuario debe ser un objeto usuario.
        """
        res = ""
        import pclases
        for modulo in [m for m in pclases.Modulo.select(orderBy = "nombre") \
                       if len([p.ventana for p in self.__usuario.permisos if p.permiso and p.ventana.modulo == m]) > 0]: 
            res += """<menu name="%s" action="M%d">""" % (modulo.nombre, modulo.id)
            res += self.__add_ventanas(modulo)
            res += """</menu>"""
        res += """<menu action="Salir"> <menuitem action="Cerrarventana"/> <menuitem action="Cerrartodo"/> </menu>"""
        return res

    def refocus_entry(self, widget, *args):
        """
        Si hay botón guardar, guarda.
        Pasa el foco al siguiente widget.
        Usar solo como callback de la señal "activate" de los Entry, que se 
        dispara al pulsar Enter o programáticamente con .activate().
        """
        if ("b_guardar" in self.wids.keys() 
           and self.wids['b_guardar'].get_property("sensitive")):
            try:
                self.wids['b_guardar'].clicked()
            except AttributeError:
                self.wids['b_guardar'].emit("clicked")
        elif ("guardar" in self.wids.keys()
              and self.wids['guardar'].get_property("sensitive")):
            try:
                self.wids['guardar'].clicked()
            except AttributeError:
                self.wids['guardar'].emit("clicked")
        widget.get_toplevel().child_focus(gtk.DIR_TAB_FORWARD)

    def build_menu_superior(self):
        """
        Construye un menú con las mismas opciones que el menú principal.
        """
        if self.__usuario != None:
            ui = """<ui>
                        <menubar name="MenuSuperior">
                 """
            ui += self.__add_modulos() 
            ui += """   </menubar>
                    </ui>
                  """
            uimanager = gtk.UIManager()
            accelgroup = uimanager.get_accel_group()
            self.wids['ventana'].add_accel_group(accelgroup)
            actiongroup = gtk.ActionGroup("UIManagerMenuSuperior")
            acciones = self.__build_acciones()
            actiongroup.add_actions(acciones)
            actiongroup.get_action("Cerrartodo").set_property("sensitive", 
                                                              False)
            uimanager.insert_action_group(actiongroup, 0)
            uimanager.add_ui_from_string(ui)
            menu = uimanager.get_widget("/MenuSuperior")
            menu.show()
        else:
            menu = gtk.Label("The kids are alright")
        return menu 

    def __build_acciones(self):
        """
        Construye una lista de acciones de menú compatible 
        con UIManager.
        """
        import pclases
        acciones = []
        for modulo in [m for m in pclases.Modulo.select(orderBy = "nombre") 
                       if len([p.ventana 
                               for p in self.__usuario.permisos if p.permiso 
                                        and p.ventana.modulo == m]) > 0]: 
            acciones.append(("M%d"%(modulo.id), None, "_%s" % (modulo.nombre)))
            ventanas = [p.ventana for p in self.__usuario.permisos 
                        if p.permiso and p.ventana.modulo == modulo]
            ventanas = utils.unificar(ventanas)
            for ventana in ventanas:
                pixbuf = None   # Tiene que ser un gtk_stock por fuerza, 
                                # no admite pixbufs
                acciones.append(("V%d" % (ventana.id), 
                                 pixbuf, 
                                 "_%s" % (ventana.descripcion), 
                                 None, 
                                 None, 
                                 self._abrir))
        # Acciones especiales:
        acciones.append(("Salir", gtk.STOCK_QUIT, "_Salir"))
        acciones.append(("Cerrarventana", None, "_Cerrar ventana", "<Control>q", "Cierra la ventana actual.", self._cerrar_ventana))
        acciones.append(("Cerrartodo", None, "_Cerrar todo", None, "Cierra todas las ventanas abiertas.", self._cerrar_todo))
        return acciones

    def _cerrar_ventana(self, b):
        """
        Cierra la ventana actual.
        """
        self.salir(None)
    
    def _cerrar_todo(self, b):
        """
        Cierra todas las ventanas abiertas. 
        """
        # TODO
        print "Cerrar todo."

    def _abrir(self, action):
        """
        Abre la ventana de la entrada de menú recibida.
        """
        import pclases, utils
        idventana = int(action.get_name().replace("V", ""))
        ventana = pclases.Ventana.get(idventana)
        clase = ventana.clase
        archivo = ventana.fichero
        if archivo.endswith('.py'):    
            # Al importar no hay que indicar extensión
            archivo = archivo[:archivo.rfind('.py')]
        if clase == 'gajim' and archivo == 'gajim':
            utils.escribir_barra_estado(self.wids['barra_estado'], "Iniciar: gajim...", self.logger, self.__usuario.usuario)
            self.abrir_gajim()
        elif clase == 'acerca_de' and archivo == 'acerca_de':
            utils.escribir_barra_estado(self.wids['barra_estado'], 'Abrir: "acerca de..."', self.logger, self.__usuario.usuario)
            self.acerca_de()
        elif 'usuario' in archivo:
            self.wids['ventana'].window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
            utils.escribir_barra_estado(self.wids['barra_estado'], "Cargar: %s.py" % archivo, self.logger, self.__usuario.usuario)
            exec "import %s" % archivo
            v = None 
            gobject.timeout_add(100, self.volver_a_cursor_original)
            if archivo == "usuarios": 
                v = usuarios.Usuarios(self.__usuario)
            elif archivo == "ventana_usuario":
                v = ventana_usuario.Usuarios(self.__usuario)
        else:
            try:
                self.wids['ventana'].window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
                utils.escribir_barra_estado(self.wids['barra_estado'], "Cargar: %s.py" % archivo, self.logger, self.__usuario.usuario)
                while gtk.events_pending(): gtk.main_iteration(False)
                try:
                    exec "reload(%s)" % archivo
                except NameError:
                    exec "import %s" % archivo
                v = None 
                gobject.timeout_add(100, self.volver_a_cursor_original)
                # Solo se permite una instancia de cada tipo de ventana. It's not a bug. It's a feature! (sí, ya :P)
                v = eval('%s.%s' % (archivo, clase))
                v(usuario = self.__usuario)
            except Exception, msg:
                self.logger.error("ventana.py::_abrir -> Excepción importando fichero ventana: %s" % msg)
                self.wids['ventana'].window.set_cursor(None)
                utils.escribir_barra_estado(self.wids['barra_estado'], "Error detectado. Iniciando informe por correo.", self.logger, self.__usuario.usuario)
                print "Se ha detectado un error"
                texto = ''
                for e in sys.exc_info():
                    texto += "%s\n" % e
                tb = sys.exc_info()[2]
                texto += "Línea %s\n" % tb.tb_lineno
                from menu import Metaf, enviar_correo
                info = Metaf() 
                import traceback
                traceback.print_tb(tb, file = info)
                texto += "%s\n" % info
                enviar_correo(texto, self.__usuario)

    def volver_a_cursor_original(self):
        """
        Calcado de menu.py. Sólo lleva las modificaciones necesarias para hacerlo funcionar desde aquí.
        """
        self.wids['ventana'].window.set_cursor(None)
        return False
    
    def abrir_gajim(self):
        """
        Calcado de menu.py. Sólo lleva las modificaciones necesarias para hacerlo funcionar desde aquí.
        """
        try:
            pwd = os.path.abspath(os.curdir)
            os.chdir(os.path.join('..', 'gajim-0.9.1', 'src'))
            sys.path.append('.')
            if os.name == 'posix':
                os.system("cd .. && ./launch.sh >/dev/null &")
            elif os.name == 'nt':
                os.startfile("gajim.pyw")
            else:
                utils.dialogo_info(titulo = "PLATAFORMA NO SOPORTADA",
                                   texto = "La ayuda on-line solo funciona en arquitecturas con plataformas POSIX o NT\n(GNU/Linux, MS-Windows, *BSD...).",
                                   padre = self.wids['ventana'])
        except:
            print "Se ha detectado un error. Volviendo a %s." % (pwd)
            if '.' in sys.path:
                sys.path.remove('.')
            os.chdir(pwd)
            texto = ''
            for e in sys.exc_info():
                texto += "%s\n" % e
            tb = sys.exc_info()[2]
            texto += "Línea %s\n" % tb.tb_lineno
            from menu import Metaf, enviar_correo
            info = Metaf() 
            import traceback
            traceback.print_tb(tb, file = info)
            texto += "%s\n" % info
            enviar_correo(texto, self.__usuario)
        else:
            if '.' in sys.path:
                sys.path.remove('.')
            os.chdir(pwd)
    
    def acerca_de(self):
        """
        Calcado de menu.py. Modificado ligeramente para hacerlo funcionar aquí.
        """
        vacerca = gtk.AboutDialog()
        vacerca.set_name('FP-INN')
        from menu import _VERSION
        vacerca.set_version(_VERSION)
        vacerca.set_comments('Software ERP para FresParaíso')
        vacerca.set_authors(['Francisco José Rodríguez Bogado <rodriguez.bogado@gmail.com>', 'Diego Muñoz Escalante <escalant3@gmail.com>'])
        logo = gtk.gdk.pixbuf_new_from_file(os.path.join('..', 'imagenes', 'logo.jpg'))
        vacerca.set_logo(logo)
        vacerca.set_license(open(os.path.join('..', 'gpl.txt')).read())
        vacerca.set_website('http://fpinn.sf.net')
        vacerca.set_artists(['Iconos gartoon por Kuswanto (a.k.a. Zeus) <zeussama@gmail.com>'])
        vacerca.set_copyright('Copyright 2005-2008  Francisco José Rodríguez Bogado.')
        vacerca.run()
        vacerca.destroy()

    def actualizar_objeto_y_enlaces(self, actualizar_ventana_tambien = True):
        if self.objeto != None:
            try:
                self.objeto.sync()
                try:
                    ajenas = [c for c in self.objeto._SO_columnDict 
                              if c.upper().endswith('ID')]
                except AttributeError:  # SQLObject > 0.6.1
                    ajenas = [c for c in self.objeto.sqlmeta.columns
                              if c.upper().endswith('ID')]
                for ajena in ajenas:
                    reg_ajena = ajena[:-2]
                    obj_d = getattr(self.objeto, reg_ajena)
                    if obj_d != None:
                        obj_d.sync()
                        # print obj_d
                try:
                    multiples = self.objeto._SO_joinList
                except AttributeError:  # SQLObject > 0.6.1
                    multiples = self.objeto.sqlmeta.joins
                for multiple in multiples:
                    lista_objs = getattr(self.objeto, multiple.joinMethodName)
                    for obj_d in [l for l in lista_objs if l != None]:
                        obj_d.sync()
                        # print obj_d
                if actualizar_ventana_tambien:
                    self.actualizar_ventana()
            except:
                self.logger.warning("ventana.py::actualizar_objeto_y_enlaces -> No se pudo forzar la actualización completa.")

    def ir_a(self, objeto):
        anterior = self.objeto
        try:
            # Anulo el aviso de actualización del objeto que deja de ser activo.
            if self.objeto != None:
                self.objeto.notificador.desactivar()
            self.objeto = objeto 
            # Activo la notificación
            self.objeto.notificador.activar(self.aviso_actualizacion)
        except:
            self.objeto = None   
        self.actualizar_ventana(objeto_anterior = anterior)
        
    def chequear_hilo(self):
        """
        Consulta el hilo notificador del objeto actual.
        En realidad es una mera excusa para obligar a GTK a 
        atender al objeto lo antes posible en caso de 
        notificación.
        """
        if self.objeto != None:
            self.objeto.chequear_cambios()
        return True

    def chequear_cambios(self):
        """ 
        Activa el botón «Guardar» si hay cambios los datos.
        El botón se debe llamar "b_guardar" y el método para 
        verificar los cambios "es_diferente" o no funcionará.
        """
        # Existe la posibilidad de que entre la tarea de chequear cambios 
        # antes de inicializar el GUI, por eso chequeo que el botón ya esté 
        # disponible a través de libglade.
        try:
            boton_guardar = self.wids['b_guardar']
        except KeyError:
            boton_guardar = None
        if boton_guardar != None:
            boton_guardar.set_sensitive(self.es_diferente())
        return True

    def actualizar_ventana(self, widget = None, objeto_anterior = None):
        """
        Actualiza el contenido de los controles de la ventana
        para que muestren todos los datos del objeto actual.
        widget no se usa. Se recibe para el caso en que se llama a 
        la función desde un botón.
        objeto_anterior es un objeo de pclases. Sería el que se 
        muestra en pantalla justo antes de llamar a actualizar_ventana
        y recargar los datos. Si se recibe y hay cambios pendientes de
        guardar, el contenido de la ventana se guarda en ese objeto
        ANTES de mostrar el nuevo (o el mismo con nueva información) 
        en los widgets de pantalla.
        """
        if "ventana" in self.wids.keys() and self.wids['ventana'] != None:
            cursor_reloj = gtk.gdk.Cursor(gtk.gdk.WATCH)
            self.wids['ventana'].window.set_cursor(cursor_reloj)
            utils.set_unset_urgency_hint(self.wids['ventana'], False)
            while gtk.events_pending(): gtk.main_iteration(False)
        seguir = self.intentar_guardar_objeto_anterior_antes_de_actualizar(
                    objeto_anterior)
        if seguir:
            if self.objeto != None:
                try:
                    # Empiezo a probar actualización profunda de cachés y demás 
                    # para evitar errores de concurrencia (espero que no 
                    # sobrecargue mucho la red)
                    # refrescar_cache_sqlobject()           
                        # Actualiza (sync) _todos_ los objetos de pclases 
                        # en memoria.
                    self.actualizar_objeto_y_enlaces(
                        actualizar_ventana_tambien = False) 
                        # Actualiza (sync) el objeto de la ventana y 
                        # todas sus relaciones.
                    # self.objeto.sync()   
                        # Por si acaso hay cambios remotos que aún no han 
                        # llegado al objeto.
                    self.rellenar_widgets()
                except sqlobject.SQLObjectNotFound:
                    utils.dialogo_info(titulo = 'REGISTRO ELIMINADO', 
                      texto = 'El registro ha sido borrado desde otro puesto.', 
                      padre = self.wids['ventana'])
                    self.objeto = None
                try:
                    self.wids['b_actualizar'].set_sensitive(False)
                except KeyError:
                    pass    # No hay botón de actualizar. "Passssa nara".
            #print "I like big butts"
            try:
                self.activar_widgets(self.objeto != None)
            except AttributeError:
                pass
            except Exception, msg:
                print "ventana.py::actualizar_ventana -> "\
                      "Excepción al activar_widgets.", msg
            #print "Guardo mi primer bigote en la cartera."
        # Vuelvo a cursor normal pase lo que pase.
        if "ventana" in self.wids.keys() and self.wids['ventana'] != None:
            self.wids['ventana'].window.set_cursor(None)

    def intentar_guardar_objeto_anterior_antes_de_actualizar(self, 
                                                             objeto_anterior):
        """
        Primero verifica si hay cambios pendientes de guardar en la ventana 
        actual antes de actualizar el objeto en pantalla.
        La forma de hacerlo es mirar si b_guardar está habilitado. 
        En ese caso intenta guardar los cambios del objeto anterior antes 
        de sustituirlo en pantalla por el nuevo (que es lo que se está 
        intentando "actualizar" en realidad, el self.objeto que aún no está 
        en pantalla).
        Devuelve True si se ha guardado y se puede continuar la actualización 
        del nuevo objeto para mostrarlo en pantalla o False si se debe 
        interrumpir y dejar que el usuario guarde o descarte antes de pasar 
        a otro objeto como self.objeto.
        """
        if not self.objeto: # Evito falsas alarmas al abrir ventanas.
            res = False
        else:
            res = True
            # XXX Highly experimental. No creo que llegue a usarse. 
            # Necesitaría parchear mucho las ventanas ya escritas. 
            # Tengo que buscar algo mejor.
            if ("b_guardar" in self.wids.keys() 
               and self.wids['b_guardar'] != None 
               and self.wids['b_guardar'].get_property("sensitive") 
               and objeto_anterior != None
               and objeto_anterior != self.objeto): # Importantísimo esto 
                # último. A veces se da al abrir ventanas lentas desde otras.
                print "Cambios pendientes de guardar... ¡PERO EL OBJETO YA "\
                      "HA CAMBIADO!" 
                #print self.objeto.id, objeto_anterior.id
                respuesta =  utils.dialogo('Hay cambios pendientes de guardar.'
                                           '\n¿Desea hacerlo ahora?', 
                                           '¿GUARDAR CAMBIOS?', 
                                           padre = self.wids['ventana'],
                                           icono = gtk.STOCK_DIALOG_WARNING,
                                           cancelar = True, 
                                           defecto = "Cancelar")
                if respuesta:
                    try:
                        tmp = self.objeto
                        self.objeto = objeto_anterior
                        #self.guardar(None) 
                        # Puede no llamarse así el callback, mejor simular el 
                        # click.
                        self.wids['b_guardar'].clicked()
                        objeto_anterior = self.objeto
                        self.objeto = tmp
                    except:
                        utils.dialogo_info(titulo = 'NO SE PUDO GUARDAR', 
                            texto = 'Los cambios no se pudieron guardar '
                                    'automáticamente.\nDebe hacerlo de f'
                                    'orma manual',
                            padre = self.wids['ventana'])
                elif respuesta == gtk.RESPONSE_CANCEL:  
                    # Cancelará el resto de eventos siempre que sea posible. 
                    # No va a poder cancelar una cadena de acciones 
                    # "programáticamente" definida (por ejemplo, no cancelará 
                    # la asignación de un contador a un cliente en clientes.py,
                    # aunque sí cancelará la acción de guardar información 
                    # modificada y tal).
                    res = False
            # XXX
        return res

    def make_funciones_ociosas(self):
        """
        Inicia las funciones ociosas de chequeo de cambios
        remotos (actualizar) y locales (guardar).
        """
        gobject.timeout_add(3000, self.chequear_hilo)
        gobject.timeout_add(2000, self.chequear_cambios)
        
    def aviso_actualizacion(self):
        """
        Muestra una ventana modal con el mensaje de objeto 
        actualizado.
        """
        # TODO: OJO: Si la ventana abre otra ventana y se cierra la primera, 
        # pero la segunda no, es posible que se intente ejecutar esta función. 
        # Por ejemplo: abrir partes_de_fabricacion_balas.py y el depurador 
        # (Ctr+Alt+q). Cambiar un valor del parte desde ipython y cerrar el 
        # parte pero no el depurador. En consola aparecerá el WARNING del 
        # except.
        try:
            self.wids['b_actualizar'].set_sensitive(True)
            utils.dialogo_info(titulo = 'ACTUALIZAR',
                texto = 'Los datos han sido modificados remotamente.\nDebe '
                        'actualizar la información mostrada en pantalla.\nP'
                        'ulse el botón «Actualizar»',
                padre = self.wids['ventana'])
        except Exception, msg:
            pass
            # DEBUG: print """WARNING: Botón «Actualizar» o "self.wids['ventana'] no encontrado. Excepción: %s""" % (msg)
        
    def salir(self, boton, event=None, mostrar_ventana=False):
        """
        Muestra una ventana de confirmación y 
        sale de la ventana cerrando el bucle
        local de gtk_main.
        Si mostrar_ventana es False, sale directamente
        sin preguntar al usuario.
        """
        try:
            b_guardar = self.wids['b_guardar']
        except KeyError:
            b_guardar = None
        if  b_guardar != None and b_guardar.get_property('sensitive'):
            # Hay cambios pendientes de guardar.
            if utils.dialogo('Hay cambios pendientes de guardar.\n¿Desea hace'
                             'rlo ahora?', 
                             '¿GUARDAR CAMBIOS?', 
                             padre = self.wids['ventana'], 
                             icono = gtk.STOCK_SAVE, 
                             #defecto = "Sí"):  # CWT: A veces en BlancoPe 
                                # abren la ventana de productos para buscar 
                                # un precio y le dan al botón antes de que se 
                                # carguen los datos, provocando que se detecte 
                                # como un falso cambio de datos de la ventana 
                                # (todo blanco) respecto a la caché (datos 
                                # reales de la BD). Al darle a ENTER, 
                                # responden Sí por defecto -hasta ahora- y 
                                # sobreescriben con blanco todos los datos del 
                                # registro en la base de datos.
                             defecto = "No"):
                try:
                    self.guardar(None)
                except:
                    utils.dialogo_info(titulo = 'NO SE PUDO GUARDAR', 
                                       texto = 'Los cambios no se pudieron gua'
                                               'rdar automáticamente.\nDebe ha'
                                               'cerlo de forma manual',
                                       padre = self.wids['ventana'])
                    return True # Si devuelvo False, None, etc... continúa la 
                                # cadena de eventos y destruye la ventana.
                                # Devuelvo True para cancelar el cierre de la 
                                # ventana. 
        if event == None:
            # Me ha invocado el botón
            if not mostrar_ventana or \
               utils.dialogo('¿Desea salir de la ventana actual?', 
                             'SALIR', 
                             padre = self.wids['ventana'], 
                             icono = gtk.STOCK_QUIT):
                self.wids['ventana'].destroy()
                return False
            else:
                return True
        else:
            return not mostrar_ventana or \
                   not utils.dialogo('¿Desea salir de la ventana actual?', 
                                     'SALIR', 
                                     padre = self.wids['ventana'],
                                     icono = gtk.STOCK_QUIT)

    def make_connections(self):
        """
        Realiza las conexiones básicas entre widgets y callbacks.
        Para el resto de conexiones, usar add_connections.
        La ventana principal DEBE llamarse "ventana".
        """
        connections = {'ventana/delete_event' : self.salir,
                       'ventana/destroy': gtk.main_quit}
        for wid_con, func in connections.iteritems():
            wid,con = wid_con.split('/')
            h_id = self.wids[wid].connect(con,func)
            try:
                self.handlers_id[wid][con].append(h_id)
            except KeyError:
                self.handlers_id[wid][con] = [h_id]

    def add_connections(self, dict):
        """
        Recorre el diccionario y crea las conexiones con 
        los callbacks.
        """
        for wid_con, func in dict.iteritems():
            wid,con = wid_con.split('/')
            h_id = self.wids[wid].connect(con,func)
            try:
                self.handlers_id[wid][con].append(h_id)
            except KeyError:
                self.handlers_id[wid][con] = [h_id]
    
    def check_permisos(self, nombre_fichero_ventana):
        """
        Activa o desactiva los controles dependiendo de los 
        permisos del usuario.
        """
        VENTANA = nombre_fichero_ventana
        if self.usuario != None and self.usuario.nivel > 0:
            ventanas = pclases.Ventana.selectBy(fichero = VENTANA)
            if ventanas.count() == 1:   # Siempre debería ser 1.
                permiso = self.usuario.get_permiso(ventanas[0])
                if permiso == None:
                    permiso = MetaPermiso()
                if permiso.escritura:
                    if self.usuario.nivel <= 1:
                        # print "Activo widgets para usuario con nivel de privilegios <= 1."
                        self.activar_widgets(True, chequear_permisos = False)
                    else:
                        # print "Activo widgets porque permiso de escritura y objeto no bloqueado o recién creado."
                        if hasattr(self.objeto, "bloqueado"):
                            condicion_bloqueo = self.objeto != None and (
                                not self.objeto.bloqueado 
                                or self._objetoreciencreado == self.objeto)
                        else:
                            condicion_bloqueo = self.objeto != None # and (not False or self._objetoreciencreado == self.objeto) = self.objeto != None and True = self.objeto != None
                        self.activar_widgets(condicion_bloqueo, 
                                             chequear_permisos = False)
                else:   # No tiene permiso de escritura. Sólo puede modificar el objeto que acaba de crear.
                    if hasattr(self, "_objetoreciencreado") and self._objetoreciencreado == self.objeto: 
                        # print "Activo widgets porque objeto recién creado aunque no tiene permiso de escritura."
                        self.activar_widgets(True, chequear_permisos = False)
                    else:
                        # print "Desactivo widgets porque no permiso de escritura."
                        self.activar_widgets(False, chequear_permisos = False)
                try:
                    self.wids['b_buscar'].set_sensitive(permiso.lectura)
                except (KeyError, AttributeError):
                    pass
                try:
                    self.wids['b_nuevo'].set_sensitive(permiso.nuevo)
                except (KeyError, AttributeError):
                    pass
        else:
            self.activar_widgets(True, chequear_permisos = False)

class MetaPermiso:
    """
    Objetos que emulan los campos básicos de la clase Permiso para 
    activar o desactivar widgets de la ventana.
    Se usa en caso de que -por el oscuro y extraño motivo que sea- 
    el usuario de la ventana no tiene definidos permisos en la misma 
    (es decir, su get_permisos devuelve None).
    """
    def __init__(self):
        """
        Todos los permisos a False.
        """
        self.lectura = False
        self.escritura = False
        self.nuevo = False
        self.permiso = False

 
