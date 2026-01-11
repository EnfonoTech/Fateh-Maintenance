// Copyright (c) 2025, fateh_maintenance and contributors
// For license information, please see license.txt

frappe.ui.form.on("Driver", {
	refresh: function(frm) {
		// Add button to load equipment template
		if (frm.doc.name && !frm.is_new()) {
			frm.add_custom_button(__("Load Equipment Template"), function() {
				let d = new frappe.ui.Dialog({
					title: __("Load Equipment Template"),
					fields: [
						{
							fieldtype: "HTML",
							options: __("This will replace all existing equipment items with the default template. Do you want to continue?")
						}
					],
					primary_action_label: __("Load Template"),
					primary_action: function() {
						d.hide();
						frappe.call({
							method: "fateh_maintenance.logistics_maintaenance.doctype.driver_equipment.driver_equipment.populate_default_equipment",
							args: {
								driver_name: frm.doc.name
							},
							freeze: true,
							freeze_message: __("Loading equipment template..."),
							callback: function(r) {
								if (!r.exc && r.message) {
									if (r.message.success) {
										frappe.show_alert({
											message: __("Equipment template loaded successfully"),
											indicator: "green"
										}, 5);
										frm.reload_doc();
									} else {
										frappe.msgprint({
											title: __("Error"),
											indicator: "red",
											message: r.message.message || __("Failed to load equipment template")
										});
									}
								} else {
									frappe.msgprint({
										title: __("Error"),
										indicator: "red",
										message: __("Failed to load equipment template. Please check the error logs.")
									});
								}
							}
						});
					}
				});
				d.show();
			}, __("Actions"));
		}
	}
});
