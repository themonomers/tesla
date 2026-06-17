package common

import (
	"log/slog"
	"net/smtp"
	"time"
)

// Send email via Google SMTP.
func SendEmail(to, subject, message, cc string) {
	tos := []string{to}
	msg := []byte("To: " + to + "\r\n" +
		"Cc: " + cc + "\r\n" +
		"Subject: " + subject + "\r\n" +
		"\r\n" +
		message)

	auth := smtp.PlainAuth("", EncryptedCfg.Notification.SenderEmail, EncryptedCfg.Notification.SenderPassword, "smtp.gmail.com")
	err := smtp.SendMail("smtp.gmail.com:587", auth, EncryptedCfg.Notification.SenderEmail, tos, msg)
	if err != nil {
		slog.Warn("Retry SendEmail(): smtp.SendMail(): " + err.Error())
		time.Sleep(WAIT_TIME * time.Second)
		SendEmail(to, subject, message, cc)
	}
}
