import frappe
from frappe.model.document import Document
from frappe.utils import nowtime


class StockPlacement(Document):
	def validate(self):
		if not self.posting_time:
			self.posting_time = nowtime()
		for row in self.items:
			if not row.from_location and not row.to_location:
				frappe.throw(f"שורה {row.idx}: יש לציין 'ממיקום' או 'למיקום' (לפחות אחד).")
			if not row.qty or row.qty <= 0:
				frappe.throw(f"שורה {row.idx}: הכמות חייבת להיות גדולה מאפס.")

	def on_submit(self):
		self.make_ledger_entries()

	def on_cancel(self):
		frappe.db.delete(
			"Location Ledger Entry",
			{"voucher_type": "Stock Placement", "voucher_no": self.name},
		)

	def make_ledger_entries(self):
		for row in self.items:
			if row.to_location:
				self._make_entry(row, row.to_location, row.qty)
			if row.from_location:
				self._make_entry(row, row.from_location, -1 * row.qty)

	def _make_entry(self, row, location, qty):
		warehouse = frappe.db.get_value("Storage Location", location, "warehouse")
		frappe.get_doc(
			{
				"doctype": "Location Ledger Entry",
				"item": row.item,
				"storage_location": location,
				"warehouse": warehouse,
				"qty": qty,
				"batch_no": row.batch_no,
				"serial_no": row.serial_no,
				"posting_date": self.posting_date,
				"posting_time": self.posting_time,
				"voucher_type": "Stock Placement",
				"voucher_no": self.name,
			}
		).insert(ignore_permissions=True)
