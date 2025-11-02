from odoo import api, fields, models
from datetime import timedelta
from odoo.exceptions import UserError


class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Property Offer"
    _order = "price desc" 
   
    price = fields.Float(string="Price")
    status = fields.Selection(
        [
            ("accepted", "Accepted"),
            ("refused", "Refused"),
        ],
        string="Status",
        copy=False
    )

    partner_id = fields.Many2one("res.partner", string="Partner", required=True)
    property_id = fields.Many2one("estate.property", string="Property", required=True)

    property_type_id = fields.Many2one(
        "estate.property.type",
        string="Property Type",
        related="property_id.property_type_id",
        store=True
    )

    validity = fields.Integer(string="Validity (days)", default=7)
    date_deadline = fields.Date(
        string="Deadline",
        compute="_compute_date_deadline",
        inverse="_inverse_date_deadline",
        store=True
    )

    @api.depends("validity", "create_date")
    def _compute_date_deadline(self):
        for record in self:
            create_date = record.create_date.date() if record.create_date else fields.Date.today()
            record.date_deadline = create_date + timedelta(days=record.validity)

    def _inverse_date_deadline(self):
        for record in self:
            if record.date_deadline:
                create_date = record.create_date.date() if record.create_date else fields.Date.today()
                record.validity = (record.date_deadline - create_date).days

    def action_accept(self):
        for record in self:
            property = record.property_id

            if property.state == "sold":
                raise UserError("Cannot accept an offer for a sold property.")

            property.selling_price = record.price
            property.buyer_id = record.partner_id
            record.status = "accepted"

            other_offers = property.offer_ids - record
            other_offers.write({"status": "refused"})

            property.state = "offer_accepted"
        return True

    def action_refuse(self):
        """رفض العرض."""
        for record in self:
            record.status = "refused"
        return True


    @api.model
    def create(self, vals_list):
        """تخصيص عملية إنشاء العرض لتحديث حالة العقار ومنع العروض المنخفضة."""
        if isinstance(vals_list, list):
            vals = vals_list[0]
        else:
            vals = vals_list

        property_id = vals.get("property_id")
        if not property_id:
            return super().create(vals_list)

        property_record = self.env["estate.property"].browse(property_id)
        existing_offers = property_record.offer_ids

        if existing_offers and vals.get("price") < max(existing_offers.mapped("price")):
            raise UserError("You cannot create an offer lower than an existing offer.")

        if property_record.state == "new":
            property_record.state = "offer_received"

        return super().create(vals_list)


    @api.constrains("price")
    def _check_offer_price(self):
        for record in self:
            if record.price <= 0:
                raise UserError("Offer price must be positive.")

            if record.price < 0.9 * record.property_id.expected_price:
                raise UserError("Offer must be at least 90% of the expected price.")

            existing_offers = record.property_id.offer_ids.filtered(lambda o: o.id != record.id)
            if existing_offers and record.price <= max(existing_offers.mapped("price")):
                raise UserError("Offer must be higher than existing offers.")
