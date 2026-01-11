# Copyright (c) 2025, fateh_maintenance and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Bed(Document):
	pass


@frappe.whitelist()
def assign_bed_to_vehicle(bed, vehicle, assign_date, assign_odometer):
	"""Assign bed to a vehicle"""
	# Check if bed is already assigned
	bed_doc = frappe.get_doc("Bed", bed)
	if bed_doc.assignment_status == "Assigned":
		frappe.throw(_("Bed {0} is already assigned to vehicle {1}").format(bed, bed_doc.current_vehicle))
	
	# Check if there's an existing assignment record
	existing_assignment = frappe.db.get_value(
		"Bed Assignment",
		{
			"bed": bed,
			"status": "Assigned"
		},
		"name"
	)
	
	if existing_assignment:
		frappe.throw(_("Bed {0} already has an active assignment. Please remove it first.").format(bed))
	
	# Create new Bed Assignment
	# Get default naming series
	from frappe.model.naming import get_default_naming_series
	naming_series = get_default_naming_series("Bed Assignment") or "BA-.YYYY.-#####"
	
	assignment = frappe.get_doc({
		"doctype": "Bed Assignment",
		"naming_series": naming_series,
		"bed": bed,
		"vehicle": vehicle,
		"assign_date": assign_date,
		"assign_odometer": float(assign_odometer),
		"status": "Assigned"
	})
	assignment.insert()
	assignment.save()
	
	frappe.msgprint(_("Bed {0} assigned to vehicle {1}").format(bed, vehicle))
	return assignment.name


@frappe.whitelist()
def remove_bed_from_vehicle(bed, remove_date, remove_odometer):
	"""Remove bed from current vehicle"""
	# Get current assignment
	assignment = frappe.db.get_value(
		"Bed Assignment",
		{
			"bed": bed,
			"status": "Assigned"
		},
		"name",
		as_dict=True
	)
	
	if not assignment:
		frappe.throw(_("Bed {0} is not currently assigned to any vehicle").format(bed))
	
	# Get assignment document
	assignment_doc = frappe.get_doc("Bed Assignment", assignment.name)
	
	# Validate odometer
	if float(remove_odometer) < float(assignment_doc.assign_odometer or 0):
		frappe.throw(_("Remove Odometer cannot be less than Assign Odometer ({0})").format(assignment_doc.assign_odometer))
	
	# Update assignment
	assignment_doc.remove_date = remove_date
	assignment_doc.remove_odometer = float(remove_odometer)
	assignment_doc.status = "Removed"
	assignment_doc.save()
	
	frappe.msgprint(_("Bed {0} removed from vehicle {1}").format(bed, assignment_doc.vehicle))
	return assignment_doc.name
