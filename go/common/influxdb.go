package common

import (
	"github.com/influxdata/influxdb/client/v2"
)

var INFLUX_HOST string
var INFLUX_PORT string
var INFLUX_USER string
var INFLUX_PASSWORD string

func init() {
	c := GetConfig()
	INFLUX_HOST, _ = c.String("influxdb.host")
	INFLUX_PORT, _ = c.String("influxdb.port")
	INFLUX_USER, _ = c.String("influxdb.user")
	INFLUX_PASSWORD, _ = c.String("influxdb.password")
}

func GetDBClient() client.HTTPClient {
	c, _ := client.NewHTTPClient(client.HTTPConfig{
		Addr:     "http://" + INFLUX_HOST + ":" + INFLUX_PORT,
		Username: INFLUX_USER,
		Password: INFLUX_PASSWORD,
	})

	return c
}
