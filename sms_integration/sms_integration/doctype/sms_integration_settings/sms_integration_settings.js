frappe.ui.form.on("SMS Integration Settings", {
	refresh(frm) {
		if (frm.doc.enabled && !frm.is_dirty()) {
			frm.add_custom_button(__("Send Test SMS"), () => show_test_sms_dialog(frm));
		}
	},
});

function show_test_sms_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Send Test SMS"),
		fields: [
			{
				fieldname: "to",
				fieldtype: "Data",
				label: __("To (E.164, e.g. +15551234567)"),
				reqd: 1,
			},
			{
				fieldname: "body",
				fieldtype: "Small Text",
				label: __("Message"),
				default: __("This is a test message from Frappe CRM."),
				reqd: 1,
			},
		],
		primary_action_label: __("Send"),
		primary_action(values) {
			frappe.call({
				method: "sms_integration.sms.api.send_test_sms",
				args: { to: values.to, body: values.body },
				freeze: true,
				callback(r) {
					if (r.message) {
						frappe.msgprint({
							title: __("Sent"),
							message: __("Message SID: {0}", [r.message.message_sid]),
							indicator: "green",
						});
						dialog.hide();
					}
				},
			});
		},
	});
	dialog.show();
}
