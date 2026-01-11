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
			"fieldname": "name",
			"label": _("Maintenance ID"),
			"fieldtype": "Link",
			"options": "Maintenance",
			"width": 150
		},
		{
			"fieldname": "linked_to_type",
			"label": _("Type"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "linked_to",
			"label": _("Vehicle/Bed"),
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
			"label": _("Odometer (KM)"),
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
			"fieldname": "supervisor",
			"label": _("Supervisor"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 150
		},
		{
			"fieldname": "mechanic",
			"label": _("Mechanic"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 150
		},
		{
			"fieldname": "material_utilization",
			"label": _("Material Cost"),
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"fieldname": "location",
			"label": _("Location"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "trigger_type",
			"label": _("Trigger Type"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "next_maintenance_date",
			"label": _("Next Date"),
			"fieldtype": "Date",
			"width": 120
		},
		{
			"fieldname": "next_maintenance_km",
			"label": _("Next KM"),
			"fieldtype": "Float",
			"width": 120
		}
	]


def get_data(filters):
	conditions = {"docstatus": ["!=", 2]}
	
	if filters.get("linked_to_type"):
		conditions["linked_to_type"] = filters.get("linked_to_type")
	
	if filters.get("linked_to"):
		conditions["linked_to"] = filters.get("linked_to")
	
	if filters.get("maintenance_type"):
		conditions["maintenance_type"] = filters.get("maintenance_type")
	
	if filters.get("status"):
		conditions["status"] = filters.get("status")
	
	if filters.get("from_date") and filters.get("to_date"):
		conditions["maintenance_date"] = ["between", [filters.get("from_date"), filters.get("to_date")]]
	elif filters.get("from_date"):
		conditions["maintenance_date"] = [">=", filters.get("from_date")]
	elif filters.get("to_date"):
		conditions["maintenance_date"] = ["<=", filters.get("to_date")]
	
	if filters.get("trigger_type"):
		conditions["trigger_type"] = filters.get("trigger_type")
	
	maintenance_records = frappe.get_all(
		"Maintenance",
		filters=conditions,
		fields=[
			"name", "linked_to_type", "linked_to", "maintenance_type", "maintenance_date",
			"odo_count", "status", "supervisor", "mechanic", "material_utilization",
			"location", "trigger_type", "next_maintenance_date", "next_maintenance_km"
		],
		order_by="maintenance_date desc, creation desc"
	)
	
	# Get employee names
	for record in maintenance_records:
		if record.get("supervisor"):
			record["supervisor"] = frappe.db.get_value("Employee", record["supervisor"], "employee_name") or record["supervisor"]
		if record.get("mechanic"):
			record["mechanic"] = frappe.db.get_value("Employee", record["mechanic"], "employee_name") or record["mechanic"]
	
	return maintenance_records
