# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from osv import fields, osv
from tools.translate import _
class many2many_filter(osv.osv_memory):
    _name = "many2many.filter"
    _description = "Many2Many filter"
    _rec_name = "product_ids_filter"
    _columns = {
       'product_ids_filter' : fields.many2many('product.product','wizard_product_rel','wizard_id','product_id','Products to be list'),
    }
    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                       context=None, toolbar=False, submenu=False):
       """
        Changes the view dynamically
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param context: A standard dictionary
        @return: New arch of view.
       """
       res = super(many2many_filter, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
       product_ids = []
       if context is None:
           context={}
       if context.get('active_model', False):
           if context['active_model'] == 'product.listing.templates':
                product_listing_id = context['active_ids']
                shop_id_val = self.pool.get('product.listing.templates').browse(cr,uid,product_listing_id[0]).shop_id.id
                one_many_true = self.pool.get('product.product').search(cr,uid,[('prods_list','=',False),('exported_to_ebay','=',True),('type','!=','service')])
                for each_product in one_many_true:
                        product_ids.append(each_product)
                one_many = self.pool.get('product.product').search(cr,uid,[('prods_list','!=',False),('exported_to_ebay','=',True)])
                for each_product in one_many:
                    cr.execute('Select shop_id from product_listing where prod_list = %s',(each_product,))
                    shop_id = filter(None, map(lambda x:x[0], cr.fetchall()))
                    if shop_id_val not in shop_id:
                        product_ids.append(each_product)
       res['fields']['product_ids_filter']['domain'] = [('id', 'in', product_ids)]
       return res
    def default_get(self, cr, uid, fields, context=None):
        res = super(many2many_filter, self).default_get(cr, uid, fields, context=context)
        picking_ids = []
        if context is None:
            context = {}
        if context.get('active_model', False):
                picking_ids = context.get('active_ids', [])
        return  res
    
    def confirm_button(self, cr, uid, ids, context=None):
        """
        This function Makes partner based on action.
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user ID for security checks,
        @param ids: List of Lead to Partner's IDs
        @param context: A standard dictionary for contextual values

        @return : Dictionary value for created Partner form.
        """
        if context is None:
            context = {}
        product_ids = []
        active_ids = context['active_ids']
        product_ids_filter =  self.browse(cr,uid,ids[0]).product_ids_filter
        for each_id in product_ids_filter:
            product_id = each_id.id
            product_ids.append(product_id)
        if product_ids:
            write = self.pool.get('product.listing.templates').write(cr,uid,active_ids[0],{'product_ids':[(6,0,product_ids)]})
        return {'type': 'ir.actions.act_window_close'}
many2many_filter()