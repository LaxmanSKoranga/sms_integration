import frappe
from frappe import _
from frappe.model.document import Document


class SMSIntegrationSettings(Document):
	def validate(self):
		if not self.enabled:
			return

		if not self.sender_phone_number and not self.messaging_service_sid:
			frappe.throw(
				_("Set either Sender Phone Number or Messaging Service SID when SMS is enabled.")
			)
