#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, mx, mx.DateTime, md5

# 0.- Recreación de la base de datos:
salida = os.popen("./init_db.sh fpinn ufpinn ufpinn 2>&1")
for l in salida.readlines():
    print l,
    if "ERROR: " in l and "no existe" not in l:
        sys.exit(1)
print

# 1.- Datos básicos: 
# Datos de la empresa, propia empresa como cliente y como proveedor.
sys.path.append(os.path.join("..", "framework"))
import pclases
dde = pclases.DatosDeLaEmpresa()
cliente = pclases.Cliente(nombre = dde.nombre, 
                          cif = dde.cif, 
                          tarifa = None)
proveedor = pclases.Proveedor(nombre = dde.nombre, 
                              cif = dde.cif)
no_conformidad = pclases.CuentaGastos(descripcion = "No conformidad")
envases = pclases.CuentaGastos(descripcion = "Envases")
salarios = pclases.CuentaGastos(descripcion = "Salarios")
gastos_generales = pclases.CuentaGastos(descripcion = "Gastos generales")
apertura = pclases.CuentaGastos(descripcion = "Gastos de apertura")
cierre = pclases.CuentaGastos(descripcion = "Gastos de cierre")
varios = pclases.CuentaGastos(descripcion = "Gastos varios")

# 2.- Datos de prueba:
import adqprod
empleado = pclases.Empleado(nombre = "Empleado de prueba", 
                            dni = "00.000.000-T")
print "Empleado creado:", empleado
#finca = pclases.Finca()
#print "Finca creada:", finca
#parcela = pclases.Parcela(finca = finca)
#print "Parcela creada:", parcela
actividad = pclases.Actividad(codigo = 1, 
                              descripcion = "Actividad de prueba", 
                              campo = False, 
                              manipulacion = False)
print "Actividad creada:", actividad
campanna = pclases.Campanna(fechaInicio = mx.DateTime.DateTimeFrom(day = 1, 
                                                                   month = 1, 
                                                                   year = 2008), 
                            fechaFin = mx.DateTime.DateTimeFrom(day = 31, 
                                                                month = 12, 
                                                                year = 2008))
print "Campaña creada:", campanna

pclases.MateriaActiva(nombre = "Acido indolacético", 
                      nombreComercial = "AI-500", 
                      listado = True, 
                      otros = False, 
                      plazoSeguridad = 15, 
                      dosis = 10)
pclases.MateriaActiva(nombre = "Citoquinina", 
                      nombreComercial = "Citonol", 
                      listado = False, 
                      otros = True, 
                      plazoSeguridad = 10, 
                      dosis = 2.5)

# Hasta aquí algunos datos básicos para pruebas unitarias. Ahora vamos con 
# datos aleatorios (muchos) para probar el rendimiento:
nombres = ("Vincent Vega", "Jules Winnfield", "Pumpkin (Ringo)", 
           "Honey Bunny (Yolanda)", "Lance", "Butch Coolidge", 
           "Marsellus Wallace", "Marvin", "Fabienne", "Jody", "Zed", 
           "Mia Wallace", "Maynard", "Paul", "Brett")
for nombre in nombres:
    pclases.Empleado(nombre = nombre)

import random
for i in range(1, 3):
    f = pclases.Finca()
    for i in range(random.randint(2, 5)):
        pclases.Parcela(finca = f, numeroDePlantas = random.randint(100, 1000))

for f in pclases.Finca.select():
    f.nombre = "Finca %02d" % f.id
for p in pclases.Parcela.select():
    p.parcela = "Parcela %03d" % p.id

for cod, actividad, campo, manipulacion in ((2, "Plantación", True, False), 
                                            (3, "Envasado", False, True), 
                                            (4, "Abono", True, False), 
                                            (5, "Carga y descarga",False,True), 
                                            (6, "Recolección", True, False)):
    pclases.Actividad(codigo = cod, 
                      descripcion = actividad, 
                      campo = campo, 
                      manipulacion = manipulacion)

pclases.Campanna(fechaInicio = mx.DateTime.DateTimeFrom(day = 1, 
                                                        month = 1, 
                                                        year = 2007), 
                 fechaFin = mx.DateTime.DateTimeFrom(day = 31, 
                                                     month = 12, 
                                                     year = 2007))
pclases.Campanna(fechaInicio = mx.DateTime.DateTimeFrom(day = 1, 
                                                        month = 1, 
                                                        year = 2009), 
                 fechaFin = mx.DateTime.DateTimeFrom(day = 31, 
                                                     month = 12, 
                                                     year = 2009))
pclases.Campanna(fechaInicio = mx.DateTime.DateTimeFrom(day = 1, 
                                                        month = 1, 
                                                        year = 2010), 
                 fechaFin = mx.DateTime.DateTimeFrom(day = 31, 
                                                     month = 12, 
                                                     year = 2010))
cuentas = (apertura, varios, cierre)

print "Creando gastos aleatoriamente..."
for i in range(100):
    while True:
        try:
            fecha = mx.DateTime.DateTimeFrom(day = random.randint(1, 31), 
                                             month = random.randint(1, 12), 
                                             year = random.randint(2007,2010)) 
        except:
            pass
        else:
            break
    g = pclases.Gasto(cuentaGastos = cuentas[random.randrange(len(cuentas))], 
                      parcela = pclases.Parcela.select()[random.randrange(pclases.Parcela.select().count())], 
                      concepto = "Gasto %d" % i, 
                      fecha = fecha, 
                      importe = round(random.random() * random.randint(100, 10000) * 100)/100, 
                      facturaCompra = None)

print "Creando jornales aleatoriamente...", 
for i in range(random.randint(500, 1000)):
        idempleado = "%04d" % pclases.Empleado.select()[random.randrange(pclases.Empleado.select().count())].id
        idactividad = "%04d" % pclases.Actividad.select()[random.randrange(pclases.Actividad.select().count())].id
        idparcela = "%04d" % pclases.Parcela.select()[random.randrange(pclases.Parcela.select().count())].id
        while True:
            try:
                fi = mx.DateTime.DateTimeFrom(day = random.randint(1, 31), 
                                              month = random.randint(1, 12), 
                                              year = random.randint(2007,2010), 
                                              hour = random.randint(0, 23), 
                                              minute = random.randint(0, 59))
            except:
                pass
            else:
                break
        inicio = fi.strftime("%Y%m%d%H%M")
        ff = fi + (mx.DateTime.oneHour * random.randint(1, 24))
        fin = ff.strftime("%Y%m%d%H%M")
        prod = random.randint(20, 900) + random.random()
        produccion = "%08d%02d" % (int(prod), 
                                   int(round((prod - int(prod)) * 100)))
        data = idempleado + idactividad + idparcela + inicio + fin + produccion
        digest = md5.new(data).hexdigest()
        paquete = data + digest
        adqprod.build_jornal(paquete)
        print ".", 

print 
print "Creando clientes...", 
for nombre in ("Dr. Peter Venkman", "Dr. Raymond Stantz", "Dana Barrett", 
               "Dr. Egon Spengler", "Louis Tully", "Janine Melnitz", 
               "Walter Peck", "Winston Zeddmore"):
    print nombre + "...",
    cifn = random.randint(10000000, 99999999)
    cifl = chr(ord('A') + random.randrange(26))
    cif = "%d-%s" % (cifn, cifl)
    pclases.Cliente(nombre = nombre, cif = cif, tarifa = None)

print

# Debe existir al menos un envase.
madera = pclases.Envase(proveedor = None, 
                         nombre = "Envase de madera de 2 kg", 
                         kg = 2)
tarrina = pclases.Envase(proveedor = None, 
                         nombre = "Tarrina de 500 gramos", 
                         kg = 0.50)

# Familias:
ffresa = pclases.Familia(nombre = "Fresa", observaciones = "Fresas y fresones.")
fframb = pclases.Familia(nombre = "Frambuesa", observaciones = "Frambuesas.")

# Un par de productos
pclases.ProductoVenta(familia = ffresa, 
                      envase = madera, 
                      precio = None, 
                      nombre = "Fresón 2 kg madera", 
                      plazoSeguridad = 0, 
                      materiaActiva = "", 
                      envasep = True, 
                      manipulacion = False, 
                      transporte = True, 
                      tarifa = False)
pclases.ProductoVenta(familia = ffresa, 
                      envase = tarrina, 
                      precio = None, 
                      nombre = "Fresón tarrina 500 gr", 
                      plazoSeguridad = 0, 
                      materiaActiva = "", 
                      envasep = True, 
                      manipulacion = True, 
                      transporte = False, 
                      tarifa = True)

# Usuario administrador con permiso sobre todas las ventanas.
admin = pclases.Usuario(usuario = "admin", 
                        passwd = md5.new("admin").hexdigest(), 
                        nombre = "Cuenta de administrador", 
                        cuenta = "rodriguez.bogado@gmail.com", 
                        cpass = "", 
                        nivel = 0, 
                        email = "rodriguez.bogado@gmail.com", 
                        smtpserver = "smtp.gmail.com", 
                        smtppassword = "", 
                        firmaTotal = True, 
                        firmaComercial = True, 
                        firmaDirector = True, 
                        firmaTecnico = True, 
                        firmaUsuario = True, 
                        observaciones = "")
nombre_modulos = (("RR.HH.", "users.png"), 
                  ("Producción", "silos.png"), 
                  ("Administración", "administracion.png"), 
                  ("Consultas", "costes.png"), 
                  ("General", "func_generales.png"), 
                  ("Ayuda", "doc_y_ayuda.png"))
modulos = {}
for (nm, icono) in nombre_modulos:
    modulos[nm] = pclases.Modulo(nombre = nm, descripcion = nm, icono = icono)

ventanas = (("Actividades de jornadas de campo", 
                "actividades.py", 
                "Actividad", 
                "actividades.png", 
                modulos['General']), 
            ("Agenda", 
                "agenda.py", 
                "Agenda", 
                "agenda.png", 
                modulos["Consultas"]), 
            ("Albaranes de salida", 
                "albaranes_de_salida.py", 
                "AlbaranesDeSalida", 
                "albaran.png", 
                modulos["Administración"]), 
            ("Clientes", 
                "clientes.py", 
                "Clientes", 
                "clientes.png", 
                modulos["General"]), 
            ("Producción por empleado", 
                "empleados_produccion.py", 
                "EmpleadosProduccion", 
                "bars.png", 
                modulos["Producción"]), 
            ("Empleados", 
                "empleados.py", 
                "Empleados", 
                "empleados.png", 
                modulos["RR.HH."]), 
            ("Facturas de venta", 
                "facturas_venta.py", 
                "FacturasVenta", 
                "factura_venta.png", 
                modulos["Administración"]), 
            ("Gestión de cobro de facturas de venta", 
                "cobro_facturas_venta.py", 
                "CobroFacturasVenta", 
                "money.png", 
                modulos["Administración"]), 
            ("Facturas de terceros", 
                "facturas_de_terceros.py", 
                "FacturasDeTerceros", 
                "factura_venta.png", 
                modulos["Administración"]), 
            ("Fincas", 
                "fincas.py", 
                "Fincas", 
                "fincas.png", 
                modulos["General"]), 
            ("Parcelas", 
                "parcelas.py", 
                "Parcelas", 
                "parcelas.png", 
                modulos["General"]), 
            ("Producción diaria por empleado", 
                "produccion_por_empleado.py", 
                "ProduccionPorEmpleado", 
                "prodporempleado.png", 
                modulos["Producción"]), 
            ("Introducir producción manualmente", 
                "jornales.py", 
                "Jornales", 
                "prodmanual.png", 
                modulos["Producción"]), 
            ("Producción por parcela", 
                "produccion_por_parcela.py", 
                "ProduccionPorParcela", 
                "prodporparcela.png", 
                modulos["Producción"]), 
            ("Productos", 
                "productos_de_venta.py", 
                "ProductosDeVenta", 
                "catalogo.png", 
                modulos["General"]), 
            ("Familias", 
                "familias.py", 
                "Familias", 
                "", 
                modulos["General"]), 
            ("Envases", 
                "envases.py", 
                "Envases", 
                "", 
                modulos["General"]), 
            ("Materias activas", 
                "materias_activas.py", 
                "MateriasActivas", 
                "materias.png", 
                modulos["General"]), 
            ("Proveedores", 
                "proveedores.py", 
                "Proveedores", 
                "proveedores.png", 
                modulos["General"]), 
            ("Salarios", 
                "salarios.py", 
                "Salarios", 
                "salarios2.png", 
                modulos["RR.HH."]), 
            ("Series de facturas de compra", 
                "serie_facturas_compra.py", 
                "SeriesFacturasCompra", 
                "", 
                modulos["General"]), 
            ("Series de facturas de venta", 
                "serie_facturas_venta.py", 
                "SeriesFacturasVenta", 
                "", 
                modulos["General"]), 
            ("Tarifas", 
                "tarifas.py", 
                "Tarifas", 
                "tarifa.png", 
                modulos["General"]), 
            ("Gastos", 
                "gastos.py", 
                "Gastos", 
                "gastos.png", 
                modulos["Administración"]), 
            ("Usuarios", 
                "usuarios.py", 
                "Usuarios", 
                "usuarios.png", 
                modulos["General"]), 
            ("Facturas de compra", 
                "facturas_compra.py", 
                "FacturasCompra", 
                "factura_compra.png", 
                modulos["Administración"]), 
            ("Facturar albaranes por lote", 
                "facturar_albaranes.py", 
                "FacturarAlbaranes", 
                "porlote.png", 
                modulos["Administración"]), 
            ("Acerca de", 
                "acerca_de", 
                "acerca_de", 
                "acerca.png", 
                modulos["Ayuda"]), 
            ("Gastos por intervalo de fechas", 
                "consulta_gastos.py", 
                "ConsultaGastos", 
                "informe.png", 
                modulos["Consultas"]), 
            ("Consulta resumen de parcelas", 
                "consulta_parcelas.py", 
                "ConsultaParcelas", 
                "informe.png", 
                modulos["Consultas"]), 
            ("Consulta resumen de clientes", 
                "consulta_clientes.py", 
                "ConsultaClientes", 
                "informe.png", 
                modulos["Consultas"]), 
            ("Consulta resumen de precios", 
                "consulta_precios.py", 
                "ConsultaPrecios", 
                "informe.png", 
                modulos["Consultas"]), 
            ("Buscar albaranes", 
                "buscar_albaranes.py", 
                "BuscarAlbaranes", 
                "informe.png", 
                modulos["Administración"]), 
            ("Facturación por intervalo de fechas", 
                "consulta_facturacion.py", 
                "ConsultaFacturacion", 
                "informe.png", 
                modulos["Consultas"]), 
            ("Albaranes pendientes de facturar", 
                "consulta_facturacion_pendiente.py", 
                "ConsultaFacturacionPendiente", 
                "informe.png", 
                modulos["Consultas"]), 
            ("Facturas pendientes de cobro", 
                "consulta_pendiente_cobro.py", 
                "ConsultaPendienteCobro", 
                "informe.png", 
                modulos["Consultas"]), 
            ("Salarios por lote", 
                "build_salarios.py", 
                "SalariosPorLote", 
                "salarios.png", 
                modulos["RR.HH."])
            )

for desc, fich, clase, icono, modulo in ventanas:
    nueva_ventana = pclases.Ventana(descripcion = desc, 
                                    fichero = fich, 
                                    clase = clase, 
                                    icono = icono, 
                                    modulo = modulo)
    pclases.Permiso(usuario = admin, 
                    ventana = nueva_ventana, 
                    permiso = True, 
                    lectura = True, 
                    escritura = True, 
                    nuevo = True)

