import frappe

STOP_KEYWORDS = {"STOP", "STOPALL", "UNSUBSCRIBE", "CANCEL", "END", "QUIT"}
START_KEYWORDS = {"START", "YES", "UNSTOP"}


def handle_keyword(from_e164: str, body: str) -> bool:
	keyword = (body or "").strip().upper()

	if keyword in STOP_KEYWORDS:
		_set_opt_out(from_e164, opted_out=True)
		return True

	if keyword in START_KEYWORDS:
		_set_opt_out(from_e164, opted_out=False)
		return True

	return False


def _set_opt_out(phone_e164: str, opted_out: bool):
	value = 1 if opted_out else 0
	opt_out_date = frappe.utils.now() if opted_out else None

	for doctype in ("CRM Lead", "CRM Deal"):
		for field in ("mobile_no", "phone"):
			for name in frappe.get_all(doctype, filters={field: phone_e164}, pluck="name"):
				frappe.db.set_value(
					doctype, name, {"custom_sms_opt_out": value, "custom_sms_opt_out_date": opt_out_date}
				)

	contact_names = set(frappe.get_all("Contact", filters={"mobile_no": phone_e164}, pluck="name"))
	contact_names.update(
		frappe.get_all("Contact Phone", filters={"phone": phone_e164}, pluck="parent")
	)
	for name in contact_names:
		frappe.db.set_value(
			"Contact", name, {"custom_sms_opt_out": value, "custom_sms_opt_out_date": opt_out_date}
		)

	frappe.db.commit()
