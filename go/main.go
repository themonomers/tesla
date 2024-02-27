package main

import (
	"fmt"
	"os"

	"github.com/themonomers/tesla/go/common"
	"github.com/themonomers/tesla/go/vehicle"
)

func main() {
	if len(os.Args) > 1 {
		switch os.Args[1] {
		case "-setchargingtime":
			vehicle.NotifyIsTeslaPluggedIn()
		case "-writem3telemetry":
			vehicle.WriteM3Telemetry()
		case "-writemxtelemetry":
			vehicle.WriteMXTelemetry()
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
	fmt.Println("-setchargingtime")
	fmt.Println("-writem3telemetry")
	fmt.Println("-writemxtelemetry")
	fmt.Println("-preconditionm3start")
	fmt.Println("-preconditionmxstart")
	fmt.Println("-preconditionm3stop")
	fmt.Println("-preconditionmxstop")
	fmt.Println("-removeteslacron")
	fmt.Println("-truncateemail")
	fmt.Println("-truncatelog")
}
