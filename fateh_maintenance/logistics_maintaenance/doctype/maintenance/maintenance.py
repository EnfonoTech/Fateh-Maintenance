# Copyright (c) 2025, fateh_maintenance and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, today, nowdate
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry


class Maintenance(Document):
	def validate(self):
		self.validate_odometer()
		self.validate_status()
		self.validate_personnel()
		self.validate_company()
		self.calculate_material_utilization()
		self.fetch_vehicle_history()
		self.check_vehicle_status()
		
	def validate_odometer(self):
		"""Validate odometer reading"""
		if self.odo_count and self.odo_count < 0:
			frappe.throw(_("Odometer Count cannot be negative"))
		
		# Check if odometer is less than last recorded (for Vehicle only)
		if self.linked_to_type == "Vehicle" and self.linked_to and self.odo_count:
			last_odo = frappe.db.get_value("Vehicle", self.linked_to, "last_odometer")
			if last_odo and self.odo_count < last_odo:
				frappe.throw(_("Odometer Count ({0}) cannot be less than last recorded odometer ({1})").format(
					self.odo_count, last_odo
				))
		
		# For Bed, check against last maintenance KM
		elif self.linked_to_type == "Bed" and self.linked_to and self.odo_count:
			last_maintenance_km = frappe.db.get_value("Bed", self.linked_to, "last_maintenance_km")
			if last_maintenance_km and self.odo_count < last_maintenance_km:
				frappe.throw(_("Odometer Count ({0}) cannot be less than last maintenance KM ({1})").format(
					self.odo_count, last_maintenance_km
				))
	
	def validate_status(self):
		"""Validate status transitions"""
		if self.is_new():
			return
			
		old_status = frappe.db.get_value(self.doctype, self.name, "status")
		
		# Once completed, cannot go back
		if old_status == "Completed" and self.status != "Completed":
			frappe.throw(_("Cannot change status from Completed"))
		
		# Once cancelled, cannot change
		if old_status == "Cancelled" and self.status != "Cancelled":
			frappe.throw(_("Cannot change status from Cancelled"))
	
	def validate_personnel(self):
		"""Validate supervisor and mechanic are active employees"""
		if self.supervisor:
			if not frappe.db.exists("Employee", {"name": self.supervisor, "status": "Active"}):
				frappe.throw(_("Supervisor must be an active employee"))
		
		if self.mechanic:
			if not frappe.db.exists("Employee", {"name": self.mechanic, "status": "Active"}):
				frappe.throw(_("Mechanic must be an active employee"))
	
	def validate_company(self):
		"""Validate and auto-set company when auto stock deduct is enabled and materials exist"""
		# Auto-set company if not set and auto stock deduct is enabled with materials
		if self.auto_stock_deduct and self.materials and not self.company:
			# Try to get default company
			default_company = frappe.defaults.get_default("company") or frappe.defaults.get_global_default("company")
			if default_company:
				self.company = default_company
			else:
				frappe.throw(_("Company is required when auto stock deduct is enabled and materials are added. Please set company field or default company in User Defaults."))
	
	def calculate_material_utilization(self):
		"""Calculate total material utilization cost"""
		total = 0
		if self.materials:
			for material in self.materials:
				if not material.amount:
					material.amount = flt(material.quantity) * flt(material.rate)
				total += flt(material.amount)
		
		self.material_utilization = total
	
	def fetch_vehicle_history(self):
		"""Auto-fetch vehicle history (Vehicle Log entries) - Only for Vehicle"""
		if self.linked_to_type != "Vehicle" or not self.linked_to:
			return
		
		# Clear existing history
		self.vehicle_history = []
		
		# Fetch recent Vehicle Log entries
		vehicle_logs = frappe.get_all(
			"Vehicle Log",
			filters={
				"license_plate": self.linked_to,
				"docstatus": 1
			},
			fields=["name", "date", "odometer", "fuel_qty", "price", "employee"],
			order_by="date desc, creation desc",
			limit=10
		)
		
		for log in vehicle_logs:
			# Build description from available fields
			description_parts = ["Vehicle Log Entry"]
			if log.fuel_qty:
				description_parts.append(f"Fuel: {log.fuel_qty}L")
			if log.employee:
				emp_name = frappe.db.get_value("Employee", log.employee, "employee_name") or log.employee
				description_parts.append(f"Employee: {emp_name}")
			
			description = " | ".join(description_parts)
			
			self.append("vehicle_history", {
				"log_date": log.date,
				"log_type": "Vehicle Log",
				"odometer": log.odometer,
				"description": description,
				"reference": log.name,
				"reference_doctype": "Vehicle Log",
				"vehicle": self.linked_to
			})
		
		# Fetch previous maintenance records
		previous_maintenance = frappe.get_all(
			"Maintenance",
			filters={
				"linked_to_type": "Vehicle",
				"linked_to": self.linked_to,
				"docstatus": 1,
				"name": ("!=", self.name) if not self.is_new() else ("!=", "")
			},
			fields=["name", "maintenance_date", "odo_count", "maintenance_type", "description"],
			order_by="maintenance_date desc, creation desc",
			limit=5
		)
		
		for maint in previous_maintenance:
			# Strip HTML tags from description if it's a Text Editor field
			desc_text = ""
			if maint.description:
				from frappe.utils import strip_html_tags
				desc_text = strip_html_tags(maint.description)
				# Limit description length
				if len(desc_text) > 100:
					desc_text = desc_text[:100] + "..."
			
			self.append("vehicle_history", {
				"log_date": maint.maintenance_date,
				"log_type": "Maintenance",
				"odometer": maint.odo_count,
				"description": f"{maint.maintenance_type}: {desc_text}",
				"reference": maint.name,
				"reference_doctype": "Maintenance",
				"vehicle": self.linked_to
			})
	
	def check_vehicle_status(self):
		"""Check and update vehicle status based on maintenance status"""
		if self.linked_to_type != "Vehicle" or not self.linked_to:
			return
		
		# When maintenance is in progress or waiting, set vehicle to maintenance mode
		if self.status in ["Waiting", "In Progress"]:
			# Update will happen in on_update
			pass
	
	def on_update(self):
		"""Update vehicle/bed status when status changes"""
		if self.has_value_changed("status"):
			if self.linked_to_type == "Vehicle":
				self.update_vehicle_status()
			elif self.linked_to_type == "Bed":
				self.update_bed_status()
	
	def update_vehicle_status(self):
		"""Update vehicle status based on maintenance status"""
		if not self.linked_to or self.linked_to_type != "Vehicle":
			return
		
		# Check if vehicle has status field (custom field)
		has_status_field = frappe.db.has_column("Vehicle", "status")
		if not has_status_field:
			return
		
		if self.status == "Completed":
			# Check if there are other pending maintenances
			pending_maint = frappe.db.exists(
				"Maintenance",
				{
					"linked_to_type": "Vehicle",
					"linked_to": self.linked_to,
					"status": ("in", ["Waiting", "In Progress"]),
					"name": ("!=", self.name),
					"docstatus": 1
				}
			)
			
			if not pending_maint:
				# No other pending maintenance, make vehicle active
				frappe.db.set_value("Vehicle", self.linked_to, "status", "Active")
			else:
				frappe.db.set_value("Vehicle", self.linked_to, "status", "In Maintenance")
		elif self.status in ["Waiting", "In Progress"]:
			frappe.db.set_value("Vehicle", self.linked_to, "status", "In Maintenance")
	
	def update_bed_status(self):
		"""Update bed status if bed maintenance is completed"""
		if not self.linked_to or self.linked_to_type != "Bed":
			return
		
		if self.status == "Completed":
			# Bed maintenance completed
			frappe.db.set_value("Bed", self.linked_to, "last_maintenance_date", self.maintenance_date)
			frappe.db.set_value("Bed", self.linked_to, "last_maintenance_km", self.odo_count)
	
	def on_submit(self):
		"""Actions when maintenance is submitted"""
		if self.status != "Completed":
			frappe.throw(_("Only Completed maintenance can be submitted"))
		
		# Update vehicle odometer if Vehicle maintenance
		if self.linked_to_type == "Vehicle" and self.linked_to and self.odo_count:
			frappe.db.set_value("Vehicle", self.linked_to, "last_odometer", int(self.odo_count))
		
		# Auto deduct stock if enabled
		if self.auto_stock_deduct and self.materials:
			self.create_stock_entry()
		
		# Make vehicle active if no other pending maintenance
		if self.linked_to_type == "Vehicle":
			self.update_vehicle_status()
		
		# Create Vehicle Log entry for this maintenance (Vehicle only)
		if self.linked_to_type == "Vehicle":
			self.create_vehicle_log()
	
	def create_stock_entry(self):
		"""Create stock entry to deduct materials"""
		if not self.materials:
			return
		
		# Get company from Maintenance document or fallback to defaults
		company = self.company
		
		if not company:
			# Try to get company from vehicle (if custom field exists)
			if self.linked_to_type == "Vehicle" and self.linked_to and frappe.db.has_column("Vehicle", "company"):
				company = frappe.db.get_value("Vehicle", self.linked_to, "company")
		
		if not company:
			# Use default company from user defaults or global defaults
			company = frappe.defaults.get_default("company") or frappe.defaults.get_global_default("company")
		
		if not company:
			frappe.throw(_("Company is required to create Stock Entry. Please set company field or default company in User Defaults."))
		
		# Create stock entry
		stock_entry = frappe.new_doc("Stock Entry")
		stock_entry.purpose = "Material Issue"
		stock_entry.company = company
		stock_entry.set_stock_entry_type()
		
		# Link to maintenance if custom field exists
		if frappe.db.has_column("Stock Entry", "custom_maintenance"):
			stock_entry.custom_maintenance = self.name
		
		for material in self.materials:
			warehouse = material.warehouse or self.default_warehouse
			if not warehouse:
				frappe.throw(_("Warehouse is required for item {0}. Please set default warehouse or warehouse in material row.").format(material.item_code))
			
			# Validate warehouse belongs to company
			warehouse_company = frappe.db.get_value("Warehouse", warehouse, "company")
			if warehouse_company and warehouse_company != company:
				frappe.throw(_("Warehouse {0} belongs to company {1}, but selected company is {2}. Please select a warehouse belonging to {2}.").format(
					warehouse, warehouse_company, company
				))
			
			# Get expense account - use from maintenance doc, or item defaults, or item group defaults
			expense_account = self.expense_account
			if not expense_account:
				# Try to get from item defaults
				item_defaults = frappe.db.get_value("Item Default", {"parent": material.item_code, "company": company}, "expense_account")
				if item_defaults:
					expense_account = item_defaults
				else:
					# Try to get from item group defaults
					item_group = frappe.db.get_value("Item", material.item_code, "item_group")
					if item_group:
						item_group_defaults = frappe.db.get_value("Item Group Default", {"parent": item_group, "company": company}, "expense_account")
						if item_group_defaults:
							expense_account = item_group_defaults
			
			# Get cost center - use from maintenance doc, or company default, or item defaults
			cost_center = self.cost_center
			if not cost_center:
				# Try to get company default cost center
				company_default_cc = frappe.db.get_value("Company", company, "cost_center")
				if company_default_cc:
					cost_center = company_default_cc
				else:
					# Try to get from item defaults
					item_defaults_cc = frappe.db.get_value("Item Default", {"parent": material.item_code, "company": company}, "buying_cost_center")
					if item_defaults_cc:
						cost_center = item_defaults_cc
			
			stock_entry.append("items", {
				"item_code": material.item_code,
				"qty": material.quantity,
				"uom": material.uom,
				"s_warehouse": warehouse,
				"rate": material.rate,
				"expense_account": expense_account,
				"cost_center": cost_center,
				"serial_no": material.serial_no,
				"batch_no": material.batch_no,
				"allow_zero_valuation_rate": 0
			})
		
		stock_entry.insert()
		stock_entry.submit()
		
		self.stock_entry = stock_entry.name
		frappe.db.set_value(self.doctype, self.name, "stock_entry", stock_entry.name)
		frappe.msgprint(_("Stock Entry {0} created and submitted").format(
			frappe.bold(stock_entry.name)
		))
	
	def create_vehicle_log(self):
		"""Create vehicle log entry for this maintenance"""
		if self.linked_to_type != "Vehicle" or not self.linked_to:
			return
		
		vehicle_log = frappe.new_doc("Vehicle Log")
		vehicle_log.license_plate = self.linked_to
		vehicle_log.date = self.maintenance_date
		vehicle_log.odometer = int(self.odo_count)
		vehicle_log.employee = self.supervisor
		
		# Set custom field if it exists
		if frappe.db.has_column("Vehicle Log", "custom_maintenance"):
			vehicle_log.custom_maintenance = self.name
		
		# Note: service_detail is a child table, so we can't set it directly
		# The maintenance information is tracked separately via custom_maintenance link
		
		vehicle_log.insert()
		vehicle_log.submit()
		
		frappe.msgprint(_("Vehicle Log {0} created").format(
			frappe.bold(vehicle_log.name)
		))
	
	def on_cancel(self):
		"""Actions when maintenance is cancelled"""
		# Reverse stock entry if created
		if self.stock_entry:
			se_doc = frappe.get_doc("Stock Entry", self.stock_entry)
			if se_doc.docstatus == 1:
				se_doc.cancel()
				frappe.msgprint(_("Stock Entry {0} has been cancelled").format(
					frappe.bold(self.stock_entry)
				))
		
		# Update vehicle status
		if self.linked_to_type == "Vehicle" and self.linked_to:
			has_status_field = frappe.db.has_column("Vehicle", "status")
			if has_status_field:
				pending_maint = frappe.db.exists(
					"Maintenance",
					{
						"linked_to_type": "Vehicle",
						"linked_to": self.linked_to,
						"status": ("in", ["Waiting", "In Progress"]),
						"name": ("!=", self.name),
						"docstatus": 1
					}
				)
				
				if not pending_maint:
					frappe.db.set_value("Vehicle", self.linked_to, "status", "Active")


@frappe.whitelist()
def get_vehicle_info(linked_to_type, linked_to):
	"""Get vehicle/bed information for auto-fill"""
	if not linked_to or not linked_to_type:
		return {}
	
	if linked_to_type == "Vehicle":
		info = frappe.db.get_value(
			"Vehicle",
			linked_to,
			[
				"last_odometer",
				"location",
				"make",
				"model",
				"license_plate"
			],
			as_dict=True
		)
		return info or {}
	elif linked_to_type == "Bed":
		info = frappe.db.get_value(
			"Bed",
			linked_to,
			[
				"last_maintenance_km",
				"last_maintenance_date",
				"total_kms_run",
				"current_vehicle"
			],
			as_dict=True
		)
		if info:
			# Map bed fields to expected format
			return {
				"last_odometer": info.get("last_maintenance_km"),
				"location": None,
				"current_vehicle": info.get("current_vehicle"),
				"total_kms_run": info.get("total_kms_run")
			}
		return {}
	
	return {}
