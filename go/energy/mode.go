package energy

import (
	"fmt"
	"time"

	"github.com/themonomers/tesla/go/common"
)

var PRIMARY_LAT float64
var PRIMARY_LNG float64
var PCT_THRESHOLD float64 = 0.5

func init() {
	var err error

	c := common.GetConfig()
	PRIMARY_LAT, err = c.Float("vehicle.primary_lat")
	common.LogError("init(): load vehicle primary lat", err)

	PRIMARY_LNG, err = c.Float("vehicle.primary_lng")
	common.LogError("init(): load vehicle primary lng", err)

	EMAIL_1, err = c.String("notification.email_1")
	common.LogError("init(): load email 1", err)
}

// Set to run on an early morning cron job (before sunrise) that will
// check today and tomorrow's weather and if more than a certain percentage
// of rain is forecasted between sunrise and sunset, set the backup reserve
// to 100% so it will reserve the battery stored energy and prioritize
// charging the battery in case there is an outage.  There tends not to be
// enough solar generation during rainy days for self-powered or time-based
// control modes while also recharging the battery to 100%.
func SetEnergyModeBasedOnWeather() {
	// get weather forecast
	wdata := common.GetDailyWeather(PRIMARY_LAT, PRIMARY_LNG)
	check_dates := []time.Time{time.Now(), time.Now().Add(time.Duration(24 * time.Hour))}
	var msg = ""

	for _, val_1 := range check_dates {
		var forecast = ""
		var rain = 0
		var total = 0

		// get sunrise and sunset times
		for _, val_2 := range wdata["daily"].([]interface{}) {
			dt := time.Unix(int64(val_2.(map[string]interface{})["dt"].(float64)), 0)

			if dt.Year() == val_1.Year() &&
				dt.Month() == val_1.Month() &&
				dt.Day() == val_1.Day() {
				sunrise := time.Unix(int64(val_2.(map[string]interface{})["sunrise"].(float64)), 0)
				sunset := time.Unix(int64(val_2.(map[string]interface{})["sunset"].(float64)), 0)

				// loop through the hourly weather matching year, month, day, and
				// between the hour values of sunrise and sunset
				for _, val_3 := range wdata["hourly"].([]interface{}) {
					dt = time.Unix(int64(val_3.(map[string]interface{})["dt"].(float64)), 0)

					if dt.Year() == val_1.Year() &&
						dt.Month() == val_1.Month() &&
						dt.Day() == val_1.Day() &&
						dt.Hour() >= sunrise.Hour() &&
						dt.Hour() <= sunset.Hour() {
						weather := val_3.(map[string]interface{})["weather"].([]interface{})[0].(map[string]interface{})["main"].(string)
						forecast += dt.Format("2006-01:02 15:04:05") + ": " + weather + "\n"

						// count how many 'Rain' hours there are
						if weather == "Rain" {
							rain += 1
						}

						// count how many total hours there are between sunrise and sunset
						total += 1
					}
				}

				// if the ratio of rain to non-rain hours is greater than a specified
				// percentage, prep content for email
				if float64(rain/total) > PCT_THRESHOLD {
					msg += "Greater than " + fmt.Sprintf("%.0f", PCT_THRESHOLD*100)
					msg += "% rain forecasted, setting backup reserve to 100%\n"
					msg += "Percent rain: "
					msg += fmt.Sprintf("%.1f", float64(rain/total*100)) + "%\n"
					msg += forecast + "\n"
				}
			}
		}
	}

	// if the ratio of rain to non-rain hours for today or tomorrow
	// is greater than a specified percentage, set backup reserve to
	// 100% and send email, otherwise set to normal backup reserve of 35%
	if msg != "" {
		SetBackupReserve(100)
		common.SendEmail(EMAIL_1, "Energy:  Setting Backup Reserve to 100%", msg, "")
	} else {
		SetBackupReserve(35)
	}
}
