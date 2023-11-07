CREATE PROCEDURE sp_ProcesarTransaccionesNoInformadas
AS
BEGIN
	--------------------- Obtener pagos no procesados
	SELECT DISTINCT TC.id Id,
					TC.id_transaccion IdTransaccion,
					TC.identification Cuit,
					TC.transaction_amount Monto,
					TC.date_created FechaTransaccion
	INTO #tmp
	FROM mercado_pago.TransaccionesConciliar AS TC
	WHERE NOT EXISTS (
		SELECT 1
		FROM mercado_pago.MercadoPagoTransacciones AS MP
		WHERE MP.id_transaccion = TC.id_transaccion
	)
	AND NOT EXISTS (
		SELECT 1
		FROM mercado_pago.TransaccionesPoliconsultorios AS PL
		WHERE PL.id_transaccion = TC.id_transaccion
	)
	AND TC.Procesado = 0
	ORDER BY TC.date_created DESC;
	--------------------- Fin obtener pagos

	--------------------- Forzar Pagos
	IF (SELECT COUNT(*) FROM #tmp) > 0
	BEGIN
		ALTER TABLE #tmp ADD Informado INT NOT NULL DEFAULT(1);
		UPDATE MP
		SET Informado = 1
		FROM mercado_pago.TransaccionesConciliar MP
		WHERE EXISTS (SELECT t.id FROM #tmp t WHERE t.Id = MP.id AND t.Informado = 1); -- marcar los pagos informados
	END;

	UPDATE mercado_pago.TransaccionesConciliar SET Procesado = 1 WHERE Procesado = 0; -- marcar que los pagos fueron procesados


	DECLARE @cuit_resp_pago VARCHAR(20),
			@Importe MONEY,
			@fechaOperacion DATETIME,
			@ID_TransaccionMP VARCHAR(100)

	DECLARE cur CURSOR FOR 
	SELECT Cuit, Monto, FechaTransaccion, IdTransaccion FROM #tmp

	OPEN cur
	FETCH NEXT FROM cur INTO @cuit_resp_pago, @Importe, @fechaOperacion, @ID_TransaccionMP

	WHILE @@FETCH_STATUS = 0
	BEGIN
		EXEC sp_ForzarTransaccion @cuit_resp_pago, @Importe, @fechaOperacion, @ID_TransaccionMP
		FETCH NEXT FROM cur INTO @cuit_resp_pago, @Importe, @fechaOperacion, @ID_TransaccionMP
	END

	CLOSE cur
	DEALLOCATE cur

	SELECT * FROM #tmp
	DROP TABLE #tmp
	--------------------- Fin Forzar Pagos
END