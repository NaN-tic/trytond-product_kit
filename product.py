# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from decimal import Decimal

from trytond.model import ModelView, ModelSQL, fields, Check, sequence_ordered
from trytond.pool import Pool, PoolMeta
from trytond.pyson import If, Eval, Bool
from trytond.i18n import gettext
from trytond.exceptions import UserError

__all__ = ['ProductKitLine', 'Product']


class ProductKitLine(sequence_ordered(), ModelSQL, ModelView):
    "Product Kit"
    __name__ = 'product.kit.line'
    parent = fields.Many2One('product.product', 'Parent Product',
        required=True, ondelete='CASCADE')
    product = fields.Many2One('product.product', 'Product', required=True,
        ondelete='CASCADE')
    product_uom_category = fields.Function(
        fields.Many2One('product.uom.category', 'Product Uom Category'),
        'on_change_with_product_uom_category')
    quantity = fields.Float('Quantity', digits=(16, Eval('unit_digits', 2)),
        required=True)
    unit = fields.Many2One('product.uom', 'Unit', required=True,
        domain=[
            If(Bool(Eval('product_uom_category')),
                ('category', '=', Eval('product_uom_category')),
                ('category', '!=', -1)),
            ],
        depends=['product', 'product_uom_category'])
    unit_digits = fields.Function(fields.Integer('Unit Digits'),
        'on_change_with_unit_digits')

    @classmethod
    def __setup__(cls):
        super(ProductKitLine, cls).__setup__()
        t = cls.__table__()
        cls._sql_constraints += [
            ('check_qty_pos', Check(t, t.quantity > 0),
                'The quantity must be bigger than 0'),
            ]

    @fields.depends('product', 'unit', 'quantity')
    def on_change_product(self):
        if not self.product:
            self.unit = None
            self.unit_digits = None
        elif not self.unit:
            self.unit = self.product.default_uom.id
            self.unit.rec_name = self.product.default_uom.rec_name
            self.unit_digits = self.product.default_uom.digits

    @fields.depends('product')
    def on_change_with_product_uom_category(self, name=None):
        if self.product:
            return self.product.default_uom_category.id

    @fields.depends('unit')
    def on_change_with_unit_digits(self, name=None):
        if self.unit:
            return self.unit.digits
        return 2

    @classmethod
    def validate(cls, kits):
        super(ProductKitLine, cls).validate(kits)
        cls.check_recursion_kits(kits)

    @classmethod
    def check_recursion_kits(cls, kits):
        def check_recursion_product(products, all_products):
            Product = Pool().get('product.product')
            if not products:
                return True
            new_products = []
            for product in Product.browse(products):
                if product.kit and product.id in all_products:
                    raise UserError(gettext('product_kit.recursive_kits'))
                elif not product.kit:
                    continue
                for line in product.kit_lines:
                    new_products.append(line.product.id)
            if new_products:
                return check_recursion_product(new_products,
                        all_products + products)
            return True

        products = []
        for kit_line in kits:
            if kit_line.product.kit:
                products += [kit_line.product.id]
        return check_recursion_product(products, [])


class Product(metaclass=PoolMeta):
    __name__ = "product.product"
    kit = fields.Boolean('Kit')
    kit_lines = fields.One2Many('product.kit.line', 'parent', 'Product kits',
        states={
            'invisible': Bool(~Eval('kit')),
            },
        depends=['kit'])
    kit_fixed_list_price = fields.Boolean('Kit Fixed List Price',
        states={
            'invisible': Bool(~Eval('kit')),
            },
        depends=['kit'],
        help='Mark this field if the list price of the kit should be fixed. '
        'Do not mark it if the price should be calculated from the sum of the '
        'prices of the products in the pack.')

    @classmethod
    def explode_kit(cls, products, quantity, unit, depth=1):
        """
        Walks through the Kit tree in depth-first order and returns
        a sorted list with all the components of the product.
        """
        uom_obj = Pool().get('product.uom')
        result = []
        for product in products:
            for line in product.kit_lines:
                qty = quantity * uom_obj.compute_qty(line.unit, line.quantity,
                        unit)
                result.append({
                        'product': line.product,
                        'quantity': qty,
                        'unit': line.unit,
                        'unit_price': Decimal('0.00'),
                        'depth': depth,
                        })
                result += cls.explode_kit([line.product], quantity,
                        line.unit, depth + 1)
        return result

    @classmethod
    def view_attributes(cls):
        return super(Product, cls).view_attributes() + [
            ('//page[@id="kit"]', 'states', {
                    'invisible': ~Eval('kit'),
                    })]
