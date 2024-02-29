package energy

import (
	"crypto/tls"
	"encoding/json"
	"net/http"

	"github.com/themonomers/tesla/go/common"
)

var ACCESS_TOKEN string
var SITE_ID string
var BATTERY_ID string
var BASE_OWNER_URL string

func init() {
	var err error

	t := common.GetToken()
	ACCESS_TOKEN, err = t.String("tesla.access_token")
	common.LogError("init(): load access token", err)

	c := common.GetConfig()
	SITE_ID, err = c.String("energy.site_id")
	common.LogError("init(): load site id", err)

	BATTERY_ID, err = c.String("energy.battery_id")
	common.LogError("init(): load battery id", err)

	BASE_OWNER_URL, err = c.String("tesla.base_owner_url")
	common.LogError("init(): load base owner url", err)

	TIMEZONE, err = c.String("general.timezone")
	common.LogError("init(): load timezone", err)
}

// Gets some quick and basic information.
func GetSiteStatus() map[string]interface{} {
	url := BASE_OWNER_URL +
		"/energy_sites/" +
		SITE_ID +
		"/site_status"

	req, err := http.NewRequest("GET", url, nil)
	common.LogError("GetSiteStatus(): http.NewRequest", err)

	req.Header.Add("authorization", "Bearer "+ACCESS_TOKEN)
	resp, err := GetHttpsClient().Do(req)
	common.LogError("GetSiteStatus(): GetHttpsClient", err)

	defer resp.Body.Close()
	body := map[string]interface{}{}
	json.NewDecoder(resp.Body).Decode(&body)

	return body
}

// Retrieves HTTPS client and ignores x509 certificate error
func GetHttpsClient() *http.Client {
	tr := &http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
	}

	return &http.Client{Transport: tr}
}
