// Copyright (c) 2026, enfono and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bed", {
	refresh(frm) {
		if (!frm.is_new()) {
			// Add Assign Bed button if bed is available
			if (frm.doc.assignment_status === "Available" || !frm.doc.assignment_status) {
				frm.add_custom_button(__("Assign Bed"), function() {
					assign_bed_to_vehicle(frm);
				}, __("Actions"));
			}
			
			// Add Remove Bed button if bed is assigned
			if (frm.doc.assignment_status === "Assigned" && frm.doc.current_vehicle) {
				frm.add_custom_button(__("Remove Bed"), function() {
					remove_bed_from_vehicle(frm);
				}, __("Actions"));
			}
		}
	}
});

function assign_bed_to_vehicle(frm) {
	// Show dialog to get vehicle and odometer reading
	let d = new frappe.ui.Dialog({
		title: __("Assign Bed to Vehicle"),
		fields: [
			{
				label: __("Vehicle"),
				fieldname: "vehicle",
				fieldtype: "Link",
				options: "Vehicle",
				reqd: 1,
				get_query: function() {
					return {
						filters: {
							docstatus: ["!=", 2]
						}
					};
				}
			},
			{
				label: __("Assign Date"),
				fieldname: "assign_date",
				fieldtype: "Date",
				reqd: 1,
				default: frappe.datetime.get_today()
			},
			{
				label: __("Odometer Reading (KM)"),
				fieldname: "assign_odometer",
				fieldtype: "Float",
				reqd: 1,
				description: __("Current odometer reading of the vehicle")
			}
		],
		primary_action_label: __("Assign"),
		primary_action(values) {
			if (!values.vehicle) {
				frappe.msgprint(__("Please select a vehicle"));
				return;
			}
			if (!values.assign_odometer && values.assign_odometer !== 0) {
				frappe.msgprint(__("Odometer reading is mandatory"));
				return;
			}
			
			frappe.call({
				method: "fateh_maintenance.logistics_maintaenance.doctype.bed.bed.assign_bed_to_vehicle",
				args: {
					bed: frm.doc.name,
					vehicle: values.vehicle,
					assign_date: values.assign_date,
					assign_odometer: values.assign_odometer
				},
				callback: function(r) {
					if (!r.exc) {
						frappe.show_alert({
							message: __("Bed assigned successfully"),
							indicator: "green"
						});
						d.hide();
						frm.reload_doc();
					}
				}
			});
		}
	});
	d.show();
}

function remove_bed_from_vehicle(frm) {
	if (!frm.doc.current_vehicle) {
		frappe.msgprint(__("Bed is not currently assigned to any vehicle"));
		return;
	}
	
	// Show dialog to get remove date and odometer reading
	let d = new frappe.ui.Dialog({
		title: __("Remove Bed from Vehicle"),
		fields: [
			{
				label: __("Current Vehicle"),
				fieldname: "vehicle",
				fieldtype: "Data",
				default: frm.doc.current_vehicle,
				read_only: 1
			},
			{
				label: __("Remove Date"),
				fieldname: "remove_date",
				fieldtype: "Date",
				reqd: 1,
				default: frappe.datetime.get_today()
			},
			{
				label: __("Odometer Reading (KM)"),
				fieldname: "remove_odometer",
				fieldtype: "Float",
				reqd: 1,
				description: __("Current odometer reading of the vehicle")
			}
		],
		primary_action_label: __("Remove"),
		primary_action(values) {
			if (!values.remove_odometer && values.remove_odometer !== 0) {
				frappe.msgprint(__("Odometer reading is mandatory"));
				return;
			}
			
			frappe.call({
				method: "fateh_maintenance.logistics_maintaenance.doctype.bed.bed.remove_bed_from_vehicle",
				args: {
					bed: frm.doc.name,
					remove_date: values.remove_date,
					remove_odometer: values.remove_odometer
				},
				callback: function(r) {
					if (!r.exc) {
						frappe.show_alert({
							message: __("Bed removed successfully"),
							indicator: "green"
						});
						d.hide();
						frm.reload_doc();
					}
				}
			});
		}
	});
	d.show();
}
