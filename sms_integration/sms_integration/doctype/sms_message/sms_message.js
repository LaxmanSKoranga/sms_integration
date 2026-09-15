const CRM_ROUTE_SEGMENT = {
	"CRM Lead": "leads",
	"CRM Deal": "deals",
};

frappe.ui.form.on("SMS Message", {
	refresh(frm) {
		const segment = CRM_ROUTE_SEGMENT[frm.doc.reference_doctype];
		if (segment && frm.doc.reference_name) {
			frm.add_custom_button(__("Open in CRM"), () => {
				window.open(`/crm/${segment}/${encodeURIComponent(frm.doc.reference_name)}`, "_blank");
			});
		}
	},
});
