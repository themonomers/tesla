package vehicle

import (
	"fmt"
)

// Script to clean up crontabs created for Tesla Climate, Charge Check, and
// Software Update.  Should be set to run in the middle of the day as all
// the crontabs are set for evening or early morning.
func RemoveTeslaCron() {
	values := [2]string{"m3", "mx"}

	for _, val := range values {
		DeleteCronTab(fmt.Sprintf("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -%s >> "+
			"/home/pi/tesla/go/cron.log 2>&1", GetInLineSub("start", val, "precondition")))
		DeleteCronTab(fmt.Sprintf("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -%s >> "+
			"/home/pi/tesla/go/cron.log 2>&1", GetInLineSub("stop", val, "precondition")))

		DeleteCronTab(fmt.Sprintf("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -%s >> "+
			"/home/pi/tesla/go/cron.log 2>&1", GetInLineSub("check", val, "charge")))

		DeleteCronTab(fmt.Sprintf("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -%s >> "+
			"/home/pi/tesla/go/cron.log 2>&1", GetInLineSub("schedule", val, "softwareupdate")))
	}
}
