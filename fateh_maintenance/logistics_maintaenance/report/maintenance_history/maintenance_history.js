frappe.query_reports["Maintenance History"] = {
	"filters": [
		{
			"fieldname": "linked_to_type",
			"label": __("Type"),
			"fieldtype": "Select",
			"options": "\nVehicle\nBed",
			"default": ""
		},
		{
			"fieldname": "linked_to",
			"label": __("Vehicle/Bed"),
			"fieldtype": "Dynamic Link",
			"options": "linked_to_type",
			"get_query": function() {
				var linked_to_type = frappe.query_report.get_filter_value("linked_to_type");
				if (linked_to_type) {
					return {
						doctype: linked_to_type,
						filters: {}
					};
				}
				return {};
			}
		},
		{
			"fieldname": "maintenance_type",
			"label": __("Maintenance Type"),
			"fieldtype": "Select",
			"options": "\nGeneral Service\nTyre Replacement\nTyre Rotation\nEngine Service\nBrake Service\nOil Change\nInspection\nRepair\nOther",
			"default": ""
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nWaiting\nIn Progress\nCompleted\nCancelled",
			"default": ""
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "trigger_type",
			"label": __("Trigger Type"),
			"fieldtype": "Select",
			"options": "\nDate Based\nKM Based\nBoth\nNone",
			"default": ""
		}
	]
};
