package energy

import (
	"log/slog"
	"strconv"
	"time"

	"github.com/influxdata/influxdb/client/v2"
	"github.com/themonomers/tesla/go/common"
	"google.golang.org/api/sheets/v4"
)

var GetDBClient = common.GetDBClient

var ENERGY_SPREADSHEET_ID string
var SUMMARY_SHEET_ID int64
var EMAIL_1 string

func init() {
	c := GetConfig()
	ENERGY_SPREADSHEET_ID, _ = c.String("google.energy_spreadsheet_id")
	summary_sheet_id, _ := c.String("google.summary_sheet_id")
	SUMMARY_SHEET_ID, _ = strconv.ParseInt(summary_sheet_id, 10, 64)
	EMAIL_1, _ = c.String("notification.email_1")
}

// Write the data for the previous day based on a cron job that runs just after
// midnight to ensure we get a full day's worth of data.
func WriteEnergyTelemetry() {
	yest := time.Now().Add(time.Duration(-24 * time.Hour))
	WriteEnergyDetailToDB(yest)
	WriteEnergySummaryToDB(yest)
	WriteBatteryChargeToDB(yest)
	WriteEnergyTOUSummaryToDB(yest)
	WriteEnergyDataToGsheet(yest)
	WriteBatteryBackupHistoryToDB()

	// send email notification
	message := ("Energy telemetry successfully logged on " +
		time.Now().Format("January 2, 2006 15:04:05") +
		".")
	common.SendEmail(EMAIL_1, "Energy Telemetry Logged", message, "")
}

// This writes solar and battery data in 5 minute increments in InfluxDB
// for a given day that can be visualized in Grafana.  This recreates the
// "Energy Usage" graph from the mobile app.
func WriteEnergyDetailToDB(date time.Time) {
	// get time series data
	data := GetPowerHistory("day", date)

	c := GetDBClient()
	defer c.Close()

	// Create a new point batch
	bp, _ := client.NewBatchPoints(client.BatchPointsConfig{
		Database: "energy",
	})

	for _, val := range data["response"].(map[string]any)["time_series"].([]any) {
		//d, err := time.Parse("2006-01-02", strings.Split(val.(map[string]any)["timestamp"].(string), "T")[0])
		d, _ := time.Parse("2006-01-02T15:04:05-07:00", val.(map[string]any)["timestamp"].(string))

		if d.Year() == date.Year() &&
			d.Month() == date.Month() &&
			d.Day() == date.Day() {
			for key, val := range val.(map[string]any) {
				if key != "timestamp" {
					// Create points and add to batch
					tags := map[string]string{"source": key}
					fields := map[string]any{
						"value": val.(float64),
					}
					pt, _ := client.NewPoint("energy_detail", tags, fields, d)
					bp.AddPoint(pt)
				}
			}
			// Write the batch
			err := c.Write(bp)
			if err != nil {
				slog.Error("WriteEnergyDetailToDB(): c.Write(): " + err.Error())
			}

			// Close client resources
			c.Close()
		}
	}
}

// Contains functions to read/write the solar and powerwall data into a
// InfluxDB for tracking, analysis, and graphs.  The data is a summary level
// down to the day.
func WriteEnergySummaryToDB(date time.Time) {
	// get local battery data
	data := getLocalSystemStatus()
	date = time.Date(date.Year(), date.Month(), date.Day(), date.Hour(), date.Minute(), date.Second(), date.Nanosecond(), time.Local)

	c := GetDBClient()
	defer c.Close()

	// Create a new point batch
	bp, _ := client.NewBatchPoints(client.BatchPointsConfig{
		Database: "energy",
	})

	// write battery data
	// Create points and add to batch
	tags := map[string]string{"source": "total_pack_energy"}
	fields := map[string]any{
		"value": data["nominal_full_pack_energy"].(float64),
	}
	pt, _ := client.NewPoint("energy_summary", tags, fields, date.Local().UTC())
	bp.AddPoint(pt)

	// get battery data
	data = GetSiteStatus()
	tags = map[string]string{"source": "percentage_charged"}
	fields = map[string]any{
		"value": data["response"].(map[string]any)["percentage_charged"].(float64),
	}
	pt, _ = client.NewPoint("energy_summary", tags, fields, date.Local().UTC())
	bp.AddPoint(pt)

	// get solar data
	data = GetSiteHistory("day", date)
	//	json, _ := json.MarshalIndent(data, "", "  ")
	//	println(string(json))

	// write solar data
	cumulative_data := make(map[string]float64)
	for _, items := range data["response"].(map[string]any)["time_series"].([]any) {
		d, _ := time.Parse("2006-01-02T15:04:05-07:00", items.(map[string]any)["timestamp"].(string))

		if d.Year() == date.Year() &&
			d.Month() == date.Month() &&
			d.Day() == date.Day() {
			for key, value := range items.(map[string]any) {
				if (key != "timestamp") &&
					(key != "raw_timestamp") &&
					(key != "grid_services_energy_exported") &&
					(key != "grid_services_energy_imported") &&
					(key != "generator_energy_exported") {
					cumulative_data[key] += value.(float64)
				}
			}
		}
	}
	//	fmt.Println("Cumulative Data:", cumulative_data)
	for key, val := range cumulative_data {
		tags = map[string]string{"source": key}
		fields = map[string]any{
			"value": val,
		}
		pt, _ = client.NewPoint("energy_summary", tags, fields, date)
		bp.AddPoint(pt)
	}

	// get solar value
	data = GetSavingsForecast("day", date)
	for _, j := range data["response"].([]any) {
		d, _ := time.Parse(time.RFC3339, j.(map[string]any)["timestamp"].(string))

		// timestamp in data is in UTC, convert to local time
		d_local := d.Local()

		// need to adjust an additional -1 days because of the lag in
		// availability of this data
		date_adj := date.Add(time.Duration(-24 * time.Hour))

		if d_local.Year() == date_adj.Year() &&
			d_local.Month() == date_adj.Month() &&
			d_local.Day() == date_adj.Day() {
			tags = map[string]string{"source": "savings_forecast"}
			fields = map[string]any{
				"value": j.(map[string]any)["value"].(float64),
			}
			pt, _ = client.NewPoint("energy_summary", tags, fields, d)
			bp.AddPoint(pt)
		}
	}

	// Write the batch
	err := c.Write(bp)
	if err != nil {
		slog.Error("WriteEnergySummaryToDB(): c.Write(): " + err.Error())
	}

	// Close client resources
	c.Close()
}

// Writes Tesla battery charge state history into an InfluxDB for
// Grafana visualization.  These are in 15 minute increments.
func WriteBatteryChargeToDB(date time.Time) {
	// get battery charge history data
	data := GetBatteryChargeHistory("day", date)

	c := GetDBClient()
	defer c.Close()

	// Create a new point batch
	bp, _ := client.NewBatchPoints(client.BatchPointsConfig{
		Database: "energy",
	})

	for _, val := range data["response"].(map[string]any)["time_series"].([]any) {
		tags := map[string]string{"source": "percentage_charged"}
		fields := map[string]any{
			"value": val.(map[string]any)["soe"].(float64),
		}
		d, _ := time.Parse("2006-01-02T15:04:05-07:00", val.(map[string]any)["timestamp"].(string))
		pt, _ := client.NewPoint("energy_detail", tags, fields, d)
		bp.AddPoint(pt)
	}

	// Write the batch
	err := c.Write(bp)
	if err != nil {
		slog.Error("WriteBatteryChargeToDB(): c.Write(): " + err.Error())
	}

	// Close client resources
	c.Close()
}

// Contains functions to read/write the solar and powerwall data, separated
// by peak/partial peak/off peak, into InfluxDB for tracking, analysis,
// and graphs.  The data is a summary level down to the day.
func WriteEnergyTOUSummaryToDB(date time.Time) {
	// get solar data for all day
	data := GetSiteHistory("day", date)
	date = time.Date(date.Year(), date.Month(), date.Day(), date.Hour(), date.Minute(), date.Second(), date.Nanosecond(), time.Local)

	// write solar data for all day
	c := GetDBClient()
	defer c.Close()

	// Create a new point batch
	bp, _ := client.NewBatchPoints(client.BatchPointsConfig{
		Database: "summary",
	})

	cumulative_data := make(map[string]float64)
	for _, items := range data["response"].(map[string]any)["time_series"].([]any) {
		d, _ := time.Parse("2006-01-02T15:04:05-07:00", items.(map[string]any)["timestamp"].(string))

		if d.Year() == date.Year() &&
			d.Month() == date.Month() &&
			d.Day() == date.Day() {
			for key, value := range items.(map[string]any) {
				if (key != "timestamp") && (key != "raw_timestamp") {
					cumulative_data[key] += value.(float64)
				}
			}
		}
	}
	for key, val := range cumulative_data {
		tags := map[string]string{"source": key}
		fields := map[string]any{
			"value": val,
		}
		pt, _ := client.NewPoint("all_day", tags, fields, date)
		bp.AddPoint(pt)
	}

	// get solar data for TOU
	data = GetSiteTOUHistory("day", date)

	// write solar data for TOU
	for key_1 := range data["response"].(map[string]any) {
		if key_1 == "off_peak" ||
			key_1 == "partial_peak" ||
			key_1 == "peak" {
			for key_2, val_2 := range data["response"].(map[string]any)[key_1].(map[string]any)["time_series"].([]any)[0].(map[string]any) {
				if key_2 != "timestamp" && key_2 != "raw_timestamp" {
					tags := map[string]string{"source": key_2}
					fields := map[string]any{
						"value": val_2.(float64),
					}
					pt, _ := client.NewPoint(key_1, tags, fields, date)
					bp.AddPoint(pt)
				}
			}
		}
	}

	// Write the batch
	err := c.Write(bp)
	if err != nil {
		slog.Error("WriteEnergyTOUSummaryToDB(): c.Write(): " + err.Error())
	}

	// Close client resources
	c.Close()
}

// Contains functions to read/write the solar and powerwall data, separated
// by peak/partial peak/off peak, into a Google Sheet for tracking, analysis,
// and graphs.  The data is a summary level down to the day.
func WriteEnergyDataToGsheet(date time.Time) {
	// get local battery data
	data := getLocalSystemStatus()

	// write total pack energy value
	open_row := common.FindOpenRow(ENERGY_SPREADSHEET_ID, "Telemetry!A:A")
	inputs := &sheets.BatchUpdateValuesRequest{
		ValueInputOption: "USER_ENTERED",
	}

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!A" + strconv.Itoa(open_row),
		Values: [][]any{{time.Now().Add(time.Duration(-24 * time.Hour)).Format("January 02, 2006")}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!B" + strconv.Itoa(open_row),
		Values: [][]any{{data["nominal_full_pack_energy"].(float64)}},
	})

	// get battery data
	data = GetSiteStatus()
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!C" + strconv.Itoa(open_row),
		Values: [][]any{{data["response"].(map[string]any)["percentage_charged"].(float64)}},
	})

	// copy formula down: column D
	copy_paste_requests := &sheets.CopyPasteRequest{
		PasteType: "PASTE_NORMAL",
		Source: &sheets.GridRange{
			SheetId:          SUMMARY_SHEET_ID,
			StartRowIndex:    4,
			EndRowIndex:      5,
			StartColumnIndex: 3,
			EndColumnIndex:   4,
		},
		Destination: &sheets.GridRange{
			SheetId:          SUMMARY_SHEET_ID,
			StartRowIndex:    int64(open_row) - 1,
			EndRowIndex:      int64(open_row),
			StartColumnIndex: 3,
			EndColumnIndex:   4,
		},
	}
	request := []*sheets.Request{{
		CopyPaste: copy_paste_requests,
	}}

	// get solar data for all day
	data = GetSiteHistory("day", date)

	cumulative_data := make(map[string]float64)
	for _, items := range data["response"].(map[string]any)["time_series"].([]any) {
		d, _ := time.Parse("2006-01-02T15:04:05-07:00", items.(map[string]any)["timestamp"].(string))

		if d.Year() == date.Year() &&
			d.Month() == date.Month() &&
			d.Day() == date.Day() {
			for key, value := range items.(map[string]any) {
				if (key != "timestamp") && (key != "raw_timestamp") {
					cumulative_data[key] += value.(float64)
				}
			}
		}
	}

	// write solar data for all day
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!F" + strconv.Itoa(open_row),
		Values: [][]any{{date.Format("January 02, 2006")}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!H" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["consumer_energy_imported_from_solar"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!I" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["consumer_energy_imported_from_battery"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!J" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["consumer_energy_imported_from_grid"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!K" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["consumer_energy_imported_from_generator"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!L" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["solar_energy_exported"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!M" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["battery_energy_exported"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!N" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["battery_energy_imported_from_solar"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!O" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["battery_energy_imported_from_grid"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!P" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["battery_energy_imported_from_generator"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!Q" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["grid_energy_imported"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!R" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["grid_energy_exported_from_solar"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!S" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["grid_energy_exported_from_battery"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!T" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["grid_energy_exported_from_generator"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!U" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["grid_services_energy_exported"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!V" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["grid_services_energy_imported"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry!W" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["generator_energy_exported"]}},
	})

	// copy formulas down: column X to AC
	copy_paste_requests = &sheets.CopyPasteRequest{
		PasteType: "PASTE_NORMAL",
		Source: &sheets.GridRange{
			SheetId:          SUMMARY_SHEET_ID,
			StartRowIndex:    4,
			EndRowIndex:      5,
			StartColumnIndex: 23,
			EndColumnIndex:   29,
		},
		Destination: &sheets.GridRange{
			SheetId:          SUMMARY_SHEET_ID,
			StartRowIndex:    int64(open_row) - 1,
			EndRowIndex:      int64(open_row),
			StartColumnIndex: 23,
			EndColumnIndex:   29,
		},
	}
	request = append(request, &sheets.Request{CopyPaste: copy_paste_requests})

	// get solar data for TOU
	data = GetSiteTOUHistory("day", date)

	// skip if system set to self-powered
	if data["response"] != "" {
		for key_1 := range data["response"].(map[string]any) { // write solar data for off peak
			switch key_1 {
			case "off_peak": // write solar data for off peak
				for _, val_2 := range data["response"].(map[string]any)[key_1].(map[string]any)["time_series"].([]any) {
					d, _ := time.Parse("2006-01-02T15:04:05-07:00", (val_2.(map[string]any)["timestamp"].(string)))

					if d.Year() == date.Year() &&
						d.Month() == date.Month() &&
						d.Day() == date.Day() {
						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!AE" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!AF" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_battery"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!AG" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_grid"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!AH" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!AI" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["solar_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!AJ" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!AK" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!AL" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_grid"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!AM" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!AN" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_imported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!AO" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!AP" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_battery"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!AQ" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!AR" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_services_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!AS" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_services_energy_imported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!AT" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["generator_energy_exported"].(float64)}},
						})

						// copy formulas down: column AU to AZ
						copy_paste_requests = &sheets.CopyPasteRequest{
							PasteType: "PASTE_NORMAL",
							Source: &sheets.GridRange{
								SheetId:          SUMMARY_SHEET_ID,
								StartRowIndex:    4,
								EndRowIndex:      5,
								StartColumnIndex: 46,
								EndColumnIndex:   52,
							},
							Destination: &sheets.GridRange{
								SheetId:          SUMMARY_SHEET_ID,
								StartRowIndex:    int64(open_row) - 1,
								EndRowIndex:      int64(open_row),
								StartColumnIndex: 46,
								EndColumnIndex:   52,
							},
						}
						request = append(request, &sheets.Request{CopyPaste: copy_paste_requests})
					}
				}
			case "partial_peak": // write solar data for partial peak
				for _, val_2 := range data["response"].(map[string]any)[key_1].(map[string]any)["time_series"].([]any) {
					d, _ := time.Parse("2006-01-02T15:04:05-07:00", (val_2.(map[string]any)["timestamp"].(string)))

					if d.Year() == date.Year() &&
						d.Month() == date.Month() &&
						d.Day() == date.Day() {
						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!BB" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!BC" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_battery"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!BD" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_grid"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!BE" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!BF" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["solar_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!BG" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!BH" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!BI" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_grid"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!BJ" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!BK" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_imported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!BL" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!BM" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_battery"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!BN" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!BO" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_services_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!BP" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_services_energy_imported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!BQ" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["generator_energy_exported"].(float64)}},
						})

						// copy formulas down: column BR to BW
						copy_paste_requests = &sheets.CopyPasteRequest{
							PasteType: "PASTE_NORMAL",
							Source: &sheets.GridRange{
								SheetId:          SUMMARY_SHEET_ID,
								StartRowIndex:    4,
								EndRowIndex:      5,
								StartColumnIndex: 69,
								EndColumnIndex:   75,
							},
							Destination: &sheets.GridRange{
								SheetId:          SUMMARY_SHEET_ID,
								StartRowIndex:    int64(open_row) - 1,
								EndRowIndex:      int64(open_row),
								StartColumnIndex: 69,
								EndColumnIndex:   75,
							},
						}
						request = append(request, &sheets.Request{CopyPaste: copy_paste_requests})
					}
				}
			case "peak": // write solar data for peak
				for _, val_2 := range data["response"].(map[string]any)[key_1].(map[string]any)["time_series"].([]any) {
					d, _ := time.Parse("2006-01-02T15:04:05-07:00", (val_2.(map[string]any)["timestamp"].(string)))

					if d.Year() == date.Year() &&
						d.Month() == date.Month() &&
						d.Day() == date.Day() {
						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!BY" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!BZ" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_battery"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!CA" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_grid"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!CB" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!CC" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["solar_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!CD" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!CE" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!CF" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_grid"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!CG" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!CH" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_imported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!CI" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!CJ" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_battery"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!CK" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!CL" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_services_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!CM" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_services_energy_imported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry!CN" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["generator_energy_exported"].(float64)}},
						})

						// copy formulas down: column CO to CT
						copy_paste_requests = &sheets.CopyPasteRequest{
							PasteType: "PASTE_NORMAL",
							Source: &sheets.GridRange{
								SheetId:          SUMMARY_SHEET_ID,
								StartRowIndex:    4,
								EndRowIndex:      5,
								StartColumnIndex: 92,
								EndColumnIndex:   98,
							},
							Destination: &sheets.GridRange{
								SheetId:          SUMMARY_SHEET_ID,
								StartRowIndex:    int64(open_row) - 1,
								EndRowIndex:      int64(open_row),
								StartColumnIndex: 92,
								EndColumnIndex:   98,
							},
						}
						request = append(request, &sheets.Request{CopyPaste: copy_paste_requests})
					}
				}
			}
		}
	}

	// copy formulas down: column CV to DK
	copy_paste_requests = &sheets.CopyPasteRequest{
		PasteType: "PASTE_NORMAL",
		Source: &sheets.GridRange{
			SheetId:          SUMMARY_SHEET_ID,
			StartRowIndex:    4,
			EndRowIndex:      5,
			StartColumnIndex: 99,
			EndColumnIndex:   115,
		},
		Destination: &sheets.GridRange{
			SheetId:          SUMMARY_SHEET_ID,
			StartRowIndex:    int64(open_row) - 1,
			EndRowIndex:      int64(open_row),
			StartColumnIndex: 99,
			EndColumnIndex:   115,
		},
	}
	request = append(request, &sheets.Request{CopyPaste: copy_paste_requests})

	// copy formulas down: column DM to DP, copy from previous row to allow for
	// changes in formula due to electricity rate changes
	copy_paste_requests = &sheets.CopyPasteRequest{
		PasteType: "PASTE_NORMAL",
		Source: &sheets.GridRange{
			SheetId:          SUMMARY_SHEET_ID,
			StartRowIndex:    int64(open_row) - 2,
			EndRowIndex:      int64(open_row) - 1,
			StartColumnIndex: 116,
			EndColumnIndex:   121,
		},
		Destination: &sheets.GridRange{
			SheetId:          SUMMARY_SHEET_ID,
			StartRowIndex:    int64(open_row) - 1,
			EndRowIndex:      int64(open_row),
			StartColumnIndex: 116,
			EndColumnIndex:   121,
		},
	}
	request = append(request, &sheets.Request{CopyPaste: copy_paste_requests})

	// batch write data and formula copies to sheet
	srv := common.GetGoogleSheetService()
	_, err := srv.Spreadsheets.Values.BatchUpdate(ENERGY_SPREADSHEET_ID, inputs).Do()
	if err != nil {
		slog.Error("WriteEnergyDataToGsheet(): srv.Spreadsheets.Values.BatchUpdate(): " + err.Error())
	}
	_, err = srv.Spreadsheets.BatchUpdate(ENERGY_SPREADSHEET_ID, &sheets.BatchUpdateSpreadsheetRequest{Requests: request}).Do()
	if err != nil {
		slog.Error("WriteEnergyDataToGsheet(): srv.Spreadsheets.BatchUpdate(): " + err.Error())
	}
}

// Compares the list of backup events already stored in the DB vs. the list
// from the Tesla and inserts any missing events.
func WriteBatteryBackupHistoryToDB() {
	// get battery backup history data
	data := GetBatteryBackupHistory()

	c := GetDBClient()
	defer c.Close()

	// get existing list of backup events saved to DB
	q := client.NewQuery("SELECT * FROM backup", "outage", "")
	db, _ := c.Query(q)

	// Create a new point batch
	bp, _ := client.NewBatchPoints(client.BatchPointsConfig{
		Database: "outage",
	})

	for _, val := range data["response"].(map[string]any)["events"].([]any) {
		var skip bool = false
		var dt time.Time

		// convert duration to hours
		duration := val.(map[string]any)["duration"].(float64) / 1000 / 60 / 60
		start, _ := time.Parse("2006-01-02T15:04:05-07:00", val.(map[string]any)["timestamp"].(string))

		if len(db.Results[0].Series) > 0 {
			for _, item := range db.Results[0].Series[0].Values {
				loc, _ := time.LoadLocation("America/Los_Angeles")
				dt, _ = time.Parse("2006-01-02T15:04:05Z", item[0].(string))
				dt = dt.In(loc)

				if start.Equal(dt) {
					skip = true
				}
			}
		}

		if !skip {
			tags := map[string]string{"source": "event"}
			fields := map[string]any{
				"value": duration,
			}
			pt, _ := client.NewPoint("backup", tags, fields, start)
			bp.AddPoint(pt)
		}
	}

	// Write the batch
	err := c.Write(bp)
	if err != nil {
		slog.Error("WriteBatteryBackupHistoryToDB(): c.Write(): " + err.Error())
	}

	// Close client resources
	c.Close()
}
