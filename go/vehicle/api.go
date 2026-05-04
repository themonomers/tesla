package vehicle

import (
	"bytes"
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"net/http"
	"net/url"
	"os"
	"time"

	"github.com/themonomers/tesla/go/common"
)

var ACCESS_TOKEN string
var BASE_OWNER_URL string
var BASE_PROXY_URL string
var CERT string
var WAIT_TIME time.Duration = 30 // seconds

func init() {
	var err error

	var t = common.GetToken()
	ACCESS_TOKEN, err = t.String("tesla.access_token")
	common.LogError("init(): load access token", err)

	var c = common.GetConfig()
	BASE_PROXY_URL, err = c.String("tesla.base_proxy_url")
	common.LogError("init(): load base proxy url", err)

	BASE_OWNER_URL, err = c.String("tesla.base_owner_url")
	common.LogError("init(): load base owner url", err)

	CERT, err = c.String("tesla.certificate")
	common.LogError("init(): load tesla certificate", err)
}

// Retrieves the vehicle data needed for higher level functions to drive
// calcuations and actions.
func GetVehicleData(vin string) map[string]any {
	var url = BASE_PROXY_URL +
		"/vehicles/" +
		vin +
		"/vehicle_data?endpoints=" +
		url.PathEscape(
			"location_data;"+
				"charge_state;"+
				"climate_state;"+
				"vehicle_state;"+
				"gui_settings;"+
				"vehicle_config;"+
				"closures_state;"+
				"drive_state")

	req, err := http.NewRequest("GET", url, nil)
	common.LogError("GetVehicleData(): http.NewRequest", err)

	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := getHttpsClient().Do(req)
	common.LogError("GetVehicleData(): getHttpClient", err)

	if resp.StatusCode != 200 {
		WakeVehicle(vin)
		time.Sleep(WAIT_TIME * time.Second)
		return GetVehicleData(vin)
	}

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

// Function to repeatedly run (after a certain wait time) to wake the vehicle up
// when it's asleep.
func WakeVehicle(vin string) map[string]any {
	var url = BASE_PROXY_URL +
		"/vehicles/" +
		vin +
		"/wake_up"

	req, err := http.NewRequest("POST", url, nil)
	common.LogError("WakeVehicle(): http.NewRequest", err)

	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := getHttpsClient().Do(req)
	common.LogError("WakeVehicle(): getHttpClient", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)

	return body
}

// Function to send API call to start charging a vehicle.
func StartCharge(vin string) map[string]any {
	if vin == MX_VIN {
		return startCharge(vin)
	}

	var url = BASE_PROXY_URL +
		"/vehicles/" +
		vin +
		"/command/charge_start"

	req, err := http.NewRequest("POST", url, nil)
	common.LogError("StartCharge(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := getHttpsClient().Do(req)
	common.LogError("StartCharge(): getHttpClient", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

func startCharge(vin string) map[string]any {
	var url = BASE_OWNER_URL +
		"/vehicles/" +
		getVehicleId(vin) +
		"/command/charge_start"

	req, err := http.NewRequest("POST", url, nil)
	common.LogError("startCharge(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := http.DefaultClient.Do(req)
	common.LogError("startCharge(): http.DefaultClient.Do", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

// Function to send API call to stop charging a vehicle.
func StopCharge(vin string) map[string]any {
	if vin == MX_VIN {
		return stopCharge(vin)
	}

	var url = BASE_PROXY_URL +
		"/vehicles/" +
		vin +
		"/command/charge_stop"

	req, err := http.NewRequest("POST", url, nil)
	common.LogError("StopCharge(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := getHttpsClient().Do(req)
	common.LogError("StopCharge(): getHttpClient", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

func stopCharge(vin string) map[string]any {
	var url = BASE_OWNER_URL +
		"/vehicles/" +
		getVehicleId(vin) +
		"/command/charge_stop"

	req, err := http.NewRequest("POST", url, nil)
	common.LogError("stopCharge(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := http.DefaultClient.Do(req)
	common.LogError("stopCharge(): http.DefaultClient.Do", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

// Uses new endpoint to add a schedule for vehicle charging.
// Scheduled Time is in minutes after midnight, e.g. 7:30 AM
// = (7 * 60) + 30 = 450
func AddChargeSchedule(vin string, lat float64, lon float64, sch_time int, id int) map[string]any {
	if vin == MX_VIN {
		return addChargeSchedule(vin, lat, lon, sch_time, id)
	}

	var url = BASE_PROXY_URL +
		"/vehicles/" +
		vin +
		"/command/add_charge_schedule"

	payload, _ := json.Marshal(map[string]any{
		"days_of_week":  "All",
		"enabled":       true,
		"start_enabled": true,
		"end_enabled":   false,
		"lat":           lat,
		"lon":           lon,
		"start_time":    sch_time,
		"one_time":      false,
		"id":            id,
	})

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(payload))
	common.LogError("AddChargeSchedule(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := getHttpsClient().Do(req)
	common.LogError("AddChargeSchedule(): getHttpClient", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

func addChargeSchedule(vin string, lat float64, lon float64, sch_time int, id int) map[string]any {
	var url = BASE_OWNER_URL +
		"/vehicles/" +
		getVehicleId(vin) +
		"/command/add_charge_schedule"

	payload, _ := json.Marshal(map[string]any{
		"days_of_week":  "All",
		"enabled":       true,
		"start_enabled": true,
		"end_enabled":   false,
		"lat":           lat,
		"lon":           lon,
		"start_time":    sch_time,
		"one_time":      false,
		"id":            id,
	})

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(payload))
	common.LogError("addChargeSchedule(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := http.DefaultClient.Do(req)
	common.LogError("addChargeSchedule(): http.DefaultClient.Do", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

// Uses new endpoint to remove a schedule for vehicle charging.
// The Owner API for this function on older model vehicles throws
// an error ("x509: certificate signed by unknown authority") unlike
// other endpoints.  This endpoint works for both newer and older model
// cars.
func RemoveChargeSchedule(vin string, id int) map[string]any {
	var url = BASE_PROXY_URL +
		"/vehicles/" +
		vin +
		"/command/remove_charge_schedule"

	payload, _ := json.Marshal(map[string]any{
		"id": id,
	})

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(payload))
	common.LogError("RemoveChargeSchedule(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := getHttpsClient().Do(req)
	common.LogError("RemoveChargeSchedule(): getHttpClient", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

// Sets the driver and/or passenger-side cabin temperature
// (and other zones if sync is enabled).
//
// d_temp:  driver side temperature in C
// p_temp:  passenger side temperature in C
func SetTemp(vin string, d_temp float64, p_temp float64) map[string]any {
	if vin == MX_VIN {
		return setTemp(vin, d_temp, p_temp)
	}

	var url = BASE_PROXY_URL +
		"/vehicles/" +
		vin +
		"/command/set_temps"

	payload, _ := json.Marshal(map[string]any{
		"driver_temp":    d_temp,
		"passenger_temp": p_temp,
	})

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(payload))
	common.LogError("SetTemp(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := getHttpsClient().Do(req)
	common.LogError("SetTemp(): getHttpClient", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

func setTemp(vin string, d_temp float64, p_temp float64) map[string]any {
	var url = BASE_OWNER_URL +
		"/vehicles/" +
		getVehicleId(vin) +
		"/command/set_temps"

	payload, _ := json.Marshal(map[string]any{
		"driver_temp":    d_temp,
		"passenger_temp": p_temp,
	})

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(payload))
	common.LogError("setTemp(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := http.DefaultClient.Do(req)
	common.LogError("setTemp(): http.DefaultClient.Do", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

// Sets seat heating. Requires preconditioning or climate keeper to be on.
//
// seat:
//
//	0: front left
//	1: front right
//	2: rear left
//	4: rear center
//	5: rear right
//
// setting:
//
//	0: off
//	1: low
//	2: medium
//	3: high
func SetSeatHeating(vin string, seat int, setting int) map[string]any {
	if vin == MX_VIN {
		return setSeatHeating(vin, seat, setting)
	}

	return setSeatTemp(vin, "heat", seat, setting)
}

func setSeatHeating(vin string, seat int, setting int) map[string]any {
	var url = BASE_OWNER_URL +
		"/vehicles/" +
		getVehicleId(vin) +
		"/command/remote_seat_heater_request"

	payload, _ := json.Marshal(map[string]any{
		"heater": seat,
		"level":  setting,
	})

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(payload))
	common.LogError("setSeatHeating(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := http.DefaultClient.Do(req)
	common.LogError("setSeatHeating(): http.DefaultClient.Do", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

// Sets seat cooling. Requires preconditioning or climate keeper to be on.
//
// seat:
//
//	1: front left
//	2: front right
//
// setting:
//
//	0: off
//	1: low
//	2: medium
//	3: high
func SetSeatCooling(vin string, seat int, setting int) map[string]any {
	if vin == MX_VIN {
		return nil
	}

	return setSeatTemp(vin, "cool", seat, setting)
}

// Function to set vehicle seat heater or cooler level.
func setSeatTemp(vin string, mode string, seat int, setting int) map[string]any {
	var url = BASE_PROXY_URL +
		"/vehicles/" +
		vin

	var payload []byte

	switch mode {
	case "heat":
		url += "/command/remote_seat_heater_request"

		payload, _ = json.Marshal(map[string]any{
			"seat_position": seat,
			"level":         setting,
		})
	case "cool":
		url += "/command/remote_seat_cooler_request"

		payload, _ = json.Marshal(map[string]any{
			"seat_position":     seat,
			"seat_cooler_level": setting,
		})
	default:
		return nil
	}

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(payload))
	common.LogError("setSeatTemp(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := getHttpsClient().Do(req)
	common.LogError("setSeatTemp(): getHttpClient", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

// Sets automatic seat heating and cooling. Requires preconditioning or
// climate keeper to be on.
//
// enable:  True/False (on/off)
// seat:
//
//	1: front left
//	2: front right
func SetSeatClimateAuto(vin string, enable bool, seat int) map[string]any {
	var url = BASE_OWNER_URL +
		"/vehicles/" +
		getVehicleId(vin) +
		"/command/remote_auto_seat_climate_request"

	payload, _ := json.Marshal(map[string]any{
		"auto_climate_on":    enable,
		"auto_seat_position": seat,
	})

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(payload))
	common.LogError("SetSeatClimateAuto(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := http.DefaultClient.Do(req)
	common.LogError("SetSeatClimateAuto(): http.DefaultClient.Do", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

// Sets steering wheel heating on/off. For vehicles that do not
// support auto steering wheel heat. Requires preconditioning or
// climate keeper to be on.
//
// enable:  True/False (on/off)
func SetSteeringWheelHeating(vin string, enable bool) map[string]any {
	var url = BASE_OWNER_URL +
		"/vehicles/" +
		getVehicleId(vin) +
		"/command/remote_steering_wheel_heater_request"

	payload, _ := json.Marshal(map[string]any{
		"on": enable,
	})

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(payload))
	common.LogError("SetSteeringWheelHeating(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := http.DefaultClient.Do(req)
	common.LogError("SetSteeringWheelHeating(): http.DefaultClient.Do", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

// Function to start vehicle preconditioning.
func StartPrecondition(vin string) map[string]any {
	if vin == MX_VIN {
		return startPrecondition(vin)
	}

	var url = BASE_PROXY_URL +
		"/vehicles/" +
		vin +
		"/command/auto_conditioning_start"

	req, err := http.NewRequest("POST", url, nil)
	common.LogError("StartPrecondition(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := getHttpsClient().Do(req)
	common.LogError("StartPrecondition(): getHttpClient", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

func startPrecondition(vin string) map[string]any {
	var url = BASE_OWNER_URL +
		"/vehicles/" +
		getVehicleId(vin) +
		"/command/auto_conditioning_start"

	req, err := http.NewRequest("POST", url, nil)
	common.LogError("startPrecondition(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := http.DefaultClient.Do(req)
	common.LogError("startPrecondition(): http.DefaultClient.Do", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

// Function to stop vehicle preconditioning.
func StopPrecondition(vin string) map[string]any {
	if vin == MX_VIN {
		return stopPrecondition(vin)
	}

	var url = BASE_PROXY_URL +
		"/vehicles/" +
		vin +
		"/command/auto_conditioning_stop"

	req, err := http.NewRequest("POST", url, nil)
	common.LogError("StopPrecondition(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := getHttpsClient().Do(req)
	common.LogError("StopPrecondition(): getHttpClient", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

func stopPrecondition(vin string) map[string]any {
	var url = BASE_OWNER_URL +
		"/vehicles/" +
		getVehicleId(vin) +
		"/command/auto_conditioning_stop"

	req, err := http.NewRequest("POST", url, nil)
	common.LogError("stopPrecondition(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := http.DefaultClient.Do(req)
	common.LogError("stopPrecondition(): http.DefaultClient.Do", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

// Retrieves the vehicle ID, which changes from time to time, by the VIN, which
// doesn't change.  The vehicle ID is required for many of the API calls.
func getVehicleId(vin string) string {
	var data = GetVehicleData(vin)

	return data["response"].(map[string]any)["id_s"].(string)
}

// Retrieves HTTP client with a workaround for error "tls: failed to verify certificate: x509:
// certificate relies on legacy Common Name field, use SANs instead" which skips the hostname
// verification for self-signed certificates.
func getHttpsClient() *http.Client {
	caCert, err := os.ReadFile(CERT)
	common.LogError("getHttpsClient(): os.ReadFile", err)

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
						common.LogError("getHttpsClient(): x509.ParseCertificate", err)
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
