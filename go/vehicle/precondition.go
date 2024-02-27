package vehicle

import (
	"strconv"
	"time"

	"github.com/themonomers/tesla/go/common"
)

var ZIPCODE string

func init() {
	var err error

	var c = common.GetConfig()
	M3_VIN, err = c.String("vehicle.m3_vin")
	common.LogError("init(): load m3 vin", err)

	MX_VIN, err = c.String("vehicle.mx_vin")
	common.LogError("init(): load mx vin", err)

	EV_SPREADSHEET_ID, err = c.String("google.ev_spreadsheet_id")
	common.LogError("init(): load ev spreadsheet id", err)

	ZIPCODE, err = c.String("weather.zipcode")
	common.LogError("init(): load weather zipcode", err)
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
	climate_config, err := srv.Spreadsheets.Values.Get(EV_SPREADSHEET_ID, "Smart Climate!B3:H24").Do()
	common.LogError("PreconditionM3Start(): srv.Spreadsheets.Values.Get", err)

	// check if eco mode is on first so we don't have to even call the Tesla API if we don't have to
	if climate_config.Values[21][0] == "on" {
		return
	}

	// get local weather
	wdata := common.GetCurrentWeather(ZIPCODE)

	// get today's day of week to compare against Google Sheet temp preferences
	// for that day
	day_of_week := time.Now().Weekday()
	var d_temp float64
	var p_temp float64
	var seats []int

	// compare temp readings and threshold to determine heating or cooling temps
	// to use
	config_temp_cold, _ := strconv.ParseFloat(climate_config.Values[19][0].(string), 64)
	config_temp_hot, _ := strconv.ParseFloat(climate_config.Values[20][0].(string), 64)

	if wdata["main"].(map[string]interface{})["temp"].(float64) < config_temp_cold {
		// get pre-heat preferences
		switch day_of_week {
		case 0: // Sunday
			// get pre-heat preferences
			d_temp, err = strconv.ParseFloat(climate_config.Values[6][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[6][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[6][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[6][3].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[6][4].(string))
			seats = append(seats, seat_set)
			seats = append(seats, -1) // placeholder for index 3 as it's not assigned in the API
			seat_set, _ = strconv.Atoi(climate_config.Values[6][5].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[6][6].(string))
			seats = append(seats, seat_set)
		case 1: // Monday
			d_temp, err = strconv.ParseFloat(climate_config.Values[0][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[0][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[0][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[0][3].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[0][4].(string))
			seats = append(seats, seat_set)
			seats = append(seats, -1) // placeholder for index 3 as it's not assigned in the API
			seat_set, _ = strconv.Atoi(climate_config.Values[0][5].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[0][6].(string))
			seats = append(seats, seat_set)
		case 2: // Tuesday
			d_temp, err = strconv.ParseFloat(climate_config.Values[1][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[1][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[1][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[1][3].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[1][4].(string))
			seats = append(seats, seat_set)
			seats = append(seats, -1) // placeholder for index 3 as it's not assigned in the API
			seat_set, _ = strconv.Atoi(climate_config.Values[1][5].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[1][6].(string))
			seats = append(seats, seat_set)
		case 3: // Wednesday
			d_temp, err = strconv.ParseFloat(climate_config.Values[2][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[2][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[2][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[2][3].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[2][4].(string))
			seats = append(seats, seat_set)
			seats = append(seats, -1) // placeholder for index 3 as it's not assigned in the API
			seat_set, _ = strconv.Atoi(climate_config.Values[2][5].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[2][6].(string))
			seats = append(seats, seat_set)
		case 4: // Thursday
			d_temp, err = strconv.ParseFloat(climate_config.Values[3][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[3][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[3][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[3][3].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[3][4].(string))
			seats = append(seats, seat_set)
			seats = append(seats, -1) // placeholder for index 3 as it's not assigned in the API
			seat_set, _ = strconv.Atoi(climate_config.Values[3][5].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[3][6].(string))
			seats = append(seats, seat_set)
		case 5: // Friday
			d_temp, err = strconv.ParseFloat(climate_config.Values[4][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[4][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[4][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[4][3].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[4][4].(string))
			seats = append(seats, seat_set)
			seats = append(seats, -1) // placeholder for index 3 as it's not assigned in the API
			seat_set, _ = strconv.Atoi(climate_config.Values[4][5].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[4][6].(string))
			seats = append(seats, seat_set)
		case 6: // Saturday
			d_temp, err = strconv.ParseFloat(climate_config.Values[5][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[5][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[5][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[5][3].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[5][4].(string))
			seats = append(seats, seat_set)
			seats = append(seats, -1) // placeholder for index 3 as it's not assigned in the API
			seat_set, _ = strconv.Atoi(climate_config.Values[5][5].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[5][6].(string))
			seats = append(seats, seat_set)
		default:
			return
		}
	} else if wdata["main"].(map[string]interface{})["temp"].(float64) > config_temp_hot {
		// get pre-cool preferences
		switch day_of_week {
		case 0: // Sunday
			d_temp, err = strconv.ParseFloat(climate_config.Values[15][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[15][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[15][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[15][3].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[15][4].(string))
			seats = append(seats, seat_set)
			seats = append(seats, -1) // placeholder for index 3 as it's not assigned in the API
			seat_set, _ = strconv.Atoi(climate_config.Values[15][5].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[15][6].(string))
			seats = append(seats, seat_set)
		case 1: // Monday
			d_temp, err = strconv.ParseFloat(climate_config.Values[9][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[9][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[9][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[9][3].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[9][4].(string))
			seats = append(seats, seat_set)
			seats = append(seats, -1) // placeholder for index 3 as it's not assigned in the API
			seat_set, _ = strconv.Atoi(climate_config.Values[9][5].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[9][6].(string))
			seats = append(seats, seat_set)
		case 2: // Tuesday
			d_temp, err = strconv.ParseFloat(climate_config.Values[10][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[10][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[10][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[10][3].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[10][4].(string))
			seats = append(seats, seat_set)
			seats = append(seats, -1) // placeholder for index 3 as it's not assigned in the API
			seat_set, _ = strconv.Atoi(climate_config.Values[10][5].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[10][6].(string))
			seats = append(seats, seat_set)
		case 3: // Wednesday
			d_temp, err = strconv.ParseFloat(climate_config.Values[11][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[11][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[11][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[11][3].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[11][4].(string))
			seats = append(seats, seat_set)
			seats = append(seats, -1) // placeholder for index 3 as it's not assigned in the API
			seat_set, _ = strconv.Atoi(climate_config.Values[11][5].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[11][6].(string))
			seats = append(seats, seat_set)
		case 4: // Thursday
			d_temp, err = strconv.ParseFloat(climate_config.Values[12][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[12][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[12][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[12][3].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[12][4].(string))
			seats = append(seats, seat_set)
			seats = append(seats, -1) // placeholder for index 3 as it's not assigned in the API
			seat_set, _ = strconv.Atoi(climate_config.Values[12][5].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[12][6].(string))
			seats = append(seats, seat_set)
		case 5: // Friday
			d_temp, err = strconv.ParseFloat(climate_config.Values[13][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[13][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[13][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[13][3].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[13][4].(string))
			seats = append(seats, seat_set)
			seats = append(seats, -1) // placeholder for index 3 as it's not assigned in the API
			seat_set, _ = strconv.Atoi(climate_config.Values[13][5].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[13][6].(string))
			seats = append(seats, seat_set)
		case 6: // Saturday
			d_temp, err = strconv.ParseFloat(climate_config.Values[14][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[14][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[14][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[14][3].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[14][4].(string))
			seats = append(seats, seat_set)
			seats = append(seats, -1) // placeholder for index 3 as it's not assigned in the API
			seat_set, _ = strconv.Atoi(climate_config.Values[14][5].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[14][6].(string))
			seats = append(seats, seat_set)
		default:
			return
		}
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

		// specific date/time to create a crontab for later this morning at
		// the preferred stop time
		stop_time := common.GetTodayTime(climate_config.Values[18][0].(string))

		// create crontab to stop preconditioning
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
	climate_config, err := srv.Spreadsheets.Values.Get(EV_SPREADSHEET_ID, "Smart Climate!I3:L24").Do()
	common.LogError("PreconditionM3Start(): srv.Spreadsheets.Values.Get", err)

	// check if eco mode is on first so we don't have to even call the Tesla API if we don't have to
	if climate_config.Values[21][0] == "on" {
		return
	}

	// get local weather
	wdata := common.GetCurrentWeather(ZIPCODE)

	// get today's day of week to compare against Google Sheet temp preferences
	// for that day
	day_of_week := time.Now().Weekday()
	var d_temp float64
	var p_temp float64
	var seats []int

	// compare temp readings and threshold to determine heating or cooling temps
	// to use
	config_temp_cold, _ := strconv.ParseFloat(climate_config.Values[19][0].(string), 64)
	config_temp_hot, _ := strconv.ParseFloat(climate_config.Values[20][0].(string), 64)

	if wdata["main"].(map[string]interface{})["temp"].(float64) < config_temp_cold {
		// get pre-heat preferences
		switch day_of_week {
		case 0: // Sunday
			// get pre-heat preferences
			d_temp, err = strconv.ParseFloat(climate_config.Values[6][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[6][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[6][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[6][3].(string))
			seats = append(seats, seat_set)
		case 1: // Monday
			d_temp, err = strconv.ParseFloat(climate_config.Values[0][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[0][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[0][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[0][3].(string))
			seats = append(seats, seat_set)
		case 2: // Tuesday
			d_temp, err = strconv.ParseFloat(climate_config.Values[1][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[1][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[1][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[1][3].(string))
			seats = append(seats, seat_set)
		case 3: // Wednesday
			d_temp, err = strconv.ParseFloat(climate_config.Values[2][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[2][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[2][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[2][3].(string))
			seats = append(seats, seat_set)
		case 4: // Thursday
			d_temp, err = strconv.ParseFloat(climate_config.Values[3][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[3][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[3][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[3][3].(string))
			seats = append(seats, seat_set)
		case 5: // Friday
			d_temp, err = strconv.ParseFloat(climate_config.Values[4][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[4][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[4][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[4][3].(string))
			seats = append(seats, seat_set)
		case 6: // Saturday
			d_temp, err = strconv.ParseFloat(climate_config.Values[5][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[5][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[5][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[5][3].(string))
			seats = append(seats, seat_set)
		default:
			return
		}
	} else if wdata["main"].(map[string]interface{})["temp"].(float64) > config_temp_hot {
		// get pre-cool preferences
		switch day_of_week {
		case 0: // Sunday
			d_temp, err = strconv.ParseFloat(climate_config.Values[15][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[15][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[15][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[15][3].(string))
			seats = append(seats, seat_set)
		case 1: // Monday
			d_temp, err = strconv.ParseFloat(climate_config.Values[9][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[9][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[9][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[9][3].(string))
			seats = append(seats, seat_set)
		case 2: // Tuesday
			d_temp, err = strconv.ParseFloat(climate_config.Values[10][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[10][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[10][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[10][3].(string))
			seats = append(seats, seat_set)
		case 3: // Wednesday
			d_temp, err = strconv.ParseFloat(climate_config.Values[11][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[11][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[11][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[11][3].(string))
			seats = append(seats, seat_set)
		case 4: // Thursday
			d_temp, err = strconv.ParseFloat(climate_config.Values[12][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[12][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[12][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[12][3].(string))
			seats = append(seats, seat_set)
		case 5: // Friday
			d_temp, err = strconv.ParseFloat(climate_config.Values[13][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[13][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[13][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[13][3].(string))
			seats = append(seats, seat_set)
		case 6: // Saturday
			d_temp, err = strconv.ParseFloat(climate_config.Values[14][0].(string), 64)
			if err != nil {
				return
			}
			p_temp, _ = strconv.ParseFloat(climate_config.Values[14][1].(string), 64)

			seat_set, _ := strconv.Atoi(climate_config.Values[14][2].(string))
			seats = append(seats, seat_set)
			seat_set, _ = strconv.Atoi(climate_config.Values[14][3].(string))
			seats = append(seats, seat_set)
		default:
			return
		}
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

		// specific date/time to create a crontab for later this morning at
		// the preferred stop time
		stop_time := common.GetTodayTime(climate_config.Values[18][0].(string))

		// create crontab to stop preconditioning
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
