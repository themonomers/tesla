package common

import (
	"bytes"
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"fmt"
	"math"
	"net/http"
	"os"
	"os/exec"
	"strconv"
	"strings"
	"time"

	"github.com/go-ini/ini"
	"github.com/ridgelines/go-config"
)

var ACCESS_TOKEN string
var LOCAL_ACCESS_TOKEN string
var PRIMARY_LAT float64
var PRIMARY_LNG float64
var SECONDARY_LAT float64
var SECONDARY_LNG float64
var R float64 = 3958.8 // Earth radius in miles
var BASE_WEATHER_URL string
var BASE_PROXY_URL string
var CERT string
var OPENWEATHERMAP_KEY string
var TIMEZONE string
var WAIT_TIME time.Duration = 30 // seconds

func init() {
	var err error

	t := GetToken()
	ACCESS_TOKEN, err = t.String("tesla.access_token")
	LogError("init(): load access token", err)

	t = GetLocalEnergyToken()
	LOCAL_ACCESS_TOKEN, err = t.String("tesla.token")
	LogError("init(): load local energy token", err)

	c := GetConfig()
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

	BASE_PROXY_URL, err = c.String("tesla.base_proxy_url")
	LogError("init(): load base proxy url", err)

	CERT, err = c.String("tesla.certificate")
	LogError("init(): load tesla certificate", err)

	TIMEZONE, err = c.String("general.timezone")
	LogError("init(): load timezone", err)
}

// Retrieves dictionary of configuration values.
func GetConfig() *config.Config {
	return getConfigFile("/home/pi/tesla/python/common/config.xor")
}

func GetLocalEnergyConfig() *config.Config {
	return getConfigFile("/home/pi/tesla/python/common/local_config.xor")
}

// Retrievies dictionary of access token values.
func GetToken() *config.Config {
	return getConfigFile("/home/pi/tesla/python/common/token.xor")
}

func GetLocalEnergyToken() *config.Config {
	return getConfigFile("/home/pi/tesla/python/common/local_token.xor")
}

// Golang ini configuration loader from a filename.
func getConfigFile(read_fn string) *config.Config {
	iniFile := newINIFile(Decrypt(read_fn))
	env := config.NewStatic(iniFile)
	c := config.NewConfig([]config.Provider{env})
	err := c.Load()
	LogErrorStdOut("getConfigFile(): c.Load()", err)

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
func IsVehicleAtPrimary(data map[string]any) bool {
	return isVehicleAtLocation(data, PRIMARY_LAT, PRIMARY_LNG)
}

func IsVehicleAtSecondary(data map[string]any) bool {
	return isVehicleAtLocation(data, SECONDARY_LAT, SECONDARY_LNG)
}

func isVehicleAtLocation(data map[string]any, lat float64, lng float64) bool {
	d := getDistance(data["response"].(map[string]any)["drive_state"].(map[string]any)["latitude"].(float64),
		data["response"].(map[string]any)["drive_state"].(map[string]any)["longitude"].(float64),
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

	date, err := time.ParseInLocation("2006-1-2 15:4", strconv.Itoa(now.Year())+"-"+strconv.Itoa(int(now.Month()))+"-"+strconv.Itoa(now.Day())+" "+t, loc)
	LogError("GetTomorrowTime(): time.ParseInLocation", err)

	return date.AddDate(0, 0, 1)
}

func GetTodayTime(t string) time.Time {
	now := time.Now()
	loc, _ := time.LoadLocation(TIMEZONE)

	date, err := time.ParseInLocation("2006-1-2 15:4", strconv.Itoa(now.Year())+"-"+strconv.Itoa(int(now.Month()))+"-"+strconv.Itoa(now.Day())+" "+t, loc)
	LogError("GetTomorrowTime(): time.ParseInLocation", err)

	return date
}

// Uses a free weather service with API to look up data by zipcode or other
// attributes.  Gets current weather conditions.
func GetCurrentWeather(lat, lng float64) map[string]any {
	url := BASE_WEATHER_URL +
		"/onecall" +
		"?lat=" + strconv.FormatFloat(lat, 'f', -1, 64) +
		"&lon=" + strconv.FormatFloat(lng, 'f', -1, 64) +
		"&appid=" + OPENWEATHERMAP_KEY +
		"&exclude=minutely,hourly,daily,alerts" +
		"&units=metric"

	resp, err := http.Get(url)
	LogError("GetCurrentWeather(): http.Get", err)

	if resp.StatusCode != 200 {
		time.Sleep(WAIT_TIME * time.Second)
		return GetCurrentWeather(lat, lng)
	}

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)

	return body
}

// Uses a free weather service with API to look up data by latitude and
// longitude or other attributes.  Gets daily weather conditions for
// today + 7 days, and hourly weather conditions for 48 hours.
func GetDailyWeather(lat, lng float64) map[string]any {
	url := BASE_WEATHER_URL +
		"/onecall" +
		"?lat=" + strconv.FormatFloat(lat, 'f', -1, 64) +
		"&lon=" + strconv.FormatFloat(lng, 'f', -1, 64) +
		"&appid=" + OPENWEATHERMAP_KEY +
		"&exclude=current,minutely,alerts" +
		"&units=metric"

	resp, err := http.Get(url)
	LogError("GetDailyWeather(): http.Get", err)

	if resp.StatusCode != 200 {
		time.Sleep(WAIT_TIME * time.Second)
		return GetDailyWeather(lat, lng)
	}

	defer resp.Body.Close()
	body := map[string]any{}
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

func FindStringIn2DArray(arr [][]any, target string) []int64 {
	i := []int64{}
	for rowIndex, row := range arr {
		for _, val := range row {
			if val == target {
				i = append(i, int64(rowIndex))
			}
		}
	}

	return i
}

// Centralize repetitive request posts.
func SendRequest(method, url, token string, payload []byte) *http.Response {
	var resp *http.Response

	req, err := http.NewRequest(method, url, bytes.NewBuffer(payload))
	LogError(url+": http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+token)
	switch token {
	case ACCESS_TOKEN:
		if strings.HasPrefix(url, BASE_PROXY_URL) {
			resp, err = getHttpsClientWithCert().Do(req)
			LogError(url+": getHttpsClientWithCert", err)
		} else {
			resp, err = http.DefaultClient.Do(req)
			LogError(url+": http.DefaultClient.Do", err)
		}
	case LOCAL_ACCESS_TOKEN:
		resp, err = getHttpsClient().Do(req)
		LogError(url+": getHttpsClient", err)
	}

	return resp
}

// Retrieves HTTPS client and ignores x509 certificate error
func getHttpsClient() *http.Client {
	tr := &http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
	}

	return &http.Client{Transport: tr}
}

// Retrieves HTTP client with a workaround for error "tls: failed to verify certificate: x509:
// certificate relies on legacy Common Name field, use SANs instead" which skips the hostname
// verification for self-signed certificates.
func getHttpsClientWithCert() *http.Client {
	caCert, err := os.ReadFile(CERT)
	LogError("getHttpsClient(): os.ReadFile", err)

	caCertPool := x509.NewCertPool()
	caCertPool.AppendCertsFromPEM(caCert)

	client := &http.Client{
		Transport: &http.Transport{
			TLSClientConfig: &tls.Config{
				InsecureSkipVerify: true, // Not actually skipping, we check the cert in VerifyPeerCertificate
				RootCAs:            caCertPool,
				VerifyPeerCertificate: func(rawCerts [][]byte, verifiedChains [][]*x509.Certificate) error {
					// Code copy/pasted and adapted from
					// https://github.com/golang/go/blob/81555cb4f3521b53f9de4ce15f64b77cc9df61b9/src/crypto/tls/handshake_client.go#L327-L344
					// but adapted to skip the hostname verification.
					// See https://github.com/golang/go/issues/21971#issuecomment-412836078.

					// If this is the first handshake on a connection, process and
					// (optionally) verify the server's certificates.
					certs := make([]*x509.Certificate, len(rawCerts))
					for i, asn1Data := range rawCerts {
						cert, err := x509.ParseCertificate(asn1Data)
						LogError("getHttpsClient(): x509.ParseCertificate", err)
						certs[i] = cert
					}

					opts := x509.VerifyOptions{
						Roots:         caCertPool,
						CurrentTime:   time.Now(),
						DNSName:       "", // <- skip hostname verification
						Intermediates: x509.NewCertPool(),
					}

					for i, cert := range certs {
						if i == 0 {
							continue
						}
						opts.Intermediates.AddCert(cert)
					}
					_, err := certs[0].Verify(opts)
					return err
				},
			},
		},
	}

	return client
}

// Converts a HTTP Response to a JSON object
func GetJson(response *http.Response) map[string]any {
	defer response.Body.Close()
	body := map[string]any{}
	json.NewDecoder(response.Body).Decode(&body)
	return body
}
