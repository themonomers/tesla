package energy

import (
	"crypto/tls"
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
	LogError("init(): load local energy token", err)

	c := common.GetLocalEnergyConfig()
	BASE_URL, err = c.String("energy.base_url")
	LogError("init(): load energy base url", err)

	c = GetConfig()
	TIMEZONE, err = c.String("general.timezone")
	LogError("init(): load timezone", err)
}

// Writes live energy data to InfluxDB, accessed locally
// from the Tesla Energy Gateway.
func WriteLiveSiteTelemetry() {
	data := getLocalMetersAggregates()

	c := GetDBClient()
	defer c.Close()

	// Create a new point batch
	bp, err := client.NewBatchPoints(client.BatchPointsConfig{
		Database: "live",
	})
	LogError("WriteLiveSiteTelemetry(): client.NewBatchPoints", err)

	// Create points and add to batch
	tags := map[string]string{"source": "solar_power"}
	fields := map[string]any{
		"value": data["solar"].(map[string]any)["instant_power"].(float64),
	}
	pt, err := client.NewPoint("energy_live", tags, fields, splitTimestamp(data["solar"].(map[string]any)["last_communication_time"].(string)))
	LogError("WriteLiveSiteTelemetry(): client.NewPoint", err)
	bp.AddPoint(pt)

	tags = map[string]string{"source": "battery_power"}
	fields = map[string]any{
		"value": data["battery"].(map[string]any)["instant_power"].(float64),
	}
	pt, err = client.NewPoint("energy_live", tags, fields, splitTimestamp(data["battery"].(map[string]any)["last_communication_time"].(string)))
	LogError("WriteLiveSiteTelemetry(): client.NewPoint", err)
	bp.AddPoint(pt)

	tags = map[string]string{"source": "grid_power"}
	fields = map[string]any{
		"value": data["site"].(map[string]any)["instant_power"].(float64),
	}
	pt, err = client.NewPoint("energy_live", tags, fields, splitTimestamp(data["site"].(map[string]any)["last_communication_time"].(string)))
	LogError("WriteLiveSiteTelemetry(): client.NewPoint", err)
	bp.AddPoint(pt)

	tags = map[string]string{"source": "load_power"}
	fields = map[string]any{
		"value": data["load"].(map[string]any)["instant_power"].(float64),
	}
	pt, err = client.NewPoint("energy_live", tags, fields, splitTimestamp(data["load"].(map[string]any)["last_communication_time"].(string)))
	LogError("WriteLiveSiteTelemetry(): client.NewPoint", err)
	bp.AddPoint(pt)

	tags = map[string]string{"source": "percentage_charged"}
	fields = map[string]any{
		"value": getLocalSystemStatusSOE()["percentage"].(float64),
	}
	pt, err = client.NewPoint("energy_live", tags, fields, time.Now())
	LogError("WriteLiveSiteTelemetry(): client.NewPoint", err)
	bp.AddPoint(pt)

	// Write the batch
	err = c.Write(bp)
	LogError("WriteLiveSiteTelemetry(): c.Write", err)

	// Close client resources
	c.Close()
}

// Retrieves site energy data locally from the Tesla
// Energy Gateway.
func getLocalMetersAggregates() map[string]any {
	url := BASE_URL +
		"/meters/aggregates"

	resp := sendGet(url)

	if resp.StatusCode != 200 {
		time.Sleep(WAIT_TIME * time.Second)
		return getLocalMetersAggregates()
	}

	return GetJson(resp)
}

// Retrieves battery charge state locally from the Tesla
// Energy Gateway.
func getLocalSystemStatusSOE() map[string]any {
	url := BASE_URL +
		"/system_status/soe"

	resp := sendGet(url)

	if resp.StatusCode != 200 {
		time.Sleep(WAIT_TIME * time.Second)
		return getLocalSystemStatusSOE()
	}

	return GetJson(resp)
}

// Provides information on batteries and inverters.
func getLocalSystemStatus() map[string]any {
	url := BASE_URL +
		"/system_status"

	resp := sendGet(url)

	if resp.StatusCode != 200 {
		time.Sleep(WAIT_TIME * time.Second)
		return getLocalSystemStatus()
	}

	return GetJson(resp)
}

// Handles the nanoseconds in the timestamp provided by the
// local Tesla Gateway that sometimes gives less digits and
// breaks the time parsing function.
func splitTimestamp(timestamp string) time.Time {
	loc, _ := time.LoadLocation(TIMEZONE)

	t, err := time.ParseInLocation("2006-01-02T15:04:05.000000-07:00", timestamp, loc)
	if err != nil {
		t, err = time.ParseInLocation("2006-01-02T15:04:05.00000-07:00", timestamp, loc)
		LogError("splitTimestamp(): time.ParseInLocation", err)
	}

	return t
}

func sendGet(url string) *http.Response {
	return sendRequest("GET", url)
}

// Centralize repetitive request posts.
func sendRequest(method, url string) *http.Response {
	req, err := http.NewRequest(method, url, nil)
	LogError(url+": http.NewRequest", err)
	req.Header.Add("authorization", "Bearer "+LOCAL_ACCESS_TOKEN)

	resp, err := getHttpsClient().Do(req)
	LogError(url+": getHttpsClient", err)

	return resp
}

// Retrieves HTTPS client and ignores x509 certificate error
func getHttpsClient() *http.Client {
	tr := &http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
	}

	return &http.Client{Transport: tr}
}
