package vehicle

// Script to clean up crontabs created for Tesla Climate, Charge Check, and
// Software Update.  Should be set to run in the middle of the day as all
// the crontabs are set for evening or early morning.
func RemoveTeslaCron() {
	DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -startm3precondition >> " +
		"/home/pi/tesla/go/cron.log 2>&1")
	DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -stopm3precondition >> " +
		"/home/pi/tesla/go/cron.log 2>&1")
	DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -startmxprecondition >> " +
		"/home/pi/tesla/go/cron.log 2>&1")
	DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -stopmxprecondition >> " +
		"/home/pi/tesla/go/cron.log 2>&1")
	DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -checkm3charge >> " +
		"/home/pi/tesla/go/cron.log 2>&1")
	DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -checkmxcharge >> " +
		"/home/pi/tesla/go/cron.log 2>&1")
	DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -schedulem3softwareupdate " +
		">> /home/pi/tesla/go/cron.log 2>&1")
	DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -schedulemxsoftwareupdate " +
		">> /home/pi/tesla/go/cron.log 2>&1")
}
