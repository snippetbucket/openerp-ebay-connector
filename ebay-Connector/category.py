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
from osv import osv, fields
import ebayerp_osv
import time
import pytz,datetime
from pytz import timezone
from datetime import date, timedelta, datetime
import libxml2
from tools.translate import _
import uuid
from operator import itemgetter
from itertools import groupby
import netsvc
logger = netsvc.Logger()
from time import gmtime, strftime
import urllib
from xml.dom.minidom import parse, parseString
##########global function for checking special characters#################
def check(string):
   import re
   pattern = r'[a-z0-9A-Z]'
   for each_string in string:
       if each_string != ' ':
            if re.search(pattern, each_string):
               print"valid string",each_string
            else:
               string = string.replace(each_string,'')
   string = string.replace(' ','')       
   return string
####################################Shipping Details#######################################
class shipping_master(osv.osv):
    _name = "shipping.master"
    _columns = {
        'name' : fields.char('Shipping Description', size=64),
        'ship_type': fields.char('Shipping Type', size=64),
        'ship_type1': fields.char('Shipping Type', size=64),
        'ship_time': fields.char('Shipping time', size=64),
        'ship_car': fields.char('Shipping Carrier', size=64),
        'ship_ser': fields.char('Shipping Service', size=64),
        'inter_ship':fields.boolean('International shipping',readonly=True),
        'cost' : fields.char('Cost($)', size=20),
        'each_add' : fields.char('Each Additional($)', size=20),
        'surch_chk' :fields.boolean('Surcharge Applicable',readonly=True),
        'dimension_chk' :fields.boolean('Dimensions Required',readonly=True),
    }
shipping_master()
class site_details(osv.osv):
    _name = "site.details"
    _columns = {
    'name': fields.char('Site Name',size=256),
    'site_id': fields.char('Site ID',size=256),
    }
site_details()
class loc_master(osv.osv):
    _name = "loc.master"
    _columns = {
        'name' : fields.char('Location Name', size=64),
        'loc_code' : fields.char('Location Code', size=64),
        'region' : fields.char('Region', size=64),
    }
loc_master()
class ship_loc_master(osv.osv):
    _name = "ship.loc.master"
    _columns = {
        'name' : fields.char('Shipping Location', size=64),
        'ship_code' : fields.char('Location Code', size=64),
    }
ship_loc_master()
############################################################################
class duration_time(osv.osv):
    _name = "duration.time"
    _columns = {
    'name': fields.char('Duration',size=64),
    'type': fields.selection([('Chinese','Auction'),('FixedPriceItem','Fixed Price'),('LeadGeneration','Classified Ad')],'Type'),
    }
duration_time()
#############################################################################
class ebayerp_instance(osv.osv):
    _name = 'ebayerp.instance'

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if not context:
            context = {}
        #ctx_view_id = context.get('default_view_id', False)
        #if ctx_view_id:
        #    mod_obj = self.pool.get('ir.model.data')
        #    model,view_id = mod_obj.get_object_reference(cr, uid, 'engineer', ctx_view_id)
        print ">>>>>>>>>>>>>>>>>>>>>>.", context, view_type, view_id
        result = super(ebayerp_instance, self).fields_view_get(cr, uid, view_id, view_type, context=context, toolbar=toolbar, submenu=submenu)
        return result
            

    def openerpFormatDate(self, srcDate):
        print"srcDate",srcDate
        srcDate = time.strptime(srcDate, "%Y-%m-%dT%H:%M:%S.000Z")
        srcDate = time.strftime("%Y-%m-%d %H:%M:%S",srcDate)
        return srcDate
    def ebay_oe_status(self, cr, uid, order_id, paid=True, context = None, defaults = None):
        saleorder_obj = self.pool.get('sale.order')
        order = saleorder_obj.browse(cr, uid, order_id, context)
        if order.ext_payment_method:
            payment_settings = saleorder_obj.payment_code_to_payment_settings(cr, uid, order.ext_payment_method, context)
            wf_service = netsvc.LocalService("workflow")
            if payment_settings:
                if payment_settings.order_policy == 'prepaid':
                    cr.execute("UPDATE sale_order SET order_policy='prepaid' where id=%d"%(order_id,))
                    cr.commit()
                    ### Confirm Sales Order
                    if payment_settings.validate_order:
                        try:
                            wf_service.trg_validate(uid, 'sale.order', order_id, 'order_confirm', cr)
                        except Exception, e:
                            self.log(cr, uid, order_id, "ERROR could not valid order")
                    ### Validate Invoice and mark it as paid
                    if payment_settings.validate_invoice:
                        print order.invoice_ids
                        for invoice in order.invoice_ids:
                            wf_service.trg_validate(uid, 'account.invoice', invoice.id, 'invoice_open', cr)
                            if payment_settings.is_auto_reconcile and paid:
                                self.pool.get('account.invoice').invoice_pay_customer(cr, uid, [invoice.id], context=context)
        return True
    def updatePartnerAddress(self, cr, uid, id, resultvals, part_id, context={}):
        if not part_id:
            return False
        address_id = self.pool.get('res.partner.address').search(cr,uid, [('ebay_address_id','=',resultvals.get('AddressID',False))])
        if not address_id:
            if resultvals.get('AddressUsage',False) != 'Invalid':
                country_id = self.pool.get('res.country').search(cr,uid,[('name','=',resultvals.get('CountryName',False))])
                if not country_id:
                    country_id = self.pool.get('res.country').search(cr,uid,[('code','=',resultvals['CountryName'][:2].upper())])
                    if not country_id:
                        country_id = self.pool.get('res.country').create(cr,uid,{'code':resultvals['CountryName'][:2], 'name':resultvals['CountryName']})
                    else:
                        country_id = country_id[0]
                else:
                    country_id = country_id[0]
                state_id = self.pool.get('res.country.state').search(cr,uid,[('name','=',resultvals['StateOrProvince'])])
                if not state_id:
                    state_id = self.pool.get('res.country.state').create(cr,uid,{'country_id':country_id, 'name':resultvals['StateOrProvince'], 'code':resultvals['StateOrProvince'][:3]})
                else:
                    state_id = state_id[0]
                email  = ''
                if resultvals['Email'] != 'Invalid Request':
                    email = resultvals.get('Email',False)
                addressvals = {
                    'name' : resultvals.get('Name',False) or '',
                    'street' : resultvals.get('Street1',False) or '',
                    'city' : resultvals.get('CityName',False) or '',
                    'street' : resultvals.get('Street1',False) or '',
                    'country_id' : country_id,
                    'phone' : resultvals.get('Phone',False) and resultvals['Phone'] or False,
                    'zip' : resultvals.get('PostalCode',False),
                    'state_id' : state_id,
                    'email' : email,
                    'partner_id' : part_id,
                    'type' : 'default',
                    'ebay_address_id' : resultvals.get('AddressID',False),
                }
                address_id = self.pool.get('res.partner.address').create(cr,uid,addressvals)
            else:
                return False
        else:
            address_id = address_id[0]
        return address_id

    def updatePartner(self, cr, uid, id, shop_id, resultvals, part_id=0, context={}):
        partner_id = False
        partnervals = {
            'customer' : True,
            'name' : resultvals.get('Name',False),
            'ebay_reg_date' : self.openerpFormatDate(resultvals['RegistrationDate']),
            'ebay_user_id' : resultvals.get('UserID',False),
            'ebay_eias_token' : resultvals.get('EIASToken',False),
            'ebay_user_id_last_changed' : self.openerpFormatDate(resultvals['UserIDLastChanged']),
            'ebay_user_emaid_id' : resultvals.get('Email',False),
            'ebay_shop_ids' : [(6,0,[shop_id])]
        }
        if part_id == 0:
            partner_id = self.pool.get('res.partner').create(cr,uid, partnervals)
        else:
            self.pool.get('res.partner').write(cr,uid, part_id, partnervals)
            partner_id = part_id
        return partner_id

    def updateProduct(self, cr, uid, id, product_id,shop_id, item_id, custom_label=False, results=False, context={}):
        shop_obj = self.pool.get('sale.shop')
        ebayerp_manage_template = self.pool.get('ebayerp.manage')
        if not results:
            results = ebayerp_manage_template.import_product(cr,uid,[shop_id],item_id)#to call import_product function which is in template.py
        else:
            results = [results]
        prodcateg_obj = self.pool.get('product.category')
        prodtemp_obj = self.pool.get('product.template')
        prod_obj = self.pool.get('product.product')
        for result in results:
            if result.get('CategoryName',False):
                categories = result.get('CategoryName',False).split(':')
                categ_id = False
                for i in range(len(categories)):
                    categ_id = prodcateg_obj.search(cr,uid,[('name','=',categories[i])])
                    if not categ_id:
                        if i == 0:
                            categ_id = prodcateg_obj.create(cr,uid,{'name':categories[i]})
                        else:
                            parent_categ_id = prodcateg_obj.search(cr,uid,[('name','=',categories[i-1])])
                            categ_id = prodcateg_obj.create(cr,uid,{'name':categories[i],'parent_id':parent_categ_id[0]})
                    else:
                        categ_id = categ_id[0]
            weight = 0.0
            weight_major = result.get('ShippingDetails',[0,'lbs']) and result['ShippingDetails'].get('WeightMajor',[0,'lbs']) and result['ShippingDetails']['WeightMajor'].split(':') or [0,'lbs']
            if weight_major[1] == 'oz':
                    weight += float(weight_major[0]) * 0.0625
            else:
                    weight += float(weight_major[0])

            weight_minor =  result.get('ShippingDetails',[0,'lbs']) and result['ShippingDetails'].get('WeightMinor',[0,'lbs']) and result['ShippingDetails']['WeightMinor'].split(':') or [0,'lbs']
            if weight_minor[1] == 'oz':
                weight += float(weight_minor[0]) * 0.0625
            else:
                weight += float(weight_minor[0])
            template_vals = {
                    'list_price' : result.get('ConvertedStartPrice',False),
                    'purchase_ok' : 'TRUE',
                    'sale_ok' : 'TRUE',
                    'name' : result.get('Title',False),
                    'type' : 'consu',
                    'procure_method' : 'make_to_stock',
                    'cost_method' : 'standard',
                    'categ_id' : categ_id,
                    'weight_net' : weight
                }
            template_search = prod_obj.browse(cr,uid,product_id).product_tmpl_id
            if template_search:
                template_id = prodtemp_obj.write(cr,uid,template_search.id,template_vals)
            template_id = prod_obj.write(cr,uid,product_id,{
                    'ebay_sku' :  result.get('SKU',False) or '',
                    'product_tmpl_id' : template_search.id,
                    'exported_to_ebay': True,
                })
            return product_id

    def createProduct(self, cr, uid, id, shop_id, item_id, custom_label=False, results=False, context={}):
        type = ''
        duration = ''
        start_tm_final = ''
        ebay_end_tm_final = ''
        ebayerp_manage_template = self.pool.get('ebayerp.manage')
        if not results:
            results = ebayerp_manage_template.import_product(cr,uid,[shop_id],item_id)#to call import_product function which is in template.py
        else:
            results = [results]
        ## Logic for creating products in OpenERP
        ###Getting Product Category
        FMT = '%Y-%m-%d %H:%M:%S'
        difft_time = datetime.utcnow() - datetime.now()
        prodcateg_obj = self.pool.get('product.category')
        prodtemp_obj = self.pool.get('product.template')
        prod_obj = self.pool.get('product.product')
        for result in results:
            if result.get('ListingType',False) =='Chinese':
                type = 'Auction'
            elif result.get('ListingType',False) =='FixedPriceItem':
                type = 'Fixed Price'
            elif result.get('ListingType',False) =='LeadGeneration':
                type = 'Classified Ad'
            else:
                type = result.get('ListingType',False)
            start_time = result.get('StartTime',False)
            if start_time:
                start_tm = self.pool.get('ebayerp.instance').openerpFormatDate(start_time)
                start_tm1 = datetime.strptime(start_tm, FMT) - difft_time
                start_tm_final = str(start_tm1)[:19]
            endtime = result.get('EndTime',False)
            if endtime:
                end_tm = self.pool.get('ebayerp.instance').openerpFormatDate(endtime)
                ebay_end_tm1 = datetime.strptime(end_tm, FMT) - difft_time
                ebay_end_tm_final = str(ebay_end_tm1)[:19]
            if result.get('ListingDuration',False) == 'Days_3':
                duration = "3 Days"
            elif result.get('ListingDuration',False) == 'Days_5':
                duration = "5 Days"
            elif result.get('ListingDuration',False) == 'Days_7':
                duration = "7 Days"
            elif result.get('ListingDuration',False) == 'Days_10':
                duration = "10 Days"
            elif result.get('ListingDuration',False) == 'Days_30':
                duration = "30 Days"
            elif result.get('ListingDuration',False) == 'Days_90':
                duration = "90 Days"
            else:
                duration = result.get('ListingDuration',False)
            listing_vals = {
                'name':item_id,
                'ebay_name': result.get('Title',False),
                'shop_id': shop_id,
                'type': type or '',
                'listing_duration': duration,
                'start_time': start_tm_final,
                'ebay_end_time': ebay_end_tm_final,
            }
#            if result.get('SKU',False):
#                prod_id = prod_obj.search(cr,uid,[('ebay_sku','=',result['SKU']),('name_template','=',result.get('Title',False))])
#                if prod_id:
#                    listing_vals['prod_list'] = prod_id[0]
#                    listing_id_search = self.pool.get('product.listing').search(cr,uid,[('name','=',item_id),('prod_list','=',prod_id[0])])
#                    if listing_id_search:
#                        return prod_id[0]
#                    else:
#                        listing_id = self.pool.get('product.listing').create(cr,uid,listing_vals)
#                        return prod_id[0]
#            elif custom_label:
#                prod_id = prod_obj.search(cr,uid,[('ebay_sku','=',custom_label),('name_template','=',result.get('Title',False))])
#                print"prod_id",prod_id
#                if prod_id:
#                    listing_vals['prod_list'] = prod_id[0]
#                    listing_id_search = self.pool.get('product.listing').search(cr,uid,[('name','=',item_id),('prod_list','=',prod_id[0])])
#                    if listing_id_search:
#                        return prod_id[0]
#                    else:
#                        listing_id = self.pool.get('product.listing').create(cr,uid,listing_vals)
#                        return prod_id[0]
#            else:
#                prod_id = prod_obj.search(cr,uid,[('name_template','=',result.get('Title',False))])
#                print"prod_id",prod_id
            item_id_search = self.pool.get('product.listing').search(cr,uid,[('name','=',item_id)])
            if item_id_search:
                prod_id = self.pool.get('product.listing').browse(cr,uid,item_id_search[0]).prod_list
                print"prod_id",prod_id
                if prod_id:
                    listing_vals['prod_list'] = prod_id.id
                    listing_id_search = self.pool.get('product.listing').search(cr,uid,[('name','=',item_id),('prod_list','=',prod_id.id)])
                    if listing_id_search:
                        return prod_id.id
                    else:
                        listing_id = self.pool.get('product.listing').create(cr,uid,listing_vals)
                        return prod_id.id
                
            if result.get('CategoryName',False):
                categories = result['CategoryName'].split(':')
                categ_id = False
                for i in range(len(categories)):
                    categ_id = prodcateg_obj.search(cr,uid,[('name','=',categories[i])])
                    if not categ_id:
                        if i == 0:
                            categ_id = prodcateg_obj.create(cr,uid,{'name':categories[i]})
                        else:
                            parent_categ_id = prodcateg_obj.search(cr,uid,[('name','=',categories[i-1])])
                            categ_id = prodcateg_obj.create(cr,uid,{'name':categories[i],'parent_id':parent_categ_id[0]})
                    else:
                        categ_id = categ_id[0]
            else:
                categ_id = self.browse(cr,uid,id).ebay_default_pro_cat.id
            weight = 0.0
            weight_major = result.get('ShippingDetails',[0,'lbs']) and result['ShippingDetails'].get('WeightMajor',[0,'lbs']) and result['ShippingDetails']['WeightMajor'].split(':') or [0,'lbs']
            if weight_major[1] == 'oz':
                weight += float(weight_major[0]) * 0.0625
            else:
                weight += float(weight_major[0])
            weight_minor =  result.get('ShippingDetails',[0,'lbs']) and result['ShippingDetails'].get('WeightMinor',[0,'lbs']) and result['ShippingDetails']['WeightMinor'].split(':') or [0,'lbs']
            if weight_minor[1] == 'oz':
                weight += float(weight_minor[0]) * 0.0625
            else:
                weight += float(weight_minor[0])
            template_vals = {
                'list_price' : result.get('ConvertedStartPrice',False) or '',
                'purchase_ok' : 'TRUE',
                'sale_ok' : 'TRUE',
                'name' : result.get('Title',False) or '',
                'type' : 'product',
                'procure_method' : 'make_to_stock',
                'cost_method' : 'standard',
                'categ_id' : categ_id,
                'weight_net' : weight,
                'description':result.get('Description',False) or ''
            }
            template_id = prodtemp_obj.create(cr,uid,template_vals)
            ### Create Product Listing
            listing_id = self.pool.get('product.listing').create(cr,uid,listing_vals)
            product_vals = {
                'ebay_sku' : custom_label or (result.get('SKU',False) and result['SKU']) or '',
                'product_tmpl_id' : template_id,
                'prods_list' : [(6,0,[listing_id])],
                'exported_to_ebay': True,}
            prod_id = prod_obj.create(cr,uid,product_vals)
            if result.get('PictureDetails',False):
               picture_url = result.get('PictureDetails',False)
               if picture_url:
                    pict_det ={
                               'chk_ebay_link' : 'TRUE',
                               'name' : result.get('Title',False) + "image",
                               'full_url':picture_url,
                               'product_id':prod_id
                               }
                    picture = self.pool.get('product.images').create(cr,uid,pict_det)
                    print"picture",picture
            if prod_id:
                inventry_obj = self.pool.get('stock.inventory')
                inventry_line_obj = self.pool.get('stock.inventory.line')
                location_idlist = self.pool.get('stock.location').search(cr,uid,[('company_id','=',1),('name','ilike','stock')])
                location_id = location_idlist[0]
                inventory_id = inventry_obj.create(cr , uid, {'name': _('INV: ') + result['Title']}, context=context)
                line_data ={
                  'inventory_id' : inventory_id,
                  'product_qty' : result.get('Quantity',False) or '',
                  'location_id' : location_id,
                  'product_id' : prod_id,
                  'product_uom' : 1,
              }
                inventry_line_obj.create(cr , uid, line_data, context=context)
                inventry_obj.action_confirm(cr, uid, [inventory_id], context=context)
                inventry_obj.action_done(cr, uid, [inventory_id], context=context)
            return prod_id

    def createEbayShippingProduct(self, cr, uid, id, context={}):
        prod_obj = self.pool.get('product.product')
        prodcateg_obj = self.pool.get('product.category')
        categ_id = prodcateg_obj.search(cr,uid,[('name','=','Service')])
        if not categ_id:
            categ_id = prodcateg_obj.create(cr,uid,{'name':'Service'})
        else:
            categ_id = categ_id[0]
        prod_id = prod_obj.create(cr,uid,{'type':'service','name':'Shipping and Handling', 'default_code':'SHIP EBAY','categ_id':categ_id})
        return prod_id

    def createAccountTax(self, cr, uid, id, value, context={}):
        accounttax_obj = self.pool.get('account.tax')
        accounttax_id = accounttax_obj.create(cr,uid,{'name':'Sales Tax(' + str(value) + '%)','amount':float(value)/100,'type_tax_use':'sale'})
        return accounttax_id

    def createInvoice(self, cr, uid, id, value, context={}):
        print "inside Ebayerp invoice"

    def createOrder(self, cr, uid, id, shop_id, resultvals, context={}):
        saleorderid = False
        increment = 1
        increment_sale = 1
        for resultval in resultvals:
            if resultval.get('ShippedTime',False) or not resultval.get('OrderLineItemID',False):
                continue
            saleorder_obj = self.pool.get('sale.order')
            saleorderline_obj = self.pool.get('sale.order.line')
            shop_name = self.pool.get('sale.shop').browse(cr,uid,shop_id).name
            filter_shop_name = check(shop_name)
#            paidtime = resultval.get('PaidTime',False)
#            if paidtime  or resultval['Status']['CheckoutStatus'] == 'CheckoutComplete':
            saleorderid = saleorder_obj.search(cr,uid,[('ebay_order_id','=',resultval['OrderLineItemID'])])
            ebaysaleshop = self.pool.get('sale.shop').browse(cr,uid,shop_id)
            if not saleorderid:
                partner_obj = self.pool.get('res.partner')
                partner_id = partner_obj.search(cr, uid, [('ebay_user_id','=',resultval['Buyer']['UserID'])]) or [0]
                partner_id = self.updatePartner(cr,uid,id,shop_id,resultval['Buyer'],partner_id[0])
                partneraddress_id = self.updatePartnerAddress(cr,uid,id,resultval['Buyer'],partner_id)
                if not partner_id or not partneraddress_id:
                    continue
                partner_order_id = partner_obj.address_get(cr,uid,[partner_id], ['contact' or 'default'])
                partner_invoice_id = partner_obj.address_get(cr,uid,[partner_id], ['invoice' or 'default'])
                partner_shipping_id = partner_obj.address_get(cr,uid,[partner_id], ['delivery' or 'default' ])
                pricelist_id = partner_obj.browse(cr,uid,partner_id)['property_product_pricelist'].id
                carrier_id = self.pool.get('delivery.carrier').search(cr,uid,[('ebay_code','=',resultval['ShippingServiceSelected']['ShippingService'])]) and self.pool.get('delivery.carrier').search(cr,uid,[('ebay_code','=',resultval['ShippingServiceSelected']['ShippingService'])])[0] or False
                ext_payment_method = resultval['Status']['PaymentMethodUsed'] != 'None' and resultval['Status']['PaymentMethodUsed'] or 'PayPal'
                company_id = self.pool.get('res.users').browse(cr,uid,uid).company_id.id
                defaults = {'company_id':company_id}
                payment_settings = saleorder_obj.payment_code_to_payment_settings(cr, uid, ext_payment_method, context)
                ordervals = {
                    'name' : filter_shop_name + '-' + resultval.get('OrderLineItemID',False),
                    'picking_policy' : payment_settings and payment_settings.picking_policy or ebaysaleshop.picking_policy or False,
                    'order_policy' : payment_settings and payment_settings.order_policy or ebaysaleshop.order_policy or False,
                    'partner_order_id' : partner_order_id['contact' or 'default'],
                    'partner_invoice_id' : partner_invoice_id['invoice' or 'default'],
                    'date_order' : self.openerpFormatDate(resultval.get('CreatedDate',False)),
                    'shop_id' : shop_id,
                    'partner_id' : partner_id,
                    'user_id' : uid,
                    'partner_shipping_id' : partner_shipping_id['delivery' or 'default'],
                    'shipped' : False,
                    'state' : 'draft',
                    'invoice_quantity' : payment_settings and payment_settings.invoice_quantity or ebaysaleshop.invoice_quantity,
                    'pricelist_id' : pricelist_id,
                    'carrier_id': carrier_id,
                    'ext_payment_method' : ext_payment_method,
                    'ebay_order_id' : resultval.get('OrderLineItemID',False)
                }
                saleorderid = saleorder_obj.create(cr,uid,ordervals)
                if not saleorderid:
                    continue

                saleorderlineids = saleorderline_obj.search(cr,uid,[('order_id','=',saleorderid)])
                if saleorderlineids:
                    return False
                ## Sale Orde Creation end ##
                product_obj = self.pool.get('product.product')
                listing_obj = self.pool.get('product.listing')
                sku = resultval['Item'].get('CustomLabel',False) and resultval['Item']['CustomLabel'] or resultval['Item'].get('SKU',False) and resultval['Item']['SKU']
                product_ids = product_obj.search(cr,uid,[('ebay_sku','=',sku),('name_template','=',resultval['Item'].get('Title',False))])
                result = False
                if not product_ids:
                    product_id = self.createProduct(cr,uid,id,shop_id,resultval['Item']['ItemID'],sku,result,context)
                else:
                    product_id = self.updateProduct(cr,uid,id,product_ids[0],shop_id,resultval['Item']['ItemID'],sku,result,context)
                    listing_ids = listing_obj.search(cr,uid,[('name','=',resultval['Item']['ItemID']),('prod_list','=',product_ids[0])])
                    if not listing_ids:
                        result = False
                        product_id = self.createProduct(cr,uid,id,shop_id,resultval['Item']['ItemID'],sku,result,context)
                    else:
                        product_id = product_ids[0]
                ### Account Tax - Needs to be tested
                tax_id = []
                if float(resultval['ShippingDetails']['SalesTaxAmount']) > 0.0:
                    ship_tax_vat = float(resultval['ShippingDetails']['SalesTaxPercent'])/100
                    acctax_id = self.pool.get('account.tax').search(cr,uid,[('type_tax_use', '=', 'sale'), ('amount', '>=', ship_tax_vat - 0.001), ('amount', '<=', ship_tax_vat + 0.001)])
                    if not acctax_id:
                        acctax_id = self.createAccountTax(cr,uid,id,resultval['ShippingDetails']['SalesTaxPercent'], context)
                        tax_id = [(6, 0, [acctax_id])]
                    else:
                        tax_id = [(6, 0, acctax_id)]
    #            saleorderlineid = saleorderline_obj.search(cr,uid,[('product_id','=',product_id),('order_id','=',saleorderid)])
    #            if not saleorderlineid:
                orderlinevals = {
                    'order_id' : saleorderid,
                    'product_uom_qty' : resultval.get('QuantityPurchased',False),
                    'product_uom' : product_obj.browse(cr,uid,product_id).product_tmpl_id.uom_id.id,
                    'name' : product_obj.browse(cr,uid,product_id).product_tmpl_id.name,
                    'price_unit' : resultval.get('TransactionPrice',False),
                    'delay' : product_obj.browse(cr,uid,product_id).product_tmpl_id.sale_delay,
                    'invoiced' : False,
                    'state' : 'confirmed',
                    'product_id' : product_id,
                    'tax_id' : tax_id
                }
                saleorderlineid = saleorderline_obj.create(cr,uid,orderlinevals)
                ## Shipping Service
                if saleorderlineid:
                    prod_shipping_id = product_obj.search(cr,uid,[('default_code','=','SHIP EBAY')])
                    if not prod_shipping_id:
                        prod_shipping_id = self.createEbayShippingProduct(cr,uid,id,context)
                    else:
                        prod_shipping_id = prod_shipping_id[0]
                    shiplineids = saleorderline_obj.search(cr,uid,[('order_id','=',saleorderid),('product_id','=',prod_shipping_id)])
                    if shiplineids:
                        return False
                    shiplineid = False
                    if resultval['ShippingServiceSelected']['ShippingService'] != 'NotSelected' and resultval['ShippingDetails']['ShippingIncludedInTax'] == 'false':
                        shiporderlinevals = {
                            'order_id' : saleorderid,
                            'product_uom_qty' : 1,
                            'product_uom' : product_obj.browse(cr,uid,prod_shipping_id).product_tmpl_id.uom_id.id,
                            'name' : product_obj.browse(cr,uid,prod_shipping_id).product_tmpl_id.name,
                            'price_unit' : float(resultval.get('ActualShippingCost') and resultval.get('ActualShippingCost',False) or 0.00) + float(resultval.get('ActualHandlingCost') and resultval['ActualHandlingCost'] or 0.00),
                            'delay' : product_obj.browse(cr,uid,prod_shipping_id).product_tmpl_id.sale_delay,
                            'invoiced' : False,
                            'state' : 'confirmed',
                            'product_id' : prod_shipping_id,
                        }
                        shiplineid = saleorderline_obj.create(cr,uid,shiporderlinevals)
                elif resultval['ShippingServiceSelected']['ShippingService'] != 'NotSelected' and resultval['ShippingDetails']['ShippingIncludedInTax'] == 'true':
                    shiporderlinevals = {
                        'order_id' : saleorderid,
                        'product_uom_qty' : 1,
                        'product_uom' : product_obj.browse(cr,uid,prod_shipping_id).product_tmpl_id.uom_id.id,
                        'name' : product_obj.browse(cr,uid,prod_shipping_id).product_tmpl_id.name,
                        'price_unit' : float(resultval.get('ActualShippingCost') and resultval.get('ActualShippingCost',False) or 0.00) + float(resultval.get('ActualHandlingCost') and resultval['ActualHandlingCost'] or 0.00),
                        'delay' : product_obj.browse(cr,uid,prod_shipping_id).product_tmpl_id.sale_delay,
                        'invoiced' : False,
                        'state' : 'confirmed',
                        'product_id' : prod_shipping_id,
                        'tax_id' : tax_id
                    }
                    shiplineid = saleorderline_obj.create(cr,uid,shiporderlinevals)
                message = _('SaleOrder %s-%s created successfully' % (filter_shop_name,resultval.get('OrderLineItemID',False) ))
                self.log(cr, uid, increment_sale, message)
                increment_sale += 1
                paid = resultval.get('PaidTime',False)
                if paid  or resultval['Status']['CheckoutStatus'] == 'CheckoutComplete':
                    company_id = self.pool.get('res.users').browse(cr,uid,uid).company_id.id
                    defaults = {'company_id':company_id}
                    ebay_oe_status = self.ebay_oe_status(cr, uid, saleorderid, paid, context, defaults)
            else:
                message = _('SaleOrder %s-%s Already Exists' % (filter_shop_name,resultval.get('OrderLineItemID',False)))
                self.log(cr, uid, increment, message)
                increment +=  1
        i = 100
        if increment_sale <= 1:
            no_saleorder = _('No More Orders Exist')
            self.log(cr, uid, i, no_saleorder)
        return True
    def create(self,cr,uid,vals,context=None):
        ids = super(ebayerp_instance, self).create(cr, uid, vals, context=context)
        if ids:
            inst_lnk = self.browse(cr,uid,ids)
            results = self.call(cr, uid, inst_lnk, 'GeteBayDetails',0)
            if results:
                site_details = results.get('SiteDetails',False)
                for each_details in site_details:
                    site_name = each_details.get('Site')
                    site_id = each_details.get('SiteID')
                    if site_id:
                        search_site = self.pool.get('site.details').search(cr,uid,[('site_id','=',site_id),('name','=',site_name)])
                        if not search_site:
                            self.pool.get('site.details').create(cr,uid,{'name':site_name,'site_id':site_id})
                shipping_master_search = self.pool.get('shipping.master').search(cr,uid,[])
                loc_master_search = self.pool.get('loc.master').search(cr,uid,[])
                ship_loc_master_search = self.pool.get('ship.loc.master').search(cr,uid,[])
                if not shipping_master_search or not loc_master_search or not ship_loc_master_search:
#                            results = self.pool.get('sale.shop').call(cr, uid, inst_lnk, 'GeteBayDetails',siteid)
                            if results:
                                results_first_array = results.get('ShippingServiceDetails',False)
                                for info in results_first_array:
                                    serv_desc = info.get('Description',False)
                                    serv_time = info.get('ShippingTimeMax',False)
                                    serv_carr = info.get('ShippingCarrier',False)
                                    inter_ship = info.get('InternationalService',False)
                                    ship_serv = info.get('ShippingService',False)
                                    ship_type = info.get('ServiceType',False)
                                    ship_type1 = info.get('ServiceType1',False)
                                    surch = info.get('SurchargeApplicable',False)
                                    dimen = info.get('DimensionsRequired',False)
                                    if dimen:
                                        if dimen == 'true':
                                            dimen_req = 'True'
                                        else:
                                            dimen_req = 'False'
                                    else:
                                        dimen_req = ''
                                    if surch:
                                        if surch == 'true':
                                            surch_app = 'True'
                                        else:
                                            surch_app = 'False'
                                    else:
                                        surch_app = ''
                                    if inter_ship:
                                        if inter_ship == 'true':
                                            foll = 'True'
                                        else:
                                            foll = 'False'
                                        if ship_type == 'Calculated':
                                            ships = {
                                                                'name':serv_desc,
                                                                'ship_time':serv_time,
                                                                'inter_ship':foll,
                                                                'ship_car':serv_carr,
                                                                'ship_ser':ship_serv,
                                                                'ship_type1':ship_type,
                                                                'surch_chk':surch_app,
                                                                'dimension_chk':dimen_req
                                                                }
                                        else:
                                            ships = {
                                                                'name':serv_desc,
                                                                'ship_time':serv_time,
                                                                'inter_ship':foll,
                                                                'ship_car':serv_carr,
                                                                'ship_ser':ship_serv,
                                                                'ship_type':ship_type,
                                                                'ship_type1':ship_type1,
                                                                'surch_chk':surch_app,
                                                                'dimension_chk':dimen_req
                                                                }
                                    else:

                                        if ship_type == 'Calculated':
                                            ships = {
                                                                'name':serv_desc,
                                                                'ship_time':serv_time,
                                                                'ship_car':serv_carr,
                                                                'ship_ser':ship_serv,
                                                                'ship_type1':ship_type,
                                                                'surch_chk':surch_app,
                                                                'dimension_chk':dimen_req
                                                                }
                                        else:
                                            ships = {
                                                                'name':serv_desc,
                                                                'ship_time':serv_time,
                                                                'ship_car':serv_carr,
                                                                'ship_ser':ship_serv,
                                                                'ship_type':ship_type,
                                                                'ship_type1':ship_type1,
                                                                'surch_chk':surch_app,
                                                                'dimension_chk':dimen_req
                                                                }
                                    if serv_desc != 'US Postal Service Ground' and serv_desc != 'USPS Priority Mail Regional Box A' and serv_desc != 'USPS Priority Mail Regional Box B' and serv_desc != 'USPS Priority Mail Regional Box A' and serv_desc != 'Local Delivery/Pickup' and serv_desc != 'USPS First Class Letter' and serv_desc != 'USPS First Class Large Envelop' and serv_desc != 'USPS First Class Parcel' and serv_desc != 'UPS Next Day Air AM' and serv_desc != 'Promotional Shipping Service' and serv_desc != 'Local Delivery' and serv_desc != 'Local Pickup' and serv_desc != 'USPS Global Express Mail' and serv_desc != 'USPS Global Priority Mail' and serv_desc != 'USPS Economy Letter Post' and serv_desc != 'USPS Economy Parcel Post' and serv_desc != 'USPS Airmail Letter Post' and serv_desc != 'USPS Global Priority Mail Flat Rate Small Envelope' and serv_desc != 'USPS Global Priority Mail Flat Rate Large Envelope' and serv_desc != 'UPS Worldwide Express Box 10Kg' and serv_desc != 'UPS Worldwide Express Box 25Kg' and serv_desc != 'UPS Worldwide Express Plus Box 10Kg' and serv_desc != 'UPS Worldwide Express Plus Box 25Kg' and serv_desc != 'Promotional Shipping Service' and serv_desc != 'USPS First Class Mail International Letter' and serv_desc != 'USPS First Class Mail International Large Envelope' and serv_desc != 'USPS First Class Mail International Parcel':
                                        search_dupl = self.pool.get('shipping.master').search(cr,uid,[('name','=',serv_desc)])
                                        if not search_dupl:
                                            create_ship = self.pool.get('shipping.master').create(cr,uid,ships)
                                results_second_array = results.get('ExcludeShippingLocationDetails',False)
                                for info1 in results_second_array:
                                    loc_name = info1.get('Description',False)
                                    loc_code = info1.get('Location',False)
                                    region = info1.get('Region',False)
                                    location = {
                                                'name':loc_name,
                                                'loc_code':loc_code,
                                                'region':region
                                                }
                                    search_dupl_loc = self.pool.get('loc.master').search(cr,uid,[('name','=',loc_name)])
                                    if not search_dupl_loc:
                                        create_loc = self.pool.get('loc.master').create(cr,uid,location)
                                results_third_array = results.get('ShippingLocationDetails',False)
                                for info2 in results_third_array:
                                    loc_code1 = info2.get('ShippingLocation',False)
                                    loc_name1 = info2.get('Description',False)
                                    if loc_code1 != 'Worldwide' and loc_code1 != 'None':
                                        ship_loc = {
                                                    'name':loc_name1,
                                                    'ship_code':loc_code1,
                                                    }
                                        search_dupl_loc_mast = self.pool.get('ship.loc.master').search(cr,uid,[('name','=',loc_name1)])
                                        if not search_dupl_loc_mast:
                                            create_ship_loc = self.pool.get('ship.loc.master').create(cr,uid,ship_loc)

            return ids
    def onchange_environment(self,cr,uid,ids,environment,context={}):
        result ={}
        if environment == 'is_sandbox':
            result['server_url'] = 'https://api.sandbox.ebay.com/ws/api.dll'
        else:
            result['server_url'] = 'https://api.ebay.com/ws/api.dll'
        return {'value':result}
    _columns = {
        'name' : fields.char('Name',size=64,required=True,help="Name of an Instance"),
        'dev_id' : fields.char('Dev ID',size=256,required=True,help="Ebay Dev ID"),
        'app_id' : fields.char('App ID',size=256,required=True,help="Ebay App ID"),
        'cert_id' : fields.char('Cert ID',size=256,required=True,help="Ebay Cert ID"),
        'server_url' : fields.char('Server URL',size=256,help="Ebay Server URL"),
        'environment' : fields.selection([('is_sandbox', 'Sandbox'),('is_production', 'Production')],'Environment',required=True),
        'auth_token' : fields.text('Token',required=True,help="Ebay Token"),
#        'ebay_default_pro_cat':fields.many2one('product.category','Default Product Category',required=True)
    }
ebayerp_instance()
################################################Category Master######################
class category_master(osv.osv):
    _name = "category.master"
    def create(self,cr,uid,vals,context={}):
        id =  super(category_master, self).create(cr, uid, vals, context)
        app_id = ''
        server_url = ''
        concate_url = ''
        category_code = ''
        if vals:
            category_code = vals.get('ebay_category_id',False)
            site_id_value = vals.get('site_id',False)
            if category_code and site_id_value:
                if id:
                    search_category_exists = self.search(cr,uid,[('ebay_category_id','=',category_code),('id','!=',id),('site_id','=',site_id_value)])
                    if search_category_exists:
                        raise osv.except_osv(_('Warning !'), _("This Category ID already exists"))
                        
            if category_code:
                search_ebay_true = self.pool.get('sale.shop').search(cr,uid,[('ebay_shop','=','TRUE')])
                if search_ebay_true:
                    inst_lnk = self.pool.get('sale.shop').browse(cr,uid,search_ebay_true[0]).instance_id
                    
                    if site_id_value:
                        siteid = self.pool.get('site.details').browse(cr,uid,site_id_value).site_id
                    environment = inst_lnk.environment
                    app_id = inst_lnk.app_id
                    if environment == 'is_sandbox':
                        server_url = "http://open.api.sandbox.ebay.com/"
                    elif environment == 'is_production':
                        server_url = "http://open.api.ebay.com/"
                    if app_id and server_url and siteid and category_code:
                        concate_url = """ %sshopping?callname=GetCategoryInfo&appid=%s&siteid=%s&CategoryID=%s&version=743&responseencoding=XML"""%(server_url,app_id,siteid,category_code)
                        try:
                            urlopen = urllib.urlopen(concate_url)
                        except Exception, e:
                            urlopen = ''
                        if urlopen:
                            mystring = urlopen.read()
                            if mystring:
                                response = parseString(mystring)
                                print"response",response
                                if response:
                                    if response.getElementsByTagName('Ack'):
                                        if response.getElementsByTagName('Ack')[0].childNodes[0].data == 'Success':
                                            if response.getElementsByTagName('LeafCategory'):
                                               leafcategory = response.getElementsByTagName('LeafCategory')[0].childNodes[0].data
                                               if leafcategory == 'false':
                                                    raise osv.except_osv(_('Warning !'), _("Category is not a Leaf Category"))
                                            else:
                                                   raise osv.except_osv(_('Warning !'), _("Category is Invalid on Current Site"))
                                        elif response.getElementsByTagName('Ack')[0].childNodes[0].data == 'Failure':
                                            long_message = response.getElementsByTagName('LongMessage')[0].childNodes[0].data
                                            raise osv.except_osv(_('Warning !'), _('%s')%(long_message))
        return id
    def write(self,cr,uid,ids,vals,context={}):
        app_id = ''
        server_url = ''
        concate_url = ''
        category_code = ''
        siteid = ''
        category_code_another = ''
        site_database_id = ''
        category_code  = vals.get('ebay_category_id',False)
        site_id_vals = vals.get('site_id',False)
        if ids:
            if type(ids) == type(int()):
                ids = [ids]
            if type(ids) == type(long()):
                ids = [ids]
            category_database = self.browse(cr,uid,ids[0]).ebay_category_id
            site_id_database = self.browse(cr,uid,ids[0]).site_id
            if not site_id_vals:
                 site_id_value = self.browse(cr,uid,ids[0]).site_id
                 site_database_id  = site_id_value.id
                 siteid = site_id_value.site_id
            else:
                site_database_id = site_id_vals
                siteid = self.pool.get('site.details').browse(cr,uid,site_database_id).site_id
            if category_code or site_id_vals:
                if category_database != category_code or site_id_vals != site_id_database:
                    vals.update({'item_specifics': False,'class_ad':False,'condition_enabled':False,'catlog_enabled':False})
                attribute_one2many = self.browse(cr,uid,ids[0]).attribute_ids
                if attribute_one2many:
                    related_attributes = self.pool.get('attribute.master').search(cr,uid,[('categ_id','=',ids[0])])
                    if related_attributes:
                        for each_att_val in related_attributes:
                            each_val =self.pool.get('attribute.value').search(cr,uid,[('att_master_id','=',each_att_val)])
                            for each_value in each_val:
                                delete_att_vals = cr.execute('delete from attribute_value where id=%s',(each_value,))
                            delete_attributes = cr.execute('delete from attribute_master where id=%s',(each_att_val,))
                search_template_cat1 = self.pool.get('ebayerp.template').search(cr,uid,[('category_id1','=',ids[0])])
                if search_template_cat1:
                    for each_template in search_template_cat1:
                        match_attribute_ids_cat1 = self.pool.get('ebayerp.template').browse(cr,uid,each_template).match_attribute_ids
                        for each_matching_ids in match_attribute_ids_cat1:
                            attribute_matching_id = each_matching_ids.id
                            ##delete from the attribute matching
                            if attribute_matching_id:
                                delete = cr.execute('delete from attribute_matching where id=%s',(attribute_matching_id,))
                search_template_cat2 = self.pool.get('ebayerp.template').search(cr,uid,[('category_id2','=',ids[0])])
                if search_template_cat2:
                    for each_template in search_template_cat2:
                        match_attribute_ids_cat1 = self.pool.get('ebayerp.template').browse(cr,uid,each_template).match_attribute_cat2
                        for each_matching_ids in match_attribute_ids_cat1:
                            attribute_matching_id = each_matching_ids.id
                            ##delete from the attribute matching
                            if attribute_matching_id:
                                delete = cr.execute('delete from attribute_matching where id=%s',(attribute_matching_id,))
            if not category_code:
                category_code = category_database
            if category_code and site_database_id:
                print"category_code_another",category_code_another
                if ids:
                    search_category_exists = self.search(cr,uid,[('ebay_category_id','=',category_code),('id','!=',ids[0]),('site_id','=',site_database_id)])
                    if search_category_exists:
                        raise osv.except_osv(_('Warning !'), _("This Category ID already exists"))
            search_ebay_true = self.pool.get('sale.shop').search(cr,uid,[('ebay_shop','=','TRUE')])
            if search_ebay_true:
                inst_lnk = self.pool.get('sale.shop').browse(cr,uid,search_ebay_true[0]).instance_id
                environment = inst_lnk.environment
                app_id = inst_lnk.app_id
                if environment == 'is_sandbox':
                    server_url = "http://open.api.sandbox.ebay.com/"
                elif environment == 'is_production':
                    server_url = "http://open.api.ebay.com/"
                if app_id and server_url and siteid and category_code:
                    concate_url = """ %sshopping?callname=GetCategoryInfo&appid=%s&siteid=%s&CategoryID=%s&version=743&responseencoding=XML"""%(server_url,app_id,siteid,category_code)
                    try:
                        urlopen = urllib.urlopen(concate_url)
                    except Exception, e:
                        urlopen = ''
                    if urlopen:
                        mystring = urlopen.read()
                        print"mystring",mystring
                        if mystring:
                            response = parseString(mystring)
                            if response:
                                if response.getElementsByTagName('Ack'):
                                    if response.getElementsByTagName('Ack')[0].childNodes[0].data == 'Success':
                                        if response.getElementsByTagName('LeafCategory'):
                                           leafcategory = response.getElementsByTagName('LeafCategory')[0].childNodes[0].data
                                           if leafcategory == 'false':
                                                raise osv.except_osv(_('Warning !'), _("Category is not a Leaf Category"))
                                        else:
                                           raise osv.except_osv(_('Warning !'), _("Category is Invalid on Current site"))
                                    elif response.getElementsByTagName('Ack')[0].childNodes[0].data == 'Failure':
                                        long_message = response.getElementsByTagName('LongMessage')[0].childNodes[0].data
                                        raise osv.except_osv(_('Warning !'), _('%s')%(long_message))
            id =  super(category_master, self).write(cr, uid, ids,vals, context)
        return id

    def get_attribute(self,cr, uid, ids, context=None):
        results = False
        attribute = False
        if ids:
            if type(ids) == type(int()):
                ids = [ids]
            if type(ids) == type(long()):
                ids = [ids]
            site_id_value = self.browse(cr,uid,ids[0]).site_id
            if site_id_value:
                siteid = site_id_value.site_id
            else:
                siteid = ''
            category_code = self.browse(cr,uid,ids[0]).ebay_category_id
            attribute_one2many = self.browse(cr,uid,ids[0]).attribute_ids
            if attribute_one2many:
                related_attributes = self.pool.get('attribute.master').search(cr,uid,[('categ_id','=',ids[0])])
                if related_attributes:
                    for each_att_val in related_attributes:
                        each_val =self.pool.get('attribute.value').search(cr,uid,[('att_master_id','=',each_att_val)])
                        for each_value in each_val:
                            delete_att_vals = cr.execute('delete from attribute_value where id=%s',(each_value,))
                        delete_attributes = cr.execute('delete from attribute_master where id=%s',(each_att_val,))
            search_template_cat1 = self.pool.get('ebayerp.template').search(cr,uid,[('category_id1','=',ids[0])])
            if search_template_cat1:
                for each_template in search_template_cat1:
                    match_attribute_ids_cat1 = self.pool.get('ebayerp.template').browse(cr,uid,each_template).match_attribute_ids
                    for each_matching_ids in match_attribute_ids_cat1:
                        attribute_matching_id = each_matching_ids.id
                        ##delete from the attribute matching
                        if attribute_matching_id:
                            delete = cr.execute('delete from attribute_matching where id=%s',(attribute_matching_id,))
            search_template_cat2 = self.pool.get('ebayerp.template').search(cr,uid,[('category_id2','=',ids[0])])
            if search_template_cat2:
                for each_template in search_template_cat2:
                    match_attribute_ids_cat1 = self.pool.get('ebayerp.template').browse(cr,uid,each_template).match_attribute_cat2
                    for each_matching_ids in match_attribute_ids_cat1:
                        attribute_matching_id = each_matching_ids.id
                        ##delete from the attribute matching
                        if attribute_matching_id:
                            delete = cr.execute('delete from attribute_matching where id=%s',(attribute_matching_id,))
            if category_code:
                search_ebay_true = self.pool.get('sale.shop').search(cr,uid,[('ebay_shop','=','TRUE')])
                if search_ebay_true:
                    leafcategory = ''
                    inst_lnk = self.pool.get('sale.shop').browse(cr,uid,search_ebay_true[0]).instance_id
                    environment = inst_lnk.environment
                    app_id = inst_lnk.app_id
                    if environment == 'is_sandbox':
                        server_url = "http://open.api.sandbox.ebay.com/"
                    elif environment == 'is_production':
                        server_url = "http://open.api.ebay.com/"
                    if app_id and server_url and siteid and category_code:
                        concate_url = """ %sshopping?callname=GetCategoryInfo&appid=%s&siteid=%s&CategoryID=%s&version=743&responseencoding=XML"""%(server_url,app_id,siteid,category_code)
                        try:
                            urlopen = urllib.urlopen(concate_url)
                        except Exception, e:
                            urlopen = ''
                        if urlopen:
                            mystring = urlopen.read()
                            print"mystring",mystring
                            if mystring:
                                response = parseString(mystring)
                                print"response",response
                                if response:
                                    if response.getElementsByTagName('Ack'):
                                        if response.getElementsByTagName('Ack')[0].childNodes[0].data == 'Success':
                                            if response.getElementsByTagName('LeafCategory'):
                                               leafcategory = response.getElementsByTagName('LeafCategory')[0].childNodes[0].data
                                               if leafcategory == 'false':
                                                    raise osv.except_osv(_('Warning !'), _("Category is not a Leaf Category"))
                                               elif leafcategory == 'true':
                                                   leafcategory = 'true'
                                            else:
                                                   raise osv.except_osv(_('Warning !'), _("Category is Invalid on Current Site"))
                                        elif response.getElementsByTagName('Ack')[0].childNodes[0].data == 'Failure':
                                            long_message = response.getElementsByTagName('LongMessage')[0].childNodes[0].data
                                            raise osv.except_osv(_('Warning !'), _('%s')%(long_message))
                    if leafcategory == 'true':
                        results = self.pool.get('sale.shop').call(cr, uid, inst_lnk, 'GetCategory2CS',category_code,siteid)
                        results1 = self.pool.get('sale.shop').call(cr, uid, inst_lnk, 'GetCategoryFeatures',category_code,siteid)
#                        shipping_master_search = self.pool.get('shipping.master').search(cr,uid,[])
#                        loc_master_search = self.pool.get('loc.master').search(cr,uid,[])
#                        ship_loc_master_search = self.pool.get('ship.loc.master').search(cr,uid,[])
#                        if not shipping_master_search or not loc_master_search or not ship_loc_master_search:
#                            results2 = self.pool.get('sale.shop').call(cr, uid, inst_lnk, 'GeteBayDetails',siteid)
#                            if results2:
#                                results_first_array = results2.get('ShippingServiceDetails',False)
#                                for info in results_first_array:
#                                    serv_desc = info.get('Description',False)
#                                    serv_time = info.get('ShippingTimeMax',False)
#                                    serv_carr = info.get('ShippingCarrier',False)
#                                    inter_ship = info.get('InternationalService',False)
#                                    ship_serv = info.get('ShippingService',False)
#                                    ship_type = info.get('ServiceType',False)
#                                    ship_type1 = info.get('ServiceType1',False)
#                                    surch = info.get('SurchargeApplicable',False)
#                                    dimen = info.get('DimensionsRequired',False)
#                                    if dimen:
#                                        if dimen == 'true':
#                                            dimen_req = 'True'
#                                        else:
#                                            dimen_req = 'False'
#                                    else:
#                                        dimen_req = ''
#                                    if surch:
#                                        if surch == 'true':
#                                            surch_app = 'True'
#                                        else:
#                                            surch_app = 'False'
#                                    else:
#                                        surch_app = ''
#                                    if inter_ship:
#                                        if inter_ship == 'true':
#                                            foll = 'True'
#                                        else:
#                                            foll = 'False'
#                                        if ship_type == 'Calculated':
#                                            ships = {
#                                                                'name':serv_desc,
#                                                                'ship_time':serv_time,
#                                                                'inter_ship':foll,
#                                                                'ship_car':serv_carr,
#                                                                'ship_ser':ship_serv,
#                                                                'ship_type1':ship_type,
#                                                                'surch_chk':surch_app,
#                                                                'dimension_chk':dimen_req
#                                                                }
#                                        else:
#                                            ships = {
#                                                                'name':serv_desc,
#                                                                'ship_time':serv_time,
#                                                                'inter_ship':foll,
#                                                                'ship_car':serv_carr,
#                                                                'ship_ser':ship_serv,
#                                                                'ship_type':ship_type,
#                                                                'ship_type1':ship_type1,
#                                                                'surch_chk':surch_app,
#                                                                'dimension_chk':dimen_req
#                                                                }
#                                    else:
#
#                                        if ship_type == 'Calculated':
#                                            ships = {
#                                                                'name':serv_desc,
#                                                                'ship_time':serv_time,
#                                                                'ship_car':serv_carr,
#                                                                'ship_ser':ship_serv,
#                                                                'ship_type1':ship_type,
#                                                                'surch_chk':surch_app,
#                                                                'dimension_chk':dimen_req
#                                                                }
#                                        else:
#                                            ships = {
#                                                                'name':serv_desc,
#                                                                'ship_time':serv_time,
#                                                                'ship_car':serv_carr,
#                                                                'ship_ser':ship_serv,
#                                                                'ship_type':ship_type,
#                                                                'ship_type1':ship_type1,
#                                                                'surch_chk':surch_app,
#                                                                'dimension_chk':dimen_req
#                                                                }
#                                    if serv_desc != 'US Postal Service Ground' and serv_desc != 'USPS Priority Mail Regional Box A' and serv_desc != 'USPS Priority Mail Regional Box B' and serv_desc != 'USPS Priority Mail Regional Box A' and serv_desc != 'Local Delivery/Pickup' and serv_desc != 'USPS First Class Letter' and serv_desc != 'USPS First Class Large Envelop' and serv_desc != 'USPS First Class Parcel' and serv_desc != 'UPS Next Day Air AM' and serv_desc != 'Promotional Shipping Service' and serv_desc != 'Local Delivery' and serv_desc != 'Local Pickup' and serv_desc != 'USPS Global Express Mail' and serv_desc != 'USPS Global Priority Mail' and serv_desc != 'USPS Economy Letter Post' and serv_desc != 'USPS Economy Parcel Post' and serv_desc != 'USPS Airmail Letter Post' and serv_desc != 'USPS Global Priority Mail Flat Rate Small Envelope' and serv_desc != 'USPS Global Priority Mail Flat Rate Large Envelope' and serv_desc != 'UPS Worldwide Express Box 10Kg' and serv_desc != 'UPS Worldwide Express Box 25Kg' and serv_desc != 'UPS Worldwide Express Plus Box 10Kg' and serv_desc != 'UPS Worldwide Express Plus Box 25Kg' and serv_desc != 'Promotional Shipping Service' and serv_desc != 'USPS First Class Mail International Letter' and serv_desc != 'USPS First Class Mail International Large Envelope' and serv_desc != 'USPS First Class Mail International Parcel':
#                                        search_dupl = self.pool.get('shipping.master').search(cr,uid,[('name','=',serv_desc)])
#                                        if not search_dupl:
#                                            create_ship = self.pool.get('shipping.master').create(cr,uid,ships)
#                                results_second_array = results2.get('ExcludeShippingLocationDetails',False)
#                                for info1 in results_second_array:
#                                    loc_name = info1.get('Description',False)
#                                    loc_code = info1.get('Location',False)
#                                    region = info1.get('Region',False)
#                                    location = {
#                                                'name':loc_name,
#                                                'loc_code':loc_code,
#                                                'region':region
#                                                }
#                                    search_dupl_loc = self.pool.get('loc.master').search(cr,uid,[('name','=',loc_name)])
#                                    if not search_dupl_loc:
#                                        create_loc = self.pool.get('loc.master').create(cr,uid,location)
#                                results_third_array = results2.get('ShippingLocationDetails',False)
#                                for info2 in results_third_array:
#                                    loc_code1 = info2.get('ShippingLocation',False)
#                                    loc_name1 = info2.get('Description',False)
#                                    if loc_code1 != 'Worldwide' and loc_code1 != 'None':
#                                        ship_loc = {
#                                                    'name':loc_name1,
#                                                    'ship_code':loc_code1,
#                                                    }
#                                        search_dupl_loc_mast = self.pool.get('ship.loc.master').search(cr,uid,[('name','=',loc_name1)])
#                                        if not search_dupl_loc_mast:
#                                            create_ship_loc = self.pool.get('ship.loc.master').create(cr,uid,ship_loc)
                        if results1:
                            item_sp_en = results1.get('ItemSpecificsEnabled',False)
                            class_ad_en = results1.get('AdFormatEnabled',False)
                            condition_enabled = results1.get('ConditionEnabled',False)
                            if item_sp_en == 'Enabled' :
                                cr.execute("UPDATE category_master SET item_specifics='True' where id=%d"%(ids[0],))
                            else:
                                 cr.execute("UPDATE category_master SET item_specifics='False' where id=%s"%(ids[0],))
                            if class_ad_en == 'ClassifiedAdEnabled' :
                                cr.execute("UPDATE category_master SET class_ad='True' where id=%s"%(ids[0],))
                            else:
                                cr.execute("UPDATE category_master SET class_ad='False' where id=%s"%(ids[0],))
                            if condition_enabled == 'Disabled' :
                                cr.execute("UPDATE category_master SET condition_enabled='False' where id=%s"%(ids[0],))
                            else:
                                cr.execute("UPDATE category_master SET condition_enabled='True' where id=%s"%(ids[0],))
                            condition_ids =  self.pool.get('condition.class').search(cr,uid,[('category_id','=',ids[0])])
                            for each_condition in condition_ids:
                                if each_condition:
                                    delete = cr.execute('delete from condition_class where id=%s',(each_condition,))
                            condition_values = results1.get('ConditionValues',False)
                            if condition_values:
                                for each_val in condition_values:
                                    condition_name = each_val.get('DisplayName',False)
                                    condition_id = each_val.get('ID',False)
                                    if condition_name and condition_id:
                                        search_conditions = self.pool.get('condition.class').search(cr,uid,[('condition_id','=',condition_id),('category_id','=',ids[0]),('name','=',condition_name)])
                                        if not search_conditions:
                                            condition_vals = {'name':condition_name,'condition_id':condition_id,'category_id':ids[0]}
                                            self.pool.get('condition.class').create(cr,uid,condition_vals)
                        if results:
                            catalog_en = results.get('CatalogEnabled',False)
                            if catalog_en == 'true' :
                                cr.execute("UPDATE category_master SET  catlog_enabled='True' where id=%s"%(ids[0]))
                            cr.execute("UPDATE category_master SET attribute_set_id=%s where id=%s"%(results.get('AttributeSetID',False),ids[0]))
                            attribute_set_id = self.browse(cr,uid,ids[0]).attribute_set_id
                            attribute = self.pool.get('sale.shop').call(cr, uid, inst_lnk, 'GetAttributesCS',attribute_set_id,siteid)
                            doc = libxml2.parseDoc(attribute.encode('utf-8'))
                            def getValuesinitial():
                                create_ids = []
                                valids = []
                                pos = 0
                                attribute_ids = [attr.content for attr in doc.xpathEval("/eBay/Characteristics/CharacteristicsSet/CharacteristicsList/Initial/Attribute/@id")]
                                for attribute_id in attribute_ids:
                                    if attribute_id != '3803' and attribute_id != '3804' and attribute_id != '3805' and attribute_id != '3806' and attribute_id != '3993' and  attribute_id != '3801' and attribute_id != '10244':
                                        search = self.pool.get('attribute.master').search(cr,uid,[('categ_id','=',ids[0]),('attribute_id','=',attribute_id)])
                                        if not search:
                                            attribute_name_array = [attr.content for attr in doc.xpathEval("/eBay/Characteristics/CharacteristicsSet/CharacteristicsList/Initial/Attribute[@id=%s]/Label" % (attribute_id))]
                                            attribute_name = attribute_name_array[0]
                                            attribute_type_array = [attr.content for attr in doc.xpathEval("/eBay/Characteristics/CharacteristicsSet/CharacteristicsList/Initial/Attribute[@id=%s]/Type" % (attribute_id))]
                                            attribute_type = attribute_type_array[0]
                                            value_list = [attr.content for attr in doc.xpathEval("/eBay/Characteristics/CharacteristicsSet/CharacteristicsList/Initial/Attribute[@id=%s]/ValueList/Value/Name" % (attribute_id))]
                                            value_id = [attr.content for attr in doc.xpathEval("/eBay/Characteristics/CharacteristicsSet/CharacteristicsList/Initial/Attribute[@id=%s]/ValueList/Value/@id" % (attribute_id))]
                                            for val in value_list:
                                                valu_search =self.pool.get('attribute.master').search(cr,uid,[('name','=',val)])
                                                if not valu_search:
                                                    valid = self.pool.get('attribute.value').create(cr,uid,{'name':val,'att_val_id':value_id[pos] })
                                                    valids.append(valid)
                                                    pos= pos + 1
                                                else:
                                                    pos= pos + 1
                                            attribute = {
                                            'name':attribute_name,
                                            'attribute_type':attribute_type,
                                            'attribute_id':attribute_id,
                                            'attribute_values':[(6,0,valids)],
                                            'categ_id':ids[0],
                                            }
                                            create_id = self.pool.get('attribute.master').create(cr,uid,attribute)
                                            create_ids.append(create_id)
                                            valids = []
                                            pos = 0
                                return
                            print getValuesinitial()
        return True

    def onchange_category_id(self,cr,uid,ids,ebay_category_id):
        domain = {}
        instance_ids = self.pool.get('sale.shop').search(cr,uid,([]))
        site_ids_array = []
        for each_id in instance_ids:
            site_ids = self.pool.get('sale.shop').browse(cr,uid,each_id).site_id
            site_ids_array.append(site_ids.id)
        domain['site_id'] = [('id', 'in', site_ids_array)]
        return {'domain':domain}
    _columns = {
        'name': fields.char('Category Name', size=64,required=True,help="Ebay Category Name"),
        'ebay_category_id' :fields.integer('Category ID',required=True, help="Ebay Category ID"),
        'attribute_ids': fields.one2many('attribute.master', 'categ_id', 'Attributes',readonly=True),
        'attribute_set_id': fields.integer('Attribute Set ID'),
        'item_specifics':fields.boolean('Item Specific Enabled',help="If checked then this category supports Custom Item Specifics",readonly=True),
        'class_ad':fields.boolean('Classified Ad Enabled',help="If checked then this category supports the Classified Ad Format",readonly=True),
        'condition_enabled':fields.boolean('Condition Enabled',help="If checked then this category supports item condition",readonly=True),
        'catlog_enabled':fields.boolean('Catlaog Enabled',help="If checked then this category is catalog enabled",readonly=True),
        'site_id' : fields.many2one('site.details','Site',required=True),
    }
#    _sql_constraints = [
#        ('category_id_uniq', 'unique(ebay_category_id)', 'This Category ID already exists !'),
#    ]
category_master()

class condition_class(osv.osv):
    _name = "condition.class"
    _columns = {
    'name': fields.char('Condition Name',size=256),
    'condition_id': fields.char('Condition ID',size=256),
    'category_id':fields.many2one('category.master','Category ID'),
    }
condition_class()
class attribute_master(osv.osv):
    _name = "attribute.master"
    _columns = {
        'name' : fields.char('Attribute Name', size=64),
        'attribute_id' : fields.integer('Attribute ID'),
        'attribute_type' : fields.char('Attribute Type', size=64),
        'categ_id' : fields.many2one('category.master', 'Category'),
    }
attribute_master()

class attribute_master(osv.osv):
    _inherit = "attribute.master"
    _columns = {
        'attribute_values' : fields.one2many('attribute.value','att_master_id','Attribute Values'),
    }
attribute_master()

class attribute_value(osv.osv):
    _name = 'attribute.value'
    _columns = {
        'name':fields.char('Attribute Value', size=64),
        'att_val_id':fields.integer('Attribute Value ID'),
        'att_master_id':fields.many2one('attribute.master','Attribute Master'),
    }
attribute_value()

class ebayerp_template(osv.osv):
    _name = "ebayerp.template"
    def create(self,cr,uid,vals,context={}):
        category_id1 = vals.get('category_id1',False)
        category_id2 = vals.get('category_id2',False)
        if category_id1 != False and category_id2 != False:
            if category_id1 == category_id2:
                raise osv.except_osv(_('Warning !'), _("Please Select Two Different Categories"))
        return super(ebayerp_template, self).create(cr, uid, vals, context=context)

    def write(self,cr,uid,ids,vals,context={}):
        if ids:
            if type(ids) == type(int()):
                    ids = [ids]
            if type(ids) == type(long()):
                    ids = [ids]
            if 'category_id1' in vals:
                category_id1 = vals.get('category_id1',False)
            else:
                category_id1 = self.browse(cr, uid, ids[0]).category_id1.id
            if 'category_id2' in vals:
                category_id2 = vals.get('category_id2',False)
            else:
                category_id2 = self.browse(cr, uid, ids[0]).category_id2.id
            if category_id1 != False and category_id2 != False:
                if category_id1 == category_id2:
                    raise osv.except_osv(_('Warning !'), _("Please Select Two Different Categories"))
        return super(ebayerp_template, self).write(cr, uid, ids, vals, context=context)
    def onchange_buyer_req(self,cr,uid,ids,only_feed_scr):
        result ={}
        if only_feed_scr == True :
             result['hv_bid'] = True
        return {'value':result}
    def onchange_buyer_req2(self,cr,uid,ids,hv_bid):
        result ={}
        if hv_bid == False :
             result['only_feed_scr'] = False
        return {'value':result}
    def update_template(self,cr, uid, ids, context=None):
        increment = 0
        i = 1
        j = 1
        k = 1
        l = 1
        postal_code_str = ''
        payment_method_str = ''
        paypal_email_str = ''
        site_id_str = ''
        previous = ''
        list_item = []
        product_long_message = ''
        shop_id_previous = ''
        site_id = ''
        new_array = []
        if type(ids) == type(int()):
            ids = [ids]
        if type(ids) == type(long()):
            ids = [ids]
        search_ebay_true = self.pool.get('sale.shop').search(cr,uid,[('ebay_shop','=','TRUE')])
        if search_ebay_true:
            inst_lnk = self.pool.get('sale.shop').browse(cr,uid,search_ebay_true[0]).instance_id
            results = self.pool.get('sale.shop').call(cr, uid, inst_lnk, 'GeteBayOfficialTime',0)
            ebay_current_time = results
            template_id = ids[0]
            template_name = self.browse(cr,uid,ids[0]).name
            check_con = self.pool.get('product.listing').search(cr,uid,[('ebay_end_time','>',ebay_current_time),('related_template','=',ids)])
            list_item = []
            if not check_con:
                self.log(cr, uid,increment, 'No More Products to Update related to %s template'%(template_name))
                return
            for condition in check_con:
                if previous:
                    shop_id_previous = self.pool.get('product.listing').browse(cr,uid,previous).shop_id
                previous = condition
                shop_id = self.pool.get('product.listing').browse(cr,uid,condition).shop_id
                inst_id = shop_id.instance_id
                shop_name = shop_id.name
                postal_code = shop_id.post_code
                if not postal_code:
                    if shop_id != shop_id_previous:
                        postal_code_str += """  %s.%s """ % (i,shop_name)
                        i=i+1
                payment_method = shop_id.pay_mthd
                if not payment_method:
                    if shop_id != shop_id_previous:
                        payment_method_str += """  %s.%s """ % (j,shop_name)
                        j=j+1
                paypal_email = shop_id.email_add
                if not paypal_email:
                    if shop_id != shop_id_previous:
                        paypal_email_str += """  %s.%s """ % (k,shop_name)
                        k=k+1
                site_id = shop_id.site_id
                if site_id:
                    siteid = site_id.site_id
                else:
                    if shop_id != shop_id_previous:
                        site_id_str += """  %s.%s """ % (l,shop_name)
                        l=l+1
                template_cat1 = self.browse(cr,uid,ids[0]).category_id1
                template_cat2 = self.browse(cr,uid,ids[0]).category_id2
                template_name = self.browse(cr,uid,ids[0]).name
                prod_list = self.pool.get('product.listing').browse(cr,uid,condition).prod_list
                if prod_list:
                    product_name = prod_list.name_template
                    product_cat1 = prod_list.cat1
                    product_cat2 = prod_list.cat2
                    if not product_cat1:
                       if not template_cat1:
                           list_message = _("Please Select the Category in Product or Template for this %s") % product_name
                           self.log(cr, uid,increment,list_message)
                       else:
                            site_id_template_cat1 = template_cat1.site_id
                            if site_id_template_cat1 != site_id:
                                list_message = _("Please Select the Proper Primary Category for %s because Site ID of Category and Shop Differs") % template_name
                                self.log(cr, uid,increment,list_message)
                            else:
                                new_array.append(condition)
                    else:
                        site_id_cat = product_cat1.site_id
                        if site_id_cat != site_id:
                            list_message = _("Please Select the Proper Primary Category for %s because Site ID of Category and Shop Differs") % product_name
                            self.log(cr, uid,increment,list_message)
                        else:
                            new_array.append(condition)
                    if not product_cat2:
                        if template_cat2:
                            site_id_template_cat2 = template_cat2.site_id
                            if site_id_template_cat2 != site_id:
                                list_message = _("Please Select the Proper Primary Category for %s because Site ID of Category and Shop Differs") % template_name
                                self.log(cr, uid,increment,list_message)
                            else:
                                new_array.append(condition)
                    else:
                        site_id_cat = product_cat2.site_id
                        if site_id_cat != site_id:
                            list_message = _("Please Select the Proper Primary Category for %s because Site ID of Category and Shop Differs") % product_name
                            self.log(cr, uid,increment,list_message)
                        else:
                            new_array.append(condition)
            if postal_code_str:
                raise osv.except_osv(_('Warning !'), _("Please Enter the Postal Code in %s")%(postal_code_str))
            elif payment_method_str:
                raise osv.except_osv(_('Warning !'), _("Please Enter the Payment Method in %s")%(payment_method_str))
            elif paypal_email_str:
                raise osv.except_osv(_('Warning !'), _("Please Enter the Email Address in %s")%(paypal_email_str))
#            elif site_id_str:
#                raise osv.except_osv(_('Warning !'), _("Please Select Site ID in %s")%(site_id_str))
            for condition in new_array:
                ebay_item_id = self.pool.get('product.listing').browse(cr,uid,condition).name
                product_id = self.pool.get('product.listing').browse(cr,uid,condition).prod_list.id
                product_search = self.pool.get('placeholder.holder').search(cr,uid,[('plc_hld','=',product_id)])
#########################################Getting Key Values from template and Product level##########
                plc_holder_chk = self.pool.get('placeholder.holder').search(cr,uid,[('plc_hld_temp','=',template_id)])
                place_obj = self.pool.get('placeholder.holder')
                subtitle_dict = {}
                for prod in product_search:
                    place_id_obj = place_obj.browse(cr,uid,prod)
                    name = place_id_obj.name
                    value = place_id_obj.value
                    subtitle_dict[name] = value
                for place in plc_holder_chk:
                    place_id_obj = place_obj.browse(cr,uid,place)
                    name = place_id_obj.name
                    value = place_id_obj.value
                    if subtitle_dict.has_key(name):
                        print"subtitle_dict.has_key(name)",subtitle_dict.has_key(name)
                    else:
                        subtitle_dict[name] = value
###############################Replacing values in subtitle###########################
                subtitle = self.browse(cr,uid,ids[0]).subtitle
                if subtitle:
                   subtitle_split  = subtitle.split(' ')
                   for each_subtitle in subtitle_split:
                       each_sub_string = str(each_subtitle)
                       if each_sub_string != '':
                           first_pos = each_sub_string.find('%')
                           if first_pos != -1:
                               last_post = each_sub_string.rfind('%')
                               if last_post != first_pos:
                                   string = each_sub_string[first_pos+1:last_post]
                                   new_string =each_sub_string.replace('%',' ')
                                   replace_str = subtitle.replace(each_sub_string,new_string)
                                   if subtitle_dict.has_key(string):
                                       place_holder_val_str_temp = subtitle_dict.get(string)
                                       subtitle_replace_temp = replace_str.replace(string,place_holder_val_str_temp)
                                   else:
                                       place_holder_val_str_temp = ''
                                       subtitle_replace_temp = replace_str.replace(string,place_holder_val_str_temp)
                                   subtitle = subtitle_replace_temp
                           subtitle_spl = subtitle
                   subtitle_finals = subtitle_spl
                   subtitle_final = subtitle_finals[:55]
                else:
                   subtitle_final = ""
####################################################Replacing values in subtitle#################################
                description_field = self.browse(cr,uid,ids[0]).description
                if description_field:
                   description_new = description_field.replace('\n',' ')
                   description_split  = description_new.split(' ')
                   for each_split in description_split:
                       each_string = str(each_split)
                       if each_string != '':
                           first_pos = each_string.find('%')
                           if first_pos != -1:
                               last_post = each_string.rfind('%')
                               if last_post != first_pos:
                                   string = each_string[first_pos+1:last_post]
                                   if subtitle_dict.has_key(string):
                                       place_holder_val_str_temp = subtitle_dict.get(string)
                                       description_new = description_new.replace('%'+string+'%',place_holder_val_str_temp)
                                   else:
                                       place_holder_val_str_temp = ''
                                       description_new = description_new.replace('%'+string+'%',place_holder_val_str_temp)
                   description_final = description_new
                else:
                   raise osv.except_osv(_('Warning !'), _("Please Enter the Description in title"))
#########################################Replacing Title#########################################
                title = self.browse(cr,uid,ids[0]).temp_name
                if title:
                   title_split  = title.split(' ')
                   for each_split in title_split:
                       each_string = str(each_split)
                       if each_string != '':
                           first_pos = each_string.find('%')
                           if first_pos != -1:
                               last_post = each_string.rfind('%')
                               if last_post != first_pos:
                                   string = each_string[first_pos+1:last_post]
                                   new_string =each_string.replace('%',' ')
                                   replace_str = title.replace(each_string,new_string)
                                   if subtitle_dict.has_key(string):
                                       place_holder_val_str_temp = subtitle_dict.get(string)
                                       subtitle_replace_temp2 = replace_str.replace(string,place_holder_val_str_temp)
                                   else:
                                       place_holder_val_str_temp = ''
                                       subtitle_replace_temp2 = replace_str.replace(string,place_holder_val_str_temp)
                                   title = subtitle_replace_temp2
                           title_spl=title

                   title_finals = title_spl
                   title_final = title_finals[:80]
                else:
                   raise osv.except_osv(_('Warning !'), _("Please Enter the Title in Template"))
                results = self.pool.get('sale.shop').call(cr, uid, inst_id, 'ReviseItem', [condition],product_id,ebay_item_id,title_final,description_final,subtitle_final,postal_code,increment,siteid)
                product_nm = self.pool.get('product.product').browse(cr,uid,product_id).name_template
                ack = results.get('Ack',False)
                if ack =='Failure':
                    if results.get('LongMessage',False):
                       long_message = results['LongMessage']
                       for each_messsge in long_message:
                           severity_code = each_messsge[0]['SeverityCode']
                           if severity_code == 'Error':
                               Longmessage = each_messsge[0]['LongMessage']
                               product_long_message = ('Error : This %s Product Cannot be Updated Because:') % (product_nm)+ ' ' + Longmessage
                               increment += 1
                               self.log(cr, uid,increment, product_long_message)
                elif ack =='Warning':
                    if results.get('LongMessage',False):
                       long_message = results['LongMessage']
                       for each_messsge in long_message:
                           severity_code = each_messsge[0]['SeverityCode']
                           if severity_code == 'Warning':
                               Longmessage = each_messsge[0]['LongMessage']
                               product_long_message = ('Warning : %s :') % (product_nm)+ ' ' + Longmessage
                               increment += 1
                               self.log(cr, uid,increment, product_long_message)
#                    self.pool.get('product.listing').write(cr,uid,condition,{'ebay_name':title_final})
                    cr.execute("UPDATE product_listing SET ebay_name='%s' where id=%d"%(title_final,condition,))
                    cr.commit()
                else:
                    list_item.append(product_id)
#                    self.pool.get('product.listing').write(cr,uid,condition,{'ebay_name':title_final})
                    cr.execute("UPDATE product_listing SET ebay_name='%s' where id=%d"%(title_final,condition,))
                    cr.commit()
            if list_item:
               for each_list_product in list_item:
                  product_name =self.pool.get('product.product').browse(cr,uid,each_list_product).name_template
                  increment += 1
                  list_message = _("%s product updated successfully on ebay") % product_name
                  self.log(cr, uid,increment, list_message)
        return True
    
    def onchange_clear_attributes(self,cr,uid,ids,cat1,cat2,context=None):
        result ={}
        domain = {}
        if cat1:
            condition_ids =  self.pool.get('condition.class').search(cr,uid,[('category_id','=',cat1)])
            condition_enabled =  self.pool.get('category.master').browse(cr,uid,cat1).condition_enabled
            if condition_enabled == False:
                if cat2:
                    condition_enabled =  self.pool.get('category.master').browse(cr,uid,cat2).condition_enabled
                    if condition_enabled == True:
                        condition_ids =  self.pool.get('condition.class').search(cr,uid,[('category_id','=',cat2)])
                        domain['condtn'] = [('id', 'in', condition_ids)]
                    else:
                        domain['condtn'] = [('id', 'in', [])]
                else:
                    domain['condtn'] = [('id', 'in', [])]
            else:
                domain['condtn'] = [('id', 'in', condition_ids)]
            if condition_ids:
                result['condtn'] = condition_ids[0]
            else:
                result['condtn'] = False
            item_specifics = self.pool.get('category.master').browse(cr,uid,cat1).item_specifics
            if item_specifics == True:
                result['item_specifics_enabled_cat1'] = 'checked'
            else:
                if cat2:
                    item_specifics = self.pool.get('category.master').browse(cr,uid,cat2).item_specifics
                    if item_specifics == True:
                        result['item_specifics_enabled_cat1'] = 'checked'
                    else:
                        result['item_specifics_enabled_cat1'] = 'unchecked'
                        if ids:
                            custom_attributes = self.browse(cr,uid,ids[0]).custom_item_specifics_generic
                            if custom_attributes:
                                for each_specifics in custom_attributes:
                                    each_specifics_id = each_specifics.id
                                    if each_specifics_id:
                                        delete = cr.execute('delete from custom_item_specifics where id=%s',(each_specifics_id,))
                else:
                    result['item_specifics_enabled_cat1'] = 'unchecked'
                    if ids:
                        custom_attributes = self.browse(cr,uid,ids[0]).custom_item_specifics_generic
                        if custom_attributes:
                            for each_specifics in custom_attributes:
                                each_specifics_id = each_specifics.id
                                if each_specifics_id:
                                    delete = cr.execute('delete from custom_item_specifics where id=%s',(each_specifics_id,))
        elif cat2:
            item_specifics = self.pool.get('category.master').browse(cr,uid,cat2).item_specifics
            if item_specifics == True:
                result['item_specifics_enabled_cat1'] = 'checked'
            else:
                result['item_specifics_enabled_cat1'] = 'unchecked'
                if ids:
                    custom_attributes = self.browse(cr,uid,ids[0]).custom_item_specifics_generic
                    if custom_attributes:
                        for each_specifics in custom_attributes:
                            each_specifics_id = each_specifics.id
                            if each_specifics_id:
                                delete = cr.execute('delete from custom_item_specifics where id=%s',(each_specifics_id,))
        else:
            result['item_specifics_enabled_cat1'] = 'unchecked'
            result['condtn'] = False
            domain['condtn'] = [('id', 'in', [])]
            if ids:
                custom_attributes = self.browse(cr,uid,ids[0]).custom_item_specifics_generic
                if custom_attributes:
                        for each_specifics in custom_attributes:
                            each_specifics_id = each_specifics.id
                            if each_specifics_id:
                                delete = cr.execute('delete from custom_item_specifics where id=%s',(each_specifics_id,))
        if len(ids):
            attribute_matching = self.browse(cr,uid,ids[0]).match_attribute_ids##for deleting the attributes
            if attribute_matching:
                for each_attribute in attribute_matching:
                    attribute_matching_id = each_attribute.id
                    if attribute_matching_id:
                        delete = cr.execute('delete from attribute_matching where id=%s',(attribute_matching_id,))
        return {'value':result,'domain':domain}

    def onchange_clear_attributes_cat2(self,cr,uid,ids,cat2,cat1,context=None):
        result ={}
        domain = {}
        if cat1:
            condition_ids =  self.pool.get('condition.class').search(cr,uid,[('category_id','=',cat1)])
            condition_enabled =  self.pool.get('category.master').browse(cr,uid,cat1).condition_enabled
            if condition_enabled == False:
                if cat2:
                    condition_enabled =  self.pool.get('category.master').browse(cr,uid,cat2).condition_enabled
                    if condition_enabled == True:
                        condition_ids =  self.pool.get('condition.class').search(cr,uid,[('category_id','=',cat2)])
                        domain['condtn'] = [('id', 'in', condition_ids)]
                    else:
                        domain['condtn'] = [('id', 'in', [])]
                else:
                    domain['condtn'] = [('id', 'in', [])]
            else:
                domain['condtn'] = [('id', 'in', condition_ids)]
            if condition_ids:
                result['condtn'] = condition_ids[0]
            else:
                result['condtn'] = False
            item_specifics = self.pool.get('category.master').browse(cr,uid,cat1).item_specifics
            if item_specifics == True:
                result['item_specifics_enabled_cat1'] = 'checked'
            else:
                if cat2:
                    item_specifics = self.pool.get('category.master').browse(cr,uid,cat2).item_specifics
                    if item_specifics == True:
                        result['item_specifics_enabled_cat1'] = 'checked'
                    else:
                        result['item_specifics_enabled_cat1'] = 'unchecked'
                        if ids:
                            custom_attributes = self.browse(cr,uid,ids[0]).custom_item_specifics_generic
                            if custom_attributes:
                                for each_specifics in custom_attributes:
                                    each_specifics_id = each_specifics.id
                                    if each_specifics_id:
                                        delete = cr.execute('delete from custom_item_specifics where id=%s',(each_specifics_id,))
                else:
                    result['item_specifics_enabled_cat1'] = 'unchecked'
                    if ids:
                        custom_attributes = self.browse(cr,uid,ids[0]).custom_item_specifics_generic
                        if custom_attributes:
                            for each_specifics in custom_attributes:
                                each_specifics_id = each_specifics.id
                                if each_specifics_id:
                                    delete = cr.execute('delete from custom_item_specifics where id=%s',(each_specifics_id,))
        elif cat2:
            item_specifics = self.pool.get('category.master').browse(cr,uid,cat2).item_specifics
            if item_specifics == True:
                result['item_specifics_enabled_cat1'] = 'checked'
            else:
                result['item_specifics_enabled_cat1'] = 'unchecked'
                if ids:
                    custom_attributes = self.browse(cr,uid,ids[0]).custom_item_specifics_generic
                    if custom_attributes:
                        for each_specifics in custom_attributes:
                            each_specifics_id = each_specifics.id
                            if each_specifics_id:
                                delete = cr.execute('delete from custom_item_specifics where id=%s',(each_specifics_id,))
        else:
            result['item_specifics_enabled_cat1'] = 'unchecked'
            result['condtn'] = False
            domain['condtn'] = [('id', 'in', [])]
            if ids:
                custom_attributes = self.browse(cr,uid,ids[0]).custom_item_specifics_generic
                if custom_attributes:
                    for each_specifics in custom_attributes:
                        each_specifics_id = each_specifics.id
                        if each_specifics_id:
                            delete = cr.execute('delete from custom_item_specifics where id=%s',(each_specifics_id,))
        if len(ids):
            attribute_matching = self.browse(cr,uid,ids[0]).match_attribute_cat2
            if attribute_matching:
                for each_attribute in attribute_matching:
                    attribute_matching_id = each_attribute.id
                    ##delete from the attribute matching
                    if attribute_matching_id:
                        delete = cr.execute('delete from attribute_matching where id=%s',(attribute_matching_id,))
        return {'value':result}
    _columns = {
        'name' : fields.char('Template name', size=64,required=True,help="Name of Template"),
        'temp_name':fields.char('Title', size=64,required=True,help="Title of Template"),
        'subtitle':fields.char('Subtitle', size=64,help="Subtitle of Template"),
        'instance_id' : fields.many2one('ebayerp.instance','Instance'),
        'bold_tl':fields.boolean('Bold title',help="If True then Displays Bold Title on Ebay"),
        'ebay_shop' : fields.many2one('sale.shop','Ebay Shop'),
        'condtn':fields.many2one('condition.class','Condition'),
        'sub_title' : fields.char('Subtitle',size=64),
        'description' : fields.text('Description',required=True,help="Template Description"),
        'category_id1' : fields.many2one('category.master','Category1',help="Primary Category"),
        'category_id2' : fields.many2one('category.master','Category2',help="Secondary Category"),
        'atribute_set_id': fields.integer('Attribute Set ID'),
        'match_attribute_ids' : fields.one2many('attribute.matching','shop_id','Attribute Values'),
        'match_attribute_cat2': fields.one2many('attribute.matching','shop_id1','Attribute Values'),
        'attribute_id' : fields.many2many('attribute.master','attribute_template_rel','template_id','attribute_id','Attribute id'),
        'array_ids':fields.char('Array ids',size=64),
        'plcs_holds': fields.one2many('placeholder.holder', 'plc_hld_temp','Place Holder'),
        'custom_item_specifics_generic': fields.one2many('custom.item.specifics','template_cat_gen','Custom Item Specifics'),
        'item_specifics_enabled_cat1':fields.selection([('checked','Checked'),('unchecked','Unchecked')],'Item Specifics Enabled'),
        ###for buyer requirements and also for returns accepted###
        'confg_name' : fields.char('Configuration name', size=64),
        'pay_pal_accnt': fields.boolean('Dont have a PayPal Account',help="""PayPal Account holders have upto an 80% lowerUnpaid Item rate."""),
        'have_rec':fields.boolean('Have recieved'),
        'unpaid_str': fields.selection([('2', '2'),('3', '3'),('4', '4'),('5', '5')],'Unpaid itemStrike(s)',),
        'unpaid_str_wthn': fields.selection([('Days_30', '1 month'),('Days_180', '6 months'),('Days_360', '12 months')],'within',),
        'pri_ship':fields.boolean('Have a primary shipping address in locations that I dont ship to (Add Exclude Locations from MyEbay)'),
        'hv_policy_vio':fields.boolean('Have'),
        'policy_vio': fields.selection([('4', '4'),('5', '5'),('6', '6'),('7', '7')],'Policy violation report(s)',),
        'policy_vio_wthn': fields.selection([('Days_30', '1 month'),('Days_180', '6 months'),],'within',),
        'hv_feed_scr':fields.boolean('Have a feedback score equal to lower than'),
        'feed_scr': fields.selection([('-1', '-1'),('-2', '-2'),('-3', '-3')],'Feed Score',),
        'hv_bid':fields.boolean('Have bid on or bought my items within the last 10 Days and met my limit of'),
        'bid': fields.selection([('1', '1'),('2', '2'),('3', '3'),('4', '4'),('5', '5'),('6', '6'),('7', '7'),('8', '8'),
                                ('9', '9'),('10', '10'),('25', '25'),('50', '50'),('75', '75'),('100', '100')],'Bid',),
        'only_feed_scr':fields.boolean('Only apply this block to buyers who have feedback score equal to or lower than'),
        'feed_scr_lwr': fields.selection([('0', '0'),('1', '1'),('2', '2'),('3', '3'),('4', '4'),('5', '5')],'Feed Score',),
        'priv_list':fields.boolean('Private Listing'),
        'check':fields.boolean('Activate Buyer Requirements',help="Activates Buyer Requirements"),
        'retur_pol': fields.selection([('ReturnsAccepted', 'Returns Accepted'),('ReturnsNotAccepted', 'Returns Not Accepted')],'Return Policy',required=True,help="Specifies Return Policy Details"),
        'add_det' : fields.text('Additional return policy details'),
        'retur_days': fields.selection([('Days_3', '3 Days'),('Days_7', '7 Days'),('Days_14', '14 Days'),('Days_30', '30 Days'),('Days_60', '60 Days')],'Item must be return within',),
        'refund_giv_as': fields.selection([('MoneyBack', 'MoneyBack'),('MerchandiseCredit', 'MerchandiseCredit'),('Exchange', 'Exchange')],'Refund will be given as',),
        'paid_by': fields.selection([('Buyer', 'Buyer'),('Seller', 'Seller')],'Return shipping will be paid by',),
        'add_inst' : fields.text('Additional Checkout Instructions',help="Payment Instructions"),
         ###Domestic shipping fields###
        'ship_type':fields.selection([('Flat', 'Flat:same cost to all buyers'),('Calculated', 'Calculated:Cost varies to buyer location'),('Freight', 'Frieght:large items over 150lbs'),('Free', 'No Shipping: Local pickup only')],'Shipping Type',required=True),
        'pack_type':fields.selection([('Letter', 'Letter'),('LargeEnvelope', 'Large Envelope'),('PackageThickEnvelope', 'Package(or thick package)'),('LargePackage', 'Large Package')],'Package Type'),
        'irreg_pack':fields.boolean('Irregular Package'),
        'min_weight':fields.char('oz', size=5),
        'max_weight':fields.char('lbs', size=5),
        'serv1':fields.many2one('shipping.master','Shipping service',required=True),
#        'related_serv1': fields.related('serv1', 'surch_chk', type='boolean',relation='shipping.master',string='TEST field'),
        'serv1_calc':fields.many2one('shipping.master','Shipping service'),###Calculated
#        'ship_serv': fields.many2many('shipping.master', 'serv1','serv_nm','serv_id', 'Shipping Services'),
        'cost' : fields.char('Cost($)', size=20),
        'each_add' : fields.char('Each Additional($)', size=20),
        'free_ship':fields.boolean('Free Shipping'),
        'serv2_chk':fields.boolean('Activate service'),
        'serv2':fields.many2one('shipping.master','Shipping service'),
        'serv2_calc':fields.many2one('shipping.master','Shipping service'),
        'cost2' : fields.char('Cost($)', size=20),
        'each_add2' : fields.char('Each Additional($)', size=20),
        'serv3_chk':fields.boolean('Activate service'),
        'serv3':fields.many2one('shipping.master','Shipping service'),
        'serv3_calc':fields.many2one('shipping.master','Shipping service'),
        'cost3' : fields.char('Cost($)', size=20),
        'each_add3' : fields.char('Each Additional($)', size=20),
        'serv4_chk':fields.boolean('Activate service'),
        'serv4':fields.many2one('shipping.master','Shipping service'),
        'serv4_calc':fields.many2one('shipping.master','Shipping service'),
        'cost4' : fields.char('Cost($)', size=20),
        'each_add4' : fields.char('Each Additional($)', size=20),
        'add_surch':fields.related('serv1', 'surch_chk', type='boolean',relation='shipping.master',string='TEST field'),
        'loc_pick':fields.boolean('Buyer can pick up the item from you.'),
        'get_it_fast':fields.boolean('Get It Fast',help="""Seller must offer a domestic overnight shipping service and 1 day handling time"""),
        'handling_cost' : fields.char('Handling Cost($)', size=20),
        'hand_time':fields.selection([('1', '1 Business Day'),('2', '2 Business Days'),('3', '3 Business Days'),('4', '4 Business Days'),('5', '5 Business Days'),('10', '10 Business Days'),('15', '15 Business Days'),('20', '20 Business Days'),('30', '30 Business Days')],'Handling Tme',required=True),
                        #####international shipping fields#########
        'int_ship_type':fields.selection([('Flat', 'Flat:same cost to all buyers'),('Calculated', 'Calculated:Cost varies to buyer location')],'Shipping Type'),
        'exclude_loc':fields.many2many('loc.master', 'loc','loc_nm','loc_id', 'Exclude Locations'),
        'inter_chk':fields.boolean('Activate International shipping'),
        'exclude_loct_chk':fields.boolean('Do not add exclude locations from My eBay'),
        'custom_loc':fields.selection([('Worldwide', 'Worldwide'),('customloc', 'Choose Custom Location'),('Canada', 'Canada')],'Ship to'),
        'intr_serv':fields.many2one('shipping.master','Shipping service'),
        'intr_serv_calc1':fields.many2one('shipping.master','Shipping service'),
        'cost_int' : fields.char('Cost($)', size=20),
        'add_int' : fields.char('Additional Cost($)', size=20),
        'add_loc_tab':fields.many2many('ship.loc.master', 'shp_temp_rel','locad_nm','locad_id', 'Additional shipping locations'),
        'custom_loc2':fields.selection([('Worldwide', 'Worldwide'),('customloc', 'Choose Custom Location'),('Canada', 'Canada')],'Ship to'),
        'intr_serv2':fields.many2one('shipping.master','Shipping service'),
        'intr_serv_calc2':fields.many2one('shipping.master','Shipping service'),
        'cost_int2' : fields.char('Cost($)', size=20),
        'add_int2' : fields.char('Additional Cost($)', size=20),
        'add_loc_tab2':fields.many2many('ship.loc.master', 'shp_temp_rel2','locad_nm2','locad_id2', 'Additional shipping locations'),
        'serv2_int_chk':fields.boolean('Activate service'),
        'custom_loc3':fields.selection([('Worldwide', 'Worldwide'),('customloc', 'Choose Custom Location'),('Canada', 'Canada')],'Ship to'),
        'intr_serv3':fields.many2one('shipping.master','Shipping service'),
        'intr_serv_calc3':fields.many2one('shipping.master','Shipping service'),
        'cost_int3' : fields.char('Cost($)', size=20),
        'add_int3' : fields.char('Additional Cost($)', size=20),
        'add_loc_tab3':fields.many2many('ship.loc.master', 'shp_temp_rel3','locad_nm3','locad_id3', 'Additional shipping locations'),
        'serv3_int_chk':fields.boolean('Activate service'),
        'custom_loc4':fields.selection([('Worldwide', 'Worldwide'),('customloc', 'Choose Custom Location'),('Canada', 'Canada')],'Ship to'),
        'intr_serv4':fields.many2one('shipping.master','Shipping service'),
        'intr_serv_calc4':fields.many2one('shipping.master','Shipping service'),
        'cost_int4' : fields.char('Cost($)', size=20),
        'add_int4' : fields.char('Additional Cost($)', size=20),
        'add_loc_tab4':fields.many2many('ship.loc.master', 'shp_temp_rel4','locad_nm4','locad_id4', 'Additional shipping locations'),
        'serv4_int_chk':fields.boolean('Activate service'),
        'custom_loc5':fields.selection([('Worldwide', 'Worldwide'),('customloc', 'Choose Custom Location'),('Canada', 'Canada')],'Ship to'),
        'intr_serv5':fields.many2one('shipping.master','Shipping service'),
        'intr_serv_calc5':fields.many2one('shipping.master','Shipping service'),
        'cost_int5' : fields.char('Cost($)', size=20),
        'add_int5' : fields.char('Additional Cost($)', size=20),
        'add_loc_tab5':fields.many2many('ship.loc.master', 'shp_temp_rel5','locad_nm5','locad_id5', 'Additional shipping locations'),
        'serv5_int_chk':fields.boolean('Activate service'),
        'add_loc':fields.selection([('unitedstates', 'Will ship to United States and the Following'),('Worldwide', 'Will ship worldwide')],'Additional ship to locations'),
        'add_loc_tab_cm':fields.many2many('ship.loc.master', 'shp_temp_rel_add','locad_nm_add','locad_id_add', 'Additional shipping locations'),
        'intr_pack_type':fields.selection([('Letter', 'Letter'),('LargeEnvelope', 'Large Envelope'),('PackageThickEnvelope', 'Package(or thick package)'),('LargePackage', 'Large Package')],'Package Type'),
        'intr_irreg_pack':fields.boolean('Irregular Package'),
        'intr_min_weight':fields.char('oz', size=5),
        'intr_max_weight':fields.char('lbs', size=5),
        'intr_handling_cost' : fields.char('Handling Cost($)', size=20),
        'act_add_loc':fields.boolean('Add Additional locations'),
        }
    _defaults = {
        'retur_pol':'ReturnsNotAccepted',
        'retur_days':'Days_3',
        'refund_giv_as':'MoneyBack',
        'paid_by':'Buyer',
        'unpaid_str':'2',
        'unpaid_str_wthn':'Days_30',
        'policy_vio':'4',
        'policy_vio_wthn':'Days_30',
        'feed_scr':'-1',
        'bid':'1',
        'feed_scr_lwr':'0',
        'handling_cost':'0.00',
        'intr_handling_cost':'0.00',
        'intr_pack_type':'Letter',
        'pack_type':'Letter',
        'ship_type':'Flat',
#        'hand_time':'1',
        'each_add':'0',
        'each_add2':'0',
        'each_add3':'0',
        'each_add4':'0',
#        'act_add_loc': lambda *a: 1,
        'item_specifics_enabled_cat1':'unchecked'
        }
ebayerp_template()

class attribute_matching(osv.osv):
    _name = "attribute.matching"
    def create(self, cr, uid, vals, context={}):
        if vals['attribute_values_id'] or vals['text_field'] != False:
            return super(attribute_matching, self).create(cr, uid, vals, context=context)
        else:
            raise osv.except_osv(_('Warning!'), _("Please select attribute value"))
#
    def write(self, cr, uid, ids, vals, context=None):
        if vals['attribute_values_id'] or vals['text_field'] != False:
            return super(attribute_matching, self).write(cr, uid, ids,vals, context=context)
        else:
            raise osv.except_osv(_('Warning!'), _("Please select attribute value"))

    def onchange_attribute_name(self,cr,uid,ids,attribute_name,context={}):
        if attribute_name:
            result ={}
            one2many = self.pool.get('attribute.master').browse(cr,uid,attribute_name).attribute_values
            if not one2many:
                result['hidden_field'] = 'NULL'
            else:
                result['hidden_field'] = 'hidden'
            return {'value':result}
    _columns = {
    'name' : fields.char('Attribute Value', size=64),
    'attribute_name' : fields.many2one('attribute.master','Attribute Name'),
    'attribute_values_id' :fields.many2one('attribute.value','Attribute Values',),
    'shop_id' :fields.many2one('ebayerp.template','Shop id'),
    'shop_id1': fields.many2one('ebayerp.template','Shop id1'),
    'product_cat1_match' : fields.many2one('product.product','Cat1 Match'),
    'product_cat2_match' :fields.many2one('product.product','Cat2 Match'),
    'text_field':fields.char('Value',size=64),
    'hidden_field':fields.char('Hidden field',size=64),
    }
    
attribute_matching()

class product_listing_templates(osv.osv):
    _name = "product.listing.templates"
    _rec_name = "shop_id"
##################################VALIDATION WHILE SAVING######################
    def create(self,cr,uid,vals,context={}):
        ids = super(product_listing_templates, self).create(cr, uid,vals, context=context)
        shop_id = vals.get('shop_id',False)
        if shop_id:
            shop_name = self.pool.get('sale.shop').browse(cr, uid, shop_id).name
            if ids:
                search_shop_exists = self.search(cr,uid,[('shop_id','=',shop_id),('id','!=',ids)])
                if search_shop_exists:
                    if shop_name:
                        raise osv.except_osv(_('Warning !'), _("This %s Shop already exists")%(shop_name))
#        if vals.get('type',False):
#            if vals['type'] =='Chinese':
#                start_price = vals.get('start_price',False)
#                if not start_price:
#                    raise osv.except_osv(_('Warning !'), _("Please select the Start Price"))
#                reserve_price = vals.get('reserve_price',False)
#                if not reserve_price:
#                    raise osv.except_osv(_('Warning !'), _("Please select the Reserve Price"))
#                buy_it_nw = vals.get('buy_it_nw',False)
#                if not buy_it_nw:
#                    raise osv.except_osv(_('Warning !'), _("Please select the Buy It Now Price"))
#            else:
#                start_price = vals.get('start_price',False)
#                if not start_price:
#                    raise osv.except_osv(_('Warning !'), _("Please select the Start Price"))
        return ids
############################function for scheduled date############################
    def write(self,cr,uid,ids,vals,context={}):
        shop_id = vals.get('shop_id',False)
        if ids:
            if type(ids) == type(int()):
                ids = [ids]
            if type(ids) == type(long()):
                ids = [ids]
            if not shop_id:
                shop_id = self.browse(cr, uid, ids[0]).shop_id.id
            if shop_id:
                shop_name = self.pool.get('sale.shop').browse(cr, uid, shop_id).name
                search_shop_exists = self.search(cr,uid,[('shop_id','=',shop_id),('id','!=',ids)])
                if search_shop_exists:
                    if shop_name:
                        raise osv.except_osv(_('Warning !'), _("This %s Shop already exists")%(shop_name))
#        if vals.get('type',False):
#            if vals['type'] =='Chinese':
#                start_price = vals.get('start_price',False)
#                if not start_price:
#                    raise osv.except_osv(_('Warning !'), _("Please select the Start Price"))
#                reserve_price = vals.get('reserve_price',False)
#                if not reserve_price:
#                    raise osv.except_osv(_('Warning !'), _("Please select the Reserve Price"))
#                buy_it_nw = vals.get('buy_it_nw',False)
#                if not buy_it_nw:
#                    raise osv.except_osv(_('Warning !'), _("Please select the Buy It Now Price"))
#            else:
#                start_price = vals.get('start_price',False)
#                if not start_price:
#                    raise osv.except_osv(_('Warning !'), _("Please select the Start Price"))
        return super(product_listing_templates, self).write(cr, uid, ids, vals, context=context)
#################################function for quantity################
#    def _my_value(self, cr, uid, ids, field_names, getprod_ids, arg, context=None):
#        realstock = 0
#        product_product_obj = self.pool.get('product.product')
#        cr.execute('select distinct product_id, location_id from stock_move where location_id in %s or location_dest_id in %s', (tuple(ids), tuple(ids)))
#        res_products_by_location = sorted(cr.dictfetchall(), key=itemgetter('location_id'))
#        products_by_location = dict((k, [v['product_id'] for v in itr]) for k, itr in groupby(res_products_by_location, itemgetter('location_id')))
#        result = dict([(i, {}.fromkeys(field_names, 0.0)) for i in ids])
#        result.update(dict([(i, {}.fromkeys(field_names, 0.0)) for i in list(set([aaa['location_id'] for aaa in res_products_by_location]))]))
#        currency_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id
#        currency_obj = self.pool.get('res.currency')
#        currency = self.pool.get('res.currency').browse(cr, uid, currency_id)
#        currency_obj.round(cr, uid, currency, 300)
#        for loc_id, product_ids in products_by_location.items():
#            for result_array in result:
#                if result_array != 8:
#                    for prod_id in product_idef _my_valueds:
#                        if prod_id == getprod_ids:
#                            for f in field_names:
#                                if f == 'stock_real':
#                                    prod = product_product_obj
#                                    p_id = prod.browse(cr, uid, prod_id)
#                                    realstock = p_id.qty_available
#        return realstock

    def _my_value(self, cr, uid, location_id, product_id, context=None):
        cr.execute(
            'select sum(product_qty) '\
            'from stock_move '\
            'where location_id NOT IN  %s '\
            'and location_dest_id = %s '\
            'and product_id  = %s '\
            'and state = %s ',tuple([(location_id,), location_id, product_id, 'done']))
        wh_qty_recieved = cr.fetchone()[0] or 0.0
                            #this gets the value which is sold and confirmed
        argumentsnw = [location_id,(location_id,),product_id,( 'done',)]#this will take reservations into account
        cr.execute(
            'select sum(product_qty) '\
            'from stock_move '\
            'where location_id = %s '\
            'and location_dest_id NOT IN %s '\
            'and product_id  = %s '\
            'and state in %s ',tuple(argumentsnw))
        qty_with_reserve = cr.fetchone()[0] or 0.0

        qty_available = wh_qty_recieved - qty_with_reserve
#        realstock = 0
#        child_ids = self.pool.get('stock.location').search(cr,uid,[('location_id','=',ids[0])])
#        if child_ids:
#            for child_id in child_ids:
#                ids.append(child_id)
#        real=0
#        for id in ids:
#            product_product_obj = self.pool.get('product.product')
#            cr.execute('select distinct product_id, location_id from stock_move where location_id in %s or location_dest_id in %s', (tuple([id]), tuple([id])))
#            res_products_by_location = sorted(cr.dictfetchall(), key=itemgetter('location_id'))
#            products_by_location = dict((k, [v['product_id'] for v in itr]) for k, itr in groupby(res_products_by_location, itemgetter('location_id')))
#            result = dict([(i, {}.fromkeys(field_names, 0.0)) for i in ids])
#            result.update(dict([(i, {}.fromkeys(field_names, 0.0)) for i in list(set([aaa['location_id'] for aaa in res_products_by_location]))]))
#            currency_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id
#            currency_obj = self.pool.get('res.currency')
#            currency = self.pool.get('res.currency').browse(cr, uid, currency_id)
#            currency_obj.round(cr, uid, currency, 300)
#            print products_by_location
#            for loc_id, product_ids in products_by_location.items():
#                print product_ids
#                for result_array in result:
#                    if result_array != 8:
#                        for prod_id in product_ids:
#                            if prod_id == getprod_ids:
#                                for f in field_names:
#                                    if f == 'stock_real':
#                                        prod = product_product_obj
#                                        p_id = prod.browse(cr, uid, prod_id)
#                                        realstock = p_id.qty_available
#            real+=realstock
#            realstock=0
#        print"real",real
        return qty_available

 ##########################################################################
    def additem(self, cr, uid, ids, itemId, context=None):
        if type(ids) == type(int()):
            ids = [ids]
        if type(ids) == type(long()):
            ids = [ids]
        list_item = []
        id = 0
        duration = ''
        product_nm = ''
        product_long_message = ''
        siteid = ''
        shop_id = self.browse(cr,uid,ids[0]).shop_id.id
        shop_name =self.browse(cr,uid,ids[0]).shop_id.name
##############################Getting additem details###################################
        inst_lnk = self.browse(cr, uid, ids[0]).shop_id.instance_id
        template_id = self.browse(cr,uid,ids[0]).template_id.id
        template_cat = self.pool.get('ebayerp.template').browse(cr,uid,template_id).category_id1
        template_cat2 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).category_id2
        template_name = self.pool.get('ebayerp.template').browse(cr,uid,template_id).name
        postal_code = self.browse(cr, uid, ids[0]).shop_id.post_code
        if not postal_code:
            raise osv.except_osv(_('Warning !'), _("Please Enter the Postal Code in %s shop")%(shop_name))
        payment_method = self.browse(cr, uid, ids[0]).shop_id.pay_mthd
        if not payment_method:
            raise osv.except_osv(_('Warning !'), _("Please Enter the Payment Method in %s shop")%(shop_name))
        paypal_email = self.browse(cr, uid, ids[0]).shop_id.email_add
        if not paypal_email:
            raise osv.except_osv(_('Warning !'), _("Please Enter the Email Address in %s shop")%(shop_name))
        site_id = self.browse(cr, uid, ids[0]).shop_id.site_id
        if site_id:
            siteid = site_id.site_id
        else:
            raise osv.except_osv(_('Warning !'), _("Please Select Site ID in %s shop")%(shop_name))
        product_ids_many = self.browse(cr,uid,ids[0]).product_ids
        type_list = self.browse(cr,uid,ids[0]).type
        start_pricelist = self.browse(cr,uid,ids[0]).start_price.id
        reserve_pricelist = self.browse(cr,uid,ids[0]).reserve_price.id
        buy_it_now = self.browse(cr,uid,ids[0]).buy_it_nw.id
        if type_list =='Chinese':
            if not start_pricelist:
                 raise osv.except_osv(_('Warning !'), _("Please select the Start Price"))
            if not reserve_pricelist:
                    raise osv.except_osv(_('Warning !'), _("Please select the Reserve Price"))
            if not buy_it_now:
                    raise osv.except_osv(_('Warning !'), _("Please select the Buy It Now Price"))
            type_name = 'Auction'
        elif type_list =='FixedPriceItem':
            if not start_pricelist:
                 raise osv.except_osv(_('Warning !'), _("Please select the Start Price"))
            type_name = 'Fixed Price'
        elif type_list =='LeadGeneration':
            if not start_pricelist:
                 raise osv.except_osv(_('Warning !'), _("Please select the Start Price"))
            type_name = 'Classified Ad'
        listing_duration = self.browse(cr,uid,ids[0]).duration.name
        if listing_duration == 'Days_3':
            duration = "3 Days"
        elif listing_duration == 'Days_5':
            duration = "5 Days"
        elif listing_duration == 'Days_7':
            duration = "7 Days"
        elif listing_duration == 'Days_10':
            duration = "10 Days"
        elif listing_duration == 'Days_30':
            duration = "30 Days"
        elif listing_duration == 'Days_90':
            duration = "90 Days"
        scheduled_time = self.browse(cr,uid,ids[0]).schedule_time
        try:
            if inst_lnk:
                results = self.call(cr, uid, inst_lnk, 'GeteBayOfficialTime',siteid)
        except Exception, e:
            raise osv.except_osv(_('Error !'),e)
            return False
#######################################################
        inst_list = self.browse(cr,uid,ids[0]).inst_list_chk
        FMT = '%Y-%m-%d %H:%M:%S'
        utc_tm = datetime.utcnow()
        utc_trunk = str(utc_tm)[:19]
        difft_time = datetime.utcnow() - datetime.now()
        if scheduled_time:
            schedule_time2 = datetime.strptime(scheduled_time, FMT) + difft_time
            schedule_time3 = str(schedule_time2)[:19]
            schedule_time5 = schedule_time3
            schedule_time = datetime.strptime(schedule_time5, FMT)
####################################End of schedule time####################
        deleted_product = []
        i=1
        k = 1
        l = 1
        m =1
        n =1
        message_cat_template2 = ''
        message_cat_product2 = ''
#        j=1
        product_names = ''
        message_cat_product = ''
        message_cat_template = ''
#        product_names_sku = ''
        for product_ids in product_ids_many:
            product_id = product_ids.id
            name = product_ids.name
#            ebay_sku = self.pool.get('product.product').browse(cr,uid,product_id).ebay_sku
#            if ebay_sku == False:
#                product_names_sku += """  %s.%s """ % (j,name)
#                j=j+1
            product_cat =self.pool.get('product.product').browse(cr,uid,product_id).cat1
            if not product_cat:
                if not template_cat:
                    product_names += """  %s.%s """ % (i,name)
                    i=i+1
                else:
                    site_id_template_cat = template_cat.site_id
                    if site_id_template_cat != site_id:
                        message_cat_template += """ %s.%s""" % (l,template_name)
                        l=l+1
            else:
                site_id_cat = product_cat.site_id
                if site_id_cat != site_id:
                    message_cat_product += """ %s.%s """ % (k,name)
                    k=k+1
            product_cat2 =self.pool.get('product.product').browse(cr,uid,product_id).cat2
            if not product_cat2:
                if template_cat2:
                    site_id_template_cat2 = template_cat2.site_id
                    if site_id_template_cat2 != site_id:
                        message_cat_template2 += """ %s.%s""" % (m,template_name)
                        m=m+1
            else:
                site_id_cat2 = product_cat2.site_id
                if site_id_cat2 != site_id:
                    message_cat_product2 += """ %s.%s""" % (n,name)
                    n = n+1
            warehouse_id = self.pool.get('sale.shop').browse(cr,uid,shop_id).warehouse_id.id
            location_id = self.pool.get('stock.warehouse').browse(cr,uid,warehouse_id).lot_stock_id.id
            function_call = self.pool.get('product.listing.templates')._my_value(cr, uid,location_id,product_id,context={})
            if function_call == 0:
                cr.execute('delete from add_prod_rel where prod_id=%d' %(product_id,))
                deleted_product.append(product_id)
#        if product_names and product_names_sku:
#            raise osv.except_osv(_('Warning!'), _("Please select the category in Product or Template for this %s product and Enter SKU for this %s")%(product_names,product_names_sku))
        if product_names:
            raise osv.except_osv(_('Warning!'), _("Please Select the Category In Product or Template For %s")%(product_names))
#        elif product_names_sku:
#            raise osv.except_osv(_('Warning!'), _("Please Enter SKU for this %s")%(product_names_sku))
        if message_cat_product:
            raise osv.except_osv(_('Warning!'), _("Please Select the Proper Primary Category for %s because Site ID of Category and Shop Differs")%(message_cat_product))
        elif message_cat_template:
            raise osv.except_osv(_('Warning!'), _("Please Select the Proper Primary Category for %s because Site ID of Category and Shop Differs")%(message_cat_template))
        if message_cat_product2:
            raise osv.except_osv(_('Warning!'), _("Please Select the Proper Secondary Category for %s because Site ID of Category and Shop Differs")%(message_cat_product2))
        elif message_cat_template2:
            raise osv.except_osv(_('Warning!'), _("Please Select the Proper Secondary Category for %s because Site ID of Category and Shop Differs")%(message_cat_template2))
        product_ids_many = self.browse(cr,uid,ids[0]).product_ids
        for product_ids in product_ids_many:
            if inst_list == True:
                utc_tm = datetime.utcnow()
                logger.notifyChannel('init', netsvc.LOG_WARNING, ' UTC TIME  %s ###'%(utc_tm))
                utc_trunk = str(utc_tm)[:19]
                inst_time = datetime.strptime(utc_trunk, FMT) + timedelta(seconds=30)
                schedule_time = inst_time
            product_id = product_ids.id
            subtitle = self.pool.get('ebayerp.template').browse(cr,uid,template_id).subtitle
            product_search = self.pool.get('placeholder.holder').search(cr,uid,[('plc_hld','=',product_id)])
#########################################Getting Key Values from template and Product level##########
            plc_holder_chk = self.pool.get('placeholder.holder').search(cr,uid,[('plc_hld_temp','=',template_id)])
            place_obj = self.pool.get('placeholder.holder')
            subtitle_dict = {}
            for prod in product_search:
                place_id_obj = place_obj.browse(cr,uid,prod)
                name = place_id_obj.name
                value = place_id_obj.value
                subtitle_dict[name] = value
            for place in plc_holder_chk:
                place_id_obj = place_obj.browse(cr,uid,place)
                name = place_id_obj.name
                value = place_id_obj.value
                if subtitle_dict.has_key(name):
                    print"subtitle_dict.has_key(name)",subtitle_dict.has_key(name)
                else:
                    subtitle_dict[name] = value
###############################Replacing values in subtitle###########################
            subtitle = self.pool.get('ebayerp.template').browse(cr,uid,template_id).subtitle
            if subtitle:
               subtitle_split  = subtitle.split(' ')
               for each_subtitle in subtitle_split:
                   each_sub_string = str(each_subtitle)
                   if each_sub_string != '':
                       first_pos = each_sub_string.find('%')
                       if first_pos != -1:
                           last_post = each_sub_string.rfind('%')
                           if last_post != first_pos:
                               string = each_sub_string[first_pos+1:last_post]
                               new_string =each_sub_string.replace('%',' ')
                               replace_str = subtitle.replace(each_sub_string,new_string)
                               if subtitle_dict.has_key(string):
                                   place_holder_val_str_temp = subtitle_dict.get(string)
                                   subtitle_replace_temp = replace_str.replace(string,place_holder_val_str_temp)
                               else:
                                   place_holder_val_str_temp = ''
                                   subtitle_replace_temp = replace_str.replace(string,place_holder_val_str_temp)
                               subtitle = subtitle_replace_temp
                       subtitle_spl = subtitle
               subtitle_finals = subtitle_spl
               subtitle_final = subtitle_finals[:55]
            else:
               subtitle_final = ""
####################################################Replacing values in subtitle#################################
            description_field = self.pool.get('ebayerp.template').browse(cr,uid,template_id).description
            if description_field:
               description_new = description_field.replace('\n',' ')
               description_split  = description_new.split(' ')
               for each_split in description_split:
                   each_string = str(each_split)
                   if each_string != '':
                       first_pos = each_string.find('%')
                       if first_pos != -1:
                           last_post = each_string.rfind('%')
                           if last_post != first_pos:
                               string = each_string[first_pos+1:last_post]
                               if subtitle_dict.has_key(string):
                                   place_holder_val_str_temp = subtitle_dict.get(string)
                                   description_new = description_new.replace('%'+string+'%',place_holder_val_str_temp)
                               else:
                                   place_holder_val_str_temp = ''
#                                   subtitle_replace_temp = replace_str.replace(string,place_holder_val_str_temp)
                                   description_new = description_new.replace('%'+string+'%',place_holder_val_str_temp)
               description_final = description_new
            else:
               raise osv.except_osv(_('Warning !'), _("Please Enter the Description in title"))
#############################################Replacing Title####################################
            title = self.pool.get('ebayerp.template').browse(cr,uid,template_id).temp_name
            if title:
               title_split  = title.split(' ')
               for each_split in title_split:
                   each_string = str(each_split)
                   if each_string != '':
                       first_pos = each_string.find('%')
                       if first_pos != -1:
                           last_post = each_string.rfind('%')
                           if last_post != first_pos:
                               string = each_string[first_pos+1:last_post]
                               new_string =each_string.replace('%',' ')
                               replace_str = title.replace(each_string,new_string)
                               if subtitle_dict.has_key(string):
                                   place_holder_val_str_temp = subtitle_dict.get(string)
                                   subtitle_replace_temp = replace_str.replace(string,place_holder_val_str_temp)
                               else:
                                   place_holder_val_str_temp = ''
                                   subtitle_replace_temp = replace_str.replace(string,place_holder_val_str_temp)
                               title = subtitle_replace_temp
                       title_spl=title
               title_finals = title_spl
               title_final = title_finals[:80]
            else:
               raise osv.except_osv(_('Warning !'), _("Please Enter the Title in Template"))
            if type_list=="Chinese":
                get_reserve_price = self.pool.get('product.pricelist').price_get(cr,uid,[reserve_pricelist],product_id,1,None,None)
                get_reserve_price_val = get_reserve_price[reserve_pricelist]
                get_start_price = self.pool.get('product.pricelist').price_get(cr,uid,[start_pricelist],product_id,1,None,None)
                get_start_price_val = get_start_price[start_pricelist]
                get_buy_it_now = self.pool.get('product.pricelist').price_get(cr,uid,[buy_it_now],product_id,1,None,None)
                get_buy_it_price_val = get_buy_it_now[buy_it_now]
                write_start_price = self.pool.get('product.product').write(cr,uid,product_id,{'start_price':get_start_price_val,'reserve_price':get_reserve_price_val,'buy_it_now_price':get_buy_it_price_val})

            else:
                get_start_price = self.pool.get('product.pricelist').price_get(cr,uid,[start_pricelist],product_id,1,None,None)
                get_start_price_val = get_start_price[start_pricelist]
                write_start_price = self.pool.get('product.product').write(cr,uid,product_id,{'start_price':get_start_price_val})
            ebay_sku = product_ids.ebay_sku
######################################
            product_nm = self.pool.get('product.product').browse(cr,uid,product_id).name_template
            results = self.pool.get('sale.shop').call(cr, uid, inst_lnk, 'AddItem',ids, product_id,title_final,description_final,type_list,schedule_time, listing_duration,ebay_sku,subtitle_final,postal_code,siteid)
            ack = results.get('Ack',False)
            if ack =='Failure':
                if results.get('LongMessage',False):
                   long_message = results['LongMessage']
                   for each_messsge in long_message:
                       severity_code = each_messsge[0]['SeverityCode']
                       if severity_code == 'Error':
                           Longmessage = each_messsge[0]['LongMessage']
                           product_long_message = ('Error : This %s Product Cannot be Listed Because:') % (product_nm)+ ' ' + Longmessage
                           id += 1
                           self.log(cr, uid,id, product_long_message)
            if ack =='Warning':
                 if results.get('LongMessage',False):
                   long_message = results['LongMessage']
                   for each_messsge in long_message:
                       severity_code = each_messsge[0]['SeverityCode']
                       if severity_code == 'Warning':
                           Longmessage = each_messsge[0]['LongMessage']
                           product_long_message = ('Warning : %s:') % (product_nm)+ ' ' + Longmessage
                           id += 1
                           self.log(cr, uid,id, product_long_message)
            item_id = results.get('ItemID',False)
            if item_id:
                endtime = results.get('EndTime',False)
                end_tm = self.pool.get('ebayerp.instance').openerpFormatDate(endtime)
                ebay_end_tm1 = datetime.strptime(end_tm, FMT) - difft_time
                ebay_end_tm2 = str(ebay_end_tm1)[:19]
                ebay_end_tm = ebay_end_tm2
                start_time = results.get('StartTime',False)
                start_tm = self.pool.get('ebayerp.instance').openerpFormatDate(start_time)
                start_tm1 = datetime.strptime(start_tm, FMT) - difft_time
                start_tm2 = str(start_tm1)[:19]
                start_tm = start_tm2
####################################mentioing the template of the particular product###################
#                assign_template = self.pool.get('product.product').write(cr,uid,product_id,{'related_template': template_id})
########################assigning the values to the one2many field##############
                listing_details = self.pool.get('product.listing').create(cr,uid,{
                'name': item_id,
                'ebay_name': title_final,
                'prod_list':product_id,
                'shop_id':shop_id,
                'ebay_end_time':ebay_end_tm,
                'start_time':start_tm,
                'type': type_name,
                'related_template': template_id,
                'listing_duration': duration,
                 })
                start_time = self.pool.get('product.listing').browse(cr,uid,listing_details).start_time
                end_time = self.pool.get('product.listing').browse(cr,uid,listing_details).ebay_end_time
                new_start_time = datetime.strptime(start_tm, "%Y-%m-%d %H:%M:%S" )
                new_end_time = datetime.strptime(ebay_end_tm, "%Y-%m-%d %H:%M:%S" )
                calculation = new_end_time - new_start_time
#                write = self.pool.get('product.listing').write(cr,uid,listing_details,{'time_remain':calculation})
                cr.execute("UPDATE product_listing SET time_remain='%s' where id=%d"%(calculation,listing_details,))
                cr.commit()
                list_item.append(product_id)
        if deleted_product:
           for each_product in deleted_product:
              product_name =self.pool.get('product.product').browse(cr,uid,each_product).name_template
              id += 1
              messagetoappend = _("%s Product Cannot be Listed Because Its Quantity is Zero") % product_name
              self.log(cr, uid,id, messagetoappend)
        if list_item:
           for each_list_product in list_item:
              product_name =self.pool.get('product.product').browse(cr,uid,each_list_product).name_template
              id += 1
              delete = cr.execute('delete from add_prod_rel where prod_id=%s and shop_id=%s',(each_list_product,ids[0]))
              list_message = _("%s Product Listed Successfully On Ebay") % product_name
              self.log(cr, uid,id, list_message)
        return
    def onchange_listing_type(self,cr,uid,ids,type):
        result = {}
        if type:
            search_duration = self.pool.get('duration.time').search(cr,uid,[('type','=',type)])
            if search_duration:
                result['duration'] = search_duration[0]
        return{'value':result}
    _columns = {
        'name' :fields.char('Name',size=64),
        'shop_id' : fields.many2one('sale.shop','Shop',required=True,help="Shop on which products to be listed"),
        'template_id': fields.many2one('ebayerp.template','Template',required=True,help="Selected Template Configuration will be applied to the Listing Products"),
        'product_id' : fields.many2one('product.product','Products'),
        'product_ids' : fields.many2many('product.product','add_prod_rel','shop_id','prod_id','Products'),
        'type' : fields.selection([('Chinese','Auction'),('FixedPriceItem','Fixed Price'),('LeadGeneration','Classified Ad')],'Type',required=True,help="Type in which Products to be listed"),
        'schedule_time' : fields.datetime('Scheduled Time',help="Time At which the product will be active on Ebay"),
        'start_price':fields.many2one('product.pricelist','Start Price',required=False,help="Selected Pricelist will be applied to the Listing Products"),
        'reserve_price':fields.many2one('product.pricelist','Reserve Price',required=False,help="Selected Pricelist will be applied to the Listing Products"),
        'buy_it_nw':fields.many2one('product.pricelist','Buy It Now Price',required=False,help="Selected Pricelist will be applied to the Listing Products"),
        'duration': fields.many2one('duration.time','Duration',required=True,help="Duration Of the Product on Ebay"),
        'ebay_name':fields.char('Ebay Title',size=64),
        'inst_list_chk' : fields.boolean('Start Listing Immediately',help="Will Active Product Immediately on Ebay"),
        
    }
    _defaults = {
        'type': 'Chinese',
        'start_price':1,
        'reserve_price':1,
        'buy_it_nw':1,
        'inst_list_chk':True,
    }
product_listing_templates()

class product_listing_templates(ebayerp_osv.ebayerp_osv):
    _inherit = "product.listing.templates"
    _name = "product.listing.templates"
product_listing_templates()


###########class for custom_item_specifics########
class custom_item_specifics(osv.osv):
    _name = "custom.item.specifics"
    _columns = {
    'name' : fields.char('Custom Item specifics', size=64),
    'custom_name' : fields.char('Name',size=50),
    'custom_value' :fields.char('Value',size=50),
    'template_cat_gen':fields.many2one('ebayerp.template','Template cat generic'),
    'product_cat_gen':fields.many2one('product.product','Product cat generic'),
    }
custom_item_specifics()
