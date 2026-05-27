package common

import (
	"log/slog"
	"net/smtp"
	"time"
)

var SENDER_EMAIL string
var SENDER_PASSWORD string

func init() {
	c := GetConfig()
	SENDER_EMAIL, _ = c.String("notification.sender_email")
	SENDER_PASSWORD, _ = c.String("notification.sender_password")
}

// Send email via Google SMTP.
func SendEmail(to, subject, message, cc string) {
	tos := []string{to}
	msg := []byte("To: " + to + "\r\n" +
		"Cc: " + cc + "\r\n" +
		"Subject: " + subject + "\r\n" +
		"\r\n" +
		message)

	auth := smtp.PlainAuth("", SENDER_EMAIL, SENDER_PASSWORD, "smtp.gmail.com")
	err := smtp.SendMail("smtp.gmail.com:587", auth, SENDER_EMAIL, tos, msg)
	if err != nil {
		slog.Warn("Retry SendEmail(): smtp.SendMail(): " + err.Error())
		time.Sleep(WAIT_TIME * time.Second)
		SendEmail(to, subject, message, cc)
	}
}
