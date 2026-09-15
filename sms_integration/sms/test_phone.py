from frappe.tests.utils import FrappeTestCase

from sms_integration.sms.phone import to_e164


class TestPhone(FrappeTestCase):
	def test_already_e164(self):
		self.assertEqual(to_e164("+16502530000"), "+16502530000")

	def test_national_number_with_region(self):
		self.assertEqual(to_e164("(650) 253-0000", default_region="US"), "+16502530000")

	def test_invalid_number_returns_none(self):
		self.assertIsNone(to_e164("not a number"))

	def test_empty_returns_none(self):
		self.assertIsNone(to_e164(""))
		self.assertIsNone(to_e164(None))
