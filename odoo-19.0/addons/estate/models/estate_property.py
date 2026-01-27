from odoo import fields, models, api
from odoo.exceptions import ValidationError, UserError
from odoo.tools import date_utils


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Real Estate Property"

    # ===== Basic fields =====
    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    description = fields.Text()
    postcode = fields.Char()

    date_availability = fields.Date(
        copy=False,
        default=lambda self: date_utils.add(fields.Date.today(), months=3)
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
            ("north", "North"),
            ("south", "South"),
            ("east", "East"),
            ("west", "West"),
        ]
    )

    # ===== Chapter 8: Computed Fields =====
    total_area = fields.Float(
        string="Total Area",
        compute="_compute_total_area"
    )

    best_price = fields.Float(
        string="Best Offer",
        compute="_compute_best_price"
    )

    # ===== State =====
    state = fields.Selection(
    [
        ("new", "New"),
        ("offer_received", "Offer Received"),
        ("offer_accepted", "Offer Accepted"),
        ("sold", "Sold"),
        ("cancelled", "Cancelled"),
    ],
    default="new",
    required=True,
    copy=False,
)

    # ===== Relations =====
    tag_ids = fields.Many2many("estate.property.tag", string="Tags")
    property_type_id = fields.Many2one("estate.property.type", string="Property Type")
    buyer_id = fields.Many2one("res.partner", string="Buyer", copy=False)
    salesperson_id = fields.Many2one(
        "res.users", string="Salesperson", default=lambda self: self.env.user
    )
    offer_ids = fields.One2many(
        "estate.property.offer", "property_id", string="Offers"
    )

    # ===== Compute =====
    @api.depends("living_area", "garden_area")
    def _compute_total_area(self):
        for record in self:
            record.total_area = (record.living_area or 0) + (record.garden_area or 0)

    @api.depends("offer_ids.price")
    def _compute_best_price(self):
        for record in self:
            record.best_price = max(record.offer_ids.mapped("price"), default=0.0)

    @api.constrains("expected_price")
    def _check_expected_price(self):
        for record in self:
            if record.expected_price <= 0:
                raise ValidationError("Expected price must be strictly positive.")

    # ===== Onchange =====
    @api.onchange("garden")
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = "north"
        else:
            self.garden_area = 0
            self.garden_orientation = False

    # ===== Chapter 9: Actions =====
    def action_sold(self):
        for record in self:
            if record.state == "cancelled":
                raise UserError("A cancelled property cannot be sold.")
            record.state = "sold"

    def action_cancel(self):
        for record in self:
            if record.state == "sold":
                raise UserError("A sold property cannot be cancelled.")
            record.state = "cancelled"
