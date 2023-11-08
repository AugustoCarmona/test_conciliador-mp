import os
import logging
import re

import requests

from datetime import datetime


def load_logger() -> logging.Logger:
    """ Configura y devuelve un objeto logger para registrar eventos.
    
    Returns:
        logging.Logger: Objeto logger configurado para registrar eventos con timestamp en un archivo.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{timestamp}_run.log"

    directorio = os.path.join('logs')
    if not os.path.exists(directorio):
        os.mkdir(directorio)

    logging.basicConfig(level=logging.DEBUG, filename=os.path.join(directorio, log_filename), filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    return logger


def call_api(URL: str) -> list:
    """ Realiza la llamada a la API y devuelve los resultados.
    
    Argumentos:
        URL (str): URL de la API a la que se va a llamar.
    
    Retorno:
        list: Lista de resultados obtenidos de la API.
    """
    logger = load_logger()
    try:
        response = requests.get(URL)
        logger.info(f'Se conecto a la API: {URL}. Response: {response}')
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f'Error al obtener la información de la API: {e}\n URL:{URL}')
    return response.json()['results']


def read_sql_file(filename):
    with open(filename, 'r') as file:
        return file.read()


def generar_lote(cursor: object) -> int:
    """ Genera y obtiene el número de lote.
    
    Argumentos:
        cursor (obj): Cursor a la base de datos.

    Retorno:
        int: Retorna el número de lote generado.
    """
    logger = load_logger()
    query = read_sql_file(os.path.join('sql', 'GenerarLote.sql'))
    cursor.execute(query)
    logger.debug(f'Query "GenerarLote":\n{query}')
    
    query = read_sql_file(os.path.join('sql', 'ObtenerLote.sql'))
    cursor.execute(query)
    lote = cursor.fetchone()[0]
    logger.debug(f'Query "ObtenerLote":\n{query}')
    logger.info(f'Lote: {lote}')
    
    return lote


# -------------------------------------------------------------------------------------------------------------
def insert_into_query(id_transaccion, identification, transaction_amount, date_created, description, metadata, operation_type, status, status_detail, lote):
    query = """
    INSERT INTO mercado_pago.TransaccionesConciliar (
        id_transaccion,
        identification,
        transaction_amount,
        date_created,
        description,
        metadata,
        operation_type,
        status,
        status_detail,
        lote,
        cuit
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, Null);
    """
    params = (id_transaccion, identification, transaction_amount, date_created, description, metadata, operation_type, status, status_detail, lote)
    return query, params


# -------------------------------------------------------------------------------------------------------------
def check_cc(cursor: object, cuit: str) -> bool:
    """ Verifica si el cuit existe en la base de datos.
    
    Argumentos:
        cursor (obj): Cursor a la base de datos.
        cuit (str): Cuit a verificar.

    Retorno:
        bool: Retorna True si el cuit existe en la base de datos, False en caso contrario.
    """
    query = f"""
    IF EXISTS (
        SELECT * FROM cuentascorrientes
        WHERE NroCtaCte = '{cuit}'
    )
    BEGIN
        SELECT 1
    END
    """
    try:
        cursor.execute(query)
        return cursor.fetchone()[0] == 1
    except Exception as e:
        logging.debug(f'No se pudo efectuar la query "check CC": {e}')
        return False


# -------------------------------------------------------------------------------------------------------------
def send_mail(cursor:object, id_transaccion: str, identification: str, transaction_amount: str, operation_type: str, status: str) -> None:
    """ Envia un mail con el mensaje especificado.

    Argumentos:
        message (str): Mensaje a enviar.
    """
    message = f"""
        Estimado, se informa que la transacción {id_transaccion} no pudo ser conciliada, ya que no existe en la base de datos
        alguna cuenta corriente que se corresponda con el Cuit {identification}.

        Monto: {transaction_amount}
        Tipo de operación: {operation_type}
        Estado: {status}
    """

    get_mails = f"""
    SELECT email_address FROM Operators
    WHERE id = 283
    """
    cursor.execute(get_mails)
    mails = cursor.fetchall()

    query= f"""
    EXEC msdb.dbo.sp_send_dbmail
    @profile_name = 'Nemesis',
    @recipients = '{mails}',
    @copy_recipients = 'acarmona@osdepym.com.ar',
    @subject = 'Transferencia no conciliada',
    @body = '{message}';
    """

    cursor.execute(query)


# -------------------------------------------------------------------------------------------------------------
def param_getter(cursor: object, lote: int, result: dict, is_test: bool = False) -> None:
    """ Extrae parámetros de un diccionario resultante de una API y ejecuta una operación de inserción en la base de datos.

    Args:
        cursor (obj): Cursor a la base de datos.
        lote (int): Lote de la transacción.
        result (dict): Diccionario que contiene la información de una transacción.
    """
    logger = load_logger()

    id_transaccion = str(result.get('id', ''))
    identification = str(result.get('payer', {}).get('identification', {}).get('number', {})) # payer -> identification -> number
    transaction_amount = str(result.get('transaction_amount', ''))
    date_created = str(result.get('date_created', ''))[:-6]
    description = str(result.get('description', ''))
    metadata = str(result.get('metadata', '')).strip("\"").replace("'", "\"")
    operation_type = str(result.get('operation_type', ''))
    status = str(result.get('status', ''))
    status_detail = str(result.get('status_detail', ''))
    external_reference = str(result.get('external_reference', ''))
    payment_link = str(result.get('point_of_interaction', {}).get('business_info', {}).get('sub_unit', ''))


    # Verifica que se trate de un pago por link de pago
    if payment_link == 'payment_link':
        metadata = 'link de pago'

    # Verifica que se trate de un pago de pago televentas
    if metadata == '{}' and external_reference and re.match("^\d+$", external_reference):
        identification = external_reference
        operation_type = 'Pago Televentas'
        description = 'Pago Televentas'
        metadata = 'Pago Televentas'

    # Se evita ingresar los pagos no aprovados con metadata vacía  o provenientes de
    # ventas presenciales, ventas de producto, qr o policonsultorios (pos payment).
    if (
        identification and transaction_amount and date_created and
        status == 'approved' and
        metadata != '{}' and
        operation_type != 'pos_payment' and
        all(substring not in description for substring in ['Venta presencial', 'Producto', 'Pago Bank Transfer QR V3 3.0'])
    ):
        
        if identification == 'None':
            pattern = r'"cuit_rp":\s*"*"?(\d+)"*"?'
            match = re.search(pattern, metadata)

            if match:
                identification = match.group(1)

        # Verifica para las transacciones que el cuit se corresponda con una cuenta corriente existente.
        if operation_type == 'money_transfer' and description != 'Devolución de Percepciones Generales':
            print("Ojo la transacción: ", id_transaccion)
            if check_cc(cursor, identification) == False:
                logger.warning(f"El cuit {identification} no existe en la base de datos.")
                send_mail(id_transaccion, identification, transaction_amount, operation_type, status)
                return

        if not is_test:
            query, params = insert_into_query (
                id_transaccion, identification,
                transaction_amount, date_created,
                description, metadata,
                operation_type, status,
                status_detail, str(lote)
            )
            try:
                cursor.execute(query, params)
                logger.info(f"Valores insertados: {params}")
            except Exception as e:
                logger.warning(f"{params}")
                logger.error(f"Hubo un fallo al ejecutar el insert: {e}")

    return (
        identification,
        transaction_amount,
        date_created,
        status,
        metadata,
        operation_type,
        description
    )