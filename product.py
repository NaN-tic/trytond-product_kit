#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this :repository contains the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, Bool
from trytond.transaction import Transaction
from trytond.pool import Pool

class ProductKitLine(ModelSQL, ModelView):
    '''Product Kit'''
    _name = 'product.kit.line'
    _description = __doc__

    parent = fields.Many2One('product.product', 'Parent Product', required=True,
            ondelete='CASCADE')
    product = fields.Many2One('product.product', 'Product', required=True,
            domain=[
                ('id', '!=', Eval('parent_parent')),
            ],
            ondelete='CASCADE')
    sequence = fields.Integer('sequence')
    quantity = fields.Float('Quantity', digits=(16, Eval('unit_digits', 2)),
            required=True, depends=['unit_digits'])
    unit = fields.Many2One('product.uom', 'Unit', required=True,
            domain=[
                ('category', '=',
                (Eval('product'), 'product.default_uom.category')),
            ],
            context={
                'category': (Eval('product'), 'product.default_uom.category'),
            },
            on_change_with=['product'],
            depends=['product'])
    unit_digits = fields.Function(fields.Integer('Unit Digits',
            on_change_with=['unit']), 'get_unit_digits')

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
            return product.sale_uom.id

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
            ('check_recursion', 'recursive_categories'),
        ]
        self._error_messages.update({
            'recursive_categories': 'You can not create recursive categories!',
        })

    def check_recursion(self, ids):
        '''
        Function that checks if there is no recursion in the tree
        :return: True or False
        '''
        return True

        records = self.browse(ids)
        visited = set()

        for record in records:
            walked = set()
            walker = record.parent
            while walker:
                if walker.id == record.product:
                    return False
                walked.add(walker.id)
                walker = walker.parent not in visited and walker.parent
            visited.update(walked)

        return True

    # TODO: Check infinite recursion

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
    #list_price = fields.Function(fields.Numeric('List Price', states=STATES,
    #        digits=(16, 4), depends=DEPENDS), 'get_list_price')
    #list_price = fields.Property(fields.Numeric('List Price', states=STATES,
    #            digits=(16, 4), depends=DEPENDS))
    #list_price_uom = fields.Function(fields.Numeric('List Price',
    #        digits=(16, 4)), 'get_price_uom')
    #def get_list_price(self, ids, name):

    def explode_kit(self, product_id, quantity, unit, depth=1):
        """
        Walks through the Kit tree in depth-first order and returns
        a sorted list with all the components of the product.
        """
        if depth == 10:
            return

        result = []
        for line in self.browse(product_id).kit_lines:
            # TODO: Calculate unit_price. Is this the appropriate place?
            result.append({
                    'product_id': line.product.id,
                    # TODO: Take into account unit of measure
                    'quantity': line.quantity * quantity,
                    'unit': line.unit.id,
                    #'unit_price': Decimal('0.00'),
                    'depth': depth,
                    })
            result += self.explode_kit(line.product.id, line.quantity, line.unit, depth+1)
        return result

Product()
