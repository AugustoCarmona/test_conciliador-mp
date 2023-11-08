import unittest
import os
import sys
from dotenv import load_dotenv
from api_request_for_tests import get_single_pay

current_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_directory))
load_dotenv()

from conciliador_mp.mp_utils import param_getter


def setup_db():
    """ Prepara una conexión a la base de datos para realizar pruebas.
    """
    test_api = os.getenv('TEST_API')
    return test_api


class TestParamGetter(unittest.TestCase):

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

    def setUp(self) -> None:
        self.test_api = setup_db()

    def template_method(self, payment):
        response = get_single_pay(self.test_api, payment)
        data = param_getter(None, 0, response, True)
        self.assertNotEqual(data[0], '')  # identification
        self.assertNotEqual(data[1], '')  # transaction_amount
        self.assertNotEqual(data[2], '')  # date_created
        self.assertEqual(data[3], 'approved')  # status
        self.assertNotEqual(data[4], '{}')  # metadata
        self.assertNotEqual(data[5], 'pos_payment')  # operation_type
        self.assertNotEqual(data[6], 'Venta Presencial')  # description
        self.assertNotEqual(data[6], 'Producto')  # description
        self.assertNotEqual(data[6], 'Pago Bank Transfer QR V3 3.0')  # description


for i, payment in enumerate(TestParamGetter.payments):
        test_func = lambda self, p=payment: TestParamGetter.template_method(self, p)
        setattr(TestParamGetter, f'test_payment_{i}', test_func)


if __name__ == "__main__":
    unittest.main()