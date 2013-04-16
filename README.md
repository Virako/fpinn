# fpinn

Software to manage the production of FresParaiso


## Requirements

For install fpinn, you need install python-glade2 python-sqlobject python-psycopg2:
    sudo apt-get install python-glade2 python-sqlobject python-psycopg2

## Configure

### Create user and database

Create a user that manage database:

    $ sudo adduser ufpinn

Enter with the postgres user:

    $ sudo su postgres

Create ROLE and database:

    $ psql

    =# CREATE USER ufpinn with password 'ufpinn';

    $ createdb fpinn -O ufpinn


### Insert tables to the database

    $ psql fpinn -U ufpinn < bd/tablas.sql

### Add config to the file ginn.conf

Configuring our server:

    You need change the file framework/ginn.conf

### Create a user in the databade

I recomended install pgadmin3and add user:

    $ sudo aptget install pgadmin3

User example:

    $ test  098f6bcd4621d373cade4e832627b4f6    Test user   test@gmail.com  test    0       smpt.gmail.com  test@gmail.com  test    t   t   t   t   t   Test user. Not use in production.

### Send mail

You need put your email and password in the file utilidades/enviar\_correo.py

Line 34 and 35.

### Execute

    $ python formularios/menu.py

## Some errors

Problem: psql: FATAL:  la autentificaci?n Peer fall? para el usuario <<ufpinn>>

SOL: modificate the /etc/postgresql/9.1/main/pg\_hba.conf Change peer by md5.

# license

Fpinn is licensed under [GPL v2](http://www.gnu.org/licenses/gpl-2.0.html)
