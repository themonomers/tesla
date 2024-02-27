package vehicle

import (
	"github.com/themonomers/tesla/go/common"
	"google.golang.org/api/sheets/v4"
)

// Creates a trigger to precondition the cabin for the following morning,
// based on if the car is at the primary location and if "Eco Mode" is off
// similar to how Nest thermostats work for vacation scenarios.  With the
// new endpoints released, you can achieve the same functionality by setting
// scheduled departure for preconditioning.  I decided to keep this code
// running as I don't drive long distances so the added feature of
// preconditioning the battery, in addition to the cabin, is a waste of
// energy (entropy) for me.
func SetM3Precondition(data map[string]interface{}, climate_config *sheets.ValueRange) {
	// check if eco mode is off first so we don't have to even call the
	// Tesla API if we don't have to
	if climate_config.Values[4][0] == "off" {
		// check if the car is with 0.25 miles of the primary location
		if common.IsVehicleAtPrimary(data) {
			// specific date/time to create a crontab for tomorrow morning at
			// the preferred start time
			start_time := common.GetTomorrowTime(climate_config.Values[0][0].(string))

			// create precondition start crontab
			common.DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 360 300 go run main.go -preconditionm3start >> /home/pi/tesla/go/cron.log 2>&1")
			common.CreateCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 360 300 go run main.go -preconditionm3start >> /home/pi/tesla/go/cron.log 2>&1",
				start_time.Minute(),
				start_time.Hour(),
				start_time.Day(),
				int(start_time.Month()))
		}
	}
}

func SetMXPrecondition(data map[string]interface{}, climate_config *sheets.ValueRange) {
	// check if eco mode is off first so we don't have to even call the
	// Tesla API if we don't have to
	if climate_config.Values[4][7] == "off" {
		// check if the car is with 0.25 miles of the primary location
		if common.IsVehicleAtPrimary(data) {
			// specific date/time to create a crontab for tomorrow morning at
			// the preferred start time
			start_time := common.GetTomorrowTime(climate_config.Values[0][0].(string))

			// create precondition start crontab
			common.DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 360 300 go run main.go -preconditionmxstart >> /home/pi/tesla/go/cron.log 2>&1")
			common.CreateCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 360 300 go run main.go -preconditionmxstart >> /home/pi/tesla/go/cron.log 2>&1",
				start_time.Minute(),
				start_time.Hour(),
				start_time.Day(),
				int(start_time.Month()))
		}
	}
}
