CREATE PROCEDURE sp_ForzarTransaccion
	@cuit_resp_pago VARCHAR(20),-- CUIT
	@Importe MONEY, -- IMPORTE
	@fechaOperacion DATETIME, -- FECHA DE OPERACION
	@ID_TransaccionMP VARCHAR(100) -- ID DE TRANSACCION
AS
	SET NOCOUNT ON;
	DECLARE
		@error VARCHAR(200),
		@mensaje VARCHAR(250) 

	IF NOT EXISTS (
			SELECT *
			FROM cuentascorrientes
			WHERE NroCtaCte = @cuit_resp_pago
		)
	BEGIN
		SELECT 'No se encuentra la cuenta corriente'
		GOTO FIN
	END

	IF EXISTS (
			SELECT *
			FROM mercado_pago.MercadoPagoTransacciones a
			WHERE a.ID_Transaccion = @ID_TransaccionMP
		)
	BEGIN
		SELECT 'Ya existe esa transaccion'
		GOTO fin
	END

	EXEC mercado_pago.spo_RegistrarCobranza
		@cuit_resp_pago , 
		@Importe , 
		@fechaOperacion , 
		@ID_TransaccionMP , 
		@error OUT, 
		@mensaje OUT

	SELECT 
		@error  OUT, 
		@mensaje OUT

	FIN:
	-- SELECT * FROM mercado_pago.MercadoPagoTransacciones WHERE cuit = @cuit_resp_pago