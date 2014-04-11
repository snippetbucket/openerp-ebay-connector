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
class catalog_enabled(osv.osv):
    _name = "catalog.enabled"
    _description = "Catalog Enabled categories"
    _columns = {
        'name': fields.char('QueryWord', size=256),
        'sequence': fields.integer('Sequence'),
        'search_query': fields.selection([('UPC','UPC'),('Brand','Brand/Model')],'Search By',required=True),
        'search_products_id': fields.one2many('search.products.output','product_ids','Searched Products',readonly=True),
    }
    def onchange_search_query(self,cr,uid,ids,search_by):
        result={}
        if search_by:
            result['sequence'] = 0
            result['name'] = 0
        return {'value':result}
    def accept_product(self,cr,uid,ids,context=None):
        if ids:
            sequence = self.browse(cr,uid,ids[0]).sequence
            one2many = self.browse(cr,uid,ids[0]).search_products_id
            if not one2many:
                self.log(cr,uid,ids[0],'First Search Products')
                return
            sequence = self.pool.get('search.products.output').search(cr,uid,[('sequence','=',sequence)])
            if sequence:
                details_url = self.pool.get('search.products.output').browse(cr,uid,sequence[0]).details_url
                product_reference_id =self.pool.get('search.products.output').browse(cr,uid,sequence[0]).product_reference_id
                print"product_reference_id",product_reference_id
                stock_photo_url = self.pool.get('search.products.output').browse(cr,uid,sequence[0]).stock_photo_url
                if stock_photo_url == False:
                    stock_photo_url = 'NULL'
                active_ids = context.get('active_ids')
                if active_ids:
                    cat1 = self.pool.get('product.product').browse(cr,uid,active_ids[0]).cat1
                    if cat1:
                        catalog_enabled_cat1 = cat1.catlog_enabled
                    cat2 = self.pool.get('product.product').browse(cr,uid,active_ids[0]).cat2
                    if cat2:
                        catalog_enabled_cat2 = cat2.catlog_enabled
                    if catalog_enabled_cat1 == True:
                        category_name = 'category1'
                    elif catalog_enabled_cat2 == True:
                        category_name = 'category2'
                    cr.execute("UPDATE product_product SET details_url='%s',product_reference_id='%s',category_name='%s',stock_photo_url='%s' where id=%d"%(details_url,product_reference_id,category_name,stock_photo_url,active_ids[0],))
                    cr.commit()
                cr.execute('delete from search_products_output')
                cr.execute('delete from catalog_enabled')
                return {'type': 'ir.actions.act_window_close'}
            else:
                self.log(cr,uid,ids[0],'Please Check the Sequence Number')

    def search_products(self,cr,uid,ids,context=None):
        if ids:
            attribute_set_id = ''
            catalog_enabled_cat1 = ''
            catalog_enabled_cat2 = ''
            siteid = ''
            active_ids = context.get('active_ids',False)
            increment = 0
            query_keyword = self.browse(cr,uid,ids[0]).name
            one2many = self.browse(cr,uid,ids[0]).search_products_id
            for each_val in one2many:
                self.pool.get('search.products.output').unlink(cr,uid,[each_val.id])
            if not query_keyword:
                self.log(cr,uid,ids[0],'Please Enter Query Keyword')
                return True
            if active_ids:
                search_ebay_true = self.pool.get('sale.shop').search(cr,uid,[('ebay_shop','=','TRUE')])
                if search_ebay_true:
                    inst_lnk = self.pool.get('sale.shop').browse(cr,uid,search_ebay_true[0]).instance_id
                    site_id = self.pool.get('sale.shop').browse(cr,uid,search_ebay_true[0]).site_id
                    shop_name = self.pool.get('sale.shop').browse(cr,uid,search_ebay_true[0]).name
                    if site_id:
                        siteid = site_id.site_id
                    else:
                        raise osv.except_osv(_('Warning !'), _("Please Select Site ID in %s shop")%(shop_name))
                    
                cat1 = self.pool.get('product.product').browse(cr,uid,active_ids[0]).cat1
                if cat1:
                    catalog_enabled_cat1 = cat1.catlog_enabled
                else:
                    self.log(cr,uid,ids[0],'Please Enter the Category1')
                    return
                cat2 = self.pool.get('product.product').browse(cr,uid,active_ids[0]).cat2
                if cat2:
                    catalog_enabled_cat2 = cat2.catlog_enabled
                if catalog_enabled_cat1 == True:
                    attribute_set_id = cat1.attribute_set_id
                elif catalog_enabled_cat2 == True:
                    attribute_set_id = cat2.attribute_set_id
                search_by = self.browse(cr,uid,ids[0]).search_query
                if inst_lnk:
                    pageNumber = 1
                    resultFinal = []
                    if attribute_set_id:
                        results = self.pool.get('sale.shop').call(cr, uid, inst_lnk, 'GetProducts',attribute_set_id,search_by,query_keyword,pageNumber,siteid)
                    if results.get('Ack',False) == 'Success':
                        while True:
                            results = self.pool.get('sale.shop').call(cr, uid, inst_lnk, 'GetProducts',attribute_set_id,search_by,query_keyword,pageNumber,siteid)
                            resultFinal = resultFinal + results.get('Product',False)
                            if results.get('HasMore',False) == 'false':
                                break
                            pageNumber = pageNumber + 1
                            if pageNumber == 5:
                                break
                    else:
                        if results.get('LongMessage',False):
                           long_message = results['LongMessage']
                           for each_messsge in long_message:
                               severity_code = each_messsge[0]['SeverityCode']
                               if severity_code == 'Error':
                                   Longmessage = each_messsge[0]['LongMessage']
                                   product_long_message =  Longmessage
                                   increment += 1
                                   self.log(cr, uid,increment, product_long_message)
                    if resultFinal:
                        i = 1
                        for each_result in resultFinal:
                            product_reference_id = each_result.get('ProductReferenceID',False)
                            details_url = each_result.get('DetailsURL',False)
                            title = each_result.get('Title',False)
                            stock_photo_url = each_result.get('StockPhotoURL',False)
                            vals = {
                            'name': title,
                            'product_reference_id':product_reference_id,
                            'details_url':details_url,
                            'product_ids':ids[0],
                            'sequence':i,
                            'stock_photo_url':stock_photo_url
                            }
                            self.pool.get('search.products.output').create(cr,uid,vals,context=None)
                            i=i+1
        return True
catalog_enabled()
class search_products_output(osv.osv):
    _name = "search.products.output"
    _columns = {
        'name': fields.char('Title', size=256),
        'product_reference_id': fields.char('Product Reference ID', size=256),
        'details_url': fields.text('Details URL'),
        'product_ids':fields.many2one('catalog.enabled','Catalog enabled'),
        'sequence':fields.char('Sequence', size=256),
        'stock_photo_url':fields.text('Stock Photo URL')
    }
search_products_output()