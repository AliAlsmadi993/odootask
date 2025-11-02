from odoo import api, fields, models

class PropertyType(models.Model):
    _name = "estate.property.type"
    _description = "Real Estate Property Type"
    _order = "sequence, name"

   
    name = fields.Char(string="Name", required=True)
    sequence = fields.Integer(string="Sequence", default=1)

   
    property_ids = fields.One2many(
        "estate.property",
        "property_type_id",
        string="Properties"
    )

    offer_ids = fields.One2many(
        "estate.property.offer",
        "property_type_id",
        string="Offers"
    )



    offer_count = fields.Integer(
        string="Offer Count",
        compute="_compute_offer_count",
        store=False
    )

    has_offers = fields.Boolean(
        string="Has Offers",
        compute="_compute_has_offers",
        store=False
    )

 
    @api.depends("offer_ids")
    def _compute_offer_count(self):
        """Compute how many offers are linked to this property type."""
        Offer = self.env["estate.property.offer"]
        for record in self:
            record.offer_count = Offer.search_count([
                ("property_type_id", "=", record.id)
            ])

    @api.depends("offer_ids")
    def _compute_has_offers(self):
        """Boolean helper to hide the stat button if there are no offers."""
        for record in self:
            record.has_offers = bool(record.offer_ids)


    def action_view_offers(self):
        """Open only offers related to this property type"""
        self.ensure_one()
        return {
        'type': 'ir.actions.act_window',
        'name': 'Offers',
        'res_model': 'estate.property.offer',
        'view_mode': 'list,form',
        'domain': [('property_type_id', '=', self.id)],
        'context': {'default_property_type_id': self.id},
    }

  