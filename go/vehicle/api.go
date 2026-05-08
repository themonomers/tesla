package vehicle

import (
	"encoding/json"
	"net/http"
	"net/url"
	"time"

	"github.com/themonomers/tesla/go/common"
)

var SendGet = common.SendGet
var SendPost = common.SendPost
var LogError = common.LogError
var GetConfig = common.GetConfig

var BASE_OWNER_URL string
var BASE_PROXY_URL string
var WAIT_TIME time.Duration = 30 // seconds

func init() {
	var err error

	var c = GetConfig()
	BASE_PROXY_URL, err = c.String("tesla.base_proxy_url")
	LogError("init(): load base proxy url", err)

	BASE_OWNER_URL, err = c.String("tesla.base_owner_url")
	LogError("init(): load base owner url", err)
}

// Retrieves the vehicle data needed for higher level functions to drive
// calcuations and actions.
func GetVehicleData(vin string) map[string]any {
	var url = BASE_PROXY_URL +
		"/vehicles/" +
		vin +
		"/vehicle_data?endpoints=" +
		url.PathEscape(
			"location_data;"+
				"charge_state;"+
				"climate_state;"+
				"vehicle_state;"+
				"gui_settings;"+
				"vehicle_config;"+
				"closures_state;"+
				"drive_state")

	resp := SendGet(url)

	if resp.StatusCode != 200 {
		WakeVehicle(vin)
		time.Sleep(WAIT_TIME * time.Second)
		return GetVehicleData(vin)
	}

	return common.GetJson(resp)
}

// Function to repeatedly run (after a certain wait time) to wake the vehicle up
// when it's asleep.
func WakeVehicle(vin string) *http.Response {
	var url = BASE_PROXY_URL +
		"/vehicles/" +
		vin +
		"/wake_up"

	return SendPost(url, nil)
}

// Function to send API call to start charging a vehicle.
func StartCharge(vin string) *http.Response {
	if vin == MX_VIN {
		return SendPost(getUrl(BASE_OWNER_URL, vin, "charge_start"), nil)
	}

	return SendPost(getUrl(BASE_PROXY_URL, vin, "charge_start"), nil)
}

// Function to send API call to stop charging a vehicle.
func StopCharge(vin string) *http.Response {
	if vin == MX_VIN {
		return SendPost(getUrl(BASE_OWNER_URL, vin, "charge_stop"), nil)
	}

	return SendPost(getUrl(BASE_PROXY_URL, vin, "charge_stop"), nil)
}

// Uses new endpoint to add a schedule for vehicle charging.
// Scheduled Time is in minutes after midnight, e.g. 7:30 AM
// = (7 * 60) + 30 = 450
func AddChargeSchedule(vin string, lat float64, lon float64, sch_time int, id int) *http.Response {
	payload, _ := json.Marshal(map[string]any{
		"days_of_week":  "All",
		"enabled":       true,
		"start_enabled": true,
		"end_enabled":   false,
		"lat":           lat,
		"lon":           lon,
		"start_time":    sch_time,
		"one_time":      false,
		"id":            id,
	})

	if vin == MX_VIN {
		return SendPost(getUrl(BASE_OWNER_URL, vin, "add_charge_schedule"), payload)
	}

	return SendPost(getUrl(BASE_PROXY_URL, vin, "add_charge_schedule"), payload)
}

// Uses new endpoint to remove a schedule for vehicle charging.
// The Owner API for this function on older model vehicles throws
// an error ("x509: certificate signed by unknown authority") unlike
// other endpoints.  This endpoint works for both newer and older model
// cars.
func RemoveChargeSchedule(vin string, id int) *http.Response {
	payload, _ := json.Marshal(map[string]any{
		"id": id,
	})

	return SendPost(getUrl(BASE_PROXY_URL, vin, "remove_charge_schedule"), payload)
}

// Sets the driver and/or passenger-side cabin temperature
// (and other zones if sync is enabled).
//
// d_temp:  driver side temperature in C
// p_temp:  passenger side temperature in C
func SetTemp(vin string, d_temp float64, p_temp float64) *http.Response {
	payload, _ := json.Marshal(map[string]any{
		"driver_temp":    d_temp,
		"passenger_temp": p_temp,
	})

	if vin == MX_VIN {
		return SendPost(getUrl(BASE_OWNER_URL, vin, "set_temps"), payload)
	}

	return SendPost(getUrl(BASE_PROXY_URL, vin, "set_temps"), payload)
}

// Sets seat heating. Requires preconditioning or climate keeper to be on.
//
// seat:
//
//	0: front left
//	1: front right
//	2: rear left
//	4: rear center
//	5: rear right
//
// setting:
//
//	0: off
//	1: low
//	2: medium
//	3: high
func SetSeatHeating(vin string, seat int, setting int) *http.Response {
	if vin == MX_VIN {
		payload, _ := json.Marshal(map[string]any{
			"heater": seat,
			"level":  setting,
		})
		return SendPost(getUrl(BASE_OWNER_URL, vin, "remote_seat_heater_request"), payload)
	}

	payload, _ := json.Marshal(map[string]any{
		"seat_position": seat,
		"level":         setting,
	})
	return SendPost(getUrl(BASE_PROXY_URL, vin, "remote_seat_heater_request"), payload)
}

// Sets seat cooling. Requires preconditioning or climate keeper to be on.
//
// seat:
//
//	1: front left
//	2: front right
//
// setting:
//
//	0: off
//	1: low
//	2: medium
//	3: high
func SetSeatCooling(vin string, seat int, setting int) *http.Response {
	payload, _ := json.Marshal(map[string]any{
		"seat_position":     seat,
		"seat_cooler_level": setting,
	})

	return SendPost(getUrl(BASE_PROXY_URL, vin, "remote_seat_cooler_request"), payload)
}

// Sets automatic seat heating and cooling. Requires preconditioning or
// climate keeper to be on.
//
// enable:  True/False (on/off)
// seat:
//
//	1: front left
//	2: front right
func SetSeatClimateAuto(vin string, enable bool, seat int) *http.Response {
	payload, _ := json.Marshal(map[string]any{
		"auto_climate_on":    enable,
		"auto_seat_position": seat,
	})

	return SendPost(getUrl(BASE_PROXY_URL, vin, "remote_auto_seat_climate_request"), payload)
}

// Sets steering wheel heating on/off. For vehicles that do not
// support auto steering wheel heat. Requires preconditioning or
// climate keeper to be on.
//
// enable:  True/False (on/off)
func SetSteeringWheelHeating(vin string, enable bool) *http.Response {
	payload, _ := json.Marshal(map[string]any{
		"on": enable,
	})

	return SendPost(getUrl(BASE_PROXY_URL, vin, "remote_steering_wheel_heater_request"), payload)
}

// Function to start vehicle preconditioning.
func StartPrecondition(vin string) *http.Response {
	if vin == MX_VIN {
		return SendPost(getUrl(BASE_OWNER_URL, vin, "auto_conditioning_start"), nil)
	}

	return SendPost(getUrl(BASE_PROXY_URL, vin, "auto_conditioning_start"), nil)
}

// Function to stop vehicle preconditioning.
func StopPrecondition(vin string) *http.Response {
	if vin == MX_VIN {
		return SendPost(getUrl(BASE_OWNER_URL, vin, "auto_conditioning_stop"), nil)
	}

	return SendPost(getUrl(BASE_PROXY_URL, vin, "auto_conditioning_stop"), nil)
}

// Schedules a vehicle software update (over the air "OTA") to be
// installed in the future.  Currently this works like the mobile
// app where you cannot schedule a time in the future like you can
// in the car.  You have to rely on crontab to mimic the behavior
// to schedule in the future.
//
// offset_sec: seconds from now, e.g. 2 minutes from now = 60 * 2 = 120
func ScheduleSoftwareUpdate(vin string, offset_sec int) *http.Response {
	payload, _ := json.Marshal(map[string]any{
		"offset_sec": offset_sec,
	})

	var resp *http.Response
	if vin == MX_VIN {
		resp = SendPost(getUrl(BASE_OWNER_URL, vin, "schedule_software_update"), payload)
	}

	resp = SendPost(getUrl(BASE_PROXY_URL, vin, "schedule_software_update"), payload)
	if resp.StatusCode != 200 {
		WakeVehicle(vin)
		time.Sleep(WAIT_TIME * time.Second)
		return ScheduleSoftwareUpdate(vin, offset_sec)
	}

	return resp
}

// Retrieves the vehicle ID, which changes from time to time, by the VIN, which
// doesn't change.  The vehicle ID is required for many of the API calls.
func getVehicleId(vin string) string {
	var data = GetVehicleData(vin)

	return data["response"].(map[string]any)["id_s"].(string)
}

// Centralize repetitive URL construction.
func getUrl(base, vin, command string) string {
	var url string
	switch base {
	case BASE_OWNER_URL:
		url = base +
			"/vehicles/" +
			getVehicleId(vin) +
			"/command/" +
			command
	case BASE_PROXY_URL:
		url = base +
			"/vehicles/" +
			vin +
			"/command/" +
			command
	}

	return url
}
