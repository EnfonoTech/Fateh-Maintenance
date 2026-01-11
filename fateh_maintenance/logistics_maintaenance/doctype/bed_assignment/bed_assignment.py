# Copyright (c) 2025, fateh_maintenance and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class BedAssignment(Document):
	def validate(self):
		self.validate_bed_availability()
		self.validate_odometer()
		self.calculate_kms_run()
		
	def validate_bed_availability(self):
		"""Check if bed is already assigned to another vehicle"""
		if self.status == "Assigned":
			existing = frappe.db.exists(
				"Bed Assignment",
				{
					"bed": self.bed,
					"status": "Assigned",
					"name": ("!=", self.name)
				}
			)
			if existing:
				frappe.throw(_("Bed {0} is already assigned to another vehicle").format(self.bed))
	
	def validate_odometer(self):
		"""Validate odometer readings"""
		if self.assign_odometer and self.assign_odometer < 0:
			frappe.throw(_("Assign Odometer cannot be negative"))
			
		if self.remove_date and not self.remove_odometer:
			frappe.throw(_("Remove Odometer is mandatory when Remove Date is set"))
			
		if self.remove_odometer and self.assign_odometer:
			if self.remove_odometer < self.assign_odometer:
				frappe.throw(_("Remove Odometer cannot be less than Assign Odometer"))
	
	def calculate_kms_run(self):
		"""Calculate total KMs run during assignment"""
		if self.remove_odometer and self.assign_odometer:
			self.total_kms_run = flt(self.remove_odometer) - flt(self.assign_odometer)
		elif self.assign_odometer:
			# If not removed yet, get current vehicle odometer if available
			vehicle_odo = self.get_current_vehicle_odometer()
			if vehicle_odo:
				self.total_kms_run = flt(vehicle_odo) - flt(self.assign_odometer)
			else:
				self.total_kms_run = 0
		else:
			self.total_kms_run = 0
	
	def get_current_vehicle_odometer(self):
		"""Get current odometer reading from vehicle"""
		try:
			return frappe.db.get_value("Vehicle", self.vehicle, "last_odometer")
		except:
			return None
	
	def on_update(self):
		"""Update bed status and vehicle odometer"""
		if self.status == "Assigned":
			self.update_bed_status()
			self.update_vehicle_odometer()
		elif self.status == "Removed":
			self.update_bed_status()
			self.update_vehicle_odometer()
	
	def update_bed_status(self):
		"""Update current assignment status in Bed doctype"""
		if not self.bed:
			return
			
		bed_doc = frappe.get_doc("Bed", self.bed)
		if self.status == "Assigned":
			bed_doc.db_set({
				"current_vehicle": self.vehicle,
				"assignment_status": "Assigned",
				"assign_date": self.assign_date
			})
		else:
			bed_doc.db_set({
				"current_vehicle": None,
				"assignment_status": "Available",
				"assign_date": None
			})
		# Update total KMs run on bed
		self.update_bed_total_kms()
	
	def update_bed_total_kms(self):
		"""Update total KMs run on the bed"""
		total_kms = frappe.db.sql("""
			SELECT SUM(total_kms_run) 
			FROM `tabBed Assignment` 
			WHERE bed = %s AND status = 'Removed'
		""", (self.bed,))
		
		if total_kms and total_kms[0][0]:
			frappe.db.set_value("Bed", self.bed, "total_kms_run", total_kms[0][0])
		else:
			frappe.db.set_value("Bed", self.bed, "total_kms_run", 0)
	
	def update_vehicle_odometer(self):
		"""Update vehicle's last_odometer when bed is assigned or removed"""
		if not self.vehicle:
			return
		
		# When assigning, update vehicle odometer to assign_odometer if it's higher
		# When removing, update vehicle odometer to remove_odometer if it's higher
		if self.status == "Assigned" and self.assign_odometer:
			current_vehicle_odo = frappe.db.get_value("Vehicle", self.vehicle, "last_odometer") or 0
			if flt(self.assign_odometer) > flt(current_vehicle_odo):
				frappe.db.set_value("Vehicle", self.vehicle, "last_odometer", int(flt(self.assign_odometer)))
		elif self.status == "Removed" and self.remove_odometer:
			current_vehicle_odo = frappe.db.get_value("Vehicle", self.vehicle, "last_odometer") or 0
			if flt(self.remove_odometer) > flt(current_vehicle_odo):
				frappe.db.set_value("Vehicle", self.vehicle, "last_odometer", int(flt(self.remove_odometer)))
