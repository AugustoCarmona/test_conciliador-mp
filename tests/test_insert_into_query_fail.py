import unittest
import pyodbc
import os
import sys
from dotenv import load_dotenv
from api_request_for_tests import get_single_pay

current_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_directory))
load_dotenv()

from conciliador_mp.mp_utils import param_getter


def setup_db():
    """ Prepara un cursor y una conexión a la base de datos para realizar pruebas.
    """
    server = os.getenv('TST_SERVER')
    db = os.getenv('DB')
    usr = os.getenv('TUSR')
    pas = os.getenv('TPASS')
    test_api = os.getenv('TEST_API')

    connection_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};Server={server};Database={db};UID={usr};PWD={pas};'
    connection = pyodbc.connect(connection_str)
    cursor = connection.cursor()
    
    return cursor, connection, test_api


class TestParamGetter(unittest.TestCase):

    payments = [
        # pos_payment (5)
        '64457981328',
        '64300395971',
        '64298960943',
        '64452873412',
        '64450735988',

        # not approved (6)
        '61219682089',
        '61360967495',
        '61379013107',
        '60855809113',
        '61169287727',
        '60291488545',

        '65973364331'
    ]

    def setUp(self) -> None:
        self.cursor, self.connection, self.test_api = setup_db()

    def template_method(self, payment):
        response = get_single_pay(self.test_api, payment)
        data = param_getter(self.cursor, 0, response["results"][0])

        self.assertTrue(
            # - generalmente pagos no approved no tienen identification
            # - usualmente venta presencial siempre es pos_payment
            # - si identification_type viene null no habrá description ambigua
            # por lo tanto los tres primeros podrían no tenerse en cuenta para condicionar (en especial casos 2 y 3)
            # data[0] == '' or  # identification
            # data[1] == '' or  # transaction_amount
            # data[2] == '' or  # date_created
            # data[4] == '{}' or  # metadata
            # data[6] == 'Venta Presencial' or data[6] == 'Producto' or data[6] == 'Pago Bank Transfer QR V3 3.0' or  # description
            
            # estos deberían ser los casos filtro
            data[3] != 'approved' or  # status
            data[5] == 'pos_payment' or  # operation_type
            data[7] != True  # insert exitoso
        )


for i, payment in enumerate(TestParamGetter.payments):
        test_func = lambda self, p=payment: TestParamGetter.template_method(self, p)
        setattr(TestParamGetter, f'test_payment_{i}', test_func)


if __name__ == "__main__":
    unittest.main()