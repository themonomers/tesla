package common

import (
	"github.com/influxdata/influxdb/client/v2"
)

var INFLUX_HOST string
var INFLUX_PORT string
var INFLUX_USER string
var INFLUX_PASSWORD string

func init() {
	var err error

	var c = GetConfig()
	INFLUX_HOST, err = c.String("influxdb.host")
	LogError("init(): influxdb host", err)

	INFLUX_PORT, err = c.String("influxdb.port")
	LogError("init(): influxdb port", err)

	INFLUX_USER, err = c.String("influxdb.user")
	LogError("init(): influxdb user", err)

	INFLUX_PASSWORD, err = c.String("influxdb.password")
	LogError("init(): influxdb password", err)
}

func GetDBClient() client.HTTPClient {
	// Create a new HTTPClient
	c, err := client.NewHTTPClient(client.HTTPConfig{
		Addr:     "http://" + INFLUX_HOST + ":" + INFLUX_PORT,
		Username: INFLUX_USER,
		Password: INFLUX_PASSWORD,
	})
	LogError("GetDBClient(): client.NewHTTPClient", err)

	return c
}
