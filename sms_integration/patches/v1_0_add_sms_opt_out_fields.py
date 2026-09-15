from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"CRM Lead": [
				{
					"fieldname": "custom_sms_opt_out",
					"fieldtype": "Check",
					"label": "SMS Opt-Out",
					"insert_after": "mobile_no",
					"default": "0",
				},
				{
					"fieldname": "custom_sms_opt_out_date",
					"fieldtype": "Datetime",
					"label": "SMS Opt-Out Date",
					"insert_after": "custom_sms_opt_out",
					"read_only": 1,
					"depends_on": "eval:doc.custom_sms_opt_out",
				},
			],
			"CRM Deal": [
				{
					"fieldname": "custom_sms_opt_out",
					"fieldtype": "Check",
					"label": "SMS Opt-Out",
					"insert_after": "mobile_no",
					"default": "0",
				},
				{
					"fieldname": "custom_sms_opt_out_date",
					"fieldtype": "Datetime",
					"label": "SMS Opt-Out Date",
					"insert_after": "custom_sms_opt_out",
					"read_only": 1,
					"depends_on": "eval:doc.custom_sms_opt_out",
				},
			],
			"Contact": [
				{
					"fieldname": "custom_sms_opt_out",
					"fieldtype": "Check",
					"label": "SMS Opt-Out",
					"insert_after": "phone_nos",
					"default": "0",
				},
				{
					"fieldname": "custom_sms_opt_out_date",
					"fieldtype": "Datetime",
					"label": "SMS Opt-Out Date",
					"insert_after": "custom_sms_opt_out",
					"read_only": 1,
					"depends_on": "eval:doc.custom_sms_opt_out",
				},
			],
		},
		update=True,
	)
