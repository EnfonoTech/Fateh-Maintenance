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
			"fieldname": "bed",
			"label": _("Bed"),
			"fieldtype": "Link",
			"options": "Bed",
			"width": 150
		},
		{
			"fieldname": "vehicle",
			"label": _("Vehicle"),
			"fieldtype": "Link",
			"options": "Vehicle",
			"width": 150
		},
		{
			"fieldname": "assign_date",
			"label": _("Assign Date"),
			"fieldtype": "Date",
			"width": 120
		},
		{
			"fieldname": "assign_odometer",
			"label": _("Assign Odometer (KM)"),
			"fieldtype": "Float",
			"width": 150
		},
		{
			"fieldname": "remove_date",
			"label": _("Remove Date"),
			"fieldtype": "Date",
			"width": 120
		},
		{
			"fieldname": "remove_odometer",
			"label": _("Remove Odometer (KM)"),
			"fieldtype": "Float",
			"width": 150
		},
		{
			"fieldname": "total_kms_run",
			"label": _("Total KMs Run"),
			"fieldtype": "Float",
			"width": 130
		},
		{
			"fieldname": "status",
			"label": _("Status"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "name",
			"label": _("Assignment ID"),
			"fieldtype": "Link",
			"options": "Bed Assignment",
			"width": 150
		}
	]


def get_data(filters):
	conditions = {"docstatus": ["!=", 2]}
	
	if filters.get("bed"):
		conditions["bed"] = filters.get("bed")
	
	if filters.get("vehicle"):
		conditions["vehicle"] = filters.get("vehicle")
	
	if filters.get("status"):
		conditions["status"] = filters.get("status")
	
	if filters.get("from_date") and filters.get("to_date"):
		conditions["assign_date"] = ["between", [filters.get("from_date"), filters.get("to_date")]]
	elif filters.get("from_date"):
		conditions["assign_date"] = [">=", filters.get("from_date")]
	elif filters.get("to_date"):
		conditions["assign_date"] = ["<=", filters.get("to_date")]
	
	assignments = frappe.get_all(
		"Bed Assignment",
		filters=conditions,
		fields=[
			"name", "bed", "vehicle", "assign_date", "assign_odometer",
			"remove_date", "remove_odometer", "total_kms_run", "status"
		],
		order_by="assign_date desc, creation desc"
	)
	
	return assignments
