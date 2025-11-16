package energy

import (
	"encoding/json"
	"net/http"
	"time"

	"github.com/influxdata/influxdb/client/v2"
	"github.com/themonomers/tesla/go/common"
)

var BASE_URL string
var LOCAL_ACCESS_TOKEN string
var TIMEZONE string
var WAIT_TIME time.Duration = 30 // seconds

func init() {
	var err error

	t := common.GetLocalEnergyToken()
	LOCAL_ACCESS_TOKEN, err = t.String("tesla.token")
	common.LogError("init(): load local energy token", err)

	c := common.GetLocalEnergyConfig()
	BASE_URL, err = c.String("energy.base_url")
	common.LogError("init(): load energy base url", err)

	c = common.GetConfig()
	TIMEZONE, err = c.String("general.timezone")
	common.LogError("init(): load timezone", err)
}

// Writes live energy data to InfluxDB, accessed locally
// from the Tesla Energy Gateway.
func WriteLiveSiteTelemetry() {
	data := getLocalMetersAggregates()

	c := common.GetDBClient()
	defer c.Close()

	// Create a new point batch
	bp, err := client.NewBatchPoints(client.BatchPointsConfig{
		Database: "live",
	})
	common.LogError("WriteLiveSiteTelemetry(): client.NewBatchPoints", err)

	// Create points and add to batch
	tags := map[string]string{"source": "solar_power"}
	fields := map[string]any{
		"value": data["solar"].(map[string]any)["instant_power"].(float64),
	}
	pt, err := client.NewPoint("energy_live", tags, fields, handleTeslaTimestamp(data["solar"].(map[string]any)["last_communication_time"].(string)))
	common.LogError("WriteLiveSiteTelemetry(): client.NewPoint", err)
	bp.AddPoint(pt)

	tags = map[string]string{"source": "battery_power"}
	fields = map[string]any{
		"value": data["battery"].(map[string]any)["instant_power"].(float64),
	}
	pt, err = client.NewPoint("energy_live", tags, fields, handleTeslaTimestamp(data["battery"].(map[string]any)["last_communication_time"].(string)))
	common.LogError("WriteLiveSiteTelemetry(): client.NewPoint", err)
	bp.AddPoint(pt)

	tags = map[string]string{"source": "grid_power"}
	fields = map[string]any{
		"value": data["site"].(map[string]any)["instant_power"].(float64),
	}
	pt, err = client.NewPoint("energy_live", tags, fields, handleTeslaTimestamp(data["site"].(map[string]any)["last_communication_time"].(string)))
	common.LogError("WriteLiveSiteTelemetry(): client.NewPoint", err)
	bp.AddPoint(pt)

	tags = map[string]string{"source": "load_power"}
	fields = map[string]any{
		"value": data["load"].(map[string]any)["instant_power"].(float64),
	}
	pt, err = client.NewPoint("energy_live", tags, fields, handleTeslaTimestamp(data["load"].(map[string]any)["last_communication_time"].(string)))
	common.LogError("WriteLiveSiteTelemetry(): client.NewPoint", err)
	bp.AddPoint(pt)

	tags = map[string]string{"source": "percentage_charged"}
	fields = map[string]any{
		"value": getLocalSystemStatusSOE()["percentage"].(float64),
	}
	pt, err = client.NewPoint("energy_live", tags, fields, time.Now())
	common.LogError("WriteLiveSiteTelemetry(): client.NewPoint", err)
	bp.AddPoint(pt)

	// Write the batch
	err = c.Write(bp)
	common.LogError("WriteLiveSiteTelemetry(): c.Write", err)

	// Close client resources
	c.Close()
}

// Retrieves site energy data locally from the Tesla
// Energy Gateway.
func getLocalMetersAggregates() map[string]any {
	url := BASE_URL +
		"/meters/aggregates"

	req, err := http.NewRequest("GET", url, nil)
	common.LogError("getLocalMetersAggregates(): http.NewRequest", err)
	req.Header.Add("authorization", "Bearer "+LOCAL_ACCESS_TOKEN)

	resp, err := GetHttpsClient().Do(req)
	common.LogError("getLocalMetersAggregates(): getHttpsClient().Do", err)

	if resp.StatusCode != 200 {
		time.Sleep(WAIT_TIME * time.Second)
		return getLocalMetersAggregates()
	}

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)

	return body
}

// Retrieves battery charge state locally from the Tesla
// Energy Gateway.
func getLocalSystemStatusSOE() map[string]any {
	url := BASE_URL +
		"/system_status/soe"

	req, err := http.NewRequest("GET", url, nil)
	common.LogError("getLocalSystemStatusSOE(): http.NewRequest", err)
	req.Header.Add("authorization", "Bearer "+LOCAL_ACCESS_TOKEN)

	resp, err := GetHttpsClient().Do(req)
	common.LogError("getLocalSystemStatusSOE(): getHttpsClient().Do", err)

	if resp.StatusCode != 200 {
		time.Sleep(WAIT_TIME * time.Second)
		return getLocalSystemStatusSOE()
	}

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)

	return body
}

// Provides information on batteries and inverters.
func getLocalSystemStatus() map[string]any {
	url := BASE_URL +
		"/system_status"

	req, err := http.NewRequest("GET", url, nil)
	common.LogError("getLocalSystemStatus(): http.NewRequest", err)
	req.Header.Add("authorization", "Bearer "+LOCAL_ACCESS_TOKEN)

	resp, err := GetHttpsClient().Do(req)
	common.LogError("getLocalSystemStatus(): getHttpsClient().Do", err)

	if resp.StatusCode != 200 {
		time.Sleep(WAIT_TIME * time.Second)
		return getLocalSystemStatus()
	}

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)

	return body
}

// Handles the nanoseconds in the timestamp provided by the
// local Tesla Gateway that sometimes gives less digits and
// breaks the time parsing function.
func handleTeslaTimestamp(timestamp string) time.Time {
	loc, _ := time.LoadLocation(TIMEZONE)

	t, err := time.ParseInLocation("2006-01-02T15:04:05.000000-07:00", timestamp, loc)
	if err != nil {
		t, err = time.ParseInLocation("2006-01-02T15:04:05.00000-07:00", timestamp, loc)
		common.LogError("timestampSplit(): time.ParseInLocation", err)
	}

	return t
}
