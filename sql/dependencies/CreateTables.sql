-- Modificación a mp.transacciones para poder utilizar una FK
ALTER TABLE mercado_pago.MercadoPagoTransacciones
ADD PRIMARY KEY (ID_MercadoPagoTransacciones);

-- Crear Tabla
CREATE TABLE mercado_pago.TransaccionesConciliar (
	id INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
	id_transaccion VARCHAR(11),
	identification VARCHAR(20),
	transaction_amount DECIMAL(10,2),
	date_created DATETIME,
	description VARCHAR(100),
	metadata VARCHAR(MAX),
	operation_type VARCHAR(20),
	status VARCHAR(30),
	status_detail VARCHAR(30),
	encontrado INT DEFAULT NULL,
	fecha_creacion DATETIME DEFAULT GETDATE(),
	id_identity VARCHAR(50),
	lote VARCHAR(10),
	cuit VARCHAR(11),
	Procesado INT DEFAULT (0),
	IdMPTransacciones INT FOREIGN KEY REFERENCES mercado_pago.MercadoPagoTransacciones (ID_MercadoPagoTransacciones),
);

CREATE INDEX idx_TransaccionesConciliar_id_transaccion 
ON mercado_pago.TransaccionesConciliar (id_transaccion);

-- Formato de los inserts
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
	cuit)
VALUES ('
	{id_transaccion}',
	'{identification}',
	'{transaction_amount}',
	'{date_created}',
	'{description}',
	'{metadata}',
	'{operation_type}',
	'{status}',
	'{status_detail}',
	0,
	Null)

-- Generar numero de lote
INSERT INTO Generadores (IdGenerador, Semilla, Incremento, PermiteReservarRangos)
VALUES ('ConciliadorMPLote', 1, 0, 0)
