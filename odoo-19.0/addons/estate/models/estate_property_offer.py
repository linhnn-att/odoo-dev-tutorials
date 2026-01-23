from odoo import fields, models, api


class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Real Estate Property Offer"
    _order = "price desc"

    price = fields.Float(required=True)

    status = fields.Selection(
        [
            ('accepted', 'Accepted'),
            ('refused', 'Refused'),
        ],
        copy=False
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Buyer",
        required=True
    )

    property_id = fields.Many2one(
        "estate.property",
        string="Property",
        required=True
    )

    @api.model
    def create(self, vals):
        offer = super().create(vals)
        if offer.property_id.state == 'new':
            offer.property_id.state = 'offer_received'
        return offer

    def action_accept(self):
        for offer in self:
            offer.status = 'accepted'

            other_offers = offer.property_id.offer_ids - offer
            other_offers.write({'status': 'refused'})

            offer.property_id.write({
                'state': 'offer_accepted',
                'selling_price': offer.price,
                'buyer_id': offer.partner_id.id,
            })

    def action_refuse(self):
        for offer in self:
            offer.status = 'refused'
