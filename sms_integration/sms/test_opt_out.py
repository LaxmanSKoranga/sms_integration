import frappe
from frappe.tests.utils import FrappeTestCase

from sms_integration.sms.api import send_sms
from sms_integration.sms.opt_out import handle_keyword

TEST_PHONE = "+15005550006"


class TestOptOut(FrappeTestCase):
	def setUp(self):
		self.lead = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Opt Out Test", "mobile_no": TEST_PHONE}
		).insert(ignore_permissions=True)
		frappe.db.commit()

	def tearDown(self):
		frappe.delete_doc("CRM Lead", self.lead.name, force=True, ignore_permissions=True)
		frappe.db.commit()

	def test_non_keyword_is_ignored(self):
		self.assertFalse(handle_keyword(TEST_PHONE, "Hello there"))
		self.lead.reload()
		self.assertFalse(self.lead.custom_sms_opt_out)

	def test_stop_sets_opt_out(self):
		self.assertTrue(handle_keyword(TEST_PHONE, "stop"))
		self.lead.reload()
		self.assertEqual(self.lead.custom_sms_opt_out, 1)
		self.assertTrue(self.lead.custom_sms_opt_out_date)

	def test_start_clears_opt_out(self):
		handle_keyword(TEST_PHONE, "STOP")
		self.lead.reload()
		self.assertEqual(self.lead.custom_sms_opt_out, 1)

		handle_keyword(TEST_PHONE, "START")
		self.lead.reload()
		self.assertEqual(self.lead.custom_sms_opt_out, 0)

	def test_send_sms_blocked_when_opted_out(self):
		handle_keyword(TEST_PHONE, "STOP")

		with self.assertRaises(frappe.ValidationError):
			send_sms(
				reference_doctype="CRM Lead",
				reference_name=self.lead.name,
				to=TEST_PHONE,
				body="Should not send",
			)
