app_name = "sms_integration"
app_title = "SMS Integration"
app_publisher = "lucky"
app_description = "Two-way Twilio SMS integration for Frappe CRM"
app_email = "lucky@example.com"
app_license = "mit"

required_apps = ["crm"]

doc_events = {
	"SMS Message": {
		"validate": "sms_integration.sms.notifications.validate",
		"on_update": "sms_integration.sms.notifications.on_update",
	},
}
