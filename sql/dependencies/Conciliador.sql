-- CA, actualizado al 111/08/2023 - 15:17

USE OSDEPYMPROD;

--------------------- Obtener pagos no procesados
SELECT DISTINCT
	tc.id Id,
	TC.id_transaccion IdTransaccion,
	SUBSTRING(TC.metadata, 14, 11) Cuit,
	TC.transaction_amount Monto,
	TC.date_created FechaTransaccion
INTO #tmp
FROM mercado_pago.TransaccionesConciliar AS TC

-- No debe existir en MercadoPagoTransacciones
WHERE NOT EXISTS (
    SELECT 1
    FROM mercado_pago.MercadoPagoTransacciones AS MP
    WHERE MP.id_transaccion = TC.id_transaccion
)

-- No debe existir en TransaccionesPoliconsultorios
AND NOT EXISTS (
    SELECT 1
    FROM mercado_pago.TransaccionesPoliconsultorios AS PL
    WHERE PL.id_transaccion = TC.id_transaccion
)
AND TC.description NOT LIKE '%Venta presencial%'
AND TC.status = 'approved'
AND TC.metadata <> '{}'
AND TC.operation_type <> 'pos_payment'
AND TC.operation_type <> 'money_transfer'
AND TC.Procesado = 0
ORDER BY TC.date_created DESC;
--------------------- Fin obtener pagos no procesados

--------------------- Redactar mail
IF (SELECT COUNT(*) FROM #tmp) > 0
BEGIN
	DECLARE @TableHTML  NVARCHAR(MAX);
	DECLARE @SendTo varchar(200)
	SELECT @SendTo = email_address FROM SQLTotalDBA.dbo.operators WHERE NAME = 'OPERACIONES_CONCILIADOR_MP'

	SET @TableHTML = N'<H1>Listado de transacciones no encontradas - MP</H1>' 

	SET @TableHTML = @TableHTML + ISNULL(
		N'<table style="width: 50%;">' +
			N'<tbody>' +
				N'<tr style="text-align: left;">' +
				N'		<th>Id de la transaccion</th>
						<th>Cuit</th>
						<th>Monto</th>
						<th>Fecha de la transaccion</th>' +
				N'</tr>' +
				CAST ((
					SELECT
						td = IdTransaccion, '',
						Cuit AS 'td', '',
						Monto AS 'td', '',
						CONVERT(VARCHAR(10), FechaTransaccion, 103) AS 'td', ''
					FROM #tmp FOR XML PATH('tr'), TYPE
				) AS NVARCHAR(MAX) ) +
			N'</tbody>' +
		N'</table>',
		'')
	ALTER TABLE #tmp ADD Informado INT NOT NULL DEFAULT(1);
	UPDATE MP
	SET Informado = 1
	FROM mercado_pago.TransaccionesConciliar MP
	-- marcar los pagos informados
	WHERE EXISTS (SELECT t.id FROM #tmp t WHERE t.Id = MP.id AND t.Informado = 1);

	EXEC msdb.dbo.sp_send_dbmail
		@profile_NAME = 'sqlservice2008',
		@Recipients = @SendTo,
		@subject = '[NEMESIS] Conciliador - Mercado Pago',  
		@body = @TableHTML,
		@body_format = 'HTML';
END;

-- marcar que los pagos fueron procesados
UPDATE mercado_pago.TransaccionesConciliar SET Procesado = 1 WHERE Procesado = 0;
-------------------- Fin redactar mail
