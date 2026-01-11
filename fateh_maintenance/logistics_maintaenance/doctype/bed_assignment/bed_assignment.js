frappe.ui.form.on('Bed Assignment', {
	refresh: function(frm) {
		if (frm.doc.vehicle && frm.doc.bed) {
			frm.add_custom_button(__('View Vehicle'), function() {
				frappe.set_route('Form', 'Vehicle', frm.doc.vehicle);
			});
			
			frm.add_custom_button(__('View Bed'), function() {
				frappe.set_route('Form', 'Bed', frm.doc.bed);
			});
		}
		
		// Show/hide remove fields based on status
		if (frm.doc.status === 'Removed') {
			frm.set_df_property('remove_date', 'reqd', 1);
			frm.set_df_property('remove_odometer', 'reqd', 1);
		} else {
			frm.set_df_property('remove_date', 'reqd', 0);
			frm.set_df_property('remove_odometer', 'reqd', 0);
		}
	},
	
	vehicle: function(frm) {
		if (frm.doc.vehicle) {
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Vehicle',
					name: frm.doc.vehicle
				},
				callback: function(r) {
					if (r.message && r.message.last_odometer) {
						if (!frm.doc.assign_odometer) {
							frm.set_value('assign_odometer', r.message.last_odometer);
						}
					}
				}
			});
		}
	},
	
	status: function(frm) {
		if (frm.doc.status === 'Removed') {
			if (!frm.doc.remove_date) {
				frm.set_value('remove_date', frappe.datetime.get_today());
			}
			frm.set_df_property('remove_date', 'reqd', 1);
			frm.set_df_property('remove_odometer', 'reqd', 1);
		} else {
			frm.set_df_property('remove_date', 'reqd', 0);
			frm.set_df_property('remove_odometer', 'reqd', 0);
		}
	},
	
	remove_odometer: function(frm) {
		if (frm.doc.remove_odometer && frm.doc.assign_odometer) {
			if (frm.doc.remove_odometer < frm.doc.assign_odometer) {
				frappe.msgprint(__('Remove Odometer cannot be less than Assign Odometer'));
				frm.set_value('remove_odometer', '');
			} else {
				// Calculate KMs run
				let kms_run = flt(frm.doc.remove_odometer) - flt(frm.doc.assign_odometer);
				frm.set_value('total_kms_run', kms_run);
			}
		}
	},
	
	assign_odometer: function(frm) {
		if (frm.doc.remove_odometer && frm.doc.assign_odometer) {
			if (frm.doc.remove_odometer < frm.doc.assign_odometer) {
				frappe.msgprint(__('Remove Odometer cannot be less than Assign Odometer'));
			} else {
				// Calculate KMs run
				let kms_run = flt(frm.doc.remove_odometer) - flt(frm.doc.assign_odometer);
				frm.set_value('total_kms_run', kms_run);
			}
		}
	}
});
