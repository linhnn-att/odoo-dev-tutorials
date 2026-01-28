from odoo import fields, models, api
from datetime import timedelta
from odoo.exceptions import UserError


class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Real Estate Property Offer"
    _order = "price desc"
    _sql_constraints = [
        (
            "check_offer_price_positive",
            "CHECK(price > 0)",
            "Offer price must be strictly positive.",
        ),
    ]

    # ===== Basic fields =====
    price = fields.Float(required=True)

    status = fields.Selection(
        [
            ("accepted", "Accepted"),
            ("refused", "Refused"),
        ],
        copy=False,
    )

    partner_id = fields.Many2one("res.partner", string="Buyer", required=True)

    property_id = fields.Many2one(
        "estate.property", string="Property", required=True, ondelete="cascade"
    )

    # ===== Chapter 8 =====
    validity = fields.Integer(string="Validity (days)", default=7)

    date_deadline = fields.Date(
        string="Deadline",
        compute="_compute_date_deadline",
        inverse="_inverse_date_deadline",
        store=True,
    )

    # ===== Compute =====
    @api.depends("create_date", "validity")
    def _compute_date_deadline(self):
        for record in self:
            if record.create_date:
                record.date_deadline = record.create_date.date() + timedelta(
                    days=record.validity
                )
            else:
                record.date_deadline = fields.Date.today() + timedelta(
                    days=record.validity
                )

    # ===== Inverse =====
    def _inverse_date_deadline(self):
        for record in self:
            if record.create_date and record.date_deadline:
                record.validity = (
                    record.date_deadline - record.create_date.date()
                ).days

    # ===== ORM Override =====
    @api.model
    def create(self, vals):
        offer = super().create(vals)
        if offer.property_id.state == "new":
            offer.property_id.state = "offer_received"
        return offer

    # ===== Business Actions (Chapter 9) =====
    def action_accept(self):
        for offer in self:
            if offer.status:
                raise UserError("This offer has already been processed.")

            offer.status = "accepted"

            # từ chối các offer khác
            other_offers = offer.property_id.offer_ids - offer
            other_offers.write({"status": "refused"})

            # cập nhật property
            offer.property_id.write(
                {
                    "state": "offer_accepted",
                    "selling_price": offer.price,
                    "buyer_id": offer.partner_id.id,
                }
            )

    def action_refuse(self):
        for offer in self:
            if offer.status:
                raise UserError("This offer has already been processed.")
            offer.status = "refused"

    def action_sold(self):
        for record in self:
            if record.state == "canceled":
                raise UserError("Canceled property cannot be sold.")
        record.state = "sold"

    def action_cancel(self):
        for record in self:
            if record.state == "sold":
                raise UserError("Sold property cannot be canceled.")
        record.state = "canceled"
