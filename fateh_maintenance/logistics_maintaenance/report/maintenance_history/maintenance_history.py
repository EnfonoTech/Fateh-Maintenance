# Copyright (c) 2025, fateh_maintenance and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"fieldname": "linked_to_type",
			"label": _("Type"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "linked_to",
			"label": _("Current Vehicle"),
			"fieldtype": "Dynamic Link",
			"options": "linked_to_type",
			"width": 150
		},
		{
			"fieldname": "maintenance_type",
			"label": _("Maintenance Type"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "maintenance_date",
			"label": _("Date"),
			"fieldtype": "Date",
			"width": 120
		},
		{
			"fieldname": "odo_count",
			"label": _("Vehicle odo After maintenance"),
			"fieldtype": "Float",
			"width": 200
		},
		{
			"fieldname": "status",
			"label": _("Status"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "trigger_date",
			"label": _("Trigger Date"),
			"fieldtype": "Date",
			"width": 120
		},
		{
			"fieldname": "trigger_km",
			"label": _("Trigger KM"),
			"fieldtype": "Float",
			"width": 120
		}
	]


def get_data(filters):
	conditions = {"docstatus": ["!=", 2]}
	
	if filters.get("linked_to_type"):
		conditions["linked_to_type"] = filters.get("linked_to_type")
	
	if filters.get("status"):
		conditions["status"] = filters.get("status")
	
	if filters.get("from_date") and filters.get("to_date"):
		conditions["maintenance_date"] = ["between", [filters.get("from_date"), filters.get("to_date")]]
	elif filters.get("from_date"):
		conditions["maintenance_date"] = [">=", filters.get("from_date")]
	elif filters.get("to_date"):
		conditions["maintenance_date"] = ["<=", filters.get("to_date")]
	
	maintenance_records = frappe.get_all(
		"Maintenance",
		filters=conditions,
		fields=["linked_to_type", "linked_to", "maintenance_type", "maintenance_date", "odo_count", "status", "trigger_date", "trigger_km"],
		order_by="maintenance_date desc, creation desc"
	)
	
	# Filter out trigger_date and trigger_km if they don't exist (None values)
	# The columns will still show but with empty values
	return maintenance_records
