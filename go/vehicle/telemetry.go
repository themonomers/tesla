package vehicle

import (
	"log/slog"
	"strconv"
	"strings"
	"time"

	"github.com/themonomers/tesla/go/common"
	"google.golang.org/api/sheets/v4"
)

var TELEMETRY_SHEET_NAME = "Telemetry"
var SHEET_PASTE_TYPE = "PASTE_NORMAL"

func WriteVehicleTelemetry() {
	writeVehicleTelemetry("Model 3", "A", 2)
	writeVehicleTelemetry("Model X", "V", 23)
}

// Contains functions to read/write the vehicle's data, e.g. mileage,
// efficiency, etc. into a Google Sheet for tracking, analysis, and graphs.
func writeVehicleTelemetry(vehicle, startLetter string, startColIdx int64) {
	// get rollup of vehicle data
	data := GetVehicleData(common.EncryptedCfg.Vehicle.MxVin)
	if vehicle == "Model 3" {
		data = GetVehicleData(common.EncryptedCfg.Vehicle.M3Vin)
	}

	startIndex := alphaToInt(startLetter)

	// write odometer value
	open_row := common.FindOpenRow(common.EncryptedCfg.Google.EvSpreadsheetId, TELEMETRY_SHEET_NAME+"!"+startLetter+":"+startLetter)
	inputs := &sheets.BatchUpdateValuesRequest{
		ValueInputOption: "USER_ENTERED",
	}
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!" + startLetter + strconv.Itoa(open_row),
		Values: [][]any{{data["response"].(map[string]any)["vehicle_state"].(map[string]any)["odometer"].(float64)}},
	})

	// write date stamp
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!" + intToAlpha(startIndex+1) + strconv.Itoa(open_row),
		Values: [][]any{{time.Now().Format("January 2, 2006")}},
	})

	// copy formulas down: Day, Daily (mi), Daily Avg (mi), Days in Svc, Est Annual (mi)
	copy_paste_requests := &sheets.CopyPasteRequest{
		PasteType: SHEET_PASTE_TYPE,
		Source: &sheets.GridRange{
			SheetId:          common.EncryptedCfg.Google.TelemetrySheetId,
			StartRowIndex:    2,
			EndRowIndex:      3,
			StartColumnIndex: startColIdx,
			EndColumnIndex:   startColIdx + 5,
		},
		Destination: &sheets.GridRange{
			SheetId:          common.EncryptedCfg.Google.TelemetrySheetId,
			StartRowIndex:    int64(open_row) - 2,
			EndRowIndex:      int64(open_row) - 1,
			StartColumnIndex: startColIdx,
			EndColumnIndex:   startColIdx + 5,
		},
	}
	request := []*sheets.Request{{
		CopyPaste: copy_paste_requests,
	}}

	// write data for efficiency calculation
	starting_range := (data["response"].(map[string]any)["charge_state"].(map[string]any)["battery_range"].(float64) /
		data["response"].(map[string]any)["charge_state"].(map[string]any)["battery_level"].(float64) /
		100.0) *
		(data["response"].(map[string]any)["charge_state"].(map[string]any)["charge_limit_soc"].(float64) /
			100.0)

	eod_range := data["response"].(map[string]any)["charge_state"].(map[string]any)["battery_range"].(float64)

	// if the starting range is less than eod range or the car is not plugged
	// in or charging state is complete, the starting range is equal to the
	// eod range because it won't charge
	if (starting_range < eod_range) ||
		(!data["response"].(map[string]any)["charge_state"].(map[string]any)["charge_port_door_open"].(bool) ||
			(data["response"].(map[string]any)["charge_state"].(map[string]any)["charging_state"].(string) == "Complete")) {
		starting_range = eod_range
	}

	// write the starting_range for the next day
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!" + intToAlpha(startIndex+7) + strconv.Itoa(open_row),
		Values: [][]any{{starting_range}},
	})
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!" + intToAlpha(startIndex+8) + strconv.Itoa(open_row-1),
		Values: [][]any{{eod_range}},
	})

	// copy formulas down: Range Used (mi), Efficiency, Energy Use (Wh/ mi)
	copy_paste_requests = &sheets.CopyPasteRequest{
		PasteType: SHEET_PASTE_TYPE,
		Source: &sheets.GridRange{
			SheetId:          common.EncryptedCfg.Google.TelemetrySheetId,
			StartRowIndex:    2,
			EndRowIndex:      3,
			StartColumnIndex: startColIdx + 7,
			EndColumnIndex:   startColIdx + 10,
		},
		Destination: &sheets.GridRange{
			SheetId:          common.EncryptedCfg.Google.TelemetrySheetId,
			StartRowIndex:    int64(open_row) - 2,
			EndRowIndex:      int64(open_row) - 1,
			StartColumnIndex: startColIdx + 7,
			EndColumnIndex:   startColIdx + 10,
		},
	}
	request = append(request, &sheets.Request{CopyPaste: copy_paste_requests})

	// write max battery capacity
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range: TELEMETRY_SHEET_NAME + "!" + intToAlpha(startIndex+12) + strconv.Itoa(open_row-1),
		Values: [][]any{{data["response"].(map[string]any)["charge_state"].(map[string]any)["battery_range"].(float64) /
			data["response"].(map[string]any)["charge_state"].(map[string]any)["battery_level"].(float64) /
			100.0}},
	})

	// copy formulas down: Battery Degradation
	copy_paste_requests = &sheets.CopyPasteRequest{
		PasteType: SHEET_PASTE_TYPE,
		Source: &sheets.GridRange{
			SheetId:          common.EncryptedCfg.Google.TelemetrySheetId,
			StartRowIndex:    2,
			EndRowIndex:      3,
			StartColumnIndex: startColIdx + 11,
			EndColumnIndex:   startColIdx + 12,
		},
		Destination: &sheets.GridRange{
			SheetId:          common.EncryptedCfg.Google.TelemetrySheetId,
			StartRowIndex:    int64(open_row) - 2,
			EndRowIndex:      int64(open_row) - 1,
			StartColumnIndex: startColIdx + 11,
			EndColumnIndex:   startColIdx + 12,
		},
	}
	request = append(request, &sheets.Request{CopyPaste: copy_paste_requests})

	// write target SoC %
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range: TELEMETRY_SHEET_NAME + "!" + intToAlpha(startIndex+14) + strconv.Itoa(open_row),
		Values: [][]any{{data["response"].(map[string]any)["charge_state"].(map[string]any)["charge_limit_soc"].(float64) /
			100.0}},
	})

	// write temperature data into telemetry sheet
	inside_temp := common.CelsiusToFahrenheit(data["response"].(map[string]any)["climate_state"].(map[string]any)["inside_temp"].(float64))
	outside_temp := common.CelsiusToFahrenheit(data["response"].(map[string]any)["climate_state"].(map[string]any)["outside_temp"].(float64))
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!" + intToAlpha(startIndex+15) + strconv.Itoa(open_row-1),
		Values: [][]any{{inside_temp}},
	})
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!" + intToAlpha(startIndex+16) + strconv.Itoa(open_row-1),
		Values: [][]any{{outside_temp}},
	})

	// write tire pressure data into telemetry sheet
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!" + intToAlpha(startIndex+17) + strconv.Itoa(open_row-1),
		Values: [][]any{{common.BarToPsi(data["response"].(map[string]any)["vehicle_state"].(map[string]any)["tpms_pressure_fl"].(float64))}},
	})
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!" + intToAlpha(startIndex+18) + strconv.Itoa(open_row-1),
		Values: [][]any{{common.BarToPsi(data["response"].(map[string]any)["vehicle_state"].(map[string]any)["tpms_pressure_fr"].(float64))}},
	})
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!" + intToAlpha(startIndex+19) + strconv.Itoa(open_row-1),
		Values: [][]any{{common.BarToPsi(data["response"].(map[string]any)["vehicle_state"].(map[string]any)["tpms_pressure_rl"].(float64))}},
	})
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!" + intToAlpha(startIndex+20) + strconv.Itoa(open_row-1),
		Values: [][]any{{common.BarToPsi(data["response"].(map[string]any)["vehicle_state"].(map[string]any)["tpms_pressure_rr"].(float64))}},
	})

	// batch write data and formula copies to sheet
	srv := GetGoogleSheetService()
	_, err := srv.Spreadsheets.Values.BatchUpdate(common.EncryptedCfg.Google.EvSpreadsheetId, inputs).Do()
	if err != nil {
		slog.Error("WriteVehicleTelemetry(" + vehicle + "): srv.Spreadsheets.Values.BatchUpdate(): " + err.Error())
	}
	_, err = srv.Spreadsheets.BatchUpdate(common.EncryptedCfg.Google.EvSpreadsheetId, &sheets.BatchUpdateSpreadsheetRequest{Requests: request}).Do()
	if err != nil {
		slog.Error("WriteVehicleTelemetry(" + vehicle + "): srv.Spreadsheets.BatchUpdate(): " + err.Error())
	}

	// send email notification
	message := vehicle + " telemetry successfully logged on " +
		time.Now().Format("January 2, 2006 15:04:05") +
		"."
	SendEmail(common.EncryptedCfg.Notification.Email1, vehicle+" Telemetry Logged", message, "")
}

// Convert a letter to its integer based alphabet position,
// starting with A = 1.
func alphaToInt(letters string) int {
	result := 0
	letters = strings.ToUpper(letters)

	for i := 0; i < len(letters); i++ {
		result = result*26 + int(letters[i]-'A'+1)
	}

	return result - 1
}

// Converts alphabet integer(s) position (A = 1) back to a letter
// or letters for incrementing purposes while also allowing
// for wrapping around Z to AA, etc. for continuous incrementing
// as used in spreadsheet columns.
func intToAlpha(startIndex int) string {
	var chars []byte
	n := startIndex

	for n >= 0 {
		chars = append(chars, byte('A'+(n%26)))
		n = (n / 26) - 1
	}

	// Reverse the slice in place
	for i, j := 0, len(chars)-1; i < j; i, j = i+1, j-1 {
		chars[i], chars[j] = chars[j], chars[i]
	}

	return string(chars)
}
