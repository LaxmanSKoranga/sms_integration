from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils.password import set_encrypted_password

from sms_integration.sms.api import send_sms

TEST_PHONE = "+15005550006"


class TestSMSMessage(FrappeTestCase):
	def setUp(self):
		self.lead = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "SMS Send Test", "mobile_no": TEST_PHONE}
		).insert(ignore_permissions=True)

		frappe.db.set_single_value("CRM Twilio Settings", "account_sid", "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
		set_encrypted_password("CRM Twilio Settings", "CRM Twilio Settings", "test-auth-token", "auth_token")
		frappe.clear_cache(doctype="CRM Twilio Settings")

		self.sms_settings = frappe.get_single("SMS Integration Settings")
		self.sms_settings.enabled = 1
		self.sms_settings.sender_phone_number = "+15005550001"
		self.sms_settings.messaging_service_sid = ""
		self.sms_settings.save(ignore_permissions=True)

	def tearDown(self):
		frappe.db.delete("SMS Message", {"reference_name": self.lead.name})
		frappe.delete_doc("CRM Lead", self.lead.name, force=True, ignore_permissions=True)
		frappe.clear_cache(doctype="CRM Twilio Settings")
		frappe.clear_cache(doctype="SMS Integration Settings")

	@patch("sms_integration.sms.api.get_twilio_client")
	def test_send_sms_logs_message(self, mock_get_client):
		fake_message = MagicMock(sid="SMtestoutbound1", status="queued")
		mock_client = MagicMock()
		mock_client.messages.create.return_value = fake_message
		mock_get_client.return_value = mock_client

		result = send_sms(
			reference_doctype="CRM Lead",
			reference_name=self.lead.name,
			to=TEST_PHONE,
			body="Hello!",
		)

		self.assertEqual(result["message_sid"], "SMtestoutbound1")
		self.assertEqual(result["status"], "Queued")

		message = frappe.get_doc("SMS Message", result["name"])
		self.assertEqual(message.direction, "Outgoing")
		self.assertEqual(message.reference_doctype, "CRM Lead")
		self.assertEqual(message.reference_name, self.lead.name)
		self.assertEqual(message.sent_by, frappe.session.user)
