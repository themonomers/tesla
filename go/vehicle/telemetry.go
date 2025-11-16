package vehicle

import (
	"strconv"
	"time"

	"github.com/themonomers/tesla/go/common"
	"google.golang.org/api/sheets/v4"
)

var TELEMETRY_SHEET_ID int64

func init() {
	var err error

	var c = common.GetConfig()
	M3_VIN, err = c.String("vehicle.m3_vin")
	common.LogError("init(): load m3 vin", err)

	MX_VIN, err = c.String("vehicle.mx_vin")
	common.LogError("init(): load mx vin", err)

	EV_SPREADSHEET_ID, err = c.String("google.ev_spreadsheet_id")
	common.LogError("init(): load ev spreadsheet id", err)

	telemetry_sheet_id, err := c.String("google.telemetry_sheet_id")
	common.LogError("init(): load telemetry sheet id", err)
	TELEMETRY_SHEET_ID, _ = strconv.ParseInt(telemetry_sheet_id, 10, 64)

	EMAIL_1, err = c.String("notification.email_1")
	common.LogError("init(): load email 1", err)
}

func WriteVehicleTelemetry() {
	writeM3Telemetry()
	writeMXTelemetry()
}

// Contains functions to read/write the vehicle's data, e.g. mileage,
// efficiency, etc. into a Google Sheet for tracking, analysis, and graphs.
func writeM3Telemetry() {
	// get rollup of vehicle data
	data := GetVehicleData(M3_VIN)

	// write odometer value
	open_row := common.FindOpenRow(EV_SPREADSHEET_ID, "Telemetry", "A:A")
	inputs := &sheets.BatchUpdateValuesRequest{
		ValueInputOption: "USER_ENTERED",
	}
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!A" + strconv.Itoa(open_row),
		Values: [][]any{{data["response"].(map[string]any)["vehicle_state"].(map[string]any)["odometer"].(float64)}},
	})

	// write date stamp
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!B" + strconv.Itoa(open_row),
		Values: [][]any{{time.Now().Format("January 2, 2006")}},
	})

	// copy mileage formulas down
	copy_paste_requests := &sheets.CopyPasteRequest{
		PasteType: "PASTE_NORMAL",
		Source: &sheets.GridRange{
			SheetId:          TELEMETRY_SHEET_ID,
			StartRowIndex:    2,
			EndRowIndex:      3,
			StartColumnIndex: 2,
			EndColumnIndex:   7,
		},
		Destination: &sheets.GridRange{
			SheetId:          TELEMETRY_SHEET_ID,
			StartRowIndex:    int64(open_row) - 2,
			EndRowIndex:      int64(open_row) - 1,
			StartColumnIndex: 2,
			EndColumnIndex:   7,
		},
	}
	request := []*sheets.Request{{
		CopyPaste: copy_paste_requests,
	}}

	// write max battery capacity
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range: "Telemetry!M" + strconv.Itoa(open_row-1),
		Values: [][]any{{data["response"].(map[string]any)["charge_state"].(map[string]any)["battery_range"].(float64) /
			data["response"].(map[string]any)["charge_state"].(map[string]any)["battery_level"].(float64) /
			100.0}},
	})

	// copy down battery degradation % formula
	copy_paste_requests = &sheets.CopyPasteRequest{
		PasteType: "PASTE_NORMAL",
		Source: &sheets.GridRange{
			SheetId:          TELEMETRY_SHEET_ID,
			StartRowIndex:    2,
			EndRowIndex:      3,
			StartColumnIndex: 13,
			EndColumnIndex:   14,
		},
		Destination: &sheets.GridRange{
			SheetId:          TELEMETRY_SHEET_ID,
			StartRowIndex:    int64(open_row) - 2,
			EndRowIndex:      int64(open_row) - 1,
			StartColumnIndex: 13,
			EndColumnIndex:   14,
		},
	}
	request = append(request, &sheets.Request{CopyPaste: copy_paste_requests})

	// write target SoC %
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range: "Telemetry!O" + strconv.Itoa(open_row),
		Values: [][]any{{data["response"].(map[string]any)["charge_state"].(map[string]any)["charge_limit_soc"].(float64) /
			100.0}},
	})

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
		Range:  "Telemetry!H" + strconv.Itoa(open_row),
		Values: [][]any{{starting_range}},
	})
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!I" + strconv.Itoa(open_row-1),
		Values: [][]any{{eod_range}},
	})

	// copy efficiency formulas down
	copy_paste_requests = &sheets.CopyPasteRequest{
		PasteType: "PASTE_NORMAL",
		Source: &sheets.GridRange{
			SheetId:          TELEMETRY_SHEET_ID,
			StartRowIndex:    2,
			EndRowIndex:      3,
			StartColumnIndex: 9,
			EndColumnIndex:   12,
		},
		Destination: &sheets.GridRange{
			SheetId:          TELEMETRY_SHEET_ID,
			StartRowIndex:    int64(open_row) - 2,
			EndRowIndex:      int64(open_row) - 1,
			StartColumnIndex: 9,
			EndColumnIndex:   12,
		},
	}
	request = append(request, &sheets.Request{CopyPaste: copy_paste_requests})

	// write temperature data into telemetry sheet
	inside_temp := data["response"].(map[string]any)["climate_state"].(map[string]any)["inside_temp"].(float64)*
		9/5 +
		32 // convert to Fahrenheit
	outside_temp := data["response"].(map[string]any)["climate_state"].(map[string]any)["outside_temp"].(float64)*
		9/5 +
		32 // convert to Fahrenheit
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!P" + strconv.Itoa(open_row-1),
		Values: [][]any{{inside_temp}},
	})
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!Q" + strconv.Itoa(open_row-1),
		Values: [][]any{{outside_temp}},
	})

	// write tire pressure data into telemetry sheet
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range: "Telemetry!R" + strconv.Itoa(open_row-1),
		Values: [][]any{{data["response"].(map[string]any)["vehicle_state"].(map[string]any)["tpms_pressure_fl"].(float64) *
			14.5038}},
	})
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range: "Telemetry!S" + strconv.Itoa(open_row-1),
		Values: [][]any{{data["response"].(map[string]any)["vehicle_state"].(map[string]any)["tpms_pressure_fr"].(float64) *
			14.5038}},
	})
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range: "Telemetry!T" + strconv.Itoa(open_row-1),
		Values: [][]any{{data["response"].(map[string]any)["vehicle_state"].(map[string]any)["tpms_pressure_rl"].(float64) *
			14.5038}},
	})
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range: "Telemetry!U" + strconv.Itoa(open_row-1),
		Values: [][]any{{data["response"].(map[string]any)["vehicle_state"].(map[string]any)["tpms_pressure_rr"].(float64) *
			14.5038}},
	})

	// batch write data and formula copies to sheet
	srv := common.GetGoogleSheetService()
	_, err := srv.Spreadsheets.Values.BatchUpdate(EV_SPREADSHEET_ID, inputs).Do()
	common.LogError("WriteM3Telemetry(): srv.Spreadsheets.Values.BatchUpdate", err)
	_, err = srv.Spreadsheets.BatchUpdate(EV_SPREADSHEET_ID, &sheets.BatchUpdateSpreadsheetRequest{Requests: request}).Do()
	common.LogError("WriteM3Telemetry(): srv.Spreadsheets.BatchUpdate", err)

	// send email notification
	message := "Model 3 telemetry successfully logged on " +
		time.Now().Format("January 2, 2006 15:04:05") +
		"."
	common.SendEmail(EMAIL_1, "Model 3 Telemetry Logged", message, "")
}

func writeMXTelemetry() {
	// get rollup of vehicle data
	data := GetVehicleData(MX_VIN)

	// write odometer value
	open_row := common.FindOpenRow(EV_SPREADSHEET_ID, "Telemetry", "V:V")
	inputs := &sheets.BatchUpdateValuesRequest{
		ValueInputOption: "USER_ENTERED",
	}
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!V" + strconv.Itoa(open_row),
		Values: [][]any{{data["response"].(map[string]any)["vehicle_state"].(map[string]any)["odometer"].(float64)}},
	})

	// write date stamp
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!W" + strconv.Itoa(open_row),
		Values: [][]any{{time.Now().Format("January 2, 2006")}},
	})

	// copy mileage formulas down
	copy_paste_requests := &sheets.CopyPasteRequest{
		PasteType: "PASTE_NORMAL",
		Source: &sheets.GridRange{
			SheetId:          TELEMETRY_SHEET_ID,
			StartRowIndex:    2,
			EndRowIndex:      3,
			StartColumnIndex: 23,
			EndColumnIndex:   28,
		},
		Destination: &sheets.GridRange{
			SheetId:          TELEMETRY_SHEET_ID,
			StartRowIndex:    int64(open_row) - 2,
			EndRowIndex:      int64(open_row) - 1,
			StartColumnIndex: 23,
			EndColumnIndex:   28,
		},
	}
	request := []*sheets.Request{{
		CopyPaste: copy_paste_requests,
	}}

	// write max battery capacity
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range: "Telemetry!AH" + strconv.Itoa(open_row-1),
		Values: [][]any{{data["response"].(map[string]any)["charge_state"].(map[string]any)["battery_range"].(float64) /
			data["response"].(map[string]any)["charge_state"].(map[string]any)["battery_level"].(float64) /
			100.0}},
	})

	// copy down battery degradation % formula
	copy_paste_requests = &sheets.CopyPasteRequest{
		PasteType: "PASTE_NORMAL",
		Source: &sheets.GridRange{
			SheetId:          TELEMETRY_SHEET_ID,
			StartRowIndex:    2,
			EndRowIndex:      3,
			StartColumnIndex: 34,
			EndColumnIndex:   35,
		},
		Destination: &sheets.GridRange{
			SheetId:          TELEMETRY_SHEET_ID,
			StartRowIndex:    int64(open_row) - 2,
			EndRowIndex:      int64(open_row) - 1,
			StartColumnIndex: 34,
			EndColumnIndex:   35,
		},
	}
	request = append(request, &sheets.Request{CopyPaste: copy_paste_requests})

	// write target SoC %
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range: "Telemetry!AJ" + strconv.Itoa(open_row),
		Values: [][]any{{data["response"].(map[string]any)["charge_state"].(map[string]any)["charge_limit_soc"].(float64) /
			100.0}},
	})

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
		Range:  "Telemetry!AC" + strconv.Itoa(open_row),
		Values: [][]any{{starting_range}},
	})
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!AD" + strconv.Itoa(open_row-1),
		Values: [][]any{{eod_range}},
	})

	// copy efficiency formulas down
	copy_paste_requests = &sheets.CopyPasteRequest{
		PasteType: "PASTE_NORMAL",
		Source: &sheets.GridRange{
			SheetId:          TELEMETRY_SHEET_ID,
			StartRowIndex:    2,
			EndRowIndex:      3,
			StartColumnIndex: 30,
			EndColumnIndex:   33,
		},
		Destination: &sheets.GridRange{
			SheetId:          TELEMETRY_SHEET_ID,
			StartRowIndex:    int64(open_row) - 2,
			EndRowIndex:      int64(open_row) - 1,
			StartColumnIndex: 30,
			EndColumnIndex:   33,
		},
	}
	request = append(request, &sheets.Request{CopyPaste: copy_paste_requests})

	// write temperature data into telemetry sheet
	inside_temp := data["response"].(map[string]any)["climate_state"].(map[string]any)["inside_temp"].(float64)*
		9/5 +
		32 // convert to Fahrenheit
	outside_temp := data["response"].(map[string]any)["climate_state"].(map[string]any)["outside_temp"].(float64)*
		9/5 +
		32 // convert to Fahrenheit
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!AK" + strconv.Itoa(open_row-1),
		Values: [][]any{{inside_temp}},
	})
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!AL" + strconv.Itoa(open_row-1),
		Values: [][]any{{outside_temp}},
	})

	// write tire pressure data into telemetry sheet
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range: "Telemetry!AM" + strconv.Itoa(open_row-1),
		Values: [][]any{{data["response"].(map[string]any)["vehicle_state"].(map[string]any)["tpms_pressure_fl"].(float64) *
			14.5038}},
	})
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range: "Telemetry!AN" + strconv.Itoa(open_row-1),
		Values: [][]any{{data["response"].(map[string]any)["vehicle_state"].(map[string]any)["tpms_pressure_fr"].(float64) *
			14.5038}},
	})
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range: "Telemetry!AO" + strconv.Itoa(open_row-1),
		Values: [][]any{{data["response"].(map[string]any)["vehicle_state"].(map[string]any)["tpms_pressure_rl"].(float64) *
			14.5038}},
	})
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range: "Telemetry!AP" + strconv.Itoa(open_row-1),
		Values: [][]any{{data["response"].(map[string]any)["vehicle_state"].(map[string]any)["tpms_pressure_rr"].(float64) *
			14.5038}},
	})

	// batch write data and formula copies to sheet
	srv := common.GetGoogleSheetService()
	_, err := srv.Spreadsheets.Values.BatchUpdate(EV_SPREADSHEET_ID, inputs).Do()
	common.LogError("WriteMXTelemetry(): srv.Spreadsheets.Values.BatchUpdate", err)
	_, err = srv.Spreadsheets.BatchUpdate(EV_SPREADSHEET_ID, &sheets.BatchUpdateSpreadsheetRequest{Requests: request}).Do()
	common.LogError("WriteMXTelemetry(): srv.Spreadsheets.BatchUpdate", err)

	// send email notification
	message := "Model X telemetry successfully logged on " +
		time.Now().Format("January 2, 2006 15:04:05") +
		"."
	common.SendEmail(EMAIL_1, "Model X Telemetry Logged", message, "")
}
