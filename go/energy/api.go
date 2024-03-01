package energy

import (
	"bytes"
	"crypto/tls"
	"encoding/json"
	"net/http"
	"time"

	"github.com/themonomers/tesla/go/common"
)

var ACCESS_TOKEN string
var SITE_ID string
var BATTERY_ID string
var BASE_OWNER_URL string

func init() {
	var err error

	t := common.GetToken()
	ACCESS_TOKEN, err = t.String("tesla.access_token")
	common.LogError("init(): load access token", err)

	c := common.GetConfig()
	SITE_ID, err = c.String("energy.site_id")
	common.LogError("init(): load site id", err)

	BATTERY_ID, err = c.String("energy.battery_id")
	common.LogError("init(): load battery id", err)

	BASE_OWNER_URL, err = c.String("tesla.base_owner_url")
	common.LogError("init(): load base owner url", err)

	TIMEZONE, err = c.String("general.timezone")
	common.LogError("init(): load timezone", err)
}

// Gets some quick and basic information.
func GetSiteStatus() map[string]interface{} {
	url := BASE_OWNER_URL +
		"/energy_sites/" +
		SITE_ID +
		"/site_status"

	req, err := http.NewRequest("GET", url, nil)
	common.LogError("GetSiteStatus(): http.NewRequest", err)

	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := GetHttpsClient().Do(req)
	common.LogError("GetSiteStatus(): GetHttpsClient", err)

	defer resp.Body.Close()
	body := map[string]interface{}{}
	json.NewDecoder(resp.Body).Decode(&body)

	return body
}

// Gets more information as well as live data such as solar production.
func GetSiteLiveStatus() map[string]interface{} {
	url := BASE_OWNER_URL +
		"/energy_sites/" +
		SITE_ID +
		"/live_status"

	req, err := http.NewRequest("GET", url, nil)
	common.LogError("GetSiteLiveStatus(): http.NewRequest", err)

	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := GetHttpsClient().Do(req)
	common.LogError("GetSiteLiveStatus(): GetHttpsClient", err)

	defer resp.Body.Close()
	body := map[string]interface{}{}
	json.NewDecoder(resp.Body).Decode(&body)

	return body
}

// Gets detailed information.
func GetSiteInfo() map[string]interface{} {
	url := BASE_OWNER_URL +
		"/energy_sites/" +
		SITE_ID +
		"/site_info"

	req, err := http.NewRequest("GET", url, nil)
	common.LogError("GetSiteInfo(): http.NewRequest", err)

	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := GetHttpsClient().Do(req)
	common.LogError("GetSiteInfo(): GetHttpsClient", err)

	defer resp.Body.Close()
	body := map[string]interface{}{}
	json.NewDecoder(resp.Body).Decode(&body)

	return body
}

// Gets summary level information about energy imports and exports down to the
// day.
func GetSiteHistory(period string, date time.Time) map[string]interface{} {
	date = time.Date(date.Year(), date.Month(), date.Day(), 23, 59, 59, 0, time.Local)

	url := BASE_OWNER_URL +
		"/energy_sites/" +
		SITE_ID +
		"/calendar_history" +
		"?kind=energy" +
		"&end_date=" + date.Format("2006-01-02T15:04:05Z") +
		"&period=" + period

	req, err := http.NewRequest("GET", url, nil)
	common.LogError("GetSiteHistory(): http.NewRequest", err)

	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := GetHttpsClient().Do(req)
	common.LogError("GetSiteHistory(): GetHttpsClient", err)

	defer resp.Body.Close()
	body := map[string]interface{}{}
	json.NewDecoder(resp.Body).Decode(&body)

	return body
}

// Get grid outage/battery backup events.
func GetBatteryBackupHistory() map[string]interface{} {
	url := BASE_OWNER_URL +
		"/energy_sites/" +
		SITE_ID +
		"/history?kind=backup"

	req, err := http.NewRequest("GET", url, nil)
	common.LogError("GetBatteryPowerHistory(): http.NewRequest", err)

	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := GetHttpsClient().Do(req)
	common.LogError("GetBatteryPowerHistory(): GetHttpsClient", err)

	defer resp.Body.Close()
	body := map[string]interface{}{}
	json.NewDecoder(resp.Body).Decode(&body)

	return body
}

// Gets summary level information about energy imports and exports down to the
// day, separated by time of use.
func GetSiteTOUHistory(period string, date time.Time) map[string]interface{} {
	s_date := time.Date(date.Year(), date.Month(), date.Day(), 0, 0, 0, 0, time.Local)
	e_date := time.Date(date.Year(), date.Month(), date.Day(), 23, 59, 59, 0, time.Local)

	url := BASE_OWNER_URL +
		"/energy_sites/" +
		SITE_ID +
		"/calendar_history" +
		"?kind=time_of_use_energy" +
		"&start_date=" + s_date.Format("2006-01-02T15:04:05Z") +
		"&end_date=" + e_date.Format("2006-01-02T15:04:05Z") +
		"&period=" + period

	req, err := http.NewRequest("GET", url, nil)
	common.LogError("GetSiteTOUHistory(): http.NewRequest", err)

	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := GetHttpsClient().Do(req)
	common.LogError("GetSiteTOUHistory(): GetHttpsClient", err)

	defer resp.Body.Close()
	body := map[string]interface{}{}
	json.NewDecoder(resp.Body).Decode(&body)

	return body
}

// Gets the historic battery charge level data in 15 minute increments that's
// shown on the mobile app.
func GetBatteryChargeHistory(period string, date time.Time) map[string]interface{} {
	date = time.Date(date.Year(), date.Month(), date.Day(), 23, 59, 59, 0, time.Local)

	url := BASE_OWNER_URL +
		"/energy_sites/" +
		SITE_ID +
		"/calendar_history" +
		"?kind=soe" +
		"&end_date=" + date.Format("2006-01-02T15:04:05Z") +
		"&period=" + period

	req, err := http.NewRequest("GET", url, nil)
	common.LogError("GetBatteryChargeHistory(): http.NewRequest", err)

	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := GetHttpsClient().Do(req)
	common.LogError("GetBatteryChargeHistory(): GetHttpsClient", err)

	defer resp.Body.Close()
	body := map[string]interface{}{}
	json.NewDecoder(resp.Body).Decode(&body)

	return body
}

// Gets energy information in 5 minute increments, with ability to query by
// date.  Used to create the "ENERGY USAGE" charts in the mobile app.
func GetPowerHistory(period string, date time.Time) map[string]interface{} {
	s_date := time.Date(date.Year(), date.Month(), date.Day(), 0, 0, 0, 0, time.Local)
	e_date := time.Date(date.Year(), date.Month(), date.Day(), 23, 59, 59, 0, time.Local)

	url := BASE_OWNER_URL +
		"/energy_sites/" +
		SITE_ID +
		"/calendar_history" +
		"?kind=power" +
		"&start_date=" + s_date.Format("2006-01-02T15:04:05Z") +
		"&end_date=" + e_date.Format("2006-01-02T15:04:05Z") +
		"&period=" + period

	req, err := http.NewRequest("GET", url, nil)
	common.LogError("GetPowerHistory(): http.NewRequest", err)

	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := GetHttpsClient().Do(req)
	common.LogError("GetPowerHistory(): GetHttpsClient", err)

	defer resp.Body.Close()
	body := map[string]interface{}{}
	json.NewDecoder(resp.Body).Decode(&body)

	return body
}

// Lists all rate tariffs available in the mobile app.
func GetRateTariffs() map[string]interface{} {
	url := BASE_OWNER_URL +
		"/energy_sites/" +
		"rate_tariffs"

	req, err := http.NewRequest("GET", url, nil)
	common.LogError("GetRateTariffs(): http.NewRequest", err)

	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := GetHttpsClient().Do(req)
	common.LogError("GetRateTariffs(): GetHttpsClient", err)

	defer resp.Body.Close()
	body := map[string]interface{}{}
	json.NewDecoder(resp.Body).Decode(&body)

	return body
}

// Lists the tariff selected for your site in the mobile
// app along with published rates, TOU schedules, etc.
func GetSiteTariff() map[string]interface{} {
	url := BASE_OWNER_URL +
		"/energy_sites/" +
		SITE_ID +
		"/tariff_rate"

	req, err := http.NewRequest("GET", url, nil)
	common.LogError("GetSiteTariff(): http.NewRequest", err)

	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := GetHttpsClient().Do(req)
	common.LogError("GetSiteTariff(): GetHttpsClient", err)

	defer resp.Body.Close()
	body := map[string]interface{}{}
	json.NewDecoder(resp.Body).Decode(&body)

	return body
}

// Gets the data for Solar Value in the mobile app to show estimated
// cost savings.
func GetSavingsForecast(period string, date time.Time) map[string]interface{} {
	s_date := time.Date(date.Year(), date.Month(), date.Day(), 0, 0, 0, 0, time.Local)
	e_date := time.Date(date.Year(), date.Month(), date.Day(), 23, 59, 59, 0, time.Local)

	url := BASE_OWNER_URL +
		"/energy_sites/" +
		SITE_ID +
		"/calendar_history" +
		"?kind=savings" +
		"&start_date=" + s_date.Format("2006-01-02T15:04:05Z") +
		"&end_date=" + e_date.Format("2006-01-02T15:04:05Z") +
		"&period=" + period +
		"&tariff=PGE-EV2-A"

	req, err := http.NewRequest("GET", url, nil)
	common.LogError("GetSavingsForecast(): http.NewRequest", err)

	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := GetHttpsClient().Do(req)
	common.LogError("GetSavingsForecast(): GetHttpsClient", err)

	defer resp.Body.Close()
	body := map[string]interface{}{}
	json.NewDecoder(resp.Body).Decode(&body)

	return body
}

// Retrieves the estimated time remaining in the powerwall(s).
func GetBackupTimeRemaining() map[string]interface{} {
	url := BASE_OWNER_URL +
		"/energy_sites/" +
		SITE_ID +
		"/backup_time_remaining"

	req, err := http.NewRequest("GET", url, nil)
	common.LogError("GetBackupTimeRemaining(): http.NewRequest", err)

	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := GetHttpsClient().Do(req)
	common.LogError("GetBackupTimeRemaining(): GetHttpsClient", err)

	defer resp.Body.Close()
	body := map[string]interface{}{}
	json.NewDecoder(resp.Body).Decode(&body)

	return body
}

// Sets battery reserve %, "Reserve for Power Outages", in the mobile app.
func SetBatteryBackupReserve(backup_percent int) map[string]interface{} {
	url := BASE_OWNER_URL +
		"/energy_sites/" +
		SITE_ID +
		"/backup"

	payload, _ := json.Marshal(map[string]interface{}{
		"backup_reserve_percent": backup_percent,
	})

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(payload))
	common.LogError("SetBatteryBackupReserve(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := GetHttpsClient().Do(req)
	common.LogError("SetBatteryBackupReserve(): GetHttpsClient", err)

	defer resp.Body.Close()
	body := map[string]interface{}{}
	json.NewDecoder(resp.Body).Decode(&body)

	return body
}

// Sets off grid vehicle charging reserve % to save for home use.
// It seems the maximum is 95% so 5% is the minimum to share with vehicle.
func SetOffGridVehicleChargingReserve(percent int) map[string]interface{} {
	url := BASE_OWNER_URL +
		"/energy_sites/" +
		SITE_ID +
		"/off_grid_vehicle_charging_reserve"

	payload, _ := json.Marshal(map[string]interface{}{
		"off_grid_vehicle_charging_reserve_percent                                                                                                                                                         ": percent,
	})

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(payload))
	common.LogError("SetOffGridVehicleChargingReserve(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := GetHttpsClient().Do(req)
	common.LogError("SetOffGridVehicleChargingReserve(): GetHttpsClient", err)

	defer resp.Body.Close()
	body := map[string]interface{}{}
	json.NewDecoder(resp.Body).Decode(&body)

	return body
}

// Retrieves HTTPS client and ignores x509 certificate error
func GetHttpsClient() *http.Client {
	tr := &http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
	}

	return &http.Client{Transport: tr}
}
