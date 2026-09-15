from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from sms_integration.sms import webhook

TEST_PHONE = "+15005550006"


class TestWebhook(FrappeTestCase):
	def setUp(self):
		self.lead = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Webhook Test", "mobile_no": TEST_PHONE}
		).insert(ignore_permissions=True)
		frappe.db.commit()

	def tearDown(self):
		frappe.db.delete("SMS Message", {"reference_name": self.lead.name})
		frappe.delete_doc("CRM Lead", self.lead.name, force=True, ignore_permissions=True)
		frappe.db.commit()

	@patch("sms_integration.sms.webhook.validate_twilio_signature")
	def test_inbound_creates_message_and_links_lead(self, mock_validate):
		mock_validate.return_value = frappe._dict(
			{"auto_create_leads": 0, "default_opt_out_message": None}
		)

		webhook.inbound(
			From=TEST_PHONE,
			To="+15005550001",
			Body="Hello from a lead",
			MessageSid="SMtestinbound1",
		)

		message = frappe.get_doc("SMS Message", {"message_sid": "SMtestinbound1"})
		self.assertEqual(message.direction, "Incoming")
		self.assertEqual(message.status, "Received")
		self.assertEqual(message.reference_doctype, "CRM Lead")
		self.assertEqual(message.reference_name, self.lead.name)

	@patch("sms_integration.sms.webhook.validate_twilio_signature")
	def test_inbound_stop_keyword_does_not_create_message(self, mock_validate):
		mock_validate.return_value = frappe._dict(
			{"auto_create_leads": 0, "default_opt_out_message": "You have been unsubscribed."}
		)

		webhook.inbound(From=TEST_PHONE, To="+15005550001", Body="STOP", MessageSid="SMtestoptout1")

		self.assertFalse(frappe.db.exists("SMS Message", {"message_sid": "SMtestoptout1"}))
		self.lead.reload()
		self.assertEqual(self.lead.custom_sms_opt_out, 1)
