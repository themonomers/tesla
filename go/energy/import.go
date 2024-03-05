package energy

import (
	"bufio"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/influxdata/influxdb/client/v2"
	"github.com/themonomers/tesla/go/common"
)

/*
// Import Tesla energy export from the mobile app pasted into a Google Sheet
// into an InfluxDB for Grafana visualization.
func ImportEnergyDetailFromGsheetToDB() {

}

// Import Tesla summary energy data from the a Google Sheet into an InfluxDB
// for Grafana visualization.
func ImportEnergySummaryFromGsheetToDB() {

}
*/

// Import Tesla battery charge state history into an InfluxDB for
// Grafana visualization.  These are in 15 minute increments.
func ImportBatteryChargeToDB() {
	WriteBatteryChargeToDB(getDateInput())
}

// Import Tesla system backup history/grid outages into an InfluxDB for
// Grafana visualization.
func ImportOutageToDB() {
	// get battery backup history data
	data := GetBatteryBackupHistory()

	c := common.GetDBClient()
	defer c.Close()

	// Create a new point batch
	bp, err := client.NewBatchPoints(client.BatchPointsConfig{
		Database: "outage",
	})
	common.LogError("ImportOutageToDB(): client.NewBatchPoints", err)

	for key, val := range data["response"].(map[string]interface{})["events"].([]interface{}) {
		fmt.Println(key + 1)

		// convert duration to hours
		duration := val.(map[string]interface{})["duration"].(float64) / 1000 / 60 / 60

		start, _ := time.Parse("2006-01-02T15:04:05-07:00", val.(map[string]interface{})["timestamp"].(string))
		fmt.Print("  start = ")
		fmt.Println(start.Format("2006-01-02 03:04:05 PM"))

		end := start.Add(time.Duration(duration * float64(time.Hour)))
		fmt.Print("  end   = ")
		fmt.Println(end.Format("2006-01-02 03:04:05 PM"))

		fmt.Print("  duration = ")
		fmt.Printf("%.2f", duration)
		fmt.Println(" hours")

		fmt.Print("import (y/n): ")
		reader := bufio.NewReader(os.Stdin)
		input, _ := reader.ReadString('\n')
		input = strings.Replace(input, "\n", "", -1)
		if input != "y" {
			continue
		}

		tags := map[string]string{"source": "event"}
		fields := map[string]interface{}{
			"value": duration,
		}
		pt, err := client.NewPoint("backup", tags, fields, start)
		common.LogError("ImportOutageToDB(): client.NewPoint", err)
		bp.AddPoint(pt)

		tags = map[string]string{"source": "event"}
		fields = map[string]interface{}{
			"value": duration,
		}
		pt, err = client.NewPoint("backup", tags, fields, end)
		common.LogError("ImportOutageToDB(): client.NewPoint", err)
		bp.AddPoint(pt)
	}

	// Write the batch
	err = c.Write(bp)
	common.LogError("ImportOutageToDB(): c.Write", err)

	// Close client resources
	c.Close()
}

// Import missing dates for Tesla Energy data for InfluxDB.  This
// has 5 minute increments of Home, Solar, Powerall, and Grid to/from
// data.
func ImportEnergyDetailToDB() {
	WriteEnergyDetailToDB(getDateInput())
}

// Import missing dates for Tesla Energy data for InfluxDB.  This
// has daily totals of Home, Solar, Powerall, and Grid to/from
// data.
func ImportEnergySummaryToDB() {
	WriteEnergySummaryToDB(getDateInput())
}

// Import missing dates for Tesla Energy Impact data for Google Sheet.
// This includes TOU (off peak, partial peak, and peak) breakdowns
// of Solar, Powerall, Grid, etc., Energy Value, and Solar Offset.
func ImportEnergyTOUSummaryToGsheet() {
	WriteEnergyTOUSummaryToGsheet(getDateInput())
}

// Import missing dates for Tesla Energy Impact data for InfluxDB.
// This includes TOU (off peak, partial peak, and peak) breakdowns
// of Solar, Powerall, Grid, etc., Energy Value, and Solar Offset.
func ImportEnergyTOUSummaryToDB() {
	WriteEnergyTOUSummaryToDB(getDateInput())
}

// Prompts for a date input from standard in.
func getDateInput() time.Time {
	fmt.Print("date(m/d/yyyy): ")
	reader := bufio.NewReader(os.Stdin)
	input, _ := reader.ReadString('\n')
	input = strings.Replace(input, "\n", "", -1)

	date, err := time.Parse("1/2/2006", input)
	if err != nil {
		fmt.Println("Error parsing date: " + err.Error())
		os.Exit(1)
	}

	fmt.Println(date.Format("1/2/2006"))
	fmt.Print("import (y/n): ")
	input, _ = reader.ReadString('\n')
	input = strings.Replace(input, "\n", "", -1)
	if input != "y" {
		os.Exit(1)
	}

	return date
}
