import frappe
from frappe import _
from twilio.request_validator import RequestValidator


def get_twilio_credentials() -> tuple[str, str]:
	twilio_settings = frappe.get_cached_doc("CRM Twilio Settings")
	account_sid = twilio_settings.account_sid
	auth_token = twilio_settings.get_password("auth_token", raise_exception=False)

	if not account_sid or not auth_token:
		frappe.throw(
			_("Twilio Account SID and Auth Token must be configured in CRM Twilio Settings before SMS can be used.")
		)

	return account_sid, auth_token


def get_sms_settings():
	settings = frappe.get_cached_doc("SMS Integration Settings")
	if not settings.enabled:
		frappe.throw(_("SMS is not enabled"), frappe.PermissionError)
	return settings


def validate_twilio_signature(request=None):
	request = request or frappe.request
	settings = get_sms_settings()
	_account_sid, auth_token = get_twilio_credentials()

	validator = RequestValidator(auth_token)

	url = settings.webhook_url_override or frappe.utils.get_url(request.path)
	params = request.form.to_dict()
	signature = request.headers.get("X-Twilio-Signature", "")

	if not signature or not validator.validate(url, params, signature):
		frappe.throw(_("Invalid Twilio signature"), frappe.PermissionError)

	return settings
