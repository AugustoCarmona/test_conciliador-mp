#!/bin/bash

sudo docker run -d \
   -e TZ=America/Argentina/Buenos_Aires --name conciliador-mp \
   -e ACCESS_TOKEN=APP_USR-3927187699882632-031520-5ec1fd871bdcd92063bfde82fe89d533-728910719 \
   -e PRD_SERVER=192.168.2.39 \
   -e TST_SERVER=SVR-SQL_TESTING\NEMESIS \
   -e DB=OSDEPYMPROD \
   -e TUSR=conciliador-mp \
   -e TPASS=testing \
   -e PUSR=conciliador-mp \
   -e PPASS=jP#2$w9@R&5zT!v8 \
   -e ENTORNO=t \
   -e FORZAR_TRANSACCIONES_CONCILIADAS=S \
   -v /var/volumenesDocker/conciliador-mp/logs/:/app/logs/ \
   -t osdepymdockerhub/conciliador-mp:1.0.0
