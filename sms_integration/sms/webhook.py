import frappe
from twilio.twiml.messaging_response import MessagingResponse
from werkzeug.wrappers import Response

from sms_integration.sms import matching, opt_out
from sms_integration.sms.api import map_twilio_status
from sms_integration.sms.phone import to_e164
from sms_integration.sms.signature import validate_twilio_signature


def _twiml_response(message: str | None = None) -> Response:
	resp = MessagingResponse()
	if message:
		resp.message(message)
	return Response(str(resp), mimetype="text/xml")


@frappe.whitelist(allow_guest=True)  # nosemgrep: guest-whitelisted-method
def inbound(**kwargs):
	settings = validate_twilio_signature()
	args = frappe._dict(kwargs)

	from_number = to_e164(args.From) or args.From
	to_number = to_e164(args.To) or args.To

	if opt_out.handle_keyword(from_number, args.Body):
		return _twiml_response(settings.default_opt_out_message)

	try:
		docname, doctype = matching.match_sender(from_number)
		auto_created = False
		if not docname and settings.auto_create_leads:
			docname = matching.get_or_create_lead(from_number)
			doctype = "CRM Lead"
			auto_created = True

		frappe.get_doc(
			{
				"doctype": "SMS Message",
				"direction": "Incoming",
				"status": "Received",
				"message_sid": args.MessageSid,
				"from_number": from_number,
				"to_number": to_number,
				"body": args.Body,
				"num_segments": args.get("NumSegments") or None,
				"reference_doctype": doctype,
				"reference_name": docname,
				"auto_created_lead": auto_created,
			}
		).insert(ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="SMS inbound webhook failed")
		frappe.db.commit()

	return _twiml_response()


@frappe.whitelist(allow_guest=True)  # nosemgrep: guest-whitelisted-method
def status_callback(**kwargs):
	validate_twilio_signature()
	args = frappe._dict(kwargs)

	name = frappe.db.get_value("SMS Message", {"message_sid": args.MessageSid}, "name")
	if not name:
		return Response("", status=200)

	try:
		frappe.db.set_value(
			"SMS Message",
			name,
			{
				"status": map_twilio_status(args.MessageStatus),
				"error_code": args.get("ErrorCode"),
				"error_message": args.get("ErrorMessage"),
			},
		)
		frappe.db.commit()

		doc = frappe.get_cached_doc("SMS Message", name)
		frappe.publish_realtime(
			"sms_message",
			{"reference_doctype": doc.reference_doctype, "reference_name": doc.reference_name, "name": name},
			after_commit=True,
		)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="SMS status callback failed")
		frappe.db.commit()

	return Response("", status=200)
