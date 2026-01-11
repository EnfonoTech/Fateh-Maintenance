# Copyright (c) 2025, fateh_maintenance and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DriverEquipment(Document):
	pass


def get_default_equipment_list():
	"""Return default equipment list with all required items"""
	return [
		{"item": "Chain Lock", "type": "count"},
		{"item": "Belt", "type": "count"},
		{"item": "Belt Lock", "type": "count"},
		{"item": "Pad Lock", "type": "count"},
		{"item": "Safety Shoe", "type": "yesno"},
		{"item": "Helmet", "type": "yesno"},
		{"item": "Tool Set", "type": "yesno"},
		{"item": "Safety Glass", "type": "yesno"},
		{"item": "Safety Corn", "type": "count"},
		{"item": "Safety Corn Light", "type": "count"},
		{"item": "First Aid Kit", "type": "yesno"},
		{"item": "Fire Extinguisher", "type": "count"},
		{"item": "Stepney", "type": "count"},
		{"item": "Measure Tap", "type": "yesno"},
		{"item": "Writing Pad", "type": "yesno"},
		{"item": "Battery Booster", "type": "yesno"},
		{"item": "HIVIS", "type": "yesno"},
		{"item": "TORCH", "type": "yesno"},
		{"item": "WARNING TRIANGLE", "type": "yesno"},
		{"item": "SPILL KIT", "type": "yesno"},
		{"item": "UNIFORM", "type": "yesno"},
		{"item": "WHEEL BLOCK", "type": "count"}
	]


@frappe.whitelist()
def populate_default_equipment(driver_name):
	"""Populate default equipment for a driver"""
	try:
		driver_doc = frappe.get_doc("Driver", driver_name)
		
		# Clear existing equipment
		driver_doc.set("equipment_list", [])
		
		# Add default equipment
		for eq in get_default_equipment_list():
			driver_doc.append("equipment_list", {
				"equipment_item": eq["item"],
				"item_type": eq["type"],
				"quantity": 0 if eq["type"] == "count" else None,
				"has_item": 0 if eq["type"] == "yesno" else None
			})
		
		driver_doc.save()
		frappe.db.commit()
		
		return {
			"success": True,
			"message": "Equipment template loaded successfully"
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error loading equipment template")
		frappe.throw(f"Error loading equipment template: {str(e)}")
