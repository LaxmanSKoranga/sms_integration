import frappe

from crm.integrations.api import get_contact_lead_or_deal_from_number


def match_sender(phone_e164: str) -> tuple[str | None, str | None]:
	if not phone_e164:
		return None, None

	try:
		docname, doctype = get_contact_lead_or_deal_from_number(phone_e164)
	except Exception:
		frappe.log_error(title="SMS: contact matching failed")
		docname, doctype = None, None

	if docname:
		return docname, doctype

	return _match_lead_or_deal_by_recency(phone_e164)


def _match_lead_or_deal_by_recency(phone_e164: str) -> tuple[str | None, str | None]:
	best_by_key: dict[tuple[str, str], dict] = {}

	for doctype in ("CRM Lead", "CRM Deal"):
		for field in ("mobile_no", "phone"):
			rows = frappe.get_all(
				doctype,
				filters={field: phone_e164},
				fields=["name", "modified"],
			)
			for row in rows:
				key = (doctype, row["name"])
				if key not in best_by_key or row["modified"] > best_by_key[key]["modified"]:
					best_by_key[key] = {"name": row["name"], "modified": row["modified"], "doctype": doctype}

	if not best_by_key:
		return None, None

	winner = max(best_by_key.values(), key=lambda row: row["modified"])
	return winner["name"], winner["doctype"]


def get_or_create_lead(phone_e164: str) -> str:
	docname, doctype = match_sender(phone_e164)
	if docname and doctype == "CRM Lead":
		return docname

	lead = frappe.get_doc(
		{
			"doctype": "CRM Lead",
			"first_name": phone_e164,
			"lead_name": phone_e164,
			"mobile_no": phone_e164,
		}
	)
	lead.insert(ignore_permissions=True)
	return lead.name
