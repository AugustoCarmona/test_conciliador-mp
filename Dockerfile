FROM laudio/pyodbc

# Instala el controlador de SQL Server
RUN apt-get update && apt-get install -y gcc freetds-dev

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

CMD ["python", "conciliador-mp/main.py"]
