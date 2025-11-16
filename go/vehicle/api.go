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

// Function to send API call to stop charging a vehicle.
func StopChargeVehicle(vin string) map[string]any {
	if vin == MX_VIN {
		return stopChargeVehicle(vin)
	}

	var url = BASE_PROXY_URL +
		"/vehicles/" +
		vin +
		"/command/charge_stop"

	req, err := http.NewRequest("POST", url, nil)
	common.LogError("StopChargeVehicle(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := getHttpsClient().Do(req)
	common.LogError("StopChargeVehicle(): getHttpClient", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

func stopChargeVehicle(vin string) map[string]any {
	var url = BASE_OWNER_URL +
		"/vehicles/" +
		getVehicleId(vin) +
		"/command/charge_stop"

	req, err := http.NewRequest("POST", url, nil)
	common.LogError("stopChargeVehicle(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := http.DefaultClient.Do(req)
	common.LogError("stopChargeVehicle(): http.DefaultClient.Do", err)

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

// Per Tesla (https://developer.tesla.com/docs/fleet-api/endpoints/vehicle-commands#set-scheduled-charging):
// This endpoint is not recommended beginning with firmware version 2024.26.
//
// Sends command and parameter to set a specific vehicle to charge
// at a scheduled time.  Scheduled Time is in minutes after midnight,
// e.g. 7:30 AM = (7 * 60) + 30 = 450
func SetScheduledCharging(vin string, sch_time int) map[string]any {
	if vin == MX_VIN {
		return setScheduledCharging(vin, sch_time)
	}

	var url = BASE_PROXY_URL +
		"/vehicles/" +
		vin +
		"/command/set_scheduled_charging"

	payload, _ := json.Marshal(map[string]any{
		"enable": true,
		"time":   sch_time,
	})

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(payload))
	common.LogError("SetScheduledCharging(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := getHttpsClient().Do(req)
	common.LogError("SetScheduledCharging(): getHttpClient", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

func setScheduledCharging(vin string, sch_time int) map[string]any {
	var url = BASE_OWNER_URL +
		"/vehicles/" +
		getVehicleId(vin) +
		"/command/set_scheduled_charging"

	payload, _ := json.Marshal(map[string]any{
		"enable": true,
		"time":   sch_time,
	})

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(payload))
	common.LogError("setScheduledCharging(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := http.DefaultClient.Do(req)
	common.LogError("setScheduledCharging(): http.DefaultClient.Do", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

// Function to set vehicle temperature.
func SetCarTemp(vin string, d_temp float64, p_temp float64) map[string]any {
	if vin == MX_VIN {
		return setCarTemp(vin, d_temp, p_temp)
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
	common.LogError("SetCarTemp(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := getHttpsClient().Do(req)
	common.LogError("SetCarTemp(): getHttpClient", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

func setCarTemp(vin string, d_temp float64, p_temp float64) map[string]any {
	var url = BASE_OWNER_URL +
		"/vehicles/" +
		getVehicleId(vin) +
		"/command/set_temps"

	payload, _ := json.Marshal(map[string]any{
		"driver_temp":    d_temp,
		"passenger_temp": p_temp,
	})

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(payload))
	common.LogError("setCarTemp(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := http.DefaultClient.Do(req)
	common.LogError("setCarTemp(): http.DefaultClient.Do", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

// Function to set vehicle seat heater level.
func SetCarSeatHeating(vin string, seat int, setting int) map[string]any {
	if vin == MX_VIN {
		return setCarSeatHeating(vin, seat, setting)
	}

	var url = BASE_PROXY_URL +
		"/vehicles/" +
		vin +
		"/command/remote_seat_heater_request"

	payload, _ := json.Marshal(map[string]any{
		"seat_position": seat,
		"level":         setting,
	})

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(payload))
	common.LogError("SetCarSeatHeating(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := getHttpsClient().Do(req)
	common.LogError("SetCarSeatHeating(): getHttpClient", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

func setCarSeatHeating(vin string, seat int, setting int) map[string]any {
	var url = BASE_OWNER_URL +
		"/vehicles/" +
		getVehicleId(vin) +
		"/command/remote_seat_heater_request"

	payload, _ := json.Marshal(map[string]any{
		"heater": seat,
		"level":  setting,
	})

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(payload))
	common.LogError("setCarSeatHeating(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := http.DefaultClient.Do(req)
	common.LogError("setCarSeatHeating(): http.DefaultClient.Do", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

// Function to start vehicle preconditioning.
func PreconditionCarStart(vin string) map[string]any {
	if vin == MX_VIN {
		return preconditionCarStart(vin)
	}

	var url = BASE_PROXY_URL +
		"/vehicles/" +
		vin +
		"/command/auto_conditioning_start"

	req, err := http.NewRequest("POST", url, nil)
	common.LogError("PreconditionCarStart(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := getHttpsClient().Do(req)
	common.LogError("PreconditionCarStart(): getHttpClient", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

func preconditionCarStart(vin string) map[string]any {
	var url = BASE_OWNER_URL +
		"/vehicles/" +
		getVehicleId(vin) +
		"/command/auto_conditioning_start"

	req, err := http.NewRequest("POST", url, nil)
	common.LogError("preconditionCarStart(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := http.DefaultClient.Do(req)
	common.LogError("preconditionCarStart(): http.DefaultClient.Do", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

// Function to stop vehicle preconditioning.
func PreconditionCarStop(vin string) map[string]any {
	if vin == MX_VIN {
		return preconditionCarStop(vin)
	}

	var url = BASE_PROXY_URL +
		"/vehicles/" +
		vin +
		"/command/auto_conditioning_stop"

	req, err := http.NewRequest("POST", url, nil)
	common.LogError("PreconditionCarStop(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := getHttpsClient().Do(req)
	common.LogError("PreconditionCarStop(): getHttpClient", err)

	defer resp.Body.Close()
	body := map[string]any{}
	json.NewDecoder(resp.Body).Decode(&body)
	return body
}

func preconditionCarStop(vin string) map[string]any {
	var url = BASE_OWNER_URL +
		"/vehicles/" +
		getVehicleId(vin) +
		"/command/auto_conditioning_stop"

	req, err := http.NewRequest("POST", url, nil)
	common.LogError("preconditionCarStop(): http.NewRequest", err)

	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := http.DefaultClient.Do(req)
	common.LogError("preconditionCarStop(): http.DefaultClient.Do", err)

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
