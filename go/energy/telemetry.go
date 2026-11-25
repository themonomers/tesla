package energy

import (
	"log/slog"
	"strconv"
	"time"

	"github.com/influxdata/influxdb/client/v2"
	"github.com/themonomers/tesla/go/common"
	"google.golang.org/api/sheets/v4"
)

var TELEMETRY_SHEET_NAME = "Telemetry"
var OUTAGE_SHEET_NAME = "Outage"
var SHEET_PASTE_TYPE = "PASTE_NORMAL"

var GetDBClient = common.GetDBClient

// Write the data for the previous day based on a cron job that runs just after
// midnight to ensure we get a full day's worth of data.
func WriteEnergyData(targetDate time.Time) {
	c := GetDBClient()
	defer c.Close()
	// get time series data
	powerHistory := GetPowerHistory("day", targetDate)

	// Create a new point batch
	bpEnergy, _ := client.NewBatchPoints(client.BatchPointsConfig{
		Database: "energy",
	})
	bpEnergy = createEnergyDetailPayload(powerHistory, bpEnergy, targetDate)

	// get summary data
	localSystemStatus := getLocalSystemStatus()
	siteStatus := GetSiteStatus()
	siteHistory := GetSiteHistory("day", targetDate)
	savingsForecast := GetSavingsForecast("day", targetDate)
	bpEnergy = createEnergySummaryPayload(localSystemStatus, siteStatus, siteHistory, savingsForecast, bpEnergy, targetDate)

	// get battery charge history data
	batteryChargeHistory := GetBatteryChargeHistory("day", targetDate)
	bpEnergy = createBatteryChargePayload(batteryChargeHistory, bpEnergy)

	bpSummary, _ := client.NewBatchPoints(client.BatchPointsConfig{
		Database: "summary",
	})
	// get solar data for TOU
	siteTOUHistory := GetSiteTOUHistory("day", targetDate)
	bpSummary = createEnergyTOUSummaryPayload(siteHistory, siteTOUHistory, bpSummary, targetDate)

	bpOutage, _ := client.NewBatchPoints(client.BatchPointsConfig{
		Database: "outage",
	})
	// get battery backup history data
	batteryBackupHistory := GetBatteryBackupHistory()
	bpOutage = createBatteryBackupPayload(batteryBackupHistory, bpOutage)

	// Write the batch
	err := c.Write(bpEnergy)
	if err != nil {
		slog.Error("WriteEnergyData(): c.Write(energy): " + err.Error())
	}
	err = c.Write(bpSummary)
	if err != nil {
		slog.Error("WriteEnergyData(): c.Write(summary): " + err.Error())
	}
	err = c.Write(bpOutage)
	if err != nil {
		slog.Error("WriteEnergyData(): c.Write(outage): " + err.Error())
	}

	// Close client resources
	c.Close()

	// write to Gsheet
	writeEnergyDataToGsheet(localSystemStatus, siteStatus, siteHistory, siteTOUHistory, batteryBackupHistory, targetDate)

	// send email notification
	message := ("Energy telemetry successfully logged on " +
		time.Now().Format("January 2, 2006 15:04:05") +
		".")
	common.SendEmail(common.EncryptedCfg.Notification.Email1, "Energy Telemetry Logged", message, "")
}

// Creates solar and battery payload in 5 minute increments in InfluxDB
// for a given day that can be visualized in Grafana.  This recreates the
// "Energy Usage" graph from the mobile app.
func createEnergyDetailPayload(powerHistory map[string]any, bp client.BatchPoints, targetDate time.Time) client.BatchPoints {
	for _, val := range powerHistory["response"].(map[string]any)["time_series"].([]any) {
		//d, err := time.Parse("2006-01-02", strings.Split(val.(map[string]any)["timestamp"].(string), "T")[0])
		d, _ := time.Parse("2006-01-02T15:04:05-07:00", val.(map[string]any)["timestamp"].(string))

		if d.Year() == targetDate.Year() &&
			d.Month() == targetDate.Month() &&
			d.Day() == targetDate.Day() {
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
		}
	}

	return bp
}

// Creates solar and powerwall summary level payload down to the day.
func createEnergySummaryPayload(localSystemStatus, siteStatus, siteHistory, savingsForecast map[string]any, bp client.BatchPoints, targetDate time.Time) client.BatchPoints {
	targetDate = time.Date(targetDate.Year(), targetDate.Month(), targetDate.Day(), targetDate.Hour(), targetDate.Minute(), targetDate.Second(), targetDate.Nanosecond(), time.Local)

	tags := map[string]string{"source": "total_pack_energy"}
	fields := map[string]any{
		"value": localSystemStatus["nominal_full_pack_energy"].(float64),
	}
	pt, _ := client.NewPoint("energy_summary", tags, fields, targetDate.Local().UTC())
	bp.AddPoint(pt)

	tags = map[string]string{"source": "percentage_charged"}
	fields = map[string]any{
		"value": siteStatus["response"].(map[string]any)["percentage_charged"].(float64),
	}
	pt, _ = client.NewPoint("energy_summary", tags, fields, targetDate.Local().UTC())
	bp.AddPoint(pt)

	cumulative_data := make(map[string]float64)
	for _, items := range siteHistory["response"].(map[string]any)["time_series"].([]any) {
		d, _ := time.Parse("2006-01-02T15:04:05-07:00", items.(map[string]any)["timestamp"].(string))

		if d.Year() == targetDate.Year() &&
			d.Month() == targetDate.Month() &&
			d.Day() == targetDate.Day() {
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
		pt, _ = client.NewPoint("energy_summary", tags, fields, targetDate)
		bp.AddPoint(pt)
	}

	for _, j := range savingsForecast["response"].([]any) {
		d, _ := time.Parse(time.RFC3339, j.(map[string]any)["timestamp"].(string))

		// timestamp in data is in UTC, convert to local time
		d_local := d.Local()

		// need to adjust an additional -1 days because of the lag in
		// availability of this data
		date_adj := targetDate.Add(time.Duration(-24 * time.Hour))

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

	return bp
}

// Creates battery charge state history payload in 15 minute increments.
func createBatteryChargePayload(batteryChargeHistory map[string]any, bp client.BatchPoints) client.BatchPoints {
	for _, val := range batteryChargeHistory["response"].(map[string]any)["time_series"].([]any) {
		tags := map[string]string{"source": "percentage_charged"}
		fields := map[string]any{
			"value": val.(map[string]any)["soe"].(float64),
		}
		d, _ := time.Parse("2006-01-02T15:04:05-07:00", val.(map[string]any)["timestamp"].(string))
		pt, _ := client.NewPoint("energy_detail", tags, fields, d)
		bp.AddPoint(pt)
	}

	return bp
}

// Creates solar and powerwall payload, separated by peak/partial peak/off peak
// in summary level down to the day.
func createEnergyTOUSummaryPayload(siteHistory, siteTOUHistory map[string]any, bp client.BatchPoints, targetDate time.Time) client.BatchPoints {
	targetDate = time.Date(targetDate.Year(), targetDate.Month(), targetDate.Day(), targetDate.Hour(), targetDate.Minute(), targetDate.Second(), targetDate.Nanosecond(), time.Local)

	cumulative_data := make(map[string]float64)
	for _, items := range siteHistory["response"].(map[string]any)["time_series"].([]any) {
		d, _ := time.Parse("2006-01-02T15:04:05-07:00", items.(map[string]any)["timestamp"].(string))

		if d.Year() == targetDate.Year() &&
			d.Month() == targetDate.Month() &&
			d.Day() == targetDate.Day() {
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
		pt, _ := client.NewPoint("all_day", tags, fields, targetDate)
		bp.AddPoint(pt)
	}

	for key_1 := range siteTOUHistory["response"].(map[string]any) {
		if key_1 == "off_peak" ||
			key_1 == "partial_peak" ||
			key_1 == "peak" {
			for key_2, val_2 := range siteTOUHistory["response"].(map[string]any)[key_1].(map[string]any)["time_series"].([]any)[0].(map[string]any) {
				if key_2 != "timestamp" && key_2 != "raw_timestamp" {
					tags := map[string]string{"source": key_2}
					fields := map[string]any{
						"value": val_2.(float64),
					}
					pt, _ := client.NewPoint(key_1, tags, fields, targetDate)
					bp.AddPoint(pt)
				}
			}
		}
	}

	return bp
}

// Compares the list of backup events already stored in the DB vs. the list
// from the Tesla and creates payload of any missing events.
func createBatteryBackupPayload(batteryBackupHistory map[string]any, bp client.BatchPoints) client.BatchPoints {
	c := GetDBClient()
	defer c.Close()

	// get existing list of backup events saved to DB
	q := client.NewQuery("SELECT * FROM backup", "outage", "")
	db, _ := c.Query(q)

	for _, val := range batteryBackupHistory["response"].(map[string]any)["events"].([]any) {
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

	// Close client resources
	c.Close()

	return bp
}

// Write the solar and powerwall data, separated by peak/partial peak/off peak,
// into a Google Sheet for tracking, analysis, and graphs.  The data is a
// summary level down to the day.
func writeEnergyDataToGsheet(localSystemStatus, siteStatus, siteHistory, siteTOUHistory, batteryBackupHistory map[string]any, targetDate time.Time) {
	// write total pack energy value
	open_row := common.FindOpenRow(common.EncryptedCfg.Google.EnergySpreadsheetId, TELEMETRY_SHEET_NAME + "!A:A")
	inputs := &sheets.BatchUpdateValuesRequest{
		ValueInputOption: "USER_ENTERED",
	}

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!A" + strconv.Itoa(open_row),
		Values: [][]any{{targetDate.Format("January 02, 2006")}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!B" + strconv.Itoa(open_row),
		Values: [][]any{{localSystemStatus["nominal_full_pack_energy"].(float64)}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!C" + strconv.Itoa(open_row),
		Values: [][]any{{siteStatus["response"].(map[string]any)["percentage_charged"].(float64)}},
	})

	// copy formula down: column D
	copy_paste_requests := &sheets.CopyPasteRequest{
		PasteType: SHEET_PASTE_TYPE,
		Source: &sheets.GridRange{
			SheetId:          common.EncryptedCfg.Google.SummarySheetId,
			StartRowIndex:    4,
			EndRowIndex:      5,
			StartColumnIndex: 3,
			EndColumnIndex:   4,
		},
		Destination: &sheets.GridRange{
			SheetId:          common.EncryptedCfg.Google.SummarySheetId,
			StartRowIndex:    int64(open_row) - 1,
			EndRowIndex:      int64(open_row),
			StartColumnIndex: 3,
			EndColumnIndex:   4,
		},
	}
	request := []*sheets.Request{{
		CopyPaste: copy_paste_requests,
	}}

	cumulative_data := make(map[string]float64)
	for _, items := range siteHistory["response"].(map[string]any)["time_series"].([]any) {
		d, _ := time.Parse("2006-01-02T15:04:05-07:00", items.(map[string]any)["timestamp"].(string))

		if d.Year() == targetDate.Year() &&
			d.Month() == targetDate.Month() &&
			d.Day() == targetDate.Day() {
			for key, value := range items.(map[string]any) {
				if (key != "timestamp") && (key != "raw_timestamp") {
					cumulative_data[key] += value.(float64)
				}
			}
		}
	}

	// write solar data for all day
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!F" + strconv.Itoa(open_row),
		Values: [][]any{{targetDate.Format("January 02, 2006")}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!H" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["consumer_energy_imported_from_solar"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!I" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["consumer_energy_imported_from_battery"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!J" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["consumer_energy_imported_from_grid"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!K" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["consumer_energy_imported_from_generator"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!L" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["solar_energy_exported"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!M" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["battery_energy_exported"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!N" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["battery_energy_imported_from_solar"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!O" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["battery_energy_imported_from_grid"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!P" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["battery_energy_imported_from_generator"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!Q" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["grid_energy_imported"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!R" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["grid_energy_exported_from_solar"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!S" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["grid_energy_exported_from_battery"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!T" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["grid_energy_exported_from_generator"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!U" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["grid_services_energy_exported"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!V" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["grid_services_energy_imported"]}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  TELEMETRY_SHEET_NAME + "!W" + strconv.Itoa(open_row),
		Values: [][]any{{cumulative_data["generator_energy_exported"]}},
	})

	// copy formulas down: column X to AC
	copy_paste_requests = &sheets.CopyPasteRequest{
		PasteType: SHEET_PASTE_TYPE,
		Source: &sheets.GridRange{
			SheetId:          common.EncryptedCfg.Google.SummarySheetId,
			StartRowIndex:    4,
			EndRowIndex:      5,
			StartColumnIndex: 23,
			EndColumnIndex:   29,
		},
		Destination: &sheets.GridRange{
			SheetId:          common.EncryptedCfg.Google.SummarySheetId,
			StartRowIndex:    int64(open_row) - 1,
			EndRowIndex:      int64(open_row),
			StartColumnIndex: 23,
			EndColumnIndex:   29,
		},
	}
	request = append(request, &sheets.Request{CopyPaste: copy_paste_requests})

	// skip if system set to self-powered
	if siteTOUHistory["response"] != "" {
		for key_1 := range siteTOUHistory["response"].(map[string]any) { // write solar data for off peak
			switch key_1 {
			case "off_peak": // write solar data for off peak
				for _, val_2 := range siteTOUHistory["response"].(map[string]any)[key_1].(map[string]any)["time_series"].([]any) {
					d, _ := time.Parse("2006-01-02T15:04:05-07:00", (val_2.(map[string]any)["timestamp"].(string)))

					if d.Year() == targetDate.Year() &&
						d.Month() == targetDate.Month() &&
						d.Day() == targetDate.Day() {
						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!AE" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!AF" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_battery"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!AG" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_grid"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!AH" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!AI" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["solar_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!AJ" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!AK" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!AL" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_grid"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!AM" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!AN" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_imported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!AO" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!AP" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_battery"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!AQ" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!AR" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_services_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!AS" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_services_energy_imported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!AT" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["generator_energy_exported"].(float64)}},
						})

						// copy formulas down: column AU to AZ
						copy_paste_requests = &sheets.CopyPasteRequest{
							PasteType: SHEET_PASTE_TYPE,
							Source: &sheets.GridRange{
								SheetId:          common.EncryptedCfg.Google.SummarySheetId,
								StartRowIndex:    4,
								EndRowIndex:      5,
								StartColumnIndex: 46,
								EndColumnIndex:   52,
							},
							Destination: &sheets.GridRange{
								SheetId:          common.EncryptedCfg.Google.SummarySheetId,
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
				for _, val_2 := range siteTOUHistory["response"].(map[string]any)[key_1].(map[string]any)["time_series"].([]any) {
					d, _ := time.Parse("2006-01-02T15:04:05-07:00", (val_2.(map[string]any)["timestamp"].(string)))

					if d.Year() == targetDate.Year() &&
						d.Month() == targetDate.Month() &&
						d.Day() == targetDate.Day() {
						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!BB" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!BC" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_battery"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!BD" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_grid"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!BE" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!BF" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["solar_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!BG" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!BH" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!BI" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_grid"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!BJ" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!BK" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_imported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!BL" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!BM" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_battery"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!BN" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!BO" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_services_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!BP" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_services_energy_imported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!BQ" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["generator_energy_exported"].(float64)}},
						})

						// copy formulas down: column BR to BW
						copy_paste_requests = &sheets.CopyPasteRequest{
							PasteType: SHEET_PASTE_TYPE,
							Source: &sheets.GridRange{
								SheetId:          common.EncryptedCfg.Google.SummarySheetId,
								StartRowIndex:    4,
								EndRowIndex:      5,
								StartColumnIndex: 69,
								EndColumnIndex:   75,
							},
							Destination: &sheets.GridRange{
								SheetId:          common.EncryptedCfg.Google.SummarySheetId,
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
				for _, val_2 := range siteTOUHistory["response"].(map[string]any)[key_1].(map[string]any)["time_series"].([]any) {
					d, _ := time.Parse("2006-01-02T15:04:05-07:00", (val_2.(map[string]any)["timestamp"].(string)))

					if d.Year() == targetDate.Year() &&
						d.Month() == targetDate.Month() &&
						d.Day() == targetDate.Day() {
						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!BY" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!BZ" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_battery"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!CA" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_grid"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!CB" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!CC" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["solar_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!CD" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!CE" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!CF" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_grid"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!CG" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!CH" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_imported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!CI" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!CJ" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_battery"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!CK" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!CL" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_services_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!CM" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_services_energy_imported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  TELEMETRY_SHEET_NAME + "!CN" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["generator_energy_exported"].(float64)}},
						})

						// copy formulas down: column CO to CT
						copy_paste_requests = &sheets.CopyPasteRequest{
							PasteType: SHEET_PASTE_TYPE,
							Source: &sheets.GridRange{
								SheetId:          common.EncryptedCfg.Google.SummarySheetId,
								StartRowIndex:    4,
								EndRowIndex:      5,
								StartColumnIndex: 92,
								EndColumnIndex:   98,
							},
							Destination: &sheets.GridRange{
								SheetId:          common.EncryptedCfg.Google.SummarySheetId,
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
		PasteType: SHEET_PASTE_TYPE,
		Source: &sheets.GridRange{
			SheetId:          common.EncryptedCfg.Google.SummarySheetId,
			StartRowIndex:    4,
			EndRowIndex:      5,
			StartColumnIndex: 99,
			EndColumnIndex:   115,
		},
		Destination: &sheets.GridRange{
			SheetId:          common.EncryptedCfg.Google.SummarySheetId,
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
		PasteType: SHEET_PASTE_TYPE,
		Source: &sheets.GridRange{
			SheetId:          common.EncryptedCfg.Google.SummarySheetId,
			StartRowIndex:    int64(open_row) - 2,
			EndRowIndex:      int64(open_row) - 1,
			StartColumnIndex: 116,
			EndColumnIndex:   121,
		},
		Destination: &sheets.GridRange{
			SheetId:          common.EncryptedCfg.Google.SummarySheetId,
			StartRowIndex:    int64(open_row) - 1,
			EndRowIndex:      int64(open_row),
			StartColumnIndex: 116,
			EndColumnIndex:   121,
		},
	}
	request = append(request, &sheets.Request{CopyPaste: copy_paste_requests})

	// get existing list of backup events saved to gsheet
	srv := common.GetGoogleSheetService()
	event_list, err := srv.Spreadsheets.Values.Get(common.EncryptedCfg.Google.EnergySpreadsheetId, OUTAGE_SHEET_NAME + "!A2:C").Do()

	open_row = common.FindOpenRow(common.EncryptedCfg.Google.EnergySpreadsheetId, OUTAGE_SHEET_NAME + "!A:A")

	for _, val := range batteryBackupHistory["response"].(map[string]any)["events"].([]any) {
		var skip bool = false
		var dt time.Time

		// convert duration to hours
		duration := val.(map[string]any)["duration"].(float64) / 1000 / 60 / 60
		start, _ := time.Parse("2006-01-02T15:04:05-07:00", val.(map[string]any)["timestamp"].(string))

		for _, item := range event_list.Values {
			loc, _ := time.LoadLocation("America/Los_Angeles")
			dt, _ = time.Parse("2006-01-02T15:04:05Z", item[0].(string))
			dt = dt.In(loc)

			if start.Equal(dt) {
				skip = true
			}
		}

		if !skip {
			inputs.Data = append(inputs.Data, &sheets.ValueRange{
				Range:  OUTAGE_SHEET_NAME + "!A" + strconv.Itoa(open_row),
				Values: [][]any{{start}},
			})
			inputs.Data = append(inputs.Data, &sheets.ValueRange{
				Range:  OUTAGE_SHEET_NAME + "!C" + strconv.Itoa(open_row),
				Values: [][]any{{duration * 60}},
			})
		}
	}

	// batch write data and formula copies to sheet
	_, err = srv.Spreadsheets.Values.BatchUpdate(common.EncryptedCfg.Google.EnergySpreadsheetId, inputs).Do()
	if err != nil {
		slog.Error("writeEnergyDataToGsheet(): srv.Spreadsheets.Values.BatchUpdate(): " + err.Error())
	}
	_, err = srv.Spreadsheets.BatchUpdate(common.EncryptedCfg.Google.EnergySpreadsheetId, &sheets.BatchUpdateSpreadsheetRequest{Requests: request}).Do()
	if err != nil {
		slog.Error("writeEnergyDataToGsheet(): srv.Spreadsheets.BatchUpdate(): " + err.Error())
	}
}
