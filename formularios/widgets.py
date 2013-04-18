#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2005-2012  Francisco José Rodríguez Bogado,                   #
#                          Diego Muñoz Escalante.                             #
#                          (bogado@qinn.es, escalant3@users.sourceforge.net)  #
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

import gtk
import gtk.glade

LANZAR_KEY_EXCEPTION = True # Si False se devuelve None cuando se busca un 
                            # widget que no existe y se ignora la excepción.

class Widgets:
    def __init__(self, gladefile):
        try:
            self.widgets = gtk.glade.XML(gladefile)
        except RuntimeError:    # No es un .glade. Debe ser un .ui
            self.widgets = self._cargar_widgets(gladefile)
        self.dynwidgets = {}    # Widgets generados dinámicamente
        # self.__keys = [w.name for w in self.widgets.get_widget_prefix('')] 
        try:
            self.__keys = self.widgets.keys()
        except AttributeError:
            self.__keys = [w.name for w in self.widgets.get_widget_prefix('')] 

    def _cargar_widgets(self, gladefile):
        """
        Carga, mediante gtk.Builder, todos los widgets del glade en la misma 
        estructura de diccionario que libglade.
        """
        builder = gtk.Builder()
        builder.add_from_file(gladefile)
        res = {}
        for w in builder.get_objects():
            if hasattr(w, "name") and w.name: # En GTK < 2.20, esto está vacío.
                name = w.name
            else:
                try:
                    name = gtk.Buildable.get_name(w)
                    w.set_property("name", name)
                except TypeError: # Los TreeSelection no implementan Buildable.
                    try:
                        str_tipo = str(type(ts)).split()[1].split(".")[1]\
                                       .replace("'", "") 
                    except:
                        str_tipo = "unknown"
                    name = "%s_%s" % (str_tipo, hash(w)) 
            res[name] = w
        return res
        
    def __getitem__(self, key):
        try:
            res = self.widgets[key]
        except (TypeError, KeyError):
            try:    # ¿Glade 3?
                res = self.widgets.get_widget(key)
            except Exception:
                # print "------------------>", e
                res = None
        #res = self.widgets.get_widget(key)
        if res == None:  # Si no es del archivo glade...
            try:         # tal vez se haya creado "programáticamente".
                res = self.dynwidgets[key]
            except KeyError:
                res = None
                if LANZAR_KEY_EXCEPTION:
                    txterror = "widgets::__getitem__ -> "\
                               "Widget '%s' no existe." % key
                    raise KeyError, txterror
        return res

    def __setitem__(self, key, value):
        # ¿No debería controlar que no existiera ya como widget del .glade?
        self.dynwidgets[key] = value
        value.set_property("name", key)
        try:
            self.__keys.remove(key)
        except ValueError:  # No está repetido.
            pass
        self.__keys.append(key)

    def keys(self):
        """
        Devuelve una lista de claves del diccionario de widgets.
        """
        return self.__keys[:]

    def __iter__(self):
        return iter(self.__keys)

    def next(self):
        index = 0
        while index < len(self.__keys):
            yield self.__keys(index)
            index += 1
        raise StopIteration

