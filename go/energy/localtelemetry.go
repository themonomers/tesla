package energy

import (
	"log/slog"
	"time"

	"github.com/influxdata/influxdb/client/v2"
	"github.com/themonomers/tesla/go/common"
)

var SendRequest = common.SendRequest

var WAIT_TIME time.Duration = 30 // seconds

// Writes live energy data to InfluxDB, accessed locally
// from the Tesla Energy Gateway.
func WriteLiveSiteTelemetry() {
	data := getLocalMetersAggregates()

	c := GetDBClient()
	defer c.Close()

	// Create a new point batch
	bp, _ := client.NewBatchPoints(client.BatchPointsConfig{
		Database: "live",
	})

	// Create points and add to batch
	tags := map[string]string{"source": "solar_power"}
	fields := map[string]any{
		"value": data["solar"].(map[string]any)["instant_power"].(float64),
	}
	pt, _ := client.NewPoint("energy_live", tags, fields, splitTimestamp(data["solar"].(map[string]any)["last_communication_time"].(string)))
	bp.AddPoint(pt)

	tags = map[string]string{"source": "battery_power"}
	fields = map[string]any{
		"value": data["battery"].(map[string]any)["instant_power"].(float64),
	}
	pt, _ = client.NewPoint("energy_live", tags, fields, splitTimestamp(data["battery"].(map[string]any)["last_communication_time"].(string)))
	bp.AddPoint(pt)

	tags = map[string]string{"source": "grid_power"}
	fields = map[string]any{
		"value": data["site"].(map[string]any)["instant_power"].(float64),
	}
	pt, _ = client.NewPoint("energy_live", tags, fields, splitTimestamp(data["site"].(map[string]any)["last_communication_time"].(string)))
	bp.AddPoint(pt)

	tags = map[string]string{"source": "load_power"}
	fields = map[string]any{
		"value": data["load"].(map[string]any)["instant_power"].(float64),
	}
	pt, _ = client.NewPoint("energy_live", tags, fields, splitTimestamp(data["load"].(map[string]any)["last_communication_time"].(string)))
	bp.AddPoint(pt)

	tags = map[string]string{"source": "percentage_charged"}
	fields = map[string]any{
		"value": getLocalSystemStatusSOE()["percentage"].(float64),
	}
	pt, _ = client.NewPoint("energy_live", tags, fields, time.Now())
	bp.AddPoint(pt)

	// Write the batch
	err := c.Write(bp)
	if err != nil {
		slog.Error("WriteLiveSiteTelemetry(): c.Write(): " + err.Error())
	}

	// Close client resources
	c.Close()
}

// Retrieves site energy data locally from the Tesla
// Energy Gateway.
func getLocalMetersAggregates() map[string]any {
	return sendGet(getLocalUrl("/meters/aggregates"))
}

// Retrieves battery charge state locally from the Tesla
// Energy Gateway.
func getLocalSystemStatusSOE() map[string]any {
	return sendGet(getLocalUrl("/system_status/soe"))
}

// Provides information on batteries and inverters.
func getLocalSystemStatus() map[string]any {
	return sendGet(getLocalUrl("/system_status"))
}

// Handles the nanoseconds in the timestamp provided by the
// local Tesla Gateway that sometimes gives less digits and
// breaks the time parsing function.
func splitTimestamp(timestamp string) time.Time {
	loc, _ := time.LoadLocation(common.LocalCfg.General.Timezone)

	t, err := time.ParseInLocation("2006-01-02T15:04:05.000000-07:00", timestamp, loc)
	if err != nil {
		t, _ = time.ParseInLocation("2006-01-02T15:04:05.00000-07:00", timestamp, loc)
	}

	return t
}

// Centralize repetitive URL construction.
func getLocalUrl(command string) string {
	return common.LocalCfg.Energy.BaseUrl + command
}

func sendGet(url string) map[string]any {
	resp, err := SendRequest("GET", url, common.LocalTokenCfg.Tesla.Token, nil)
	if err != nil {
		slog.Warn("Retry sendGet(): SendRequest(): " + err.Error())
		time.Sleep(WAIT_TIME * time.Second)
		sendGet(url)
	}

	if resp.StatusCode != 200 {
		time.Sleep(WAIT_TIME * time.Second)
		return sendGet(url)
	}

	return GetJson(resp)
}
