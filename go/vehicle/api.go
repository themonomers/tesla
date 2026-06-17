package vehicle

import (
	"encoding/json"
	"net/http"
	"net/url"
	"time"

	"github.com/themonomers/tesla/go/common"
)

var SendRequest = common.SendRequest

var WAIT_TIME time.Duration = 30 // seconds

// Retrieves the vehicle data needed for higher level functions to drive
// calcuations and actions.
func GetVehicleData(vin string) map[string]any {
	var url = common.Cfg.Uri.TeslaBaseProxyUrl +
		"/api/1/vehicles/" +
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
	var url = common.Cfg.Uri.TeslaBaseProxyUrl +
		"/api/1/vehicles/" +
		vin +
		"/wake_up"

	return SendPost(url, nil)
}

// Function to send API call to start charging a vehicle.
func StartCharge(vin string) *http.Response {
	return SendPost(getUrl(vin, "charge_start"), nil)
}

// Function to send API call to stop charging a vehicle.
func StopCharge(vin string) *http.Response {
	return SendPost(getUrl(vin, "charge_stop"), nil)
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

	return SendPost(getUrl(vin, "add_charge_schedule"), payload)
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

	return SendPost(getUrl(vin, "remove_charge_schedule"), payload)
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

	return SendPost(getUrl(vin, "set_temps"), payload)
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
	payload, _ := json.Marshal(map[string]any{
		"seat_position": seat,
		"level":         setting,
	})

	return SendPost(getUrl(vin, "remote_seat_heater_request"), payload)
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

	return SendPost(getUrl(vin, "remote_seat_cooler_request"), payload)
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

	return SendPost(getUrl(vin, "remote_auto_seat_climate_request"), payload)
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

	return SendPost(getUrl(vin, "remote_steering_wheel_heater_request"), payload)
}

// Function to start vehicle preconditioning.
func StartPrecondition(vin string) *http.Response {
	return SendPost(getUrl(vin, "auto_conditioning_start"), nil)
}

// Function to stop vehicle preconditioning.
func StopPrecondition(vin string) *http.Response {
	return SendPost(getUrl(vin, "auto_conditioning_stop"), nil)
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

	resp := SendPost(getUrl(vin, "schedule_software_update"), payload)
	if resp.StatusCode != 200 {
		WakeVehicle(vin)
		time.Sleep(WAIT_TIME * time.Second)
		return ScheduleSoftwareUpdate(vin, offset_sec)
	}

	return resp
}

// Centralize repetitive URL construction.
func getUrl(vin, command string) string {
	return (common.Cfg.Uri.TeslaBaseProxyUrl +
		"/api/1/vehicles/" +
		vin +
		"/command/" +
		command)
}

func SendGet(url string) *http.Response {
	return SendRequest("GET", url, common.TokenCfg.Tesla.AccessToken, nil)
}

func SendPost(url string, payload []byte) *http.Response {
	return SendRequest("POST", url, common.TokenCfg.Tesla.AccessToken, payload)
}
