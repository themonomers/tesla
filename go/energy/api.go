package energy

import (
	"encoding/json"
	"net/http"
	"time"

	"github.com/themonomers/tesla/go/common"
	"github.com/themonomers/tesla/go/vehicle"
)

var SendGet = vehicle.SendGet
var SendPost = vehicle.SendPost
var GetJson = common.GetJson
var GetConfig = common.GetConfig
var GetUri = common.GetUri

var SITE_ID string
var BASE_PROXY_URL string

func init() {
	c := GetConfig()
	SITE_ID, _ = c.String("energy.site_id")

	BASE_PROXY_URL = GetUri().Tesla.BaseProxyUrl
}

// Gets some quick and basic information.
func GetSiteStatus() map[string]any {
	return GetJson(SendGet(getUrl("site_status")))
}

// Gets more information as well as live data such as solar production.
func GetSiteLiveStatus() map[string]any {
	return GetJson(SendGet(getUrl("live_status")))
}

// Gets detailed information.
func GetSiteInfo() map[string]any {
	return GetJson(SendGet(getUrl("site_info")))
}

// Gets summary level information about energy imports and exports down to the
// day.
func GetSiteHistory(period string, date time.Time) map[string]any {
	date = time.Date(date.Year(), date.Month(), date.Day(), 23, 59, 59, 0, time.Local)

	command := "calendar_history" +
		"?kind=energy" +
		"&end_date=" + date.UTC().Format("2006-01-02T15:04:05Z") +
		"&period=" + period

	return GetJson(SendGet(getUrl(command)))
}

// Get grid outage/battery backup events.
func GetBatteryBackupHistory() map[string]any {
	return GetJson(SendGet(getUrl("calendar_history?kind=backup")))
}

// Gets summary level information about energy imports and exports down to the
// day, separated by time of use.
func GetSiteTOUHistory(period string, date time.Time) map[string]any {
	s_date := time.Date(date.Year(), date.Month(), date.Day(), 0, 0, 0, 0, time.Local)
	e_date := time.Date(date.Year(), date.Month(), date.Day(), 23, 59, 59, 0, time.Local)

	command := "calendar_history" +
		"?kind=time_of_use_energy" +
		"&start_date=" + s_date.UTC().Format("2006-01-02T15:04:05Z") +
		"&end_date=" + e_date.UTC().Format("2006-01-02T15:04:05Z") +
		"&period=" + period

	return GetJson(SendGet(getUrl(command)))
}

// Gets the historic battery charge level data in 15 minute increments that's
// shown on the mobile app.
func GetBatteryChargeHistory(period string, date time.Time) map[string]any {
	date = time.Date(date.Year(), date.Month(), date.Day(), 23, 59, 59, 0, time.Local)

	command := "calendar_history" +
		"?kind=soe" +
		"&end_date=" + date.UTC().Format("2006-01-02T15:04:05Z") +
		"&period=" + period

	return GetJson(SendGet(getUrl(command)))
}

// Gets energy information in 5 minute increments, with ability to query by
// date.  Used to create the "ENERGY USAGE" charts in the mobile app.
func GetPowerHistory(period string, date time.Time) map[string]any {
	s_date := time.Date(date.Year(), date.Month(), date.Day(), 0, 0, 0, 0, time.Local)
	e_date := time.Date(date.Year(), date.Month(), date.Day(), 23, 59, 59, 0, time.Local)

	command := "calendar_history" +
		"?kind=power" +
		"&start_date=" + s_date.UTC().Format("2006-01-02T15:04:05Z") +
		"&end_date=" + e_date.UTC().Format("2006-01-02T15:04:05Z") +
		"&period=" + period

	return GetJson(SendGet(getUrl(command)))
}

// Lists all rate tariffs available in the mobile app.
func GetRateTariffs() map[string]any {
	url := BASE_PROXY_URL +
		"/api/1/energy_sites/" +
		"rate_tariffs"

	return GetJson(SendGet(url))
}

// Lists the tariff selected for your site in the mobile
// app along with published rates, TOU schedules, etc.
func GetSiteTariff() map[string]any {
	return GetJson(SendGet(getUrl("tariff_rate")))
}

// Gets the data for Solar Value in the mobile app to show estimated
// cost savings.
func GetSavingsForecast(period string, date time.Time) map[string]any {
	s_date := time.Date(date.Year(), date.Month(), date.Day(), 0, 0, 0, 0, time.Local)
	e_date := time.Date(date.Year(), date.Month(), date.Day(), 23, 59, 59, 0, time.Local)

	command := "calendar_history" +
		"?kind=savings" +
		"&start_date=" + s_date.UTC().Format("2006-01-02T15:04:05Z") +
		"&end_date=" + e_date.UTC().Format("2006-01-02T15:04:05Z") +
		"&period=" + period +
		"&tariff=PGE-EV2-A"

	return GetJson(SendGet(getUrl(command)))
}

// Retrieves the estimated time remaining in the powerwall(s).
func GetBackupTimeRemaining() map[string]any {
	return GetJson(SendGet(getUrl("backup_time_remaining")))
}

// Changes Operational Mode in the mobile app to "Backup-only".
// This doesn't appear to be any setting in the mobile app
// but this API call still forces the system to only use the
// battery in an outage.  This also has a side effect of hiding
// the Time of Use card as well as returns an empty response
// when calling the API for Time of Use data.
func SetOperationalModeBackup() *http.Response {
	return setOperationalMode("backup")
}

// Changes Operational Mode in the mobile app to "Self-Powered".
func SetOperationalModeSelfPowered() *http.Response {
	return setOperationalMode("self_consumption")
}

// Changes Operational Mode in the mobile app to "Time-Based Control".
func SetOperationalModeTimeBasedControl() *http.Response {
	return setOperationalMode("autonomous")
}

// Changes Operational Mode setting in the mobile app.
func setOperationalMode(mode string) *http.Response {
	payload, _ := json.Marshal(map[string]any{
		"default_real_mode": mode,
	})

	return SendPost(getUrl("operation"), payload)
}

// Changes Energy Exports in the mobile app to "Everything".
// Defaults Grid Charging setting to "No".
func SetEnergyExportsEverything() *http.Response {
	return setGridImportExport("battery_ok", true)
}

// Changes Energy Exports in the mobile app to "Solar".
// Defaults Grid Charging setting to "No".
func SetEnergyExportsSolar() *http.Response {
	return setGridImportExport("pv_only", true)
}

// Changes Energy Exports and Grid Charging settings in the mobile app.
func setGridImportExport(export_rule string, disallow_grid_charging bool) *http.Response {
	payload, _ := json.Marshal(map[string]any{
		"customer_preferred_export_rule":                 export_rule,
		"disallow_charge_from_grid_with_solar_installed": disallow_grid_charging,
	})

	return SendPost(getUrl("grid_import_export"), payload)

}

// Sets "Reserve Energy for Grid Outages", % Backup, in the mobile app.
func SetBackupReserve(backup_percent int) *http.Response {
	payload, _ := json.Marshal(map[string]any{
		"backup_reserve_percent": backup_percent,
	})

	return SendPost(getUrl("backup"), payload)
}

// Sets off grid vehicle charging reserve % to save for home use.
// It seems the maximum is 95% so 5% is the minimum to share with vehicle.
func SetOffGridVehicleChargingReserve(percent int) *http.Response {
	payload, _ := json.Marshal(map[string]any{
		"off_grid_vehicle_charging_reserve_percent                                                                                                                                                         ": percent,
	})

	return SendPost(getUrl("off_grid_vehicle_charging_reserve"), payload)
}

// Centralize repetitive URL construction.
func getUrl(command string) string {
	return (BASE_PROXY_URL +
		"/api/1/energy_sites/" +
		SITE_ID +
		"/" +
		command)
}
