package common

import (
	"net/smtp"
)

var SENDER_EMAIL string
var SENDER_PASSWORD string

func init() {
	var err error

	var c = GetConfig()
	SENDER_EMAIL, err = c.String("notification.sender_email")
	LogError("init(): load notification sender email", err)

	SENDER_PASSWORD, err = c.String("notification.sender_password")
	LogError("init(): load notification sender password", err)
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
	LogError("SendEmail(): smtp.SendMail", err)
}
