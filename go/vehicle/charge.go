package vehicle

import (
	"math"
	"strconv"
	"time"

	"github.com/themonomers/tesla/go/common"
)

type Range struct {
	Start time.Time
	End   time.Time
}

var M3_VIN string
var MX_VIN string
var EV_SPREADSHEET_ID string
var EMAIL_1 string
var EMAIL_2 string

var MX_FULL_CHARGE_RATE_AT_PRIMARY float64 = 25   // (mi/hr)
var M3_FULL_CHARGE_RATE_AT_PRIMARY float64 = 37   // (mi/hr)
var MX_FULL_CHARGE_RATE_AT_SECONDARY float64 = 20 // (mi/hr)
var M3_FULL_CHARGE_RATE_AT_SECONDARY float64 = 30 // (mi/hr)

func init() {
	var err error

	var c = common.GetConfig()
	M3_VIN, err = c.String("vehicle.m3_vin")
	common.LogError("init(): load m3 vin", err)

	MX_VIN, err = c.String("vehicle.mx_vin")
	common.LogError("init(): load mx vin", err)

	EV_SPREADSHEET_ID, err = c.String("google.ev_spreadsheet_id")
	common.LogError("init(): load ev spreadsheet id", err)

	EMAIL_1, err = c.String("notification.email_1")
	common.LogError("init(): load email 1", err)

	EMAIL_2, err = c.String("notification.email_2")
	common.LogError("init(): load email 2", err)
}

// Checks to see if the vehicles are plugged in, inferred from the charge
// port door status, and sends an email to notify if it's not.  Also sets
// scheduled charging time to start charging at the calculated date and time.
// Skips if it's not within 0.25 miles from the primary location.
//
// If one of the other cars is in the secondary location, set time charge
// start time based on the secondary charge rate and set the charge start
// time for the one at the primary location to charge at full charge rate.
func NotifyIsTeslaPluggedIn() {
	// get all vehicle data to avoid repeat API calls
	m3_data := GetVehicleData(M3_VIN)
	mx_data := GetVehicleData(MX_VIN)

	// get car info
	charge_port_door_open := m3_data["response"].(map[string]any)["charge_state"].(map[string]any)["charge_port_door_open"].(bool)
	battery_level := m3_data["response"].(map[string]any)["charge_state"].(map[string]any)["battery_level"].(float64)
	battery_range := m3_data["response"].(map[string]any)["charge_state"].(map[string]any)["battery_range"].(float64)

	// get charging configuration info
	srv := common.GetGoogleSheetService()
	charge_config, err := srv.Spreadsheets.Values.Get(EV_SPREADSHEET_ID, "Smart Charger!A3:C11").Do()
	common.LogError("NotifyIsTeslaPluggedIn(): srv.Spreadsheets.Values.Get", err)

	// get climate configuration info
	climate_config, err := srv.Spreadsheets.Values.Get(EV_SPREADSHEET_ID, "Smart Climate!A3:P22").Do()
	common.LogError("NotifyIsTeslaPluggedIn(): srv.Spreadsheets.Values.Get", err)

	// check if email notification is set to "on" first
	if charge_config.Values[8][1] == "on" {
		// send an email if the charge port door is not open, i.e. not plugged in
		if !charge_port_door_open {
			common.SendEmail(EMAIL_1,
				"Please Plug In Your Model 3",
				getPluggedInMessage("Model 3", battery_level, battery_range),
				"")
		}
	}

	charge_port_door_open = mx_data["response"].(map[string]any)["charge_state"].(map[string]any)["charge_port_door_open"].(bool)
	battery_level = mx_data["response"].(map[string]any)["charge_state"].(map[string]any)["battery_level"].(float64)
	battery_range = mx_data["response"].(map[string]any)["charge_state"].(map[string]any)["battery_range"].(float64)

	// check if email notification is set to "on" first
	if charge_config.Values[8][2] == "on" {
		// send an email if the charge port door is not open, i.e. not plugged in
		if !charge_port_door_open {
			common.SendEmail(EMAIL_2,
				"Please Plug In Your Model X",
				getPluggedInMessage("Model X", battery_level, battery_range),
				EMAIL_1)
		}
	}

	// set cars for scheduled charging
	day_of_week := time.Now().AddDate(0, 0, 1).Format("Monday")
	dow_index := common.FindStringIn2DArray(charge_config.Values, day_of_week)
	m3_target_finish_time := common.GetTomorrowTime(charge_config.Values[dow_index[0]][1].(string))
	mx_target_finish_time := common.GetTomorrowTime(charge_config.Values[dow_index[0]][2].(string))

	dow_index = common.FindStringIn2DArray(climate_config.Values, day_of_week)
	m3_climate_start_time := common.GetTomorrowTime(climate_config.Values[dow_index[0]][8].(string))
	mx_climate_start_time := common.GetTomorrowTime(climate_config.Values[dow_index[0]][14].(string))

	scheduleM3Charging(m3_data, mx_data, m3_target_finish_time, mx_target_finish_time)
	scheduleMXCharging(m3_data, mx_data, m3_target_finish_time, mx_target_finish_time)

	// set cabin preconditioning the next morning
	SetM3Precondition(m3_data, climate_config.Values[19][1].(string), m3_climate_start_time)
	SetMXPrecondition(mx_data, climate_config.Values[19][10].(string), mx_climate_start_time)
}

// Called by a crontab to read vehicle range and expected charge
// finish time from a Google Sheet, then call the API to set a time
// for scheduled charging in the vehicle.
func scheduleM3Charging(m3_data map[string]any, mx_data map[string]any, m3_target_finish_time time.Time, mx_target_finish_time time.Time) {
	var start_time time.Time

	if m3_data["response"].(map[string]any)["charge_state"].(map[string]any)["charging_state"].(string) != "Complete" {
		// get calculated start time depending on location of cars
		if common.IsVehicleAtPrimary(m3_data) &&
			common.IsVehicleAtPrimary(mx_data) {
			start_time = calculateScheduledCharging("m3_primary_shared_charging",
				m3_data,
				mx_data,
				m3_target_finish_time,
				mx_target_finish_time)
		} else if common.IsVehicleAtPrimary(m3_data) &&
			!common.IsVehicleAtPrimary(mx_data) {
			start_time = calculateScheduledCharging("m3_primary_full_rate",
				m3_data,
				mx_data,
				m3_target_finish_time,
				mx_target_finish_time)
		} else if common.IsVehicleAtSecondary(m3_data) {
			start_time = calculateScheduledCharging("m3_secondary_full_rate",
				m3_data,
				mx_data,
				m3_target_finish_time,
				mx_target_finish_time)
		} else {
			return
		}

		//		fmt.Println(start_time)

		total_minutes := (start_time.Hour() * 60) + start_time.Minute()

		// Remove any previous scheduled charging by this program, temporarily set to
		// id=1, until I can figure out how to view the list of charge schedules and
		// their corresponding ID's.
		RemoveChargeSchedule(M3_VIN, 1)
		AddChargeSchedule(M3_VIN, m3_data["response"].(map[string]any)["drive_state"].(map[string]any)["latitude"].(float64), m3_data["response"].(map[string]any)["drive_state"].(map[string]any)["longitude"].(float64), total_minutes, 1)
		StopChargeVehicle(M3_VIN) // for some reason charging starts sometimes after scheduled charging API is called

		// send email notification
		common.SendEmail(EMAIL_1,
			"Model 3 Set to Charge",
			getScheduledChargeMessage("Model 3", m3_data, start_time, m3_target_finish_time),
			"")
	}
}

func scheduleMXCharging(m3_data map[string]any, mx_data map[string]any, m3_target_finish_time time.Time, mx_target_finish_time time.Time) {
	var start_time time.Time

	if mx_data["response"].(map[string]any)["charge_state"].(map[string]any)["charging_state"].(string) != "Complete" {
		// get calculated start time depending on location of cars
		if common.IsVehicleAtPrimary(mx_data) &&
			common.IsVehicleAtPrimary(m3_data) {
			start_time = calculateScheduledCharging("mx_primary_shared_charging",
				m3_data,
				mx_data,
				m3_target_finish_time,
				mx_target_finish_time)
		} else if common.IsVehicleAtPrimary(mx_data) &&
			!common.IsVehicleAtPrimary(m3_data) {
			start_time = calculateScheduledCharging("mx_primary_full_rate",
				m3_data,
				mx_data,
				m3_target_finish_time,
				mx_target_finish_time)
		} else if common.IsVehicleAtSecondary(mx_data) {
			start_time = calculateScheduledCharging("mx_secondary_full_rate",
				m3_data,
				mx_data,
				m3_target_finish_time,
				mx_target_finish_time)
		} else {
			return
		}

		//		fmt.Println(start_time)

		total_minutes := (start_time.Hour() * 60) + start_time.Minute()

		RemoveChargeSchedule(MX_VIN, 1)
		AddChargeSchedule(MX_VIN, mx_data["response"].(map[string]any)["drive_state"].(map[string]any)["latitude"].(float64), mx_data["response"].(map[string]any)["drive_state"].(map[string]any)["longitude"].(float64), total_minutes, 1)
		StopChargeVehicle(MX_VIN) // for some reason charging starts sometimes after scheduled charging API is called

		// send email notification
		common.SendEmail(EMAIL_1,
			"Model X Set to Charge",
			getScheduledChargeMessage("Model X", mx_data, start_time, mx_target_finish_time),
			"")
	}
}

// Calculates the scheduled charging time for 2 vehicles depending
// on their location, charge state, and finish time.
func calculateScheduledCharging(scenario string, m3_data map[string]any, mx_data map[string]any, m3_target_finish_time time.Time, mx_target_finish_time time.Time) time.Time {
	var m3_start_time time.Time
	var mx_start_time time.Time

	// Calculate how many miles are needed for charging based on
	// current range and charging % target
	mx_current_range := mx_data["response"].(map[string]any)["charge_state"].(map[string]any)["battery_range"].(float64)
	m3_current_range := m3_data["response"].(map[string]any)["charge_state"].(map[string]any)["battery_range"].(float64)

	mx_max_range := (mx_data["response"].(map[string]any)["charge_state"].(map[string]any)["battery_range"].(float64) /
		(mx_data["response"].(map[string]any)["charge_state"].(map[string]any)["battery_level"].(float64) / 100.0))
	m3_max_range := (m3_data["response"].(map[string]any)["charge_state"].(map[string]any)["battery_range"].(float64) /
		(m3_data["response"].(map[string]any)["charge_state"].(map[string]any)["battery_level"].(float64) / 100.0))

	mx_charge_limit := mx_data["response"].(map[string]any)["charge_state"].(map[string]any)["charge_limit_soc"].(float64) / 100.0
	m3_charge_limit := m3_data["response"].(map[string]any)["charge_state"].(map[string]any)["charge_limit_soc"].(float64) / 100.0

	mx_target_range := mx_max_range * mx_charge_limit
	m3_target_range := m3_max_range * m3_charge_limit

	mx_miles_needed := 0.0
	if (mx_target_range - mx_current_range) > 0 {
		mx_miles_needed = mx_target_range - mx_current_range
	}
	m3_miles_needed := 0.0
	if (m3_target_range - m3_current_range) > 0 {
		m3_miles_needed = m3_target_range - m3_current_range
	}

	// Calculate scheduled charging time based on location of cars
	if scenario == "mx_primary_shared_charging" || scenario == "m3_primary_shared_charging" {
		mx_charging_time_at_full_rate := mx_miles_needed / MX_FULL_CHARGE_RATE_AT_PRIMARY // hours
		m3_charging_time_at_full_rate := m3_miles_needed / M3_FULL_CHARGE_RATE_AT_PRIMARY // hours

		mx_start_time_at_full_rate := mx_target_finish_time.Add(time.Duration(-mx_charging_time_at_full_rate * float64(time.Hour)))
		m3_start_time_at_full_rate := m3_target_finish_time.Add(time.Duration(-m3_charging_time_at_full_rate * float64(time.Hour)))

		// Determine if there is a charging time overlap
		overlap := getRangeOverlap(mx_start_time_at_full_rate, mx_target_finish_time, m3_start_time_at_full_rate, m3_target_finish_time)

		// 1.  Charging times don't overlap
		//
		//                                     Charging at full rate   | 10:00
		// Car 1                           |===========================|
		// Car 2 |======================|
		//        Charging at full rate | 7:00
		if overlap <= 0 {
			if scenario == "m3_primary_shared_charging" {
				return m3_start_time_at_full_rate
			}

			if scenario == "mx_primary_shared_charging" {
				return mx_start_time_at_full_rate
			}
		} else {
			// 2a.  Charging times overlap, fully with different finish times
			//
			//       Charging at
			//       full rate                        Charging at full rate | 10:00
			// Car 1 |============|==============|==========================|
			// Car 2              |==============|
			//             Charging at half rate | 7:00
			if !mx_target_finish_time.Equal(m3_target_finish_time) &&
				((mx_start_time_at_full_rate.Before(m3_start_time_at_full_rate) && mx_target_finish_time.After(m3_target_finish_time)) ||
					(m3_start_time_at_full_rate.Before(mx_start_time_at_full_rate) && m3_target_finish_time.After(mx_target_finish_time))) {
				// Find the longer session
				if mx_target_finish_time.Sub(mx_start_time_at_full_rate).Seconds() > m3_target_finish_time.Sub(m3_start_time_at_full_rate).Seconds() {
					// Car 2
					m3_charging_time_at_half_rate := m3_miles_needed / (M3_FULL_CHARGE_RATE_AT_PRIMARY / 2)
					m3_start_time = m3_target_finish_time.Add(time.Duration(-m3_charging_time_at_half_rate * float64(time.Hour)))

					// Car 1
					mx_miles_added_at_full_rate := mx_target_finish_time.Sub(m3_target_finish_time).Seconds() / 60 / 60 * MX_FULL_CHARGE_RATE_AT_PRIMARY
					mx_miles_added_at_half_rate := m3_charging_time_at_half_rate * (MX_FULL_CHARGE_RATE_AT_PRIMARY / 2)
					mx_miles_remaining := mx_miles_needed - mx_miles_added_at_full_rate - mx_miles_added_at_half_rate
					mx_start_time = mx_target_finish_time.Add(time.Duration(-mx_miles_added_at_full_rate / MX_FULL_CHARGE_RATE_AT_PRIMARY * float64(time.Hour)))
					mx_start_time = mx_start_time.Add(time.Duration(-mx_miles_added_at_half_rate / (MX_FULL_CHARGE_RATE_AT_PRIMARY / 2) * float64(time.Hour)))
					mx_start_time = mx_start_time.Add(time.Duration(-mx_miles_remaining / MX_FULL_CHARGE_RATE_AT_PRIMARY * float64(time.Hour)))

				} else {
					// Car 2
					mx_charging_time_at_half_rate := mx_miles_needed / (MX_FULL_CHARGE_RATE_AT_PRIMARY / 2)
					mx_start_time = mx_target_finish_time.Add(time.Duration(-mx_charging_time_at_half_rate * float64(time.Hour)))

					// Car 1
					m3_miles_added_at_full_rate := m3_target_finish_time.Sub(mx_target_finish_time).Seconds() / 60 / 60 * M3_FULL_CHARGE_RATE_AT_PRIMARY
					m3_miles_added_at_half_rate := mx_charging_time_at_half_rate * (M3_FULL_CHARGE_RATE_AT_PRIMARY / 2)
					m3_miles_remaining := m3_miles_needed - m3_miles_added_at_full_rate - m3_miles_added_at_half_rate
					m3_start_time = m3_target_finish_time.Add(time.Duration(-m3_miles_added_at_full_rate / M3_FULL_CHARGE_RATE_AT_PRIMARY * float64(time.Hour)))
					m3_start_time = m3_start_time.Add(time.Duration(-m3_miles_added_at_half_rate / (M3_FULL_CHARGE_RATE_AT_PRIMARY / 2) * float64(time.Hour)))
					m3_start_time = m3_start_time.Add(time.Duration(-m3_miles_remaining / M3_FULL_CHARGE_RATE_AT_PRIMARY * float64(time.Hour)))
				}
				// 2b.  Charging times overlap, partially
				//
				//                                        Charging at full rate | 10:00
				// Car 1                      |=======|=========================|
				// Car 2 |====================|=======|
				//        Charging at full            | 7:00
				//        rate                Charging at
				//                            half rate
			} else if mx_target_finish_time.After(m3_target_finish_time) {
				// Car 1
				mx_miles_added_at_full_rate := mx_target_finish_time.Sub(m3_target_finish_time).Seconds() /
					60 /
					60 *
					MX_FULL_CHARGE_RATE_AT_PRIMARY
				mx_miles_remaining := mx_miles_needed - mx_miles_added_at_full_rate
				mx_charging_time_at_half_rate := mx_miles_remaining / (MX_FULL_CHARGE_RATE_AT_PRIMARY / 2) // hours
				mx_start_time := m3_target_finish_time.Add(time.Duration(-mx_charging_time_at_half_rate * float64(time.Hour)))

				// Car 2
				m3_miles_added_at_half_rate := m3_target_finish_time.Sub(mx_start_time).Seconds() /
					60 /
					60 *
					(M3_FULL_CHARGE_RATE_AT_PRIMARY / 2)
				m3_miles_remaining := m3_miles_needed - m3_miles_added_at_half_rate
				m3_charging_time_at_full_rate = m3_miles_remaining / M3_FULL_CHARGE_RATE_AT_PRIMARY // hours
				m3_start_time = mx_start_time.Add(time.Duration(-m3_charging_time_at_full_rate * float64(time.Hour)))
			} else if mx_target_finish_time.Before(m3_target_finish_time) {
				// Car 1
				m3_miles_added_at_full_rate := m3_target_finish_time.Sub(mx_target_finish_time).Seconds() /
					60 /
					60 *
					M3_FULL_CHARGE_RATE_AT_PRIMARY
				m3_miles_remaining := m3_miles_needed - m3_miles_added_at_full_rate
				m3_charging_time_at_half_rate := m3_miles_remaining / (M3_FULL_CHARGE_RATE_AT_PRIMARY / 2) // hours
				m3_start_time = mx_target_finish_time.Add(time.Duration(-m3_charging_time_at_half_rate * float64(time.Hour)))

				// Car 2
				mx_miles_added_at_half_rate := mx_target_finish_time.Sub(m3_start_time).Seconds() /
					60 /
					60 *
					(MX_FULL_CHARGE_RATE_AT_PRIMARY / 2)
				mx_miles_remaining := mx_miles_needed - mx_miles_added_at_half_rate
				mx_charging_time_at_full_rate = mx_miles_remaining / MX_FULL_CHARGE_RATE_AT_PRIMARY // hours
				mx_start_time = m3_start_time.Add(time.Duration(-mx_charging_time_at_full_rate * float64(time.Hour)))

				// 2c.  Charging times overlap, fully with the same finish times
				//
				// For the longer/earlier start time, calculate the start time based on a part of
				// the charging session being at half rate and another part at full rate.  The session
				// will charge at half rate when the other car begins charging but the difference in
				// miles/charge that starts before the other car will be at full rate.
				//
				//                                  Charging at half rate   | 07:00
				// Car 1                        |===========================|
				// Car 2 |======================|===========================|
				//        Charging at full rate
			} else if mx_target_finish_time.Equal(m3_target_finish_time) {
				mx_charging_time_at_half_rate := mx_miles_needed / (MX_FULL_CHARGE_RATE_AT_PRIMARY / 2) // hours
				m3_charging_time_at_half_rate := m3_miles_needed / (M3_FULL_CHARGE_RATE_AT_PRIMARY / 2) // hours

				mx_start_time_at_half_rate := mx_target_finish_time.Add(time.Duration(-mx_charging_time_at_half_rate * float64(time.Hour)))
				m3_start_time_at_half_rate := m3_target_finish_time.Add(time.Duration(-m3_charging_time_at_half_rate * float64(time.Hour)))

				if mx_start_time_at_half_rate.Before(m3_start_time_at_half_rate) {
					// Car 1 (The shorter/later start time will charge at half rate the entire session)
					m3_start_time = m3_start_time_at_half_rate

					// Car 2
					mx_miles_added_at_half_rate := mx_target_finish_time.Sub(m3_start_time_at_half_rate).Seconds() /
						60 /
						60 *
						(MX_FULL_CHARGE_RATE_AT_PRIMARY / 2)
					mx_miles_remaining := mx_miles_needed - mx_miles_added_at_half_rate
					mx_miles_remaining_charging_time_at_full_rate := mx_miles_remaining / MX_FULL_CHARGE_RATE_AT_PRIMARY
					mx_start_time = m3_start_time_at_half_rate.Add(time.Duration(-mx_miles_remaining_charging_time_at_full_rate * float64(time.Hour)))
				} else {
					// Car 1 (The shorter/later start time will charge at half rate the entire session)
					mx_start_time = mx_start_time_at_half_rate

					// Car 2
					m3_miles_added_at_half_rate := m3_target_finish_time.Sub(mx_start_time_at_half_rate).Seconds() /
						60 /
						60 *
						(M3_FULL_CHARGE_RATE_AT_PRIMARY / 2)
					m3_miles_remaining := m3_miles_needed - m3_miles_added_at_half_rate
					m3_miles_remaining_charging_time_at_full_rate := m3_miles_remaining / M3_FULL_CHARGE_RATE_AT_PRIMARY
					m3_start_time = mx_start_time_at_half_rate.Add(time.Duration(-m3_miles_remaining_charging_time_at_full_rate * float64(time.Hour)))
				}
			}

			if scenario == "m3_primary_shared_charging" {
				return m3_start_time
			}

			if scenario == "mx_primary_shared_charging" {
				return mx_start_time
			}
		}
	} else if scenario == "mx_primary_full_rate" {
		mx_start_time = mx_target_finish_time.Add(time.Duration(-mx_miles_needed / MX_FULL_CHARGE_RATE_AT_PRIMARY * float64(time.Hour)))

		return mx_start_time
	} else if scenario == "m3_primary_full_rate" {
		m3_start_time = m3_target_finish_time.Add(time.Duration(-m3_miles_needed / M3_FULL_CHARGE_RATE_AT_PRIMARY * float64(time.Hour)))

		return m3_start_time
	} else if scenario == "mx_secondary_full_rate" {
		mx_start_time = mx_target_finish_time.Add(time.Duration(-mx_miles_needed / MX_FULL_CHARGE_RATE_AT_SECONDARY * float64(time.Hour)))

		return mx_start_time
	} else if scenario == "m3_secondary_full_rate" {
		m3_start_time = m3_target_finish_time.Add(time.Duration(-m3_miles_needed / M3_FULL_CHARGE_RATE_AT_SECONDARY * float64(time.Hour)))

		return m3_start_time
	}

	return time.Now()
}

// Helper function to determine how many seconds 2 ranges of times overlap.
func getRangeOverlap(mx_start_time_at_full_rate, mx_target_finish_time, m3_start_time_at_full_rate, m3_target_finish_time time.Time) float64 {
	r1 := Range{Start: mx_start_time_at_full_rate, End: mx_target_finish_time}
	r2 := Range{Start: m3_start_time_at_full_rate, End: m3_target_finish_time}

	latest_start := latestTime(r1.Start, r2.Start)
	earliest_end := earliestTime(r1.End, r2.End)

	// Handle potential negative duration (overlapping ranges or incorrect calculations)
	delta := earliest_end.Sub(latest_start)
	if delta < 0 {
		delta = 0 // Set overlap to 0 if duration is negative
	}

	return math.Max(0, delta.Seconds())
}

func latestTime(t1, t2 time.Time) time.Time {
	if t1.After(t2) {
		return t1
	}
	return t2
}

func earliestTime(t1, t2 time.Time) time.Time {
	if t1.Before(t2) {
		return t1
	}
	return t2
}

func getScheduledChargeMessage(vehicle string, data map[string]any, start_time time.Time, finish_time time.Time) string {
	message := "The " + vehicle + " is set to charge at " +
		start_time.Format("January 2, 2006 15:04") +
		" to " +
		strconv.FormatFloat(data["response"].(map[string]any)["charge_state"].(map[string]any)["charge_limit_soc"].(float64), 'f', -1, 64) + "%" +
		" by " + finish_time.Format("15:04") + ", " +
		strconv.FormatFloat((data["response"].(map[string]any)["charge_state"].(map[string]any)["battery_range"].(float64)/
			data["response"].(map[string]any)["charge_state"].(map[string]any)["battery_level"].(float64)*
			data["response"].(map[string]any)["charge_state"].(map[string]any)["charge_limit_soc"].(float64)), 'f', 0, 64) + " miles of estimated range.  " +
		"The Model 3 is currently at " +
		strconv.FormatFloat(data["response"].(map[string]any)["charge_state"].(map[string]any)["battery_level"].(float64), 'f', 0, 64) + "%, " +
		strconv.FormatFloat(data["response"].(map[string]any)["charge_state"].(map[string]any)["battery_range"].(float64), 'f', 0, 64) + " miles of estimated range."

	return message
}

func getPluggedInMessage(vehicle string, battery_level float64, battery_range float64) string {
	message := "Your car is not plugged in.  \n\nCurrent battery level is " +
		strconv.FormatFloat(battery_level, 'f', -1, 64) +
		"%, " +
		strconv.FormatFloat(battery_range, 'f', -1, 64) +
		" estimated miles.  \n\n-Your " + vehicle

	return message
}
