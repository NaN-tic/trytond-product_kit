#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this :repository contains the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, Bool
from trytond.pool import Pool
from decimal import Decimal

class ProductKitLine(ModelSQL, ModelView):
    '''Product Kit'''
    _name = 'product.kit.line'
    _description = __doc__

    parent = fields.Many2One('product.product', 'Parent Product', required=True,
            ondelete='CASCADE')
    product = fields.Many2One('product.product', 'Product', required=True,
#            domain=[
#                ('id', '!=', Eval('parent_parent')),
#            ],
            ondelete='CASCADE')
    product_uom_category = fields.Function(
        fields.Many2One('product.uom.category', 'Product Uom Category',
            on_change_with=['product']),
        'get_product_uom_category')
    
    sequence = fields.Integer('sequence')
    quantity = fields.Float('Quantity', digits=(16, Eval('unit_digits', 2)),
            required=True, depends=['unit_digits'])
    unit = fields.Many2One('product.uom', 'Unit', required=True,
            domain=[
                ('category', '=', Eval('product_uom_category')),
            ],
            context={
                'category': (Eval('product'), 'product.default_uom.category'),
            },
            on_change_with=['product'],
            depends=['product', 'product_uom_category'])
    unit_digits = fields.Function(fields.Integer('Unit Digits',
            on_change_with=['unit']), 'get_unit_digits')

    def on_change_with_product_uom_category(self, vals):
        product_obj = Pool().get('product.product')
        if vals.get('product'):
            product = product_obj.browse(vals['product'])
            return product.default_uom_category.id

    def get_product_uom_category(self, ids, name):
        categories = {}
        for line in self.browse(ids):
            categories[line.id] = line.product.default_uom_category.id
        return categories

    def get_unit_digits(self, ids, name):
        res = {}
        for line in self.browse(ids):
            if line.unit:
                res[line.id] = line.unit.digits
            else:
                res[line.id] = 2
        return res

    def on_change_with_unit(self, vals):
        product_obj = Pool().get('product.product')
        if vals.get('product'):
            product = product_obj.browse(vals['product'])
            return product.default_uom.id

    def on_change_with_unit_digits(self, vals):
        uom_obj = Pool().get('product.uom')
        if vals.get('unit'):
            uom = uom_obj.browse(vals['unit'])
            return uom.digits
        return 2

    def __init__(self):
        super(ProductKitLine, self).__init__()
        self._order.insert(0, ('sequence', 'ASC'))

        self._constraints += [
            ('check_recursion', 'recursive_kits'),
        ]
        self._error_messages.update({
            'recursive_kits': 'You can not create recursive kits!',
        })

    def check_recursion(self, ids, parent='parent'):

        def check_recursion_product(products, all_products):
            product_obj = Pool().get('product.product')

            if not products:
                return True
            
            new_products =[]
            for product in product_obj.browse(products):
                if product.kit and product.id in all_products:
                    return False
                elif not product.kit:
                    continue                    
                new_products.append(product.id)

            if new_products:
                return check_recursion_product(new_products,
                        all_products + products)

            return True

        products=[]
        for kit_line in self.browse(ids):
            if kit_line.product.kit:
                products += [ kit_line.product.id]

        return check_recursion_product( products, products )

ProductKitLine()

STATES = {
    'readonly': ~Eval('active', True),
}
DEPENDS = ['active']

class Product(ModelSQL, ModelView):
    _name = "product.product"

    kit = fields.Boolean('Kit?')
    kit_lines = fields.One2Many('product.kit.line', 'parent', 
            'Components', states={
                    'readonly': Bool(~Eval('kit')),
                    }, depends=['kit'])
    kit_fixed_list_price = fields.Boolean('Fixed List Price', help='Mark this '
            'field if the list price of the kit should be fixed. Do not mark '
            'it if the price should be calculated from the sum of the prices '
            'of the products in the pack.'),


    def explode_kit(self, product_id, quantity, unit, depth=1):
        """
        Walks through the Kit tree in depth-first order and returns
        a sorted list with all the components of the product.
        """
        uom_obj = Pool().get('product.uom')
        result = []
        for line in self.browse(product_id).kit_lines:
            qty = quantity * uom_obj.compute_qty(line.unit, line.quantity, unit)
            result.append({
                    'product_id': line.product.id,
                    'quantity': qty,
                    'unit': line.unit.id,
                    'unit_price': Decimal('0.00'),
                    'depth': depth,
                    })
            result += self.explode_kit(line.product.id, quantity,
                    line.unit, depth+1)
        return result

Product()
