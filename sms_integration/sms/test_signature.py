import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils.password import set_encrypted_password
from twilio.request_validator import RequestValidator

from sms_integration.sms.signature import validate_twilio_signature

AUTH_TOKEN = "12345"
URL = "https://mycompany.com/myapp.php?foo=1&bar=2"
PARAMS = {
	"CallSid": "CA1234567890ABCDE",
	"Caller": "+14158675310",
	"Digits": "1234",
	"From": "+14158675310",
	"To": "+18005551212",
}
VALID_SIGNATURE = RequestValidator(AUTH_TOKEN).compute_signature(URL, PARAMS)


class _FakeForm:
	def __init__(self, data):
		self._data = data

	def to_dict(self):
		return dict(self._data)


class _FakeRequest:
	def __init__(self, params, signature, path="/myapp.php"):
		self.form = _FakeForm(params)
		self.headers = {"X-Twilio-Signature": signature}
		self.path = path


class TestSignature(FrappeTestCase):
	def setUp(self):
		frappe.db.set_single_value("CRM Twilio Settings", "account_sid", "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
		set_encrypted_password("CRM Twilio Settings", "CRM Twilio Settings", AUTH_TOKEN, "auth_token")
		frappe.clear_cache(doctype="CRM Twilio Settings")

		sms_settings = frappe.get_single("SMS Integration Settings")
		sms_settings.enabled = 1
		sms_settings.sender_phone_number = "+15005550006"
		sms_settings.webhook_url_override = URL
		sms_settings.save(ignore_permissions=True)

	def tearDown(self):
		frappe.clear_cache(doctype="CRM Twilio Settings")
		frappe.clear_cache(doctype="SMS Integration Settings")

	def test_valid_signature_passes(self):
		request = _FakeRequest(PARAMS, VALID_SIGNATURE)
		validate_twilio_signature(request)

	def test_tampered_param_is_rejected(self):
		tampered = dict(PARAMS)
		tampered["Digits"] = "9999"
		request = _FakeRequest(tampered, VALID_SIGNATURE)
		with self.assertRaises(frappe.PermissionError):
			validate_twilio_signature(request)

	def test_missing_signature_is_rejected(self):
		request = _FakeRequest(PARAMS, "")
		with self.assertRaises(frappe.PermissionError):
			validate_twilio_signature(request)
