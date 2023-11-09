import os
import sys
import pytest
import pyodbc
from dotenv import load_dotenv
from api_request_for_tests import get_single_pay

current_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_directory))
load_dotenv()

from conciliador_mp.mp_utils import param_getter

# Define el fixture que manejará la conexión a la base de datos
@pytest.fixture(scope="session")
def db_connection():
    server = os.getenv('TST_SERVER')
    db = os.getenv('DB')
    usr = os.getenv('TUSR')
    pas = os.getenv('TPASS')

    connection_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};Server={server};Database={db};UID={usr};PWD={pas};'
    connection = pyodbc.connect(connection_str)
    cursor = connection.cursor()
    
    # Te devuelve un cursor y una conexión para usar en tus pruebas
    yield cursor, connection

    # Después de las pruebas, cierra la conexión y el cursor
    cursor.close()
    connection.close()


payments = [
        '66041643775',
        '66201361486',
        '66028465159',
        '66199333742',
        '66197434780',
        '66197358844',
        '66024218145',
        '66023939283',
        '66196265166',
        '66120313704',
        '65973145875',
        '65973364331',
        '66201662948',
        '65956319237',
        '65944588841',
        '66017573321'
    ]

def template_method(payment):
    response = get_single_pay(os.getenv('TEST_API'), payment)
    data = param_getter(None, 0, response, True)
    assert data[0] != ''  # identification
    assert data[1] != ''  # transaction_amount
    assert data[2] != ''  # date_created
    assert data[3] == 'approved'  # status
    assert data[4] != '{}'  # metadata
    assert data[5] != 'pos_payment'  # operation_type
    assert data[6] not in ['Venta Presencial', 'Producto', 'Pago Bank Transfer QR V3 3.0']  # description

@pytest.mark.parametrize("payment", payments)
def test_payment(payment):
    template_method(payment)
