frappe.ui.form.on('Maintenance', {
	refresh: function(frm) {
		// Add custom buttons
		if (frm.doc.linked_to && !frm.is_new()) {
			if (frm.doc.linked_to_type === 'Vehicle') {
				frm.add_custom_button(__('View Vehicle'), function() {
					frappe.set_route('Form', 'Vehicle', frm.doc.linked_to);
				});
			} else if (frm.doc.linked_to_type === 'Bed') {
				frm.add_custom_button(__('View Bed'), function() {
					frappe.set_route('Form', 'Bed', frm.doc.linked_to);
				});
			}
			
			if (frm.doc.stock_entry) {
				frm.add_custom_button(__('View Stock Entry'), function() {
					frappe.set_route('Form', 'Stock Entry', frm.doc.stock_entry);
				});
			}
		}
		
		// Set query for warehouse in materials table
		frm.set_query('warehouse', 'materials', function(doc, cdt, cdn) {
			let filters = {
				'is_group': 0
			};
			if (frm.doc.company) {
				filters['company'] = frm.doc.company;
			}
			return { filters: filters };
		});
		
		// Set query for default_warehouse
		frm.set_query('default_warehouse', function() {
			let filters = {
				'is_group': 0
			};
			if (frm.doc.company) {
				filters['company'] = frm.doc.company;
			}
			return { filters: filters };
		});
		
		// Set query for expense_account - only show Profit and Loss accounts
		frm.set_query('expense_account', function() {
			let filters = {
				'report_type': 'Profit and Loss',
				'is_group': 0
			};
			if (frm.doc.company) {
				filters['company'] = frm.doc.company;
			}
			return { filters: filters };
		});
		
		// Set query for cost_center - only show non-group cost centers for company
		frm.set_query('cost_center', function() {
			let filters = {
				'is_group': 0
			};
			if (frm.doc.company) {
				filters['company'] = frm.doc.company;
			}
			return { filters: filters };
		});
		
		// Auto-set company if not set
		if (frm.is_new() && !frm.doc.company) {
			frm.set_value('company', frappe.defaults.get_default('company'));
		}
		
		// Auto-fill vehicle/bed info
		if (frm.doc.linked_to && frm.is_new() && frm.doc.linked_to_type) {
			frappe.call({
				method: 'fateh_maintenance.logistics_maintaenance.doctype.maintenance.maintenance.get_vehicle_info',
				args: {
					linked_to_type: frm.doc.linked_to_type,
					linked_to: frm.doc.linked_to
				},
				callback: function(r) {
					if (r.message) {
						// For Bed, use total_kms_run; for Vehicle, use last_odometer
						if (frm.doc.linked_to_type === 'Bed' && r.message.total_kms_run) {
							frm.set_value('odo_count', r.message.total_kms_run);
						} else if (r.message.last_odometer) {
							frm.set_value('odo_count', r.message.last_odometer);
						}
						if (r.message.location && !frm.doc.location) {
							frm.set_value('location', r.message.location);
						}
					}
				}
			});
		}
	},
	
	linked_to_type: function(frm) {
		// Clear linked_to when type changes
		if (frm.doc.linked_to_type) {
			frm.set_value('linked_to', '');
			frm.refresh_field('linked_to');
		}
		// Location field is available for both Vehicle and Bed
	},
	
	linked_to: function(frm) {
		if (frm.doc.linked_to && frm.doc.linked_to_type) {
			frappe.call({
				method: 'fateh_maintenance.logistics_maintaenance.doctype.maintenance.maintenance.get_vehicle_info',
				args: {
					linked_to_type: frm.doc.linked_to_type,
					linked_to: frm.doc.linked_to
				},
				callback: function(r) {
					if (r.message) {
						// For Bed, use total_kms_run; for Vehicle, use last_odometer
						if (frm.doc.linked_to_type === 'Bed' && r.message.total_kms_run) {
							frm.set_value('odo_count', r.message.total_kms_run);
						} else if (r.message.last_odometer) {
							frm.set_value('odo_count', r.message.last_odometer);
						}
						if (r.message.location && !frm.doc.location) {
							frm.set_value('location', r.message.location);
						}
					}
				}
			});
		}
	},
	
	company: function(frm) {
		// When company changes, refresh warehouse filters
		if (frm.doc.company && frm.doc.materials) {
			frm.refresh_field('materials');
		}
	},
	
	status: function(frm) {
		// When status changes to Completed, trigger validation
		if (frm.doc.status === 'Completed') {
			if (!frm.doc.maintenance_date) {
				frm.set_value('maintenance_date', frappe.datetime.get_today());
			}
		}
	},
	
	// Material amount calculation removed - Stock Entry uses stock UOM rate automatically
	
	default_warehouse: function(frm) {
		// Update warehouse in all material rows if default_warehouse is set
		if (frm.doc.default_warehouse && frm.doc.materials) {
			frm.doc.materials.forEach(function(row) {
				if (!row.warehouse) {
					frappe.model.set_value(row.doctype, row.name, 'warehouse', frm.doc.default_warehouse);
				}
			});
			frm.refresh_field('materials');
		}
	}
});

// Material rate/amount removed - Stock Entry uses stock UOM rate automatically
frappe.ui.form.on('Maintenance Material', {
	
	item_code: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.item_code) {
			frappe.db.get_value('Item', row.item_code, ['item_name', 'stock_uom'], function(r) {
				if (r) {
					frappe.model.set_value(cdt, cdn, 'item_name', r.item_name);
					if (!row.uom) {
						frappe.model.set_value(cdt, cdn, 'uom', r.stock_uom);
					}
				}
			});
		}
	},
	
	warehouse: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		// Validate warehouse is not a group warehouse
		if (row.warehouse) {
			frappe.db.get_value('Warehouse', row.warehouse, 'is_group', function(r) {
				if (r && r.is_group) {
					frappe.msgprint(__('Please select a non-group warehouse'));
					frappe.model.set_value(cdt, cdn, 'warehouse', '');
				}
			});
		}
	},
	
	materials_add: function(frm, cdt, cdn) {
		// Set default warehouse from parent if available
		let row = locals[cdt][cdn];
		if (frm.doc.default_warehouse && !row.warehouse) {
			frappe.model.set_value(cdt, cdn, 'warehouse', frm.doc.default_warehouse);
		}
	}
});
