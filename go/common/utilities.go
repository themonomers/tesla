package common

import (
	"bytes"
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"fmt"
	"log/slog"
	"math"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

var R float64 = 3958.8           // Earth radius in miles
var WAIT_TIME time.Duration = 30 // seconds

// Calculates if the distance of the car is greater than 0.25 miles away from the
// primary location.  The calculation uses Haversine Formula expressed in terms of a
// two-argument inverse tangent function to calculate the great circle distance
// between two points on the Earth. This is the method recommended for
// calculating short distances by Bob Chamberlain (rgc@jpl.nasa.gov) of Caltech
// and NASA's Jet Propulsion Laboratory as described on the U.S. Census Bureau
// Web site.
func IsVehicleAtPrimary(data map[string]any) bool {
	return isVehicleAtLocation(data, EncryptedCfg.Vehicle.PrimaryLat, EncryptedCfg.Vehicle.PrimaryLng)
}

func IsVehicleAtSecondary(data map[string]any) bool {
	return isVehicleAtLocation(data, EncryptedCfg.Vehicle.SecondaryLat, EncryptedCfg.Vehicle.SecondaryLng)
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
	loc, _ := time.LoadLocation(Cfg.General.Timezone)

	date, _ := time.ParseInLocation("2006-1-2 15:4", strconv.Itoa(now.Year())+"-"+strconv.Itoa(int(now.Month()))+"-"+strconv.Itoa(now.Day())+" "+t, loc)

	return date.AddDate(0, 0, 1)
}

func GetTodayTime(t string) time.Time {
	now := time.Now()
	loc, _ := time.LoadLocation(Cfg.General.Timezone)

	date, _ := time.ParseInLocation("2006-1-2 15:4", strconv.Itoa(now.Year())+"-"+strconv.Itoa(int(now.Month()))+"-"+strconv.Itoa(now.Day())+" "+t, loc)

	return date
}

// Uses a free weather service with API to look up data by zipcode or other
// attributes.  Gets current weather conditions.
func GetCurrentWeather(lat, lng float64) map[string]any {
	url := Cfg.Uri.OpenweathermapBaseUrl +
		"/onecall" +
		"?lat=" + strconv.FormatFloat(lat, 'f', -1, 64) +
		"&lon=" + strconv.FormatFloat(lng, 'f', -1, 64) +
		"&appid=" + EncryptedCfg.Weather.OpenweathermapKey +
		"&exclude=minutely,hourly,daily,alerts" +
		"&units=metric"

	resp, _ := http.Get(url)

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
	url := Cfg.Uri.OpenweathermapBaseUrl +
		"/onecall" +
		"?lat=" + strconv.FormatFloat(lat, 'f', -1, 64) +
		"&lon=" + strconv.FormatFloat(lng, 'f', -1, 64) +
		"&appid=" + EncryptedCfg.Weather.OpenweathermapKey +
		"&exclude=current,minutely,alerts" +
		"&units=metric"

	resp, _ := http.Get(url)

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
	if err != nil {
		slog.Error("CreateCronTab(): exec.Command(): " + err.Error())
	}
}

// Removes crontab for a single command.
func DeleteCronTab(command string) {
	err := exec.Command("bash", "-c", "(crontab -l | grep -v '"+command+"') | crontab -").Run()
	if err != nil {
		slog.Error("DeleteCronTab(): exec.Command(): " + err.Error())
	}
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

// Retrieves absolute filepath based on standardized file structure.
func GetFilePath(file string) string {
	cwd, _ := os.Getwd()
	parent := filepath.Dir(cwd)

	return parent + "/python" + strings.TrimPrefix(file, ".")
}

// Centralize repetitive request posts.
func SendRequest(method, url, token string, payload []byte) *http.Response {
	var resp *http.Response

	req, _ := http.NewRequest(method, url, bytes.NewBuffer(payload))

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+token)
	switch token {
	case TokenCfg.Tesla.AccessToken:
		if strings.HasPrefix(url, Cfg.Uri.TeslaBaseProxyUrl) {
			resp, _ = getHttpsClientWithCert().Do(req)
		} else {
			resp, _ = http.DefaultClient.Do(req)
		}
	case LocalTokenCfg.Tesla.Token:
		resp, _ = getHttpsClient().Do(req)
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
	caCert, _ := os.ReadFile(GetFilePath(Cfg.File.TeslaCert))

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
						cert, _ := x509.ParseCertificate(asn1Data)
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

// Construct conditional in-line string substitutions
func GetInLineSub(prefix, vin, suffix string) string {
	var s string

	switch vin {
	case EncryptedCfg.Vehicle.M3Vin:
		s = prefix + "m3" + suffix
	case EncryptedCfg.Vehicle.MxVin:
		s = prefix + "mx" + suffix
	}

	return s
}
