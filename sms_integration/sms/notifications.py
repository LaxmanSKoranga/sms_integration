import frappe
from frappe import _
from frappe.desk.doctype.notification_log.notification_log import enqueue_create_notification

from crm.api.doc import get_assigned_users

from sms_integration.sms.matching import match_sender


def validate(doc, method=None):
	if doc.reference_doctype and doc.reference_name:
		return

	phone = doc.from_number if doc.direction == "Incoming" else doc.to_number
	try:
		docname, doctype = match_sender(phone)
	except Exception:
		frappe.log_error(title="SMS Message: contact resolution failed")
		return

	if docname:
		doc.reference_doctype = doctype
		doc.reference_name = docname


def on_update(doc, method=None):
	frappe.publish_realtime(
		"sms_message",
		{
			"reference_doctype": doc.reference_doctype,
			"reference_name": doc.reference_name,
			"name": doc.name,
		},
		after_commit=True,
	)

	if doc.direction == "Incoming":
		notify_assigned_users(doc)


def notify_assigned_users(doc):
	if not (doc.reference_doctype and doc.reference_name):
		return

	users = get_assigned_users(doc.reference_doctype, doc.reference_name)
	if not users:
		return

	enqueue_create_notification(
		users,
		{
			"type": "Alert",
			"document_type": doc.reference_doctype,
			"document_name": doc.reference_name,
			"subject": _("New SMS from {0}").format(doc.from_number),
			"email_content": frappe.utils.escape_html(doc.body or ""),
			"from_user": doc.owner,
		},
	)
