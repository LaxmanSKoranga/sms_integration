import frappe
from frappe import _
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from sms_integration.sms.phone import to_e164
from sms_integration.sms.signature import get_sms_settings, get_twilio_credentials

TWILIO_STATUS_MAP = {
	"queued": "Queued",
	"sending": "Sending",
	"sent": "Sent",
	"delivered": "Delivered",
	"undelivered": "Undelivered",
	"failed": "Failed",
	"received": "Received",
}


def map_twilio_status(twilio_status: str) -> str:
	return TWILIO_STATUS_MAP.get((twilio_status or "").lower(), "Queued")


def get_status_callback_url() -> str:
	return frappe.utils.get_url("/api/method/sms_integration.sms.webhook.status_callback")


def get_twilio_client() -> Client:
	account_sid, auth_token = get_twilio_credentials()
	return Client(account_sid, auth_token)


@frappe.whitelist()
def is_sms_enabled() -> bool:
	return bool(frappe.db.get_single_value("SMS Integration Settings", "enabled"))


@frappe.whitelist()
def send_sms(reference_doctype: str, reference_name: str, to: str | None = None, body: str | None = None) -> dict:
	reference_doc = frappe.get_doc(reference_doctype, reference_name)
	reference_doc.check_permission("read")

	if reference_doc.get("custom_sms_opt_out"):
		frappe.throw(_("This contact has opted out of SMS and cannot be messaged."))

	if not body or not body.strip():
		frappe.throw(_("Message body is required."))

	if not to:
		frappe.throw(_("This record has no phone number to send an SMS to."))

	settings = get_sms_settings()

	to_number = to_e164(to)
	if not to_number:
		frappe.throw(_("{0} is not a valid phone number").format(to))

	message_doc = frappe.get_doc(
		{
			"doctype": "SMS Message",
			"direction": "Outgoing",
			"status": "Queued",
			"from_number": settings.sender_phone_number or "",
			"to_number": to_number,
			"body": body,
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"sent_by": frappe.session.user,
		}
	).insert(ignore_permissions=True)

	client = get_twilio_client()
	send_kwargs = {"to": to_number, "body": body, "status_callback": get_status_callback_url()}
	if settings.messaging_service_sid:
		send_kwargs["messaging_service_sid"] = settings.messaging_service_sid
	else:
		send_kwargs["from_"] = settings.sender_phone_number

	try:
		message = client.messages.create(**send_kwargs)
	except TwilioRestException as e:
		message_doc.db_set({"status": "Failed", "error_message": str(e)})
		frappe.log_error(title="SMS send failed")
		frappe.throw(_("Failed to send SMS: {0}").format(e.msg))
	else:
		message_doc.db_set(
			{"message_sid": message.sid, "status": map_twilio_status(message.status)}
		)

	frappe.publish_realtime(
		"sms_message",
		{"reference_doctype": reference_doctype, "reference_name": reference_name, "name": message_doc.name},
		after_commit=True,
	)

	return {
		"name": message_doc.name,
		"status": message_doc.status,
		"message_sid": message_doc.message_sid,
	}


@frappe.whitelist()
def send_test_sms(to: str, body: str) -> dict:
	settings = get_sms_settings()

	to_number = to_e164(to)
	if not to_number:
		frappe.throw(_("{0} is not a valid phone number").format(to))

	client = get_twilio_client()
	send_kwargs = {"to": to_number, "body": body}
	if settings.messaging_service_sid:
		send_kwargs["messaging_service_sid"] = settings.messaging_service_sid
	else:
		send_kwargs["from_"] = settings.sender_phone_number

	try:
		message = client.messages.create(**send_kwargs)
	except TwilioRestException as e:
		frappe.throw(_("Failed to send SMS: {0}").format(e.msg))

	return {"message_sid": message.sid, "status": message.status}


@frappe.whitelist()
def get_sms_messages(reference_doctype: str, reference_name: str) -> list[dict]:
	reference_doc = frappe.get_doc(reference_doctype, reference_name)
	reference_doc.check_permission("read")

	return frappe.get_all(
		"SMS Message",
		filters={"reference_doctype": reference_doctype, "reference_name": reference_name},
		fields=[
			"name",
			"direction",
			"status",
			"from_number",
			"to_number",
			"body",
			"error_code",
			"error_message",
			"creation",
			"sent_by",
			"is_opt_out_event",
		],
		order_by="creation asc",
	)
