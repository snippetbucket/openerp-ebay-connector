  # -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Bista Solutions (www.bistasolutions.com). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from osv import fields, osv
from tools.translate import _
class create_ebay_shop(osv.osv_memory):
    _name = "create.ebay.shop"
    _description = "Create Ebay Shop"
    def view_init(self, cr, uid, fields_list, context=None):
        if context is None:
            context = {}
        res = super(create_ebay_shop, self).view_init(cr, uid, fields_list, context=context)
        active_ids = context.get('active_ids',[])
        if active_ids:
            search_shop = self.pool.get('sale.shop').search(cr,uid,[('instance_id','=',active_ids[0])])
            if search_shop:
                raise osv.except_osv(_('Warning !'), _('Shop Is Already Created'))
        return res
    def create_ebay_shop_action(self, cr, uid, ids, context=None):
        data_ebay_shop = self.read(cr, uid, ids, context=context)[0]
        shop_vals = {
            'name' : data_ebay_shop.get('name',False),
            'warehouse_id' : data_ebay_shop.get('warehouse_id',False),
#            'cust_address' : data_ebay_shop.get('cust_address',False),
            'company_id' : data_ebay_shop.get('company_id',False),
            'instance_id' : context.get('active_id') and context['active_id'] or False,
            'ebay_shop' : True,
            'pay_mthd':data_ebay_shop.get('pay_mthd',False),
            'email_add':data_ebay_shop.get('email_add',False),
            'post_code':data_ebay_shop.get('post_code',False),
            'site_id': data_ebay_shop.get('site_id',False),
        }
        ebay_shop_id = self.pool.get('sale.shop').create(cr,uid,shop_vals,context)
        if ebay_shop_id:
            message = _('%s Shop Successfully Created!')%(data_ebay_shop['name'])
            self.pool.get('sale.shop').log(cr, uid, ebay_shop_id, message)
            return {'type': 'ir.actions.act_window_close'}
        else:
            message = _('Error creating ebay shop')
            self.log(cr, uid, ids[0], message)
            return False

    _columns = {
        'name': fields.char('Shop Name', size=64, required=True),
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse',required=True),
#        'cust_address': fields.many2one('res.partner.address', 'Address', required=True),
        'company_id': fields.many2one('res.company', 'Company', required=False),
        'pay_mthd': fields.selection([('PayPal', 'PayPal')],'Payment Methods',required=True),
        'email_add' : fields.char('Email', size=126,required=True),
        'post_code':fields.char('Postal Code',size=64,help="Enter the Postal Code for Item Location",required=True),
        'site_id' : fields.many2one('site.details','Site',required=True),
    }
    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'sale.shop', context=c),
    }
create_ebay_shop()
