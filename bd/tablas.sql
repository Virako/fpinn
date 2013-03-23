--------------------------------------------------------------------------------
-- Copyright (C) 2005, 2006 Francisco José Rodríguez Bogado,                   -
--                          (pacoqueen@users.sourceforge.net                   -
--                                                                             -
-- This file is part of F.P.-INN.                                             -
--                                                                             -
-- F.P.-INN is free software; you can redistribute it and/or modify           -
-- it under the terms of the GNU General Public License as published by        -
-- the Free Software Foundation; either version 2 of the License, or           -
-- (at your option) any later version.                                         -
--                                                                             -
-- F.P.-INN is distributed in the hope that it will be useful,                -
-- but WITHOUT ANY WARRANTY; without even the implied warranty of              -
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               -
-- GNU General Public License for more details.                                -
--                                                                             -
-- You should have received a copy of the GNU General Public License           -
-- along with F.P.-INN; if not, write to the Free Software                    -
-- Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA  -
--------------------------------------------------------------------------------

--------- N O T A S ----------------------------------------
-- su -c "su postgres -c \"createuser -s -d -R ufpinn && echo ALTER USER ufpinn WITH PASSWORD \'ufpinn\'\; | psql template1\""
-- su 
-- vi /etc/postgresql/8.2/main/pg_hba.conf
--   local fpinn ufpinn trust
--   host fpinn ufpinn 0.0.0.0/0 password
--   :wq
-- /etc/init.d/postgresql-8.2 reload
-- exit
-- ./init_db.sh fpinn ufpinn ufpinn
------------------------------------------------------------

--------------
-- Personal --
--------------
CREATE TABLE empleado(
    id SERIAL PRIMARY KEY, 
    nombre TEXT, 
    domicilio TEXT DEFAULT '', 
    ciudad TEXT DEFAULT '', 
    poblacion TEXT DEFAULT '', 
    cp TEXT DEFAULT '', 
    pais TEXT DEFAULT '', 
    fecha_nacimiento DATE DEFAULT CURRENT_DATE, 
    estado_civil TEXT DEFAULT '', 
    dni TEXT DEFAULT '', 
    numero_seguridad_social TEXT DEFAULT '', 
    telefono TEXT DEFAULT '', 
    vivienda TEXT DEFAULT '', 
    correo_electronico TEXT DEFAULT '', 
    ccc TEXT DEFAULT '', 
    fecha_alta DATE DEFAULT CURRENT_DATE, 
    observaciones TEXT DEFAULT '', 
    precio_diario FLOAT DEFAULT 0.0, 
    precio_hora_campo FLOAT DEFAULT 0.0, 
    precio_hora_manipulacion FLOAT DEFAULT 0.0
);

-------------
-- Campaña --
-------------
CREATE TABLE campanna(
    id SERIAL PRIMARY KEY, 
    fecha_inicio DATE DEFAULT CURRENT_DATE, 
    fecha_fin DATE DEFAULT CURRENT_DATE
);

------------
-- Fincas --
------------
CREATE TABLE finca(
    id SERIAL PRIMARY KEY, 
    nombre TEXT DEFAULT '', 
    provincia TEXT DEFAULT '', 
    poligono TEXT DEFAULT '', 
    superficie FLOAT DEFAULT 0.0, 
    altitud FLOAT DEFAULT 0.0, 
    poblacion TEXT DEFAULT '', 
    parcela TEXT DEFAULT '', 
    coordenadas_utm_e FLOAT DEFAULT 0.0, 
    coordenadas_utm_n FLOAT DEFAULT 0.0, 
    coordenadas_utm_h INT DEFAULT 0, 
    coordenadas_utm_b CHAR DEFAULT ' ', 
    ruta_plano TEXT DEFAULT ''
);

--------------
-- Parcelas --
--------------
CREATE TABLE parcela(
    id SERIAL PRIMARY KEY, 
    finca_id INT REFERENCES finca, 
    parcela TEXT DEFAULT '', 
    sector_de_riego TEXT DEFAULT '', 
    superficie FLOAT DEFAULT 0.0, 
    ruta_plano TEXT DEFAULT '', 
    propia BOOLEAN DEFAULT TRUE, 
    numero_de_plantas INT DEFAULT 0, 
    repr_ancho INT DEFAULT 1,   -- Ancho del widget con la imagen de la parcela
                                -- en la consulta produccion_por_parcela. 
    repr_alto INT DEFAULT 1,    -- Alto de la representación para el widget de 
                                -- la misma consulta.
    repr_orden INT DEFAULT -1   -- Orden relativo entre parcelas de la misma 
                                -- finca. -1 = sin orden específico.
);

---------------
-- Actividad --
---------------
-- Una actividad define el trabajo realizado por un empleado de campo 
-- en una jornada determinada. Provendrá de un nodo externo de adquisición
-- de datos en forma de número entero, que se corresponderá con una de 
-- las actividades de la tabla siguiente.
CREATE TABLE actividad(
    id SERIAL PRIMARY KEY, 
    codigo INT NOT NULL UNIQUE, 
    descripcion TEXT DEFAULT '', 
    observaciones TEXT DEFAULT '', 
    campo BOOLEAN DEFAULT TRUE, 
    manipulacion BOOLEAN DEFAULT FALSE, 
    CHECK (NOT (campo AND manipulacion))
);

-------------------
-- Cuenta gastos --
-------------------
CREATE TABLE cuenta_gastos(
    id SERIAL PRIMARY KEY, 
    descripcion TEXT DEFAULT ''
); 

---------------------
-- Tabla proveedor --
---------------------
CREATE TABLE proveedor(
    id SERIAL PRIMARY KEY,
    nombre TEXT,
    cif TEXT DEFAULT '',
    direccion TEXT DEFAULT '',
    pais TEXT DEFAULT '',
    ciudad TEXT DEFAULT '',
    provincia TEXT DEFAULT '',
    cp TEXT DEFAULT '',
    telefono TEXT DEFAULT '',
    fax TEXT DEFAULT '',
    contacto TEXT DEFAULT '',
    observaciones TEXT DEFAULT '',
    -- Segunda dirección
    direccionfacturacion TEXT DEFAULT '',
    paisfacturacion TEXT DEFAULT '',
    ciudadfacturacion TEXT DEFAULT '',
    provinciafacturacion TEXT DEFAULT '',
    cpfacturacion TEXT DEFAULT '',
    email TEXT DEFAULT '',
    documentodepago TEXT DEFAULT '',
    vencimiento TEXT DEFAULT '',    -- En principio va igual que los 
                                    -- vencimientos de clientes.
    diadepago TEXT DEFAULT '',  -- El día en que se harán los pagos realmente 
                                -- (independientemente de lo que marque
                                -- el vencimiento, el pago se puede hacer días 
                                -- antes o días después, en un día del
                                -- mes fijo) P.ej: El vencimiento cumple el 
                                -- 15 de enero pero siempre se le paga al 
                                -- proveedor los días 5 de cada mes.
                                -- De momento es texto (aunque en teoría 
                                -- sería un INT) para contemplar la posibilidad
                                -- de meter días concatenados con comas -por 
                                -- ejemplo- y así expresar que se le
                                -- pagan -por ejemplo one more time- los días 
                                -- 5 y 20 de cada mes.
    correoe TEXT DEFAULT '',
    web TEXT DEFAULT '',
    banco TEXT DEFAULT '',
    swif TEXT DEFAULT '',
    iban TEXT DEFAULT '',
    cuenta TEXT DEFAULT '',
    inhabilitado BOOLEAN DEFAULT FALSE,
    motivo TEXT DEFAULT '',     -- Si está inhabilitado no se permitirá 
                                -- hacerle más pedidos de compra.(CWT)
    iva FLOAT DEFAULT 0.16      -- Iva por defecto del proveedor (16% a no 
                                -- ser que sea extranjero).
);

----------------------------------
-- Series de números de factura --
----------------------------------
CREATE TABLE serie_facturas_compra(
    id SERIAL PRIMARY KEY, 
    prefijo TEXT DEFAULT '', 
    contador INT DEFAULT 1, 
    sufijo TEXT DEFAULT '', 
    observaciones TEXT DEFAULT '', 
    b BOOLEAN DEFAULT FALSE, 
    posiciones INT DEFAULT 1    -- Posiciones numéricas a completar con ceros.
);

------------------------
-- Facturas de compra --
------------------------
CREATE TABLE factura_compra(
    id SERIAL PRIMARY KEY,  
    proveedor_id INT REFERENCES proveedor, 
    serie_facturas_compra_id INT REFERENCES serie_facturas_compra, 
    fecha DATE DEFAULT CURRENT_DATE, 
    numfactura TEXT DEFAULT '' NOT NULL
); 

------------
-- Gastos --
------------
CREATE TABLE gasto(
    id SERIAL PRIMARY KEY, 
    cuenta_gastos_id INT REFERENCES cuenta_gastos,
    factura_compra_id INT REFERENCES factura_compra DEFAULT NULL, 
    parcela_id INT REFERENCES parcela DEFAULT NULL, 
    codigo TEXT DEFAULT '', 
    concepto TEXT DEFAULT '', 
    fecha DATE DEFAULT CURRENT_DATE, 
    importe FLOAT DEFAULT 0.0
); 

--------------
-- Salarios --
--------------
CREATE TABLE salario(
    id SERIAL PRIMARY KEY, 
    gasto_id INT REFERENCES gasto, 
    empleado_id INT REFERENCES empleado, 
    actividad_id INT REFERENCES actividad, 
    fecha DATE DEFAULT CURRENT_DATE, 
    horas_campo FLOAT DEFAULT 0.0, 
    horas_manipulacion FLOAT DEFAULT 0.0, 
    total_euros FLOAT DEFAULT 0.0
);

--------------
-- Jornales --
--------------
CREATE TABLE jornal(
    id SERIAL PRIMARY KEY, 
    empleado_id INT REFERENCES empleado, 
    campanna_id INT REFERENCES campanna, 
    actividad_id INT REFERENCES actividad, 
    parcela_id INT REFERENCES parcela, 
    salario_id INT REFERENCES salario DEFAULT NULL, 
    fechahora_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
    fechahora_fin TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
    produccion FLOAT DEFAULT 0.0 
);

---------------------------
-- Familias de productos --
---------------------------
CREATE TABLE familia(
    id SERIAL PRIMARY KEY, 
    nombre TEXT DEFAULT '', 
    observaciones TEXT DEFAULT ''
);

-------------
-- Envases --
-------------
-- La referencia a un proveedor es porque los envases usados en las 
-- ventas provienen de un proveedor (aunque no necesariamente debe 
-- guardarse en la BD y puede dejarse a nulo), aunque no se controle la 
-- compra de los mismos más allá de la gestión de sus facturas (ni entrada 
-- de materiales, ni pedidos, etc.)
CREATE TABLE envase(
    id SERIAL PRIMARY KEY, 
    proveedor_id INT REFERENCES proveedor DEFAULT NULL,--Proveedor por defecto.
    nombre TEXT DEFAULT '', 
    kg FLOAT DEFAULT 0.0,   -- Kilogramos de capacidad del envase.
    minimo FLOAT DEFAULT 0.0, 
    existencias FLOAT DEFAULT 0.0
);

CREATE TABLE tarrina(
    -- Puede ser cesta, tapa o flowpack.
    id SERIAL PRIMARY KEY, 
    proveedor_id INT REFERENCES proveedor DEFAULT NULL,--Proveedor por defecto.
    nombre TEXT DEFAULT '', 
    gr FLOAT DEFAULT 0.0, -- Capacidad en gramos.
    unidad TEXT DEFAULT '', -- Metros si es flowpack, unidad si es cesta, etc.
    minimo FLOAT DEFAULT 0.0, 
    existencias FLOAT DEFAULT 0.0
);

---------------------------------------------------------
-- Configuración de empaquetado de tarrinas en envases. --
---------------------------------------------------------
-- Relación muchos a muchos entre tarrinas y envases, con atributo numérico.
CREATE TABLE empaquetado(
    id SERIAL PRIMARY KEY, 
    envase_id INT REFERENCES envase DEFAULT NULL, 
    tarrina_id INT REFERENCES tarrina DEFAULT NULL, 
    cantidad INT DEFAULT 0  
);

-------------
-- Tarifas --
-------------
CREATE TABLE tarifa(
    id SERIAL PRIMARY KEY, 
    nombre TEXT DEFAULT ''
);

-----------------------
-- Precios de tarifa --
-----------------------
-- Conjunto de conceptos más una cantidad arbitraria.
CREATE TABLE precio(
    id SERIAL PRIMARY KEY, 
    tarifa_id INT REFERENCES tarifa, 
    descripcion TEXT DEFAULT '',    -- Descripción identificativa del precio
    importe_adicional FLOAT DEFAULT 0.0     -- a.k.a. precio base.
);

---------------
-- Conceptos --
---------------
-- Conceptos que componen un precio de una tarifa.
CREATE TABLE concepto(
    id SERIAL PRIMARY KEY, 
    precio_id INT REFERENCES precio, 
    concepto TEXT DEFAULT '', 
    importe FLOAT DEFAULT 0.0
);

-------------------------
-- Productos de venta  --
-------------------------
CREATE TABLE producto_venta(
    id SERIAL PRIMARY KEY, 
    familia_id INT REFERENCES familia DEFAULT NULL, 
    envase_id INT REFERENCES envase DEFAULT NULL, 
    precio_id INT REFERENCES precio DEFAULT NULL,   -- Precio por defecto, 
        -- que debe existir como precio y presumiblemente pertenecer a una 
        -- tarifa. No es un importe únicamente porque el precio debe  
        -- englobar conceptos a desglosar.
    nombre TEXT DEFAULT '', 
    plazo_seguridad INT DEFAULT 0,  
        -- Valor por defecto para fertilizaciones, enmiendas y fitosanitarios
        -- de este producto
    materia_activa TEXT DEFAULT '', 
        -- Valor por defecto para fertilizaciones, enmiendas y fitosanitarios
        -- de este producto
    -- Cada campo de los 4 siguientes que esté a True, crea un concepto 
    -- "por defecto" al crear un precio para el producto.
    envasep BOOLEAN DEFAULT FALSE, 
    manipulacion BOOLEAN DEFAULT FALSE, 
    transporte BOOLEAN DEFAULT FALSE, 
    categoria TEXT DEFAULT '', 
    tarifa BOOLEAN DEFAULT FALSE,    -- ¿Tarifa? ¿Pone eso en el cuaderno?
    codigo TEXT DEFAULT ''  -- No único porque serán pocos los que lo lleven.
);

--------------------------------------------------------
-- Relación muchos a muchos entre productos y precios.--
--------------------------------------------------------
CREATE TABLE precio_producto_venta(
    precio_id INT REFERENCES precio, 
    producto_venta_id INT REFERENCES producto_venta
);

CREATE INDEX precioid ON precio_producto_venta(precio_id);
CREATE INDEX productoventaid ON precio_producto_venta(producto_venta_id);

-------------------------
-- Prácticas cuturales --
-------------------------
CREATE TABLE practica_cutural(
    id SERIAL PRIMARY KEY, 
    campanna_id INT REFERENCES campanna, 
    parcela_id INT REFERENCES parcela, 
    fecha DATE DEFAULT CURRENT_DATE, 
    practica TEXT DEFAULT '', 
    maquinaria TEXT DEFAULT '', 
    observaciones TEXT DEFAULT ''
);

--------------
-- Cultivos --
--------------
CREATE TABLE cultivo(
    id SERIAL PRIMARY KEY, 
    campanna_id INT REFERENCES campanna, 
    parcela_id INT REFERENCES parcela, 
    cultivo TEXT DEFAULT '', 
    variedad TEXT DEFAULT '', 
    siembra DATE DEFAULT CURRENT_DATE, 
    recoleccion_inicio DATE DEFAULT CURRENT_DATE, 
    recoleccion_fin DATE DEFAULT CURRENT_DATE, 
    hidroponico BOOLEAN DEFAULT FALSE, 
    tradicional BOOLEAN DEFAULT FALSE
);

---------------------
-- Fertilizaciones --
---------------------
CREATE TABLE fertilizacion(
    id SERIAL PRIMARY KEY, 
    campanna_id INT REFERENCES campanna, 
    parcela_id INT REFERENCES parcela, 
    producto_venta_id INT REFERENCES producto_venta DEFAULT NULL, 
    materia_activa TEXT DEFAULT '', 
    nombre TEXT DEFAULT '',  
    listado BOOLEAN DEFAULT FALSE, 
    otros BOOLEAN DEFAULT FALSE, 
    fecha DATE DEFAULT CURRENT_DATE, 
    plazo_seguridad INT DEFAULT 0, 
    dosis FLOAT DEFAULT 0.0, 
    observaciones TEXT DEFAULT ''
);

---------------
-- Enmiendas --
---------------
CREATE TABLE enmienda(
    id SERIAL PRIMARY KEY, 
    campanna_id INT REFERENCES campanna, 
    parcela_id INT REFERENCES parcela, 
    producto_venta_id INT REFERENCES producto_venta DEFAULT NULL, 
    materia_activa TEXT DEFAULT '', 
    nombre TEXT DEFAULT '', 
    listado BOOLEAN DEFAULT FALSE, 
    otros BOOLEAN DEFAULT FALSE, 
    fecha DATE DEFAULT CURRENT_DATE, 
    plazo_seguridad INT DEFAULT 0, 
    dosis FLOAT DEFAULT 0.0, 
    observaciones TEXT DEFAULT ''
);

---------------------
-- Fitosanitarios  --
---------------------
CREATE TABLE fitosanitario(
    id SERIAL PRIMARY KEY, 
    campanna_id INT REFERENCES campanna, 
    parcela_id INT REFERENCES parcela, 
    producto_venta_id INT REFERENCES producto_venta DEFAULT NULL, 
    materia_activa TEXT DEFAULT '', 
    nombre TEXT DEFAULT '', 
    listado BOOLEAN DEFAULT FALSE, 
    otros BOOLEAN DEFAULT FALSE, 
    fecha DATE DEFAULT CURRENT_DATE, 
    plazo_seguridad INT DEFAULT 0, 
    dosis FLOAT DEFAULT 0.0, 
    observaciones TEXT DEFAULT ''
);

----------------------
-- Materias activas --
----------------------
-- Catálogo de materias activas. Valen para rellenar los valores 
-- por defecto en los fitosanitarios, enmiendas y demás de las parcelas.
CREATE TABLE materia_activa(
    id SERIAL PRIMARY KEY, 
    nombre TEXT DEFAULT '', 
    nombre_comercial TEXT DEFAULT '',   -- Producto aplicado por defecto. 
    listado BOOLEAN DEFAULT FALSE, 
    otros BOOLEAN DEFAULT FALSE, 
    plazo_seguridad INT DEFAULT 0, 
    dosis FLOAT DEFAULT 0.0
);

--------------
-- Imágenes --
--------------
-- Cada fotografía es un registro con:
-- * Un campo BLOB para la imagen en sí en binario.
-- * Un campo de texto con el modo.
-- * Un entero para el alto.
-- * Un entero para el ancho.
-- * Un texto para el título.
-- * Un texto para observaciones.
CREATE TABLE imagen(
    id SERIAL PRIMARY KEY, 
    empleado_id INT REFERENCES empleado, 
    imagen BYTEA DEFAULT NULL, 
    modo TEXT DEFAULT NULL, 
    alto INT DEFAULT 0, 
    ancho INT DEFAULT 0, 
    titulo TEXT DEFAULT '', 
    observaciones TEXT DEFAULT '' 
);

----------
-- Pago --
----------
CREATE TABLE pago(
    id SERIAL PRIMARY KEY,  
    factura_compra_id INT REFERENCES factura_compra, 
    fecha DATE DEFAULT CURRENT_DATE, 
    importe FLOAT DEFAULT 0.0
);

--------------------------
-- Vencimientos de pago --
--------------------------
CREATE TABLE vencimiento_pago(
    id SERIAL PRIMARY KEY,  
    factura_compra_id INT REFERENCES factura_compra, 
    fecha DATE DEFAULT CURRENT_DATE, 
    importe FLOAT DEFAULT 0.0
);

---------------------------------
-- Series de facturas de venta --
---------------------------------
CREATE TABLE serie_facturas_venta(
    id SERIAL PRIMARY KEY, 
    prefijo TEXT DEFAULT '', 
    contador INT DEFAULT 1, 
    sufijo TEXT DEFAULT '', 
    observaciones TEXT DEFAULT '', 
    b BOOLEAN DEFAULT FALSE, 
    posiciones INT DEFAULT 1    -- Posiciones numéricas a completar con ceros.
);

--------------
-- Clientes --
--------------
CREATE TABLE cliente(
    id SERIAL PRIMARY KEY,
    nombre TEXT DEFAULT '',
    cif TEXT DEFAULT '',
    tarifa_id INT REFERENCES tarifa DEFAULT NULL,
--    contador_id INT REFERENCES contador DEFAULT NULL,
    telefono TEXT DEFAULT '',
    fax TEXT DEFAULT '', 
    direccion TEXT DEFAULT '',
    pais TEXT DEFAULT '',
    cp TEXT DEFAULT '',
    ciudad TEXT DEFAULT '',
    provincia TEXT DEFAULT '',
    iva FLOAT DEFAULT 0.16,
    direccionfacturacion TEXT DEFAULT '',
    paisfacturacion TEXT DEFAULT '',
    ciudadfacturacion TEXT DEFAULT '',
    provinciafacturacion TEXT DEFAULT '',
    cpfacturacion TEXT DEFAULT '',
    nombref TEXT DEFAULT '',    -- Nombre de facturación (por si difiere del 
                                -- del cliente en la factura).
    email TEXT DEFAULT '',      -- Dirección (o direcciones separadas por 
                                -- coma) de correo electrónico.
    contacto TEXT DEFAULT '',
    observaciones TEXT DEFAULT '',
    vencimientos TEXT DEFAULT '',   -- 30, 30-60, 90 D.F.F., etc...
    formadepago TEXT DEFAULT '',    -- Efectivo, pagaré, transferencia...
    diadepago TEXT DEFAULT '',  -- El día en que se harán los pagos realmente 
                                -- (independientemente de lo que marque
                                -- el vencimiento, el pago se puede hacer días 
                                -- antes o días después, en un día del
                                -- mes fijo) P.ej: El vencimiento cumple el 
                                -- 15 de enero pero siempre se le paga al 
                                -- proveedor los días 5 de cada mes.
                                -- De momento es texto (aunque en teoría 
                                -- sería un INT) para contemplar la posibilidad
                                -- de meter días concatenados con comas -por 
                                -- ejemplo- y así expresar que se le
                                -- pagan -por ejemplo one more time- los 
                                -- días 5 y 20 de cada mes.
--    cuenta_origen_id INT REFERENCES cuenta_origen DEFAULT NULL -- NEW! 
        -- 26/02/07. Cuenta bancaria _destino_ por defecto para transferencias.
    inhabilitado BOOLEAN DEFAULT FALSE, 
    motivo TEXT DEFAULT '',     -- Si está inhabilitado no se permitirá 
                                --hacerle más pedidos de venta.
    -- NEW! 29/07/2008 - Contador por defecto para las facturas del cliente.
    serie_facturas_venta_id INT REFERENCES serie_facturas_venta DEFAULT NULL, 
    -- NEW! 29/07/2008 - Comisión por defecto al hacer un albarán.
    comision FLOAT DEFAULT 0.0      -- Gastos de comisión.
);

---------
-- CMR --
---------
-- Documentos de transporte. Puede haber varios 
-- albaranes en un solo CMR, aunque lo normal es  
-- que por cada CMR haya un albarán.
CREATE TABLE cmr(
    id SERIAL PRIMARY KEY, 
    fecha_salida DATE DEFAULT CURRENT_DATE
);

--------------------
-- Transportistas --
--------------------
CREATE TABLE transportista(
    id SERIAL PRIMARY KEY, 
    dni TEXT DEFAULT '', 
    nombre TEXT DEFAULT '', 
    agencia TEXT DEFAULT '', 
    telefono TEXT DEFAULT '', 
    matricula TEXT DEFAULT ''
);

-------------------------
-- Albaranes de salida --
-------------------------
CREATE TABLE albaran_salida(
    id SERIAL PRIMARY KEY, 
    cmr_id INT REFERENCES cmr DEFAULT NULL, 
    cliente_id INT REFERENCES cliente, 
    transportista_id INT REFERENCES transportista, 
    fecha DATE DEFAULT CURRENT_DATE, 
    numalbaran TEXT DEFAULT '' UNIQUE NOT NULL, 
    transporte FLOAT DEFAULT 0.0,   -- Gastos por transporte.
    comision FLOAT DEFAULT 0.0,     -- Gastos de comisión.
    descarga FLOAT DEFAULT 0.0,     -- Gastos de descarga.
    bloqueado BOOLEAN DEFAULT FALSE, 
    -- Datos de envío
    nombre_envio TEXT DEFAULT '', 
    direccion TEXT DEFAULT '', 
    cp TEXT DEFAULT '', 
    ciudad TEXT DEFAULT '', 
    telefono TEXT DEFAULT '', 
    pais TEXT DEFAULT '', 
    observaciones TEXT DEFAULT ''
);

-----------------------
-- Facturas de venta --
-----------------------
CREATE TABLE factura_venta(
    id SERIAL PRIMARY KEY, 
    cliente_id INT REFERENCES cliente, 
    serie_facturas_venta_id INT REFERENCES serie_facturas_venta, 
    proveedor_id INT REFERENCES proveedor DEFAULT NULL, 
    fecha DATE DEFAULT CURRENT_DATE, 
    numfactura TEXT DEFAULT '' UNIQUE NOT NULL, 
    bloqueada BOOLEAN DEFAULT FALSE, 
    descuento FLOAT DEFAULT 0.0, 
    comision FLOAT DEFAULT 0.0, 
    transporte FLOAT DEFAULT 0.0, 
    iva FLOAT DEFAULT 0.16, 
    observaciones TEXT DEFAULT '', 
    descuento_numerico FLOAT DEFAULT 0.0, 
    concepto_descuento_numerico TEXT DEFAULT ''
); 

---------------------------
-- Vencimientos de cobro --
---------------------------
CREATE TABLE vencimiento_cobro(
    id SERIAL PRIMARY KEY, 
    factura_venta_id INT REFERENCES factura_venta NOT NULL, 
    fecha DATE DEFAULT CURRENT_DATE, 
    importe FLOAT DEFAULT 0.0
);

------------
-- Cobros --
------------
CREATE TABLE cobro(
    id SERIAL PRIMARY KEY, 
    factura_venta_id INT REFERENCES factura_venta NOT NULL, 
    fecha DATE DEFAULT CURRENT_DATE, 
    importe FLOAT DEFAULT 0.0, 
    observaciones TEXT DEFAULT ''
);

----------------
-- Documentos --
----------------
-- Documentos adjuntos al personal.
CREATE TABLE documento(
    id SERIAL PRIMARY KEY, 
    empleado_id INT REFERENCES empleado, 
    cobro_id INT REFERENCES cobro, 
    gasto_id INT REFERENCES gasto, 
    nombre TEXT DEFAULT '',     -- Nombre descriptivo
    nombre_fichero TEXT NOT NULL,   -- Nombre del fichero. SIN RUTAS.
    observaciones TEXT DEFAULT ''
);

-----------
-- Palés --
-----------
--(colección de envases -líneas de venta-)
CREATE TABLE pale(
    id SERIAL PRIMARY KEY, 
    codigo TEXT DEFAULT '' -- Generalmente en blanco.
);

---------------------
-- Líneas de venta --
---------------------
CREATE TABLE linea_de_venta(
    id SERIAL PRIMARY KEY, 
    envase_id INT REFERENCES envase, 
    producto_venta_id INT REFERENCES producto_venta, 
    albaran_salida_id INT REFERENCES albaran_salida, 
    factura_venta_id INT REFERENCES factura_venta, 
    pale_id INT REFERENCES pale, 
    tarifa_id INT REFERENCES tarifa, 
    parcela_id INT REFERENCES parcela DEFAULT NULL, 
    cantidad FLOAT DEFAULT 0.0, 
    precio FLOAT DEFAULT 0.0
);

-------------------
-- Conceptos LDV --
-------------------
-- Conceptos que componen un precio de una tarifa. Copia "snapshot" para 
-- conservar los costes del producto al facturar las líneas de venta.
CREATE TABLE concepto_ldv(
    id SERIAL PRIMARY KEY, 
    linea_de_venta_id INT REFERENCES linea_de_venta, 
    concepto_id INT REFERENCES concepto,    -- Concepto del que procede. 
        -- Puede ser NULL cuando el concepto original se haya eliminado y 
        -- la LDV relacionada haya sido facturada y, por tanto, este 
        -- conceptoLDV es inmutable.
    texto_concepto TEXT DEFAULT '', 
    importe FLOAT DEFAULT 0.0
);

------------------------------------------
-- Tabla de servicios facturables       --
-- (Servicios de facturas de terceros)  --
------------------------------------------
CREATE TABLE servicio(
    id SERIAL PRIMARY KEY,
    factura_venta_id INT REFERENCES factura_venta,
    concepto TEXT,
    cantidad FLOAT DEFAULT 1.0, 
    precio FLOAT,
    descuento FLOAT DEFAULT 0.0
);

-----------------------
-- TABLAS AUXILIARES --
-----------------------
CREATE TABLE usuario(
    id SERIAL PRIMARY KEY,
    usuario VARCHAR(16) UNIQUE NOT NULL CHECK (usuario <> ''),  
        -- Usuario de la aplicación
    passwd CHAR(32) NOT NULL,   -- MD5 de la contraseña
    nombre TEXT DEFAULT '',     -- Nombre completo del usuario
    cuenta TEXT DEFAULT '',     -- Cuenta de correo de soporte
    cpass TEXT DEFAULT '',      
        -- Contraseña del correo de soporte. TEXTO PLANO.
    nivel INT DEFAULT 5,        -- 0 es el mayor. 5 es el menor.
        -- Además de los permisos sobre ventanas, para un par de casos 
        -- especiales se mirará el nivel de privilegios para permitir volver 
        -- a desbloquear partes, editar albaranes antiguos y cosas así...
    email TEXT DEFAULT '',          
        -- NEW! 25/10/2006. Dirección de correo electrónico del 
        -- usuario (propia, no soporte).
    smtpserver TEXT DEFAULT '',     
        -- NEW! 25/10/2006. Servidor SMTP correspondiente a la dirección 
        -- anterior por donde enviar, por ejemplo, albaranes.
    smtpuser TEXT DEFAULT '',       
        -- NEW! 25/10/2006. Usuario para autenticación en el servidor 
        -- SMTP (si fuera necesario)
    smtppassword TEXT DEFAULT '',   
        -- NEW! 25/10/2006. Contraseña para autenticación en el servidor 
        -- SMTP (si fuera necesario).
    firma_total BOOLEAN DEFAULT FALSE,      
        -- NEW! 26/02/2007. Puede firmar por cualquiera de los 4 roles en 
        -- facturas de compra.
    firma_comercial BOOLEAN DEFAULT FALSE,  
        -- NEW! 26/02/2007. Puede firmar como director comercial.
    firma_director BOOLEAN DEFAULT FALSE,   
        -- NEW! 26/02/2007. Puede firmar como director general.
    firma_tecnico BOOLEAN DEFAULT FALSE,    
        -- NEW! 26/02/2007. Puede firmar como director técnico.
    firma_usuario BOOLEAN DEFAULT FALSE,    
        -- NEW! 26/02/2007. Puede firmar como usuario (confirmar total de 
        -- factura).
    observaciones TEXT DEFAULT ''   -- NEW! 26/02/2007. Observaciones.
);

CREATE TABLE modulo(
    id SERIAL PRIMARY KEY,
    nombre TEXT,
    icono TEXT,
    descripcion TEXT
);

CREATE TABLE ventana(
    id SERIAL PRIMARY KEY,
    modulo_id INT REFERENCES modulo,
    descripcion TEXT,
    fichero TEXT,           -- Nombre del fichero .py
    clase TEXT,             -- Nombre de la clase principal de la ventana.
    icono TEXT DEFAULT ''   -- Fichero del icono o '' para el icono por defecto
);

CREATE TABLE permiso(
    -- Relación muchos a muchos con atributo entre usuarios y ventanas.
    id SERIAL PRIMARY KEY,
    usuario_id INT REFERENCES usuario,
    ventana_id INT REFERENCES ventana,
    permiso BOOLEAN DEFAULT False,   
        -- Indica si tiene permiso o no para abrir la ventana.
    --    PRIMARY KEY(usuario_id, ventana_id)   SQLObject requiere que cada tabla tenga un único ID.
    lectura BOOLEAN DEFAULT False,
    escritura BOOLEAN DEFAULT False,
    nuevo BOOLEAN DEFAULT False     
        -- Nuevos permisos. Entrarán en la siguiente versión.
);

CREATE TABLE alerta(
    id SERIAL PRIMARY KEY,
    usuario_id INT REFERENCES usuario,
    mensaje TEXT DEFAULT '',
    fechahora TIMESTAMP DEFAULT LOCALTIMESTAMP(0),
    entregado BOOLEAN DEFAULT False
);

CREATE TABLE datos_de_la_empresa(
    -- Datos de la empresa. Aparecen en los informes, facturas, albaranes, 
    -- etc... Además, también sirven para determinar si un cliente es 
    -- extranjero, generar albaranes internos...
    id SERIAL PRIMARY KEY,      
        -- Lo requiere SQLObject, pero no debería haber más de un registro aquí.
    nombre TEXT DEFAULT 'FresParaíso',
    cif TEXT DEFAULT 'X-00.000.000',
    dirfacturacion TEXT DEFAULT 'Dirección facturación', 
    cpfacturacion TEXT DEFAULT '00000',
    ciudadfacturacion TEXT DEFAULT 'Ciudad facturación',
    provinciafacturacion TEXT DEFAULT 'Provincia facturación',
    direccion TEXT DEFAULT 'Dirección postal',
    cp TEXT DEFAULT '00000',
    ciudad TEXT DEFAULT 'Ciudad',
    provincia TEXT DEFAULT 'Provincia',
    telefono TEXT DEFAULT '000000000',
    fax TEXT DEFAULT '000000000',
    email TEXT DEFAULT 'usuario@dominio.com', 
    paisfacturacion TEXT DEFAULT 'España', 
    pais TEXT DEFAULT 'España', 
    telefonofacturacion TEXT DEFAULT '000000000', 
    faxfacturacion TEXT DEFAULT '000000000',
    nombre_responsable_compras TEXT DEFAULT 'Nombre Apellido1 Apellido2', 
    telefono_responsable_compras TEXT DEFAULT '000000000', 
    nombre_contacto TEXT DEFAULT 'Nombre Apellido1 Apellido2', 
    registro_mercantil TEXT DEFAULT 'Inscrita en el Registro Mercantil de XXX, Tomo XXX - Folio XXX - Hoja nº XX-00000 - C.I.F. X-00000000', 
    email_responsable_compras TEXT DEFAULT 'usuario@dominio.com', 
    logo TEXT DEFAULT 'logo_fresparaiso.png',  
        -- Nombre de fichero (solo nombre, no ruta completa) de la imagen 
        -- del logo de la empresa.
    logo2 TEXT DEFAULT 'logo_fresparaiso.png',  -- Nombre del logo alternativo
    bvqi BOOLEAN DEFAULT FALSE,  
        -- True si hay que imprimir el logo de calidad certificada BVQI
    -- Dirección para albaran alternativo (albaran composan)
    nomalbaran2 TEXT DEFAULT '', 
    diralbaran2 TEXT DEFAULT '', 
    cpalbaran2 TEXT DEFAULT '', 
    ciualbaran2 TEXT DEFAULT '', 
    proalbaran2 TEXT DEFAULT '', 
    telalbaran2 TEXT DEFAULT '', 
    faxalbaran2 TEXT DEFAULT '', 
    regalbaran2 TEXT DEFAULT '', 
    irpf FLOAT DEFAULT 0.0, 
        -- NEW! 10/04/07. Si -0.15 aparecerá el campo IRPF en las facturas 
        -- de venta para descontarse de la base imponible
    es_sociedad BOOLEAN DEFAULT TRUE,   
        -- NEW! 02/05/07. Si es True la empresa es una sociedad. Si False, la 
        -- empresa es persona física o persona jurídica. En los impresos se 
        -- usará "nombre" como nombre comercial y nombre_contacto como nombre 
        -- fiscal de facturación.
        -- También servirá para discernir si mostrar servicios y transportes 
        -- en albaranes y si valorar o no albaranes en el PDF generado al 
        -- imprimir.
        -- OJO: También se usa para escribir "FÁBRICA" o "TIENDA" en los 
        -- pedidos de compra, etc.
    logoiso1 TEXT DEFAULT '',   
        -- NEW! 27/06/07. Si bvqi es True en algunos impresos aparecerá 
        -- este logo.
    logoiso2 TEXT DEFAULT ''   
        -- NEW! 27/06/07. Si bvqi es True en algunos impresos aparecerá 
        -- este logo.
);

----------------------------------------------------
-- Estadísticas de ventanas abiertas por usuario. --
----------------------------------------------------
-- NEW! 16/12/2007 --
---------------------
CREATE TABLE estadistica(
    id SERIAL PRIMARY KEY, 
    usuario_id INT REFERENCES usuario, 
    ventana_id INT REFERENCES ventana,
    veces INT DEFAULT 0, 
    ultima_vez TIMESTAMP DEFAULT LOCALTIMESTAMP(0)
);


