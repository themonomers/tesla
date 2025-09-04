package vehicle

import (
	"strconv"
	"time"

	"github.com/themonomers/tesla/go/common"
)

var PRIMARY_LAT float64
var PRIMARY_LNG float64

func init() {
	var err error

	var c = common.GetConfig()
	M3_VIN, err = c.String("vehicle.m3_vin")
	common.LogError("init(): load m3 vin", err)

	MX_VIN, err = c.String("vehicle.mx_vin")
	common.LogError("init(): load mx vin", err)

	EV_SPREADSHEET_ID, err = c.String("google.ev_spreadsheet_id")
	common.LogError("init(): load ev spreadsheet id", err)

	PRIMARY_LAT, err = c.Float("vehicle.primary_lat")
	common.LogError("init(): load vehicle primary lat", err)

	PRIMARY_LNG, err = c.Float("vehicle.primary_lng")
	common.LogError("init(): load vehicle primary lng", err)
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
func PreconditionM3Start() {
	// get configuration info
	srv := common.GetGoogleSheetService()
	climate_config, err := srv.Spreadsheets.Values.Get(EV_SPREADSHEET_ID, "Smart Climate!A3:P22").Do()
	common.LogError("PreconditionM3Start(): srv.Spreadsheets.Values.Get", err)

	// check if eco mode is on first so we don't have to even call the Tesla API if we don't have to
	if climate_config.Values[19][1] == "on" {
		return
	}

	// get local weather
	wdata := common.GetCurrentWeather(PRIMARY_LAT, PRIMARY_LNG)

	// get today's day of week to compare against Google Sheet temp preferences
	// for that day
	day_of_week := time.Now().Format("Monday")
	dow_index := common.FindStringIn2DArray(climate_config.Values, day_of_week)
	var d_temp float64
	var p_temp float64
	var seats []int
	var stop_time time.Time

	// compare temp readings and threshold to determine heating or cooling temps
	// to use
	config_temp_cold, _ := strconv.ParseFloat(climate_config.Values[17][1].(string), 64)
	config_temp_hot, _ := strconv.ParseFloat(climate_config.Values[18][1].(string), 64)

	if wdata["current"].(map[string]interface{})["temp"].(float64) < config_temp_cold {
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

		stop_time = common.GetTodayTime(climate_config.Values[dow_index[0]][9].(string))
	} else if wdata["current"].(map[string]interface{})["temp"].(float64) > config_temp_hot {
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
		seat_set, _ = strconv.Atoi(climate_config.Values[dow_index[1]][5].(string))
		seats = append(seats, seat_set)
		seats = append(seats, -1) // placeholder for index 3 as it's not assigned in the API
		seat_set, _ = strconv.Atoi(climate_config.Values[dow_index[1]][6].(string))
		seats = append(seats, seat_set)
		seat_set, _ = strconv.Atoi(climate_config.Values[dow_index[1]][7].(string))
		seats = append(seats, seat_set)

		stop_time = common.GetTodayTime(climate_config.Values[dow_index[1]][9].(string))
	} else {
		return // outside temp is within cold and hot thresholds so no preconditioning required; inside and outside car temp readings seem to be inaccurate until the HVAC runs
	}

	// no need to execute if unsure where the car is or if it's in motion
	data := GetVehicleData(M3_VIN)
	if common.IsVehicleAtPrimary(data) {
		// send command to start auto conditioning
		PreconditionCarStart(M3_VIN)

		// set driver and passenger temps
		SetCarTemp(M3_VIN, d_temp, p_temp)

		// set seat heater settings
		for i := 0; i < len(seats); i++ {
			if i == 3 {
				continue // # skip index 3 as it's not assigned in the API
			}
			SetCarSeatHeating(M3_VIN, i, seats[i])
		}

		// create crontab to stop preconditioning at preferred time later in the day
		common.DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 360 300 go run main.go -preconditionm3stop >> /home/pi/tesla/go/cron.log 2>&1")
		common.CreateCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 360 300 go run main.go -preconditionm3stop >> /home/pi/tesla/go/cron.log 2>&1",
			stop_time.Minute(),
			stop_time.Hour(),
			stop_time.Day(),
			int(stop_time.Month()))
	}
}

func PreconditionMXStart() {
	// get configuration info
	srv := common.GetGoogleSheetService()
	climate_config, err := srv.Spreadsheets.Values.Get(EV_SPREADSHEET_ID, "Smart Climate!A3:P22").Do()
	common.LogError("PreconditionM3Start(): srv.Spreadsheets.Values.Get", err)

	// check if eco mode is on first so we don't have to even call the Tesla API if we don't have to
	if climate_config.Values[19][10] == "on" {
		return
	}

	// get local weather
	wdata := common.GetCurrentWeather(PRIMARY_LAT, PRIMARY_LNG)

	// get today's day of week to compare against Google Sheet temp preferences
	// for that day
	day_of_week := time.Now().Format("Monday")
	dow_index := common.FindStringIn2DArray(climate_config.Values, day_of_week)
	var d_temp float64
	var p_temp float64
	var seats []int
	var stop_time time.Time

	// compare temp readings and threshold to determine heating or cooling temps
	// to use
	config_temp_cold, _ := strconv.ParseFloat(climate_config.Values[17][10].(string), 64)
	config_temp_hot, _ := strconv.ParseFloat(climate_config.Values[18][10].(string), 64)

	if wdata["current"].(map[string]interface{})["temp"].(float64) < config_temp_cold {
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

		stop_time = common.GetTodayTime(climate_config.Values[dow_index[0]][15].(string))
	} else if wdata["current"].(map[string]interface{})["temp"].(float64) > config_temp_hot {
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

		stop_time = common.GetTodayTime(climate_config.Values[dow_index[1]][15].(string))
	} else {
		return // outside temp is within cold and hot thresholds so no preconditioning required; inside and outside car temp readings seem to be inaccurate until the HVAC runs
	}

	// no need to execute if unsure where the car is or if it's in motion
	data := GetVehicleData(MX_VIN)
	if common.IsVehicleAtPrimary(data) {
		// send command to start auto conditioning
		PreconditionCarStart(MX_VIN)

		// set driver and passenger temps
		SetCarTemp(MX_VIN, d_temp, p_temp)

		// set seat heater settings
		for i := 0; i < len(seats); i++ {
			if i == 3 {
				continue // # skip index 3 as it's not assigned in the API
			}
			SetCarSeatHeating(MX_VIN, i, seats[i])
		}

		// create crontab to stop preconditioning at preferred time later in the day
		common.DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 360 300 go run main.go -preconditionmxstop >> /home/pi/tesla/go/cron.log 2>&1")
		common.CreateCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 360 300 go run main.go -preconditionmxstop >> /home/pi/tesla/go/cron.log 2>&1",
			stop_time.Minute(),
			stop_time.Hour(),
			stop_time.Day(),
			int(stop_time.Month()))
	}
}

// Sends command to stop vehicle preconditioning based on a previously scheduled
// crontab configured in a Google Sheet.
func PreconditionM3Stop() {
	preconditionStop(M3_VIN)
}

func PreconditionMXStop() {
	preconditionStop(MX_VIN)
}

func preconditionStop(vin string) {
	data := GetVehicleData(vin)

	if common.IsVehicleAtPrimary(data) {
		if data["response"].(map[string]interface{})["drive_state"].(map[string]interface{})["shift_state"] != nil {
			if data["response"].(map[string]interface{})["drive_state"].(map[string]interface{})["shift_state"].(string) != "D" &&
				data["response"].(map[string]interface{})["drive_state"].(map[string]interface{})["shift_state"].(string) != "R" &&
				data["response"].(map[string]interface{})["drive_state"].(map[string]interface{})["shift_state"].(string) != "N" { // only execute if the car is at primary location and in park
				PreconditionCarStop(vin)
			}
		} else {
			PreconditionCarStop(vin) // for some cars the shift_state is nil while in park
		}
	}
}

// Script to clean up crontabs created for Tesla Smart Climate.  Should be
// set to run in the middle of the day as all the crontabs are evening or
// early morning.
func RemoveTeslaCron() {
	common.DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 360 300 go run main.go -preconditionm3start >> /home/pi/tesla/go/cron.log 2>&1")
	common.DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 360 300 go run main.go -preconditionm3stop >> /home/pi/tesla/go/cron.log 2>&1")
	common.DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 360 300 go run main.go -preconditionmxstart >> /home/pi/tesla/go/cron.log 2>&1")
	common.DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 360 300 go run main.go -preconditionmxstop >> /home/pi/tesla/go/cron.log 2>&1")
}
