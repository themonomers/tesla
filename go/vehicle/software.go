package vehicle

import (
	"fmt"
	"time"
)

// Mimics scheduling a software update from the vehicle interface
// by using crontab.
func ScheduleUpdate(vin string, time time.Time) {
	DeleteCronTab(fmt.Sprintf("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -%s "+
		">> /home/pi/tesla/go/cron.log 2>&1", GetInLineSub("schedule", vin, "softwareupdate")))
	CreateCronTab(fmt.Sprintf("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -%s "+
		">> /home/pi/tesla/go/cron.log 2>&1", GetInLineSub("schedule", vin, "softwareupdate")),
		time.Minute(),
		time.Hour(),
		time.Day(),
		int(time.Month()))
}
