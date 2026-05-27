package vehicle

import (
	"fmt"
	"log/slog"
	"strconv"
	"time"

	"github.com/themonomers/tesla/go/common"
)

var GetTodayTime = common.GetTodayTime

var PRIMARY_LAT float64
var PRIMARY_LNG float64

func init() {
	c := GetConfig()
	PRIMARY_LAT, _ = c.Float("vehicle.primary_lat")
	PRIMARY_LNG, _ = c.Float("vehicle.primary_lng")
}

// Creates a trigger to precondition the cabin for the following morning,
// based on if the car is at the primary location and if "Eco Mode" is off
// similar to how Nest thermostats work for vacation scenarios.  With the
// new endpoints released, you can achieve the same functionality by setting
// scheduled departure for preconditioning.  I decided to keep this code
// running as I don't drive long distances so the added feature of
// preconditioning the battery, in addition to the cabin, is a waste of
// energy (entropy) for me.
func SetPrecondition(data map[string]any, eco_mode string, start_time time.Time) time.Time {
	vin := data["response"].(map[string]any)["vin"].(string)

	// check if eco mode is off first so we don't have to even call the
	// Tesla API if we don't have to
	if eco_mode == "off" {
		// check if the car is with 0.25 miles of the primary location
		if IsVehicleAtPrimary(data) {
			// create precondition start crontab at preferred time tomorrow
			DeleteCronTab(fmt.Sprintf("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go "+
				"-%s >> /home/pi/tesla/go/cron.log 2>&1", GetInLineSub("start", vin, "precondition")))
			CreateCronTab(fmt.Sprintf("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go "+
				"-%s >> /home/pi/tesla/go/cron.log 2>&1", GetInLineSub("start", vin, "precondition")),
				start_time.Minute(),
				start_time.Hour(),
				start_time.Day(),
				int(start_time.Month()))
		}

		return start_time
	} else {
		return time.Time{}
	}
}

// Checks a Google Sheet for heating and cooling preferences and sends a command
// to precondition the car.  Includes seat heating preferences. Originally this
// just used the inside car temp but to also account for the outside temperature,
// it might be more comfortable for the occupants to look at the average of the
// two to determine when to pre-heat/cool.
//
// Trying to use a weather API instead of the inside or outside temp data from
// the cars.  The temp data from the cars don't seem to be accurate enough
// and not representative of passenger comfort of when to pre-heat/cool.
func StartM3Precondition() {
	// get configuration info
	srv := GetGoogleSheetService()
	climate_config, err := srv.Spreadsheets.Values.Get(EV_SPREADSHEET_ID, "Climate!A3:P22").Do()
	if err != nil {
		slog.Error("StartM3Precondition(): srv.Spreadsheets.Values.Get(): " + err.Error())
	}

	// check if eco mode is on first so we don't have to even call the Tesla API if we don't have to
	if climate_config.Values[19][1] == "on" {
		return
	}

	// get local weather
	wdata := common.GetCurrentWeather(PRIMARY_LAT, PRIMARY_LNG)

	// get today's day of week to compare against Google Sheet temp preferences
	// for that day
	day_of_week := time.Now().Format("Monday")
	dow_index := FindStringIn2DArray(climate_config.Values, day_of_week)
	var d_temp float64
	var p_temp float64
	var seats []int
	var stop_time time.Time
	var mode string

	// compare temp readings and threshold to determine heating or cooling temps
	// to use
	config_temp_cold, _ := strconv.ParseFloat(climate_config.Values[17][1].(string), 64)
	config_temp_hot, _ := strconv.ParseFloat(climate_config.Values[18][1].(string), 64)

	if wdata["current"].(map[string]any)["temp"].(float64) < config_temp_cold {
		// get pre-heat preferences
		d_temp, err = strconv.ParseFloat(climate_config.Values[dow_index[0]][1].(string), 64)
		if err != nil {
			return
		}
		p_temp, _ = strconv.ParseFloat(climate_config.Values[dow_index[0]][2].(string), 64)

		seat_set, _ := strconv.Atoi(climate_config.Values[dow_index[0]][3].(string))
		seats = append(seats, seat_set)
		seat_set, _ = strconv.Atoi(climate_config.Values[dow_index[0]][4].(string))
		seats = append(seats, seat_set)
		seat_set, _ = strconv.Atoi(climate_config.Values[dow_index[0]][5].(string))
		seats = append(seats, seat_set)
		seats = append(seats, -1) // placeholder for index 3 as it's not assigned in the API
		seat_set, _ = strconv.Atoi(climate_config.Values[dow_index[0]][6].(string))
		seats = append(seats, seat_set)
		seat_set, _ = strconv.Atoi(climate_config.Values[dow_index[0]][7].(string))
		seats = append(seats, seat_set)

		if climate_config.Values[dow_index[0]][9].(string) == "skip" {
			return
		} else {
			stop_time = GetTodayTime(climate_config.Values[dow_index[0]][9].(string))
		}

		mode = "heat"
	} else if wdata["current"].(map[string]any)["temp"].(float64) > config_temp_hot {
		// get pre-cool preferences
		d_temp, err = strconv.ParseFloat(climate_config.Values[dow_index[1]][1].(string), 64)
		if err != nil {
			return
		}
		p_temp, _ = strconv.ParseFloat(climate_config.Values[dow_index[1]][2].(string), 64)

		seat_set, _ := strconv.Atoi(climate_config.Values[dow_index[1]][3].(string))
		seats = append(seats, seat_set)
		seat_set, _ = strconv.Atoi(climate_config.Values[dow_index[1]][4].(string))
		seats = append(seats, seat_set)

		if climate_config.Values[dow_index[1]][9].(string) == "skip" {
			return
		} else {
			stop_time = GetTodayTime(climate_config.Values[dow_index[1]][9].(string))
		}

		mode = "cool"
	} else {
		return // outside temp is within cold and hot thresholds so no preconditioning required; inside and outside car temp readings seem to be inaccurate until the HVAC runs
	}

	// no need to execute the car is not at primary location
	data := GetVehicleData(M3_VIN)
	if IsVehicleAtPrimary(data) {
		// send command to start auto conditioning
		StartPrecondition(M3_VIN)

		// set driver and passenger temps
		SetTemp(M3_VIN, d_temp, p_temp)

		// set seat heater settings
		for i := 0; i < len(seats); i++ {
			if i == 3 {
				continue // # skip index 3 as it's not assigned in the API
			}

			switch mode {
			case "heat":
				SetSeatHeating(M3_VIN, i, seats[i])
			case "cool":
				SetSeatCooling(M3_VIN, i+1, seats[i])
			}
		}

		// create crontab to stop preconditioning at preferred time later in the day
		setupStopCron(M3_VIN, stop_time)
	}
}

func StartMXPrecondition() {
	// get configuration info
	srv := GetGoogleSheetService()
	climate_config, err := srv.Spreadsheets.Values.Get(EV_SPREADSHEET_ID, "Climate!A3:P22").Do()
	if err != nil {
		slog.Error("StartMXPrecondition(): srv.Spreadsheets.Values.Get(): " + err.Error())
	}

	// check if eco mode is on first so we don't have to even call the Tesla API if we don't have to
	if climate_config.Values[19][10] == "on" {
		return
	}

	// get local weather
	wdata := common.GetCurrentWeather(PRIMARY_LAT, PRIMARY_LNG)

	// get today's day of week to compare against Google Sheet temp preferences
	// for that day
	day_of_week := time.Now().Format("Monday")
	dow_index := FindStringIn2DArray(climate_config.Values, day_of_week)
	var d_temp float64
	var p_temp float64
	var seats []int
	var stop_time time.Time

	// compare temp readings and threshold to determine heating or cooling temps
	// to use
	config_temp_cold, _ := strconv.ParseFloat(climate_config.Values[17][10].(string), 64)
	config_temp_hot, _ := strconv.ParseFloat(climate_config.Values[18][10].(string), 64)

	if wdata["current"].(map[string]any)["temp"].(float64) < config_temp_cold {
		// get pre-heat preferences
		d_temp, err = strconv.ParseFloat(climate_config.Values[dow_index[0]][10].(string), 64)
		if err != nil {
			return
		}
		p_temp, _ = strconv.ParseFloat(climate_config.Values[dow_index[0]][11].(string), 64)

		seat_set, _ := strconv.Atoi(climate_config.Values[dow_index[0]][12].(string))
		seats = append(seats, seat_set)
		seat_set, _ = strconv.Atoi(climate_config.Values[dow_index[0]][13].(string))
		seats = append(seats, seat_set)

		if climate_config.Values[dow_index[0]][15].(string) == "skip" {
			return
		} else {
			stop_time = GetTodayTime(climate_config.Values[dow_index[0]][15].(string))
		}
	} else if wdata["current"].(map[string]any)["temp"].(float64) > config_temp_hot {
		// get pre-cool preferences
		d_temp, err = strconv.ParseFloat(climate_config.Values[dow_index[1]][10].(string), 64)
		if err != nil {
			return
		}
		p_temp, _ = strconv.ParseFloat(climate_config.Values[dow_index[1]][11].(string), 64)

		seat_set, _ := strconv.Atoi(climate_config.Values[dow_index[1]][12].(string))
		seats = append(seats, seat_set)
		seat_set, _ = strconv.Atoi(climate_config.Values[dow_index[1]][13].(string))
		seats = append(seats, seat_set)

		if climate_config.Values[dow_index[1]][15].(string) == "skip" {
			return
		} else {
			stop_time = GetTodayTime(climate_config.Values[dow_index[1]][15].(string))
		}
	} else {
		return // outside temp is within cold and hot thresholds so no preconditioning required; inside and outside car temp readings seem to be inaccurate until the HVAC runs
	}

	// no need to execute if the car is not at primary location
	data := GetVehicleData(MX_VIN)
	if IsVehicleAtPrimary(data) {
		// send command to start auto conditioning
		StartPrecondition(MX_VIN)

		// set driver and passenger temps
		SetTemp(MX_VIN, d_temp, p_temp)

		// set seat heater settings
		for i := 0; i < len(seats); i++ {
			if i == 3 {
				continue // # skip index 3 as it's not assigned in the API
			}
			SetSeatHeating(MX_VIN, i, seats[i])
		}

		// create crontab to stop preconditioning at preferred time later in the day
		setupStopCron(MX_VIN, stop_time)
	}
}

// Sends command to stop vehicle preconditioning based on a previously scheduled
// crontab configured in a Google Sheet.
func StopPreconditionCheck(vin string) {
	data := GetVehicleData(vin)

	if IsVehicleAtPrimary(data) {
		if data["response"].(map[string]any)["drive_state"].(map[string]any)["shift_state"] != nil {
			if data["response"].(map[string]any)["drive_state"].(map[string]any)["shift_state"].(string) != "D" &&
				data["response"].(map[string]any)["drive_state"].(map[string]any)["shift_state"].(string) != "R" &&
				data["response"].(map[string]any)["drive_state"].(map[string]any)["shift_state"].(string) != "N" { // only execute if the car is at primary location and in park
				StopPrecondition(vin)
			}
		} else {
			StopPrecondition(vin) // for some cars the shift_state is nil while in park
		}
	}
}

func setupStopCron(vin string, stop_time time.Time) {
	DeleteCronTab(fmt.Sprintf("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -%s >> "+
		"/home/pi/tesla/go/cron.log 2>&1", GetInLineSub("stop", vin, "precondition")))
	CreateCronTab(fmt.Sprintf("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -%s >> "+
		"/home/pi/tesla/go/cron.log 2>&1", GetInLineSub("stop", vin, "precondition")),
		stop_time.Minute(),
		stop_time.Hour(),
		stop_time.Day(),
		int(stop_time.Month()))
}
