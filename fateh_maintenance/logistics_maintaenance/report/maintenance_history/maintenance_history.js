frappe.query_reports["Maintenance History"] = {
	"filters": [
		{
			"fieldname": "linked_to_type",
			"label": __("Linked To Type"),
			"fieldtype": "Select",
			"options": ["", "Vehicle", "Bed"],
			"default": "",
			"reqd": 0
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": ["", "Waiting", "In Progress", "Completed", "Cancelled"],
			"reqd": 0
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 0
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 0
		}
	]
};
