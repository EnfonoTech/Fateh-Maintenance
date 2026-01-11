# Copyright (c) 2025, fateh_maintenance and contributors
# For license information, please see license.txt

import frappe
from fateh_maintenance.logistics_maintaenance.doctype.driver_equipment.driver_equipment import get_default_equipment_list


def populate_default_equipment(doc, method):
	"""Populate default equipment list when Driver is created or if empty"""
	# Only populate if equipment_list is empty
	if not doc.get("equipment_list") or len(doc.get("equipment_list", [])) == 0:
		# Add default equipment
		for eq in get_default_equipment_list():
			doc.append("equipment_list", {
				"equipment_item": eq["item"],
				"item_type": eq["type"],
				"quantity": 0 if eq["type"] == "count" else None,
				"has_item": 0 if eq["type"] == "yesno" else None
			})
