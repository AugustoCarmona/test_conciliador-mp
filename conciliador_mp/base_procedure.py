from datetime import datetime, timedelta
import os
import pyodbc

import mp_utils as utils


logger = utils.load_logger()

class BaseProcedure():
    """ Clase Base para la ejecución de procedimientos en la base de datos y llamadas a la API.
    
    Atributos:
        ACCESS_TOKEN (str): Token de acceso para la API.
        SERVER (str): Dirección del servidor de la base de datos.
        DB (str): Nombre de la base de datos.
        USR (str): Nombre de usuario para la base de datos.
        PASS (str): Contraseña para la base de datos.
        begin_date (datetime): Fecha de inicio para la consulta.
        end_date (datetime): Fecha de fin para la consulta.
        cursor (pyodbc.Cursor): Cursor para interactuar con la base de datos.
        connection (pyodbc.Connection): Conexión a la base de datos.
        lote (int): Número de lote.
        transfer_ids (dict): Diccionario para guardar IDs de transferencia.
    """

    def __init__(self, entorno: str) -> None:
        """ Inicializa los parámetros de la clase.

        Argumentos:
            entorno (str): El entorno en el que se está ejecutando ('TESTING' o 'PRODUCCION').
        """
        self.ACCESS_TOKEN, self.SERVER, self.DB, self.USR, self.PASS = self.__get_secrets(entorno)
        self.begin_date, self.end_date, self.cursor, self.connection = self.__setup_data()
        self.lote = utils.generar_lote(self.cursor)
        self.transfer_ids = {}

        logger.info(f'Servidor: {self.SERVER}')
        logger.info(f'Base de datos: {self.DB}')


    # ----------------- Inicio set up
    def __get_secrets(self, entorno: str) -> tuple:
        """ Obtiene secretos de las variables de entorno.
        
        Argumentos:
            entorno (str): El entorno en el que se está ejecutando ('TESTING' o 'PRODUCCION').
        
        Retorno:
            tuple: Retorna una tupla con los secretos obtenidos.
        """
        usr = ''
        pas = ''
        if entorno == 'TESTING':
            servidor = os.getenv('TST_SERVER')
            logger.info(f"Verificacion del servidor obtenido de variables de entorno: {servidor}")
            usr = os.getenv('TUSR')
            pas = os.getenv('TPASS')
        else:
            servidor = os.getenv('PRD_SERVER')
            logger.info(f"Verificacion del servidor obtenido de variables de entorno: {servidor}")
            usr = os.getenv('PUSR')
            pas = os.getenv('PPASS')
        return os.getenv('ACCESS_TOKEN'), servidor, os.getenv('DB'), usr, pas


    def __setup_data(self) -> tuple:
        """ Configura la conexión a la base de datos y establece las fechas de inicio y fin.
        La fecha de inicio se basa en la ultima fecha procesada en TransaccionesConciliar.
        Adapta las fechas al formato admitido por Mercado Pago.

        Retorno:
            tuple: Retorna una tupla con la fecha de inicio, la fecha de fin, el cursor y la conexión a la base de datos.
        """
        connection_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};Server={self.SERVER};Database={self.DB};UID={self.USR};PWD={self.PASS};'
        logger.debug(f"{connection_str}")
        try:
            connection = pyodbc.connect(connection_str)
            cursor = connection.cursor()
        except Exception as e:
            connection = cursor = None
            logger.debug(f"{e}")
            logger.error("No se ha podido conectar a la base de datos.")

        query = utils.read_sql_file(os.path.join('sql', 'ObtenerUltimaFecha.sql'))
        cursor.execute(query)
        ultima_fecha = cursor.fetchone()[0]
        logger.info(f'Ultima fecha ingresada: {ultima_fecha}')

        ultima_fecha = ultima_fecha + timedelta(seconds=1)
        begin_date = ultima_fecha.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '-04:00'
        end_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '-04:00'
        logger.debug(f'Fecha de inicio: {begin_date}')
        logger.debug(f'Fecha de finalizacion: {end_date}')
        return begin_date, end_date, cursor, connection
    # ----------------- Fin set up    


    def __get_payments_from_api(self) -> None:
        """ Obtiene pagos desde la API y los procesa.
        
        Realiza una serie de llamadas a la API para obtener y procesar pagos.
        """
        offset = counter = 0  # offset incrementará el paginado para poder procesar iterativamente los pagos a través de la API si hay más de 1000 pagos.
        URL = f"{os.getenv('URLA')}{self.ACCESS_TOKEN}{os.getenv('URLB')}{self.begin_date}&end_date={self.end_date}&limit=1000&offset={offset}"
        
        while True:
            results = utils.call_api(URL)
            if not results:
                break
            for result in results:
                counter += 1
                try:
                    utils.param_getter(self.cursor, self.lote, self.transfer_ids, result)
                    self.connection.commit()
                except Exception as e:
                    logger.error(f"No se pudo obtener los parametros suficientes del pago o insertarlos a la base de datos: {e}")
                    raise
            offset += 1000
            URL = f"{os.getenv('URLA')}{self.ACCESS_TOKEN}{os.getenv('URLB')}{self.begin_date}&end_date={self.end_date}&limit=1000&offset={offset}"


    def __force_transaction(self) -> None:
        """ Invoca al stored procedure sp_ProcesarTransaccionesNoInformadas para forzar todos los pagos conciliados."""
        query = 'EXEC sp_ProcesarTransaccionesNoInformadas;'
        try:
            self.cursor.execute(query)
        except Exception as e:
            logger.error(f"Error en execute: {e}")
        # inserts = self.cursor.fetchall()
        # formatted_inserts = [f"Transaccion: {record[0]}, Cuit: {record[1]}, Monto: {record[2]}, FechaTransaccion: {record[3]}," for record in inserts]
        # logger.info(f'Cantidad de pagos insertados: {len(inserts)}')
        # logger.info(f'Pagos insertados: {formatted_inserts}')


    # ----------------------------------------------------------------------------------------------------------------------------------------------
    def run(self):
        """
        Ejecuta el procedimiento principal.
        
        Este método es el punto de entrada para la ejecución de toda la clase. Realiza todas las operaciones necesarias en orden.
        """
        try:
            self.__get_payments_from_api()
            forzar = os.getenv('FORZAR_TRANSACCIONES_CONCILIADAS')
            if forzar == 's':
                self.__force_transaction()

        except:
            logger.error("Error al intentar obtener los pagos de la API:")
            raise

        finally:
            if self.connection:
                self.connection.close()
