package vehicle

import (
	"github.com/themonomers/tesla/go/common"
)

// Script to clean up crontabs created for Tesla Climate and Charge Check.
// Should be set to run in the middle of the day as all the crontabs are
// evening or early morning.
func RemoveTeslaCron() {
	common.DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -preconditionm3start >> /home/pi/tesla/go/cron.log 2>&1")
	common.DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -preconditionm3stop >> /home/pi/tesla/go/cron.log 2>&1")
	common.DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -preconditionmxstart >> /home/pi/tesla/go/cron.log 2>&1")
	common.DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -preconditionmxstop >> /home/pi/tesla/go/cron.log 2>&1")
	common.DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -chargecheckm3 >> /home/pi/tesla/go/cron.log 2>&1")
	common.DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -chargecheckmx >> /home/pi/tesla/go/cron.log 2>&1")
}
