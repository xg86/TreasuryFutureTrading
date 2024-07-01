Option Base 1

Function PLConvergenceStrategy(Weights, 
								Prices, 
								ExitUp As Double, 
								Optional ExitDown, 
								Optional nTime As Integer = 0, 
								Optional nFut As Integer = 0)
								
	Dim PL As Double, i As Integer, j As Integer, Tmp As Double, P0 As Double, Res
	ReDim Res(1, 2) As Double
	If nFut = 0 Then 
		nFut = Weights.Cells.Count
	If nTime = 0 Then 
		nTime = Prices.Rows.Count
	
	For j = 1 To nFut
		P0 = P0 + Weights(1, j) * Prices(1, j)
	Next j
	
	For i = 2 To nTime
		Tmp = 0
		For j = 1 To nFut
			Tmp = Tmp + Weights(1, j) * Prices(i, j)
		Next j
		If Tmp <= P0 - ExitUp Then 
			Res(1, 1) = ExitUp:  Exit For
			
		If Not IsEmpty(ExitDown) And Not IsMissing(ExitDown) Then 
			If Tmp >= P0 + ExitDown Then 
				Res(1, 1) = -ExitDown: Exit For
	Next i
	
	If i > nTime Then 
		Res(1, 1) = P0 - Tmp
		
	Res(1, 2) = i - 1
	
	PLConvergenceStrategy = Res
End Function

Function PLConvergencePositionW(Positions, 
								Prices, 
								PointValue, 
								ExitUp As Double, 
								Optional ExitDown, 
								Optional Notional As Double = 1, 
								Optional nTime = 0, 
								Optional nFut As Integer = 0)
								
	Dim Weights, ExitUpW As Double, ExitDownW, i As Integer, Res
	
	If nFut = 0 Then 
		nFut = Positions.Cells.Count
	If nTime = 0 Then 
		nTime = Prices.Rows.Count
	ReDim Weights(1, nFut) As Double
	
	For i = 1 To nFut
		Weights(1, i) = Positions(1, i) * PointValue(1, i) / Notional
	Next i
	
	ExitUpW = ExitUp / Notional
	
	If IsMissing(ExitDown) Or IsEmpty(ExitDown) Then 
		ExitDownW = ExitDown 
	Else 
		ExitDownW = ExitDown / Notional
	
	Res = PLConvergenceStrategy(Weights, Prices, ExitUpW, ExitDownW, CInt(nTime), nFut)
	
	Res(1, 1) = Notional * Res(1, 1)
	
	PLConvergencePositionW = Res
End Function

Function PLConvergencePosition(Positions, 
								Prices, 
								PointValue, 
								ExitUp As Double,  '$D$3(exit=2)*$AG63(tick size), take profit
								Optional ExitDown, ' (=StopLoss,20)*$AG63(tick size)
								Optional nTime = -1, 
								Optional nFut As Integer = -1)
		Dim PL As Double, i As Integer, j As Integer, Tmp As Double, P0 As Double, Res
		
		'On Error GoTo ErrHandle
		ReDim Res(1, 3) As Double
		
		If nFut = -1 Then 
			nFut = Positions.Cells.Count

		If nTime = -1 Then 
			nTime = Prices.Rows.Count - 1
		
		For j = 1 To nFut
			P0 = P0 + Positions(1, j) * Prices(1, j) * PointValue(1, j)
		Next j
		
		For i = 2 To nTime
			Tmp = 0
			For j = 1 To nFut
				Tmp = Tmp + Positions(1, j) * Prices(i, j) * PointValue(1, j)
			Next j
			If Tmp >= P0 + ExitUp Then 'take profit
				'Tmp = 0
				'For j = 1 To nFut
				'    Tmp = Tmp + Positions(1, j) * Prices(i + 1, j) * PointValue(1, j)
				'Next j
				Res(1, 1) = Tmp - P0
				Res(1, 2) = i - 1
				Res(1, 3) = 1
				Exit For
			End If
			If Not IsEmpty(ExitDown) And Not IsMissing(ExitDown) Then
				If Tmp <= P0 - ExitDown Then 'stop loss
					'Tmp = 0
					'For j = 1 To nFut
					'    Tmp = Tmp + Positions(1, j) * Prices(i + 1, j) * PointValue(1, j)
					'Next j
					Res(1, 1) = Tmp - P0
					Res(1, 2) = i - 1
					Res(1, 3) = 2
					Exit For
				End If
			End If
		Next i
		If i > nTime Then 'expire time . unwind
			Tmp = 0
			For j = 1 To nFut
				Tmp = Tmp + Positions(1, j) * Prices(i - 1, j) * PointValue(1, j)
			Next j
			Res(1, 1) = Tmp - P0
			Res(1, 2) = i - 1
			Res(1, 3) = 3
		End If
		PLConvergencePosition = Res
		'Exit Function
		'ErrHandle:
		'Stop
		'Resume Next
End Function

Function CumulPositions(Positions, 
						Prices, 
						PointValue, 
						Ticks, ' T-score
						TriggerT As Double, 
						Sigmas,  '(z-score)
						TriggerS, 
						TickSize, 
						ExitUp As Double, 
						Optional ExitDown = Empty, 
						Optional nTime As Integer = -1, 
						Optional nFut As Integer = -1,  ' constant 5
						Optional Decay As Double = 0, 
						Optional MaxPos As Integer = 0) '30$B$6
					
	Dim i As Integer, j As Integer, k As Integer, TmpW, TmpP, PL, NumPos, CumPos, TmpUp As Double, TmpDown
	'On Error GoTo ErrHandle
	If nTime = -1 Then 
		nTime = Positions.Rows.Count
	If nFut = -1 Then 
		nFut = Positions.Columns.Count
	
	ReDim CumPos(nTime, nFut + 1) As Double
	ReDim NumPos(nTime, 1) As Integer
	
	For i = 1 To nTime
		If Ticks(i, 1) <= -TriggerT And Sigmas(i, 1) <= -TriggerS Then
			TmpW = Positions
			TmpP = Prices
			TmpUp = ExitUp * TickSize(i, 1)
			
			If Not IsEmpty(ExitDown) And Not IsMissing(ExitDown) Then 
				TmpDown = ExitDown * TickSize(i, 1) 
			Else 
				TmpDown = ExitDown
			k = ShiftArray(TmpW, i - 1, nTime, nFut)
			k = ShiftArray(TmpP, i - 1, nTime, nFut)
			
			PL = PLConvergencePosition(TmpW, TmpP, PointValue, TmpUp, TmpDown, nTime - i, nFut)
			
			If MaxPos > 0 And NumPos(i, 1) < MaxPos Then
				For k = 0 To PL(1, 2) - 1
					NumPos(i + k, 1) = NumPos(i + k, 1) + 1
					For j = 1 To nFut
						CumPos(i + k, j) = CumPos(i + k, j) + Positions(i, j) / NumPos(i, 1) ^ Decay
					Next j
					CumPos(i + k, nFut + 1) = NumPos(i + k, 1)
				Next k
			End If
		End If
	Next i
	
	CumulPositions = CumPos
	'Exit Function
	'ErrHandle:
	'Stop
	'Resume Next
End Function

Function ComputePositions(Weights, 
							Prices, 
							Ticks, 
							Trigger As Double, 
							ExitUp As Double, 
							Optional ExitDown = Empty, 
							Optional nTime As Integer = 0, 
							Optional nFut As Integer = 0, 
							Optional Decay As Double = 0, 
							Optional MaxPos As Integer = 0)
							
	Dim i As Integer, j As Integer, k As Integer, TmpW, TmpP, Positions, PL, NumPos
	'Weights = Range("Weights").Value
	'Prices = Range("Prices").Value
	'Ticks = Range("Ticks").Value
	'Trigger = Range("Trigger").Value
	'nTime = UBound(Weights, 1)
	'nFut = UBound(Weights, 2)
	If nTime = 0 Then nTime = Weights.Rows.Count
	If nFut = 0 Then nFut = Weights.Columns.Count
	
	ReDim Positions(nTime, nFut + 1) As Double
	ReDim NumPos(nTime, 1) As Integer
	
	For i = 1 To nTime
		If Ticks(i, 1) >= Trigger Then
			TmpW = Weights
			TmpP = Prices
			k = ShiftArray(TmpW, i - 1, nTime, nFut)
			k = ShiftArray(TmpP, i - 1, nTime, nFut)
			PL = PLConvergenceStrategy(TmpW, TmpP, ExitUp, ExitDown, nTime - i + 1, nFut)
			If MaxPos > 0 And NumPos(i, 1) < MaxPos Then
				For k = 0 To PL(1, 2) - 1
					NumPos(i + k, 1) = NumPos(i + k, 1) + 1
					For j = 1 To nFut
						Positions(i + k, j) = Positions(i + k, j) + Weights(i, j) / NumPos(i, 1) ^ Decay
					Next j
					Positions(i + k, nFut + 1) = NumPos(i + k, 1)
				Next k
			End If
		End If
	Next i
	ComputePositions = Positions
End Function

Function ShiftArray(ByRef XX, Shift As Integer, Optional nRow As Integer = 0, Optional nCol As Integer = 0) As Integer
	Dim i As Integer, j As Integer
	If nRow = 0 Then nRow = UBound(XX, 1)
	If nCol = 0 Then nCol = UBound(XX, 2)
	If Shift <= 0 Then ShiftArray = 0: Exit Function
	If Shift > nRow Then Shift = nRow
	For i = 1 To nRow - Shift
		For j = 1 To nCol
			XX(i, j) = XX(i + Shift, j)
		Next j
	Next i
	For i = nRow - Shift + 1 To nRow
		For j = 1 To nCol
			XX(i, j) = 0
		Next j
	Next i
	ShiftArray = Shift
End Function

