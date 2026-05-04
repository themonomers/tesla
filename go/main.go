package main

import (
	"fmt"
	"os"

	"github.com/themonomers/tesla/go/common"
	"github.com/themonomers/tesla/go/energy"
	"github.com/themonomers/tesla/go/vehicle"
)

func main() {
	if len(os.Args) > 1 {
		switch os.Args[1] {
		// vehicle
		case "-notify":
			vehicle.NotifyIsTeslaPluggedIn()
		case "-earliest":
			vehicle.ChargeEarliest()
		case "-writevehicletelemetry":
			vehicle.WriteVehicleTelemetry()
		case "-startm3precondition":
			vehicle.StartM3Precondition()
		case "-startmxprecondition":
			vehicle.StartMXPrecondition()
		case "-stopm3precondition":
			vehicle.StopM3Precondition()
		case "-stopmxprecondition":
			vehicle.StopMXPrecondition()
		case "-checkm3charge":
			vehicle.CheckM3Charge()
		case "-checkmxcharge":
			vehicle.CheckMXCharge()
		case "-removeteslacron":
			vehicle.RemoveTeslaCron()
		// energy
		case "-writelivesitetelemetry":
			energy.WriteLiveSiteTelemetry()
		case "-writeenergytelemetry":
			energy.WriteEnergyTelemetry()
		case "-setenergymodebasedonweather":
			energy.SetEnergyModeBasedOnWeather()
		case "-importenergydetailtodb":
			energy.ImportEnergyDetailToDB()
		case "-importenergysummarytodb":
			energy.ImportEnergySummaryToDB()
		case "-importenergytousummarytodb":
			energy.ImportEnergyTOUSummaryToDB()
		case "-importenergydatatogsheet":
			energy.ImportEnergyDataToGsheet()
		case "-importbatterychargetodb":
			energy.ImportBatteryChargeToDB()
		case "-importoutagetodb":
			energy.ImportOutageToDB()
		// maintenance
		case "-truncateemail":
			common.TruncateEmail()
		case "-truncatelog":
			common.TruncateLog()
		default:
			printUsage()
		}
	} else {
		printUsage()
	}
}

func printUsage() {
	fmt.Println("Usage:  ")
	fmt.Println("\n## Vehicle ##") // vehicle
	fmt.Println("-notify")
	fmt.Println("-earliest")
	fmt.Println("-writevehicletelemetry")
	fmt.Println("-startm3precondition")
	fmt.Println("-startmxprecondition")
	fmt.Println("-stopm3precondition")
	fmt.Println("-stopmxprecondition")
	fmt.Println("-checkm3charge")
	fmt.Println("-checkmxcharge")
	fmt.Println("-removeteslacron")
	fmt.Println("\n## Energy ##") // energy
	fmt.Println("-writelivesitetelemetry")
	fmt.Println("-writeenergytelemetry")
	fmt.Println("-setenergymodebasedonweather")
	fmt.Println("-importenergydetailtodb")
	fmt.Println("-importenergysummarytodb")
	fmt.Println("-importenergytousummarytodb")
	fmt.Println("-importenergydatatogsheet")
	fmt.Println("-importbatterychargetodb")
	fmt.Println("-importoutagetodb")
	fmt.Println("\n## Maintenance ##") // maintenance
	fmt.Println("-truncateemail")
	fmt.Println("-truncatelog")
}
