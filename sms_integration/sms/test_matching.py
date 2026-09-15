import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_to_date, now_datetime

from sms_integration.sms.matching import get_or_create_lead, match_sender

TEST_PHONE = "+15005550006"


class TestMatching(FrappeTestCase):
	def tearDown(self):
		for name in frappe.get_all("CRM Lead", filters={"mobile_no": TEST_PHONE}, pluck="name"):
			frappe.delete_doc("CRM Lead", name, force=True, ignore_permissions=True)
		frappe.db.rollback()

	def test_no_match_returns_none(self):
		docname, doctype = match_sender(TEST_PHONE)
		self.assertIsNone(docname)
		self.assertIsNone(doctype)

	def test_duplicate_number_most_recently_updated_wins(self):
		older = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Older Lead", "mobile_no": TEST_PHONE}
		).insert(ignore_permissions=True)
		newer = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Newer Lead", "mobile_no": TEST_PHONE}
		).insert(ignore_permissions=True)

		frappe.db.set_value(
			"CRM Lead", older.name, "modified", add_to_date(now_datetime(), hours=-1), update_modified=False
		)
		frappe.db.set_value(
			"CRM Lead", newer.name, "modified", now_datetime(), update_modified=False
		)

		docname, doctype = match_sender(TEST_PHONE)
		self.assertEqual(doctype, "CRM Lead")
		self.assertEqual(docname, newer.name)

	def test_get_or_create_lead_creates_once(self):
		name = get_or_create_lead(TEST_PHONE)
		self.assertTrue(frappe.db.exists("CRM Lead", name))

		name_again = get_or_create_lead(TEST_PHONE)
		self.assertEqual(name, name_again)
