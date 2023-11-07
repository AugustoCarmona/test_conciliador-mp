# Mercado pago - Conciliador de Transacciones

![Mercado Pago](https://http2.mlstatic.com/frontend-assets/home-landing/logo-mercadopago.jpg)

## ¿Cómo correr el conciliador?

> Para poder ejecutar el servicio, una vez que haya sido descargado del repositorio de GitHub, es necesario seguir los pasos que se indican a continuación:

1. Crear un entorno virtual.
Es importante crear un entorno virtual en la carpeta principal del proyecto para gestionar las dependencias del proyecto.
```python
$ python -m venv nombre_del_entorno
```

Una vez creado se deberá activar dicho entorno con el siguiente comando.
```python
$ .\nombre_del_entorno\Scripts\activate
```

2. Instalar dependencias del proyecto.
```python
$ pip install -r requirements.txt
```

3. Archivo .env.
Será necesario crear un archivo llamado `.env`, el cual contendrá información sobre las variables de entorno que utilizará el servicio para conectarse a la base de datos y a la api de Mercado Pago. Dentro de dicho archivo se puede copiar y pegar los siguientes datos (siempre respetando el nombre de la variable y completándola con su información correspondiente):

    ```
    # los siguientes datos son solo de caracter ilustrativo

    # API
    URLA=https://api.mercadopago.com/v1/payments/search?access_token=
    URLB=&range=date_created&begin_date=

    # Secretos
    ACCESS_TOKEN=XXXXXXXXXXXXXXXXXXXXXXXXXXX
    PRD_SERVER=192.168.1.1
    TST_SERVER=SVR-SQL_TESTING\NEMESIS
    DB=OSDEPYMPROD
    TUSR=conciliador
    TPASS=fLjG86kN3
    PUSR=conciliador
    PPASS=fLjG86kN3
    ENTORNO=p
    FORZAR_TRANSACCIONES_CONCILIADAS=s
    ```

4. Comando de ejecución.
    1. Dentro del directorio del proyecto, navegar a la carpeta con el mismo nombre "conciliador-mp" y ejecutar el comando.
    Comando para la ejecución por defecto (Producción):
    ```python
    $ python main.py
    ```

    2. Comando para ejecutar en Testing:
    ```python
    $ python main.py --env t
    ```

---
Una vez que el servicio haya corrido se habrán cargado todas las transacciones de Mercado Pago disponibles desde el último período hasta la fecha actual a la tabla mercado_pago."TransaccionesConciliar".

### Conciliador.sql
Luego de realizada dicha cargar el script contenido en la carpeta sql/dependencies llamado Conciliador.sql será el encargado de hacer una comparación entre los registros de la tabla "TransaccionesConciliar" y las tablas "MercadoPagoTransacciones" y "TransaccionesPoliconsultorios", enviando un mail que contenga informacion por cada pago que exista en "TransaccionesConciliar" y no exista en alguna de las otras dos tablas.

Una vez informados dichos pagos faltantes podrán ser forzados a su base de datos correspondiente sin problema.

---
## Módulos del código

### conciliador-mp
Contiene la lógica principal del servicio.
- main.py: se ocupa de recibir el comando de ejecución para establecer un entorno de producción o testing segun corresponda, instanciar al procedimiento base, y llamar a su método de ejecución.
- base_procedure.py: contiene la lógica principal del servicio. Realiza una consulta iterativa (por paginación) a la API de Mercado Pago hasta haber obtenido todos los pagos procesados a la fecha. Una vez obtenidos dichos pagos los inserta en la tabla "TransaccionesConciliar".

##### Subdirectorios:
- utils: contiene funciones que fueron modularizadas a fin de evitar codigo repetido y mantener buenas prácticas de desarrollo
    - get_query.py: obtiene la query solicitada de la carpeta "sql" y la disponibiliza para consultarla.
    - load_logger.py: disponibiliza el logger para el registro del servicio. Guarda los logs en /logs/app.logs.

### SQL
Contiene los archivos .sql necesarios para que el servicio realice consultas a la base de datos.
- ObtenerUltimaFecha: obtiene la última fecha en la que se tiene registro de haberse ejecutado el servicio.
- GenerarLote: genera un número de lote nuevo para la carga actual.
- ObtenerLote: obtiene el número de lote generado.

##### Subdirectorios:
- Dependencies: contiene aquellos archivos .sql que serán necesarios para que las consultas del conciliador se puedan realizar.
    - CreateTables.sql: crea la tabla TransaccionesConciliar y sus indices correspondientes en caso de que esta no exista
    - Conciliador: Se ocupa de comparar los valores de "TransaccionesConciliar", "MercadoPagoTransacciones" y "TransaccionesPoliconsultorios" e informa aquellos que no existan en alguna de las dos últimas tablas.

---
[Documentación de Mercado Pago](https://www.mercadopago.com.ar/developers/es/reference/payments/_payments_search/get) utilizada para el desarrollo de este servicio.


*Desarrollado por Augusto Carmona.*

<!-- Actualizado al 12/09/2023 -->