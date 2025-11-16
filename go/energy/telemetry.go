package energy

import (
	"strconv"
	"time"

	"github.com/influxdata/influxdb/client/v2"
	"github.com/themonomers/tesla/go/common"
	"google.golang.org/api/sheets/v4"
)

var ENERGY_SPREADSHEET_ID string
var SUMMARY_SHEET_ID int64
var EMAIL_1 string

func init() {
	var err error

	c := common.GetConfig()
	ENERGY_SPREADSHEET_ID, err = c.String("google.energy_spreadsheet_id")
	common.LogError("init(): load energy spreadsheet id", err)

	summary_sheet_id, err := c.String("google.summary_sheet_id")
	common.LogError("init(): load energy summary sheet id", err)
	SUMMARY_SHEET_ID, _ = strconv.ParseInt(summary_sheet_id, 10, 64)

	EMAIL_1, err = c.String("notification.email_1")
	common.LogError("init(): load email 1", err)
}

// Write the data for the previous day based on a cron job that runs just after
// midnight to ensure we get a full day's worth of data.
func WriteEnergyTelemetry() {
	yest := time.Now().Add(time.Duration(-24 * time.Hour))
	WriteEnergyDetailToDB(yest)
	WriteEnergySummaryToDB(yest)
	WriteBatteryChargeToDB(yest)
	WriteEnergyTOUSummaryToDB(yest)
	WriteEnergyTOUSummaryToGsheet(yest)

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

	c := common.GetDBClient()
	defer c.Close()

	// Create a new point batch
	bp, err := client.NewBatchPoints(client.BatchPointsConfig{
		Database: "energy",
	})
	common.LogError("WriteEnergyDetailToDB(): client.NewBatchPoints", err)

	for _, val := range data["response"].(map[string]any)["time_series"].([]any) {
		//d, err := time.Parse("2006-01-02", strings.Split(val.(map[string]any)["timestamp"].(string), "T")[0])
		d, err := time.Parse("2006-01-02T15:04:05-07:00", val.(map[string]any)["timestamp"].(string))
		common.LogError("WriteEnergyDetailToDB(): time.Parse", err)

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
					pt, err := client.NewPoint("energy_detail", tags, fields, d)
					common.LogError("WriteEnergyDetailToDB(): client.NewPoint", err)
					bp.AddPoint(pt)
				}
			}
			// Write the batch
			err = c.Write(bp)
			common.LogError("WriteEnergyDetailToDB(): c.Write", err)

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

	c := common.GetDBClient()
	defer c.Close()

	// Create a new point batch
	bp, err := client.NewBatchPoints(client.BatchPointsConfig{
		Database: "energy",
	})
	common.LogError("WriteEnergySummaryToDB(): client.NewBatchPoints", err)

	// write battery data
	// Create points and add to batch
	tags := map[string]string{"source": "total_pack_energy"}
	fields := map[string]any{
		"value": data["nominal_full_pack_energy"].(float64),
	}
	pt, err := client.NewPoint("energy_summary", tags, fields, date.Local().UTC())
	common.LogError("WriteEnergySummaryToDB(): client.NewPoint", err)
	bp.AddPoint(pt)

	// get battery data
	data = GetSiteStatus()
	tags = map[string]string{"source": "percentage_charged"}
	fields = map[string]any{
		"value": data["response"].(map[string]any)["percentage_charged"].(float64),
	}
	pt, err = client.NewPoint("energy_summary", tags, fields, date.Local().UTC())
	common.LogError("WriteEnergySummaryToDB(): client.NewPoint", err)
	bp.AddPoint(pt)

	// get solar data
	data = GetSiteHistory("day", date)
	d, err := time.Parse("2006-01-02T15:04:05-07:00", data["response"].(map[string]any)["time_series"].([]any)[0].(map[string]any)["timestamp"].(string))
	common.LogError("WriteEnergySummaryToDB(): time.Parse", err)

	// write solar data
	if d.Year() == date.Year() &&
		d.Month() == date.Month() &&
		d.Day() == date.Day() {
		for key, val := range data["response"].(map[string]any)["time_series"].([]any)[0].(map[string]any) {
			if key != "timestamp" &&
				key != "grid_services_energy_exported" &&
				key != "grid_services_energy_imported" &&
				key != "generator_energy_exported" {
				tags = map[string]string{"source": key}
				fields = map[string]any{
					"value": val.(float64),
				}
				pt, err = client.NewPoint("energy_summary", tags, fields, d)
				common.LogError("WriteEnergySummaryToDB(): client.NewPoint", err)
				bp.AddPoint(pt)
			}
		}
	}

	// get solar value
	data = GetSavingsForecast("day", date)
	for _, j := range data["response"].([]any) {
		d, err = time.Parse("2006-01-02T15:04:05-07:00", j.(map[string]any)["timestamp"].(string))
		common.LogError("WriteEnergySummaryToDB(): time.Parse", err)

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
			pt, err = client.NewPoint("energy_summary", tags, fields, d)
			common.LogError("WriteEnergySummaryToDB(): client.NewPoint", err)
			bp.AddPoint(pt)
		}
	}

	// Write the batch
	err = c.Write(bp)
	common.LogError("WriteEnergySummaryToDB(): c.Write", err)

	// Close client resources
	c.Close()
}

// Writes Tesla battery charge state history into an InfluxDB for
// Grafana visualization.  These are in 15 minute increments.
func WriteBatteryChargeToDB(date time.Time) {
	// get battery charge history data
	data := GetBatteryChargeHistory("day", date)

	c := common.GetDBClient()
	defer c.Close()

	// Create a new point batch
	bp, err := client.NewBatchPoints(client.BatchPointsConfig{
		Database: "energy",
	})
	common.LogError("WriteBatteryChargeToDB(): client.NewBatchPoints", err)

	for _, val := range data["response"].(map[string]any)["time_series"].([]any) {
		tags := map[string]string{"source": "percentage_charged"}
		fields := map[string]any{
			"value": val.(map[string]any)["soe"].(float64),
		}
		d, _ := time.Parse("2006-01-02T15:04:05-07:00", val.(map[string]any)["timestamp"].(string))
		pt, err := client.NewPoint("energy_detail", tags, fields, d)
		common.LogError("WriteBatteryChargeToDB(): client.NewPoint", err)
		bp.AddPoint(pt)
	}

	// Write the batch
	err = c.Write(bp)
	common.LogError("WriteBatteryChargeToDB(): c.Write", err)

	// Close client resources
	c.Close()
}

// Contains functions to read/write the solar and powerwall data, separated
// by peak/partial peak/off peak, into InfluxDB for tracking, analysis,
// and graphs.  The data is a summary level down to the day.
func WriteEnergyTOUSummaryToDB(date time.Time) {
	// get solar data for all day
	data := GetSiteHistory("day", date)

	// write solar data for all day
	c := common.GetDBClient()
	defer c.Close()

	// Create a new point batch
	bp, err := client.NewBatchPoints(client.BatchPointsConfig{
		Database: "summary",
	})
	common.LogError("WriteEnergyTOUSummaryToDB(): client.NewBatchPoints", err)

	d, err := time.Parse("2006-01-02T15:04:05-07:00", data["response"].(map[string]any)["time_series"].([]any)[0].(map[string]any)["timestamp"].(string))
	common.LogError("WriteEnergyTOUSummaryToDB(): time.Parse", err)

	if d.Year() == date.Year() &&
		d.Month() == date.Month() &&
		d.Day() == date.Day() {
		for key, val := range data["response"].(map[string]any)["time_series"].([]any)[0].(map[string]any) {
			if key != "timestamp" {
				tags := map[string]string{"source": key}
				fields := map[string]any{
					"value": val.(float64),
				}
				pt, err := client.NewPoint("all_day", tags, fields, d)
				common.LogError("WriteEnergyTOUSummaryToDB(): client.NewPoint", err)
				bp.AddPoint(pt)
			}
		}
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
					pt, err := client.NewPoint(key_1, tags, fields, d)
					common.LogError("WriteEnergyTOUSummaryToDB(): client.NewPoint", err)
					bp.AddPoint(pt)
				}
			}
		}
	}

	// Write the batch
	err = c.Write(bp)
	common.LogError("WriteEnergyTOUSummaryToDB(): c.Write", err)

	// Close client resources
	c.Close()
}

// Contains functions to read/write the solar and powerwall data, separated
// by peak/partial peak/off peak, into a Google Sheet for tracking, analysis,
// and graphs.  The data is a summary level down to the day.
func WriteEnergyTOUSummaryToGsheet(date time.Time) {
	// get local battery data
	data := getLocalSystemStatus()

	// write total pack energy value
	open_row := common.FindOpenRow(ENERGY_SPREADSHEET_ID, "Telemetry-Summary", "A:A")
	inputs := &sheets.BatchUpdateValuesRequest{
		ValueInputOption: "USER_ENTERED",
	}

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry-Summary!A" + strconv.Itoa(open_row),
		Values: [][]any{{time.Now().Add(time.Duration(-24 * time.Hour)).Format("January 02, 2006")}},
	})

	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry-Summary!B" + strconv.Itoa(open_row),
		Values: [][]any{{data["nominal_full_pack_energy"].(float64)}},
	})

	// get battery data
	data = GetSiteStatus()
	inputs.Data = append(inputs.Data, &sheets.ValueRange{
		Range:  "Telemetry-Summary!C" + strconv.Itoa(open_row),
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

	// write solar data for all day
	d, err := time.Parse("2006-01-02T15:04:05-07:00", data["response"].(map[string]any)["time_series"].([]any)[0].(map[string]any)["timestamp"].(string))
	common.LogError("WriteEnergySummaryToDB(): time.Parse", err)

	// write solar data
	if d.Year() == date.Year() &&
		d.Month() == date.Month() &&
		d.Day() == date.Day() {
		for _, val := range data["response"].(map[string]any)["time_series"].([]any) {
			inputs.Data = append(inputs.Data, &sheets.ValueRange{
				Range:  "Telemetry-Summary!F" + strconv.Itoa(open_row),
				Values: [][]any{{d.Format("January 02, 2006")}},
			})

			inputs.Data = append(inputs.Data, &sheets.ValueRange{
				Range:  "Telemetry-Summary!H" + strconv.Itoa(open_row),
				Values: [][]any{{val.(map[string]any)["consumer_energy_imported_from_solar"].(float64)}},
			})

			inputs.Data = append(inputs.Data, &sheets.ValueRange{
				Range:  "Telemetry-Summary!I" + strconv.Itoa(open_row),
				Values: [][]any{{val.(map[string]any)["consumer_energy_imported_from_battery"].(float64)}},
			})

			inputs.Data = append(inputs.Data, &sheets.ValueRange{
				Range:  "Telemetry-Summary!J" + strconv.Itoa(open_row),
				Values: [][]any{{val.(map[string]any)["consumer_energy_imported_from_grid"].(float64)}},
			})

			inputs.Data = append(inputs.Data, &sheets.ValueRange{
				Range:  "Telemetry-Summary!K" + strconv.Itoa(open_row),
				Values: [][]any{{val.(map[string]any)["consumer_energy_imported_from_generator"].(float64)}},
			})

			inputs.Data = append(inputs.Data, &sheets.ValueRange{
				Range:  "Telemetry-Summary!L" + strconv.Itoa(open_row),
				Values: [][]any{{val.(map[string]any)["solar_energy_exported"].(float64)}},
			})

			inputs.Data = append(inputs.Data, &sheets.ValueRange{
				Range:  "Telemetry-Summary!M" + strconv.Itoa(open_row),
				Values: [][]any{{val.(map[string]any)["battery_energy_exported"].(float64)}},
			})

			inputs.Data = append(inputs.Data, &sheets.ValueRange{
				Range:  "Telemetry-Summary!N" + strconv.Itoa(open_row),
				Values: [][]any{{val.(map[string]any)["battery_energy_imported_from_solar"].(float64)}},
			})

			inputs.Data = append(inputs.Data, &sheets.ValueRange{
				Range:  "Telemetry-Summary!O" + strconv.Itoa(open_row),
				Values: [][]any{{val.(map[string]any)["battery_energy_imported_from_grid"].(float64)}},
			})

			inputs.Data = append(inputs.Data, &sheets.ValueRange{
				Range:  "Telemetry-Summary!P" + strconv.Itoa(open_row),
				Values: [][]any{{val.(map[string]any)["battery_energy_imported_from_generator"].(float64)}},
			})

			inputs.Data = append(inputs.Data, &sheets.ValueRange{
				Range:  "Telemetry-Summary!Q" + strconv.Itoa(open_row),
				Values: [][]any{{val.(map[string]any)["grid_energy_imported"].(float64)}},
			})

			inputs.Data = append(inputs.Data, &sheets.ValueRange{
				Range:  "Telemetry-Summary!R" + strconv.Itoa(open_row),
				Values: [][]any{{val.(map[string]any)["grid_energy_exported_from_solar"].(float64)}},
			})

			inputs.Data = append(inputs.Data, &sheets.ValueRange{
				Range:  "Telemetry-Summary!S" + strconv.Itoa(open_row),
				Values: [][]any{{val.(map[string]any)["grid_energy_exported_from_battery"].(float64)}},
			})

			inputs.Data = append(inputs.Data, &sheets.ValueRange{
				Range:  "Telemetry-Summary!T" + strconv.Itoa(open_row),
				Values: [][]any{{val.(map[string]any)["grid_energy_exported_from_generator"].(float64)}},
			})

			inputs.Data = append(inputs.Data, &sheets.ValueRange{
				Range:  "Telemetry-Summary!U" + strconv.Itoa(open_row),
				Values: [][]any{{val.(map[string]any)["grid_services_energy_exported"].(float64)}},
			})

			inputs.Data = append(inputs.Data, &sheets.ValueRange{
				Range:  "Telemetry-Summary!V" + strconv.Itoa(open_row),
				Values: [][]any{{val.(map[string]any)["grid_services_energy_imported"].(float64)}},
			})

			inputs.Data = append(inputs.Data, &sheets.ValueRange{
				Range:  "Telemetry-Summary!W" + strconv.Itoa(open_row),
				Values: [][]any{{val.(map[string]any)["generator_energy_exported"].(float64)}},
			})
		}
	}

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
			if key_1 == "off_peak" {
				for _, val_2 := range data["response"].(map[string]any)[key_1].(map[string]any)["time_series"].([]any) {
					d, _ = time.Parse("2006-01-02T15:04:05-07:00", (val_2.(map[string]any)["timestamp"].(string)))

					if d.Year() == date.Year() &&
						d.Month() == date.Month() &&
						d.Day() == date.Day() {
						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!AE" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!AF" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_battery"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!AG" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_grid"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!AH" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!AI" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["solar_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!AJ" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!AK" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!AL" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_grid"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!AM" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!AN" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_imported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!AO" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!AP" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_battery"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!AQ" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!AR" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_services_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!AS" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_services_energy_imported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!AT" + strconv.Itoa(open_row),
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
			} else if key_1 == "partial_peak" { // write solar data for partial peak
				for _, val_2 := range data["response"].(map[string]any)[key_1].(map[string]any)["time_series"].([]any) {
					d, _ = time.Parse("2006-01-02T15:04:05-07:00", (val_2.(map[string]any)["timestamp"].(string)))

					if d.Year() == date.Year() &&
						d.Month() == date.Month() &&
						d.Day() == date.Day() {
						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!BB" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!BC" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_battery"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!BD" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_grid"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!BE" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!BF" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["solar_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!BG" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!BH" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!BI" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_grid"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!BJ" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!BK" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_imported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!BL" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!BM" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_battery"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!BN" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!BO" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_services_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!BP" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_services_energy_imported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!BQ" + strconv.Itoa(open_row),
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
			} else if key_1 == "peak" { // write solar data for peak
				for _, val_2 := range data["response"].(map[string]any)[key_1].(map[string]any)["time_series"].([]any) {
					d, _ = time.Parse("2006-01-02T15:04:05-07:00", (val_2.(map[string]any)["timestamp"].(string)))

					if d.Year() == date.Year() &&
						d.Month() == date.Month() &&
						d.Day() == date.Day() {
						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!BY" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!BZ" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_battery"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!CA" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_grid"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!CB" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["consumer_energy_imported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!CC" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["solar_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!CD" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!CE" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!CF" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_grid"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!CG" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["battery_energy_imported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!CH" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_imported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!CI" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_solar"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!CJ" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_battery"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!CK" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_energy_exported_from_generator"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!CL" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_services_energy_exported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!CM" + strconv.Itoa(open_row),
							Values: [][]any{{val_2.(map[string]any)["grid_services_energy_imported"].(float64)}},
						})

						inputs.Data = append(inputs.Data, &sheets.ValueRange{
							Range:  "Telemetry-Summary!CN" + strconv.Itoa(open_row),
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
	_, err = srv.Spreadsheets.Values.BatchUpdate(ENERGY_SPREADSHEET_ID, inputs).Do()
	common.LogError("WriteM3Telemetry(): srv.Spreadsheets.Values.BatchUpdate", err)
	_, err = srv.Spreadsheets.BatchUpdate(ENERGY_SPREADSHEET_ID, &sheets.BatchUpdateSpreadsheetRequest{Requests: request}).Do()
	common.LogError("WriteM3Telemetry(): srv.Spreadsheets.BatchUpdate", err)
}
