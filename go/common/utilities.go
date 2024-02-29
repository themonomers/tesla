package common

import (
	"encoding/json"
	"fmt"
	"math"
	"net/http"
	"os/exec"
	"strconv"
	"time"

	"github.com/go-ini/ini"
	"github.com/ridgelines/go-config"
)

var PRIMARY_LAT float64
var PRIMARY_LNG float64
var SECONDARY_LAT float64
var SECONDARY_LNG float64
var R float64 = 3958.8 // Earth radius in miles
var BASE_WEATHER_URL string
var OPENWEATHERMAP_KEY string
var TIMEZONE string

func init() {
	var err error

	var c = GetConfig()
	PRIMARY_LAT, err = c.Float("vehicle.primary_lat")
	LogError("init(): load vehicle primary lat", err)

	PRIMARY_LNG, err = c.Float("vehicle.primary_lng")
	LogError("init(): load vehicle primary lng", err)

	SECONDARY_LAT, err = c.Float("vehicle.secondary_lat")
	LogError("init(): load vehicle secondary lat", err)

	SECONDARY_LNG, err = c.Float("vehicle.secondary_lng")
	LogError("init(): load vehicle secondary lng", err)

	OPENWEATHERMAP_KEY, err = c.String("weather.openweathermap_key")
	LogError("init(): load open weather map key", err)

	BASE_WEATHER_URL, err = c.String("weather.base_url")
	LogError("init(): load open weather map key", err)

	TIMEZONE, err = c.String("general.timezone")
	LogError("init(): load timezone", err)
}

// Retrieves dictionary of configuration values.
func GetConfig() *config.Config {
	return getConfigFile("/home/pi/tesla/python/config.xor")
}

func GetLocalEnergyConfig() *config.Config {
	return getConfigFile("/home/pi/tesla/python/local_config.xor")
}

// Retrievies dictionary of access token values.
func GetToken() *config.Config {
	return getConfigFile("/home/pi/tesla/python/token.xor")
}

func GetLocalEnergyToken() *config.Config {
	return getConfigFile("/home/pi/tesla/python/local_token.xor")
}

// Golang ini configuration loader from a filename.
func getConfigFile(read_fn string) *config.Config {
	iniFile := newINIFile(Decrypt(read_fn))
	env := config.NewStatic(iniFile)
	c := config.NewConfig([]config.Provider{env})
	err := c.Load()
	LogError("getConfigFile(): c.Load()", err)

	return c
}

// Replaces the github.com/ridgelines/go-config function, which only
// takes a filename (string), with the loading function from the
// github.com/go-ini/ini function which also takes raw data ([]byte).
// This avoids having to read the encrypted file, decrypt it, and write
// it to the file system.
func newINIFile(data []byte) map[string]string {
	settings := map[string]string{}

	config, err := ini.Load(data)
	LogError("NewINIFile(): ini.Load", err)

	for _, section := range config.Sections() {
		for _, key := range section.Keys() {
			token := fmt.Sprintf("%s.%s", section.Name(), key.Name())
			settings[token] = key.String()
		}
	}

	return settings
}

// Calculates if the distance of the car is greater than 0.25 miles away from the
// primary location.  The calculation uses Haversine Formula expressed in terms of a
// two-argument inverse tangent function to calculate the great circle distance
// between two points on the Earth. This is the method recommended for
// calculating short distances by Bob Chamberlain (rgc@jpl.nasa.gov) of Caltech
// and NASA's Jet Propulsion Laboratory as described on the U.S. Census Bureau
// Web site.
func IsVehicleAtPrimary(data map[string]interface{}) bool {
	return isVehicleAtLocation(data, PRIMARY_LAT, PRIMARY_LNG)
}

func IsVehicleAtSecondary(data map[string]interface{}) bool {
	return isVehicleAtLocation(data, SECONDARY_LAT, SECONDARY_LNG)
}

func isVehicleAtLocation(data map[string]interface{}, lat float64, lng float64) bool {
	d := getDistance(data["response"].(map[string]interface{})["drive_state"].(map[string]interface{})["latitude"].(float64),
		data["response"].(map[string]interface{})["drive_state"].(map[string]interface{})["longitude"].(float64),
		lat,
		lng)

	// check if the car is more than a quarter of a mile away
	return d < 0.25
}

func getDistance(car_lat, car_lng, x_lat, x_lng float64) float64 {
	diff_lat := toRad(car_lat - x_lat)
	diff_lng := toRad(car_lng - x_lng)

	a := ((math.Sin(diff_lat/2) * math.Sin(diff_lat/2)) +
		math.Cos(x_lat)*
			math.Cos(car_lat)*
			(math.Sin(diff_lng/2)*math.Sin(diff_lng/2)))
	c := 2 * math.Atan2(math.Sqrt(a), math.Sqrt(1-a))
	d := R * c

	return d
}

func toRad(x float64) float64 {
	return x * math.Pi / 180
}

// Helps format the charging or preconditioning time by defaulting the date.
func GetTomorrowTime(t string) time.Time {
	now := time.Now()
	loc, _ := time.LoadLocation(TIMEZONE)

	date, err := time.ParseInLocation("2006-1-02 15:4", strconv.Itoa(now.Year())+"-"+strconv.Itoa(int(now.Month()))+"-"+strconv.Itoa(now.Day())+" "+t, loc)
	LogError("GetTomorrowTime(): time.ParseInLocation", err)

	return date.AddDate(0, 0, 1)
}

func GetTodayTime(t string) time.Time {
	now := time.Now()
	loc, _ := time.LoadLocation(TIMEZONE)

	date, err := time.ParseInLocation("2006-1-02 15:4", strconv.Itoa(now.Year())+"-"+strconv.Itoa(int(now.Month()))+"-"+strconv.Itoa(now.Day())+" "+t, loc)
	LogError("GetTomorrowTime(): time.ParseInLocation", err)

	return date
}

// Uses a free weather service with API to look up data by zipcode or other
// attributes.  Gets current weather conditions.
func GetCurrentWeather(zipcode string) map[string]interface{} {
	url := BASE_WEATHER_URL +
		"/weather" +
		"?zip=" + zipcode +
		"&APPID=" + OPENWEATHERMAP_KEY +
		"&units=metric"

	resp, err := http.Get(url)
	LogError("GetCurrentWeather(): http.Get", err)

	defer resp.Body.Close()
	body := map[string]interface{}{}
	json.NewDecoder(resp.Body).Decode(&body)

	return body
}

// Creates crontab entry for a single command.
func CreateCronTab(command string, minute int, hour int, dom int, mon int) {
	cron := fmt.Sprint(minute) + " " + fmt.Sprint(hour) + " " + fmt.Sprint(dom) + " " + fmt.Sprint(mon) + " * " + command

	err := exec.Command("bash", "-c", "(crontab -l && echo '"+cron+"') | crontab -").Run()
	LogError("CreateCronTab(): exec.Command", err)
}

// Removes crontab for a single command.
func DeleteCronTab(command string) {
	err := exec.Command("bash", "-c", "(crontab -l | grep -v '"+command+"') | crontab -").Run()
	LogError("DeleteCronTab(): exec.Command", err)
}
