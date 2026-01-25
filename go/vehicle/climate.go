package vehicle

import (
	"time"

	"github.com/themonomers/tesla/go/common"
)

// Creates a trigger to precondition the cabin for the following morning,
// based on if the car is at the primary location and if "Eco Mode" is off
// similar to how Nest thermostats work for vacation scenarios.  With the
// new endpoints released, you can achieve the same functionality by setting
// scheduled departure for preconditioning.  I decided to keep this code
// running as I don't drive long distances so the added feature of
// preconditioning the battery, in addition to the cabin, is a waste of
// energy (entropy) for me.
func SetM3Precondition(data map[string]any, eco_mode string, start_time time.Time) time.Time {
	// check if eco mode is off first so we don't have to even call the
	// Tesla API if we don't have to
	if eco_mode == "off" {
		// check if the car is with 0.25 miles of the primary location
		if common.IsVehicleAtPrimary(data) {
			// create precondition start crontab at preferred time tomorrow
			common.DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -preconditionm3start >> /home/pi/tesla/go/cron.log 2>&1")
			common.CreateCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -preconditionm3start >> /home/pi/tesla/go/cron.log 2>&1",
				start_time.Minute(),
				start_time.Hour(),
				start_time.Day(),
				int(start_time.Month()))
		}

		return start_time
	} else {
		return time.Time{}
	}
}

func SetMXPrecondition(data map[string]any, eco_mode string, start_time time.Time) time.Time {
	// check if eco mode is off first so we don't have to even call the
	// Tesla API if we don't have to
	if eco_mode == "off" {
		// check if the car is with 0.25 miles of the primary location
		if common.IsVehicleAtPrimary(data) {
			// create precondition start crontab at preferred time tomorrow
			common.DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -preconditionmxstart >> /home/pi/tesla/go/cron.log 2>&1")
			common.CreateCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -preconditionmxstart >> /home/pi/tesla/go/cron.log 2>&1",
				start_time.Minute(),
				start_time.Hour(),
				start_time.Day(),
				int(start_time.Month()))
		}

		return start_time
	} else {
		return time.Time{}
	}
}
