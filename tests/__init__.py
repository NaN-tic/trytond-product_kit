# This file is part product_kit module for Tryton.  The COPYRIGHT file at the
# top level of this repository contains the full copyright notices and license
# terms.
try:
    from trytond.modules.product_kit.tests.test_product_kit import suite
except ImportError:
    from .test_product_kit import suite

__all__ = ['suite']
