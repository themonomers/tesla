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
		case "-setchargingtime":
			vehicle.NotifyIsTeslaPluggedIn()
		case "-writevehicletelemetry":
			vehicle.WriteVehicleTelemetry()
		case "-preconditionm3start":
			vehicle.PreconditionM3Start()
		case "-preconditionmxstart":
			vehicle.PreconditionMXStart()
		case "-preconditionm3stop":
			vehicle.PreconditionM3Stop()
		case "-preconditionmxstop":
			vehicle.PreconditionMXStop()
		case "-removeteslacron":
			vehicle.RemoveTeslaCron()
		// energy
		case "-writelivesitetelemetry":
			energy.WriteLiveSiteTelemetry()
		case "-writeenergytelemetry":
			energy.WriteEnergyTelemetry()
		case "-setenergymodebasedonweather":
			energy.SetEnergyModeBasedOnWeather()
		case "-importbatterychargetodb":
			energy.ImportBatteryChargeToDB()
		case "-importoutagetodb":
			energy.ImportOutageToDB()
		case "-importenergydetailtodb":
			energy.ImportEnergyDetailToDB()
		case "-importenergysummarytodb":
			energy.ImportEnergySummaryToDB()
		case "-importenergytousummarytogsheet":
			energy.ImportEnergyTOUSummaryToGsheet()
		case "-importenergytousummarytodb":
			energy.ImportEnergyTOUSummaryToDB()
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
	fmt.Println("-setchargingtime")
	fmt.Println("-writevehicletelemetry")
	fmt.Println("-preconditionm3start")
	fmt.Println("-preconditionmxstart")
	fmt.Println("-preconditionm3stop")
	fmt.Println("-preconditionmxstop")
	fmt.Println("-removeteslacron")
	fmt.Println("\n## Energy ##") // energy
	fmt.Println("-writelivesitetelemetry")
	fmt.Println("-writeenergytelemetry")
	fmt.Println("-setenergymodebasedonweather")
	fmt.Println("-importbatterychargetodb")
	fmt.Println("-importoutagetodb")
	fmt.Println("-importenergydetailtodb")
	fmt.Println("-importenergysummarytodb")
	fmt.Println("-importenergytousummarytogsheet")
	fmt.Println("-importenergytousummarytodb")
	fmt.Println("\n## Maintenance ##") // maintenance
	fmt.Println("-truncateemail")
	fmt.Println("-truncatelog")
}
