import datetime
import os
import time as tm
from dotenv import load_dotenv
import schedule
from mp_utils import load_logger
import base_procedure

load_dotenv()
logger = load_logger()

def job() -> None:
    """ Realiza la tarea programada para la extraccion y procesamiento de datos.
    """
    try:
        start_time = tm.time()
        logger.info("Iniciando aplicacion")
        entorno = 'TESTING' if os.getenv('ENTORNO') == 't' else 'PRODUCCION'
        logger.info(f'Ejecutando en {entorno}')
        retriever = base_procedure.BaseProcedure(entorno)
        retriever.run()
        end_time = tm.time()
        elapsed_time = end_time - start_time
        logger.info(f'Tiempo de extraccion: {elapsed_time} segundos')
        act_time = datetime.datetime.now().strftime("%H:%M:%S")
        logger.info(f"Ultima ejecucion: {act_time}.\nEstado: ejecucion exitosa.")
    except:
        act_time = datetime.datetime.now().strftime("%H:%M:%S")
        logger.info(f"Ultima ejecucion: {act_time}.\nEstado: ejecucion fallida.")

def main() -> None:
    """ Programa la ejecucion recurrente de la tarea especificada.
    """
    logger.info("Conciliador de pagos - Osdepym/Mercado Pago")
    schedule.every(10).minutes.do(job)
    while True:
        schedule.run_pending()
        tm.sleep(1)

if __name__ == "__main__":
    """ Punto de entrada del script. Ejecuta la tarea una vez al inicio.
    """
    job()
    main()
