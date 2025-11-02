from odoo import api, fields, models
from datetime import timedelta, date
from odoo.exceptions import UserError, ValidationError

class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Estate Property"
    _order = "id desc"

 
    name = fields.Char(required=True)
    description = fields.Text()
    postcode = fields.Char()
    date_availability = fields.Date(
        copy=False,
        default=lambda self: date.today() + timedelta(days=90)
    )
    expected_price = fields.Float(required=True)
    selling_price = fields.Float(readonly=True, copy=False)

    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer()
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    garden_orientation = fields.Selection(
        [
            ('north', 'North'),
            ('south', 'South'),
            ('east', 'East'),
            ('west', 'West'),
        ],
        string="Garden Orientation"
    )
    total_area = fields.Float(compute="_compute_total_area")


    @api.onchange("garden")
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = "north"
        else:
            self.garden_area = 0
            self.garden_orientation = False

  
    property_type_id = fields.Many2one(
        "estate.property.type",
        string="Property Type"
    )
    tag_ids = fields.Many2many(
        "estate.property.tag",
        string="Tags"
    )
    offer_ids = fields.One2many(
        "estate.property.offer",
        "property_id",
        string="Offers"
    )

 
    buyer_id = fields.Many2one(
        "res.partner",
        string="Buyer",
        copy=False
    )
    salesperson_id = fields.Many2one(
        "res.users",
        string="Salesperson",
        default=lambda self: self.env.user
    )
    best_price = fields.Float(
        string="Best Offer",
        compute="_compute_best_price"
    )


    active = fields.Boolean(default=True)
    state = fields.Selection(
        [
            ('new', 'New'),
            ('offer_received', 'Offer Received'),
            ('offer_accepted', 'Offer Accepted'),
            ('sold', 'Sold'),
            ('canceled', 'Canceled'),
        ],
        required=True,
        copy=False,
        default='new'
    )



    def unlink(self):
        for rec in self:
            if rec.state not in ("new", "canceled"):
                raise UserError("Only new or canceled properties can be deleted.")
        return super().unlink()

    @api.depends("living_area", "garden_area")
    def _compute_total_area(self):
        """Compute total area as sum of living + garden area"""
        for record in self:
            record.total_area = (record.living_area or 0) + (record.garden_area or 0)

    @api.depends("offer_ids.price")
    def _compute_best_price(self):
        """Compute the highest offer price"""
        for record in self:
            if record.offer_ids:
                record.best_price = max(record.offer_ids.mapped("price"))
            else:
                record.best_price = 0.0

    def action_sold(self):
        for record in self:
            if record.state == "canceled":
                raise UserError("Canceled properties cannot be sold.")
            record.state = "sold"
        return True

    def action_cancel(self):
        for record in self:
            if record.state == "sold":
                raise UserError("Sold properties cannot be canceled.")
            record.state = "canceled"
        return True
    

    @api.constrains("name", "expected_price", "selling_price")
    def _check_property_constraints(self):
        for record in self:
            if record.expected_price <= 0:
                raise ValidationError("Expected price must be strictly positive.")

            if record.selling_price < 0:
                raise ValidationError("Selling price cannot be negative.")

            if (
                record.selling_price
                and record.selling_price < 0.9 * record.expected_price
            ):
                raise ValidationError(
                    "Selling price cannot be lower than 90% of the expected price."
                )

            if not record.name or len(record.name.strip()) < 3:
                raise ValidationError("Property name must have at least 3 characters.")

            existing = self.search(
                [
                    ("name", "=", record.name.strip()),
                    ("id", "!=", record.id),
                ],
                limit=1,
            )
            if existing:
                raise ValidationError("Property name must be unique.")


    _sql_constraints = [
        (
            "check_expected_price_positive",
            "CHECK(expected_price > 0)",
            "Expected price must be positive.",
        ),
        (
            "check_selling_price_positive",
            "CHECK(selling_price >= 0)",
            "Selling price cannot be negative.",
        ),
        (
            "unique_property_name",
            "UNIQUE(name)",
            "The property name must be unique.",
        ),
    ]



