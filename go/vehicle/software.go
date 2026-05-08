package vehicle

var M3_SOFTWARE_UPDATE_TIME = "2:30"
var MX_SOFTWARE_UPDATE_TIME = "1:30"

// Mimics scheduling a software update from the vehicle interface
// by using crontab.
func ScheduleUpdate(vin string) {
	switch vin {
	case M3_VIN:
		time := GetTomorrowTime(M3_SOFTWARE_UPDATE_TIME)
		DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -schedulem3softwareupdate " +
			">> /home/pi/tesla/go/cron.log 2>&1")
		CreateCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -schedulem3softwareupdate "+
			">> /home/pi/tesla/go/cron.log 2>&1",
			time.Minute(),
			time.Hour(),
			time.Day(),
			int(time.Month()))
	case MX_VIN:
		time := GetTomorrowTime(MX_SOFTWARE_UPDATE_TIME)
		DeleteCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -schedulemxsoftwareupdate " +
			">> /home/pi/tesla/go/cron.log 2>&1")
		CreateCronTab("cd /home/pi/tesla/go && /usr/bin/timeout -k 60 300 go run main.go -schedulemxsoftwareupdate "+
			">> /home/pi/tesla/go/cron.log 2>&1",
			time.Minute(),
			time.Hour(),
			time.Day(),
			int(time.Month()))
	}
}
