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
from datetime import date, timedelta
from time import gmtime, strftime
from datetime import datetime
import netsvc
logger = netsvc.Logger()
from tools.translate import _

class ebayerp_relist(osv.osv):
    _name = "ebayerp.relist"
#######################################create function#########################################
    def create(self,cr,uid,vals,context={}):
        ids = super(ebayerp_relist, self).create(cr, uid, vals, context=context)
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
#########################write function############################################
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
                shop_id = shop_id
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
        return super(ebayerp_relist, self).write(cr, uid, ids, vals, context=context)
#    
    def relist_products(self, cr, uid, ids, context=None):
        product_nm = ''
        list_item = []
        increment = 0
        duration = ''
        product_long_message = ''
        site_id = ''
        if type(ids) == type(int()):
            ids = [ids]
        if type(ids) == type(long()):
            ids = [ids]
        shop_id = self.browse(cr, uid, ids[0]).shop_id.id
        shop_name =self.browse(cr,uid,ids[0]).shop_id.name
        site_id = self.browse(cr, uid, ids[0]).shop_id.site_id
        if site_id:
            siteid = site_id.site_id
        else:
            raise osv.except_osv(_('Warning !'), _("Please Select Site ID in %s shop")%(shop_name))
######################For time##################
        inst_lnk = self.browse(cr, uid, ids[0]).shop_id.instance_id
        try:
            results = self.call(cr, uid, inst_lnk, 'GeteBayOfficialTime',siteid)
        except Exception, e:
            raise osv.except_osv(_('Error !'),e)
            return False
        template_id = self.browse(cr,uid,ids[0]).template_id.id
        template_cat = self.pool.get('ebayerp.template').browse(cr,uid,template_id).category_id1
        template_cat2 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).category_id2
        shop_lnk = self.browse(cr, uid, ids, context)[0].shop_id
        postal_code = shop_lnk.post_code
        if not postal_code:
            raise osv.except_osv(_('Warning !'), _("Please Enter the Postal Code in %s shop")%(shop_name))
        payment_method = self.browse(cr, uid, ids[0]).shop_id.pay_mthd
        if not payment_method:
            raise osv.except_osv(_('Warning !'), _("Please Enter the Payment Method in %s shop")%(shop_name))
        paypal_email = self.browse(cr, uid, ids[0]).shop_id.email_add
        if not paypal_email:
            raise osv.except_osv(_('Warning !'), _("Please Enter the Email Address in %s shop")%(shop_name))
        product_ids_many = self.browse(cr,uid,ids[0]).rel_prod
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
        list_durtn = self.browse(cr,uid,ids[0]).list_durtn.name
        if list_durtn == 'Days_3':
           duration = "3 Days"
        elif list_durtn == 'Days_5':
           duration = "5 Days"
        elif list_durtn == 'Days_7':
           duration = "7 Days"
        elif list_durtn == 'Days_10':
           duration = "10 Days"
        elif list_durtn == 'Days_30':
           duration = "30 Days"
        elif list_durtn == 'Days_90':
           duration = "90 Days"
        scheduled_time = self.browse(cr,uid,ids[0]).schedule_time
##################################Schedule Time logic starts############################
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
##################################Schedule Time logic ends############################
        deleted_product = []
        product_names = ''
#        product_names_sku = ''
        i=1
#        j=1
        k = 1
        l = 1
        m =1
        n =1
        message_cat_template2 = ''
        message_cat_product2 = ''
        message_cat_product = ''
        message_cat_template = ''
        for product_ids in product_ids_many:
           product_id = product_ids.id
           name = product_ids.name
#           ebay_sku = self.pool.get('product.product').browse(cr,uid,product_id).ebay_sku
#           if ebay_sku == False:
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
                        message_cat_template += """ %s.%s""" % (l,name)
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
                        message_cat_template2 += """ %s.%s""" % (m,name)
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
            raise osv.except_osv(_('Warning!'), _("Please select the category in Product or Template for this %s")%(product_names))
#        elif product_names_sku:
#            raise osv.except_osv(_('Warning!'), _("Please Enter SKU for this %s")%(product_names_sku))
        if message_cat_product:
            raise osv.except_osv(_('Warning!'), _("Please select the Proper Primary Category for %s because Site ID of Category and Shop Differs")%(message_cat_product))
        elif message_cat_template:
            raise osv.except_osv(_('Warning!'), _("Please select the Proper Primary Category for %s because Site ID of Category and Shop Differs")%(message_cat_template))

        if message_cat_product2:
            raise osv.except_osv(_('Warning!'), _("Please select the Proper Secondary Category for %s because Site ID of Category and Shop Differs")%(message_cat_product2))
        elif message_cat_template2:
            raise osv.except_osv(_('Warning!'), _("Please select the Proper Secondary Category for %s because Site ID of Category and Shop Differs")%(message_cat_template2))
        product_ids_many = self.browse(cr,uid,ids[0]).rel_prod
##################filtering expired products from product listing for ############
        for product_ids in product_ids_many:
            if inst_list == True:
                utc_tm = datetime.utcnow()
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
####################################################Replacing values in Description#################################
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
                                   description_new = description_new.replace('%'+string+'%',place_holder_val_str_temp)
               description_final = description_new
            else:
               raise osv.except_osv(_('Warning !'), _("Please Enter the Description in title"))
####################################Replacing title##########################################
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
            cr.execute('Select max(ebay_end_time) from product_listing where shop_id=%s and prod_list=%s',(shop_id,product_id,))
            id = filter(None, map(lambda x:x[0], cr.fetchall()))
            cr.execute('Select name from product_listing where ebay_end_time=%s',(id))
            item_id = filter(None, map(lambda x:x[0], cr.fetchall()))
            new_item_id = item_id[0]
##### From add items to relist########
#            if type_list=="Chinese":
#                get_reserve_price = self.pool.get('product.pricelist').price_get(cr,uid,[reserve_pricelist],product_id,1,None,None)
#                get_reserve_price_val = get_reserve_price[reserve_pricelist]
#                get_start_price = self.pool.get('product.pricelist').price_get(cr,uid,[start_pricelist],product_id,1,None,None)
#                get_start_price_val = get_start_price[start_pricelist]
#                get_buy_it_now = self.pool.get('product.pricelist').price_get(cr,uid,[buy_it_now],product_id,1,None,None)
#                get_buy_it_price_val = get_buy_it_now[buy_it_now]
#            else:
#                get_start_price = self.pool.get('product.pricelist').price_get(cr,uid,[start_pricelist],product_id,1,None,None)
#                get_start_price_val = get_start_price[start_pricelist]
            ebay_sku = product_ids.ebay_sku
            product_nm = self.pool.get('product.product').browse(cr,uid,product_id).name_template
            results =  self.call(cr, uid, inst_lnk, 'RelistItem',ids,product_id,new_item_id,title_final,description_final, type_list,schedule_time,list_durtn,ebay_sku,subtitle_final,postal_code,siteid)
            ack = results.get('Ack',False)
            if ack =='Failure':
                if results.get('LongMessage',False):
                       long_message = results['LongMessage']
                       for each_messsge in long_message:
                           severity_code = each_messsge[0]['SeverityCode']
                           if severity_code == 'Error':
                               Longmessage = each_messsge[0]['LongMessage']
                               product_long_message = ('Error : This %s product cannot be relisted because:') % (product_nm)+ ' ' + Longmessage
                               increment += 1
                               self.log(cr, uid,increment, product_long_message)
            if ack =='Warning':
                if results.get('LongMessage',False):
                   long_message = results['LongMessage']
                   for each_messsge in long_message:
                       severity_code = each_messsge[0]['SeverityCode']
                       if severity_code == 'Warning':
                           Longmessage = each_messsge[0]['LongMessage']
                           product_long_message = ('Warning : %s:') % (product_nm)+ ' ' + Longmessage
                           increment += 1
                           self.log(cr, uid,increment, product_long_message)
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
#                assign_template = self.pool.get('product.product').write(cr,uid,product_id,{'related_template': template_id})
                listing_details = self.pool.get('product.listing').create(cr,uid,{
                'name': item_id,
                'ebay_name': title_final,
                'prod_list':product_id,
                'shop_id':shop_id,
                'ebay_end_time':ebay_end_tm,
                'start_time':start_tm,
            #            'ebay_item_id':item_id,
                'type': type_name,
                'related_template': template_id,
                'listing_duration': duration,
                 })
                start_time = self.pool.get('product.listing').browse(cr,uid,listing_details).start_time
                end_time = self.pool.get('product.listing').browse(cr,uid,listing_details).ebay_end_time
                new_start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S" )
                new_end_time = datetime.strptime(ebay_end_tm, "%Y-%m-%d %H:%M:%S" )
                calculation = new_end_time - new_start_time
#                write = self.pool.get('product.listing').write(cr,uid,listing_details,{'time_remain':calculation})
                cr.execute("UPDATE product_listing SET time_remain='%s' where id=%d"%(calculation,listing_details,))
                cr.commit()
                list_item.append(product_id)
        if deleted_product:
           for each_product in deleted_product:
              product_name =self.pool.get('product.product').browse(cr,uid,each_product).name_template
              increment += 1
              messagetoappend = _("%s product cannot be listed because quantity is zero") % product_name
              self.log(cr, uid,increment, messagetoappend)
        if list_item:
           for each_list_product in list_item:
              product_name =self.pool.get('product.product').browse(cr,uid,each_list_product).name_template
              increment += 1
              delete = cr.execute('delete from shop_prod_rel where prod_id=%s and shop_id=%s',(each_list_product,ids[0]))
              list_message = _("%s product relisted successfully on ebay") % product_name
              self.log(cr, uid,increment, list_message)
        return
    def onchange_listing_type(self,cr,uid,ids,type):
        result = {}
        if type:
            search_duration = self.pool.get('duration.time').search(cr,uid,[('type','=',type)])
            if search_duration:
                result['list_durtn'] = search_duration[0]
        return{'value':result}
    _rec_name = 'shop_id'
    _columns = {
#        'name' :fields.char('Name',size=64),
       'shop_id' : fields.many2one('sale.shop','Ebay Shop',required=True,help="Shop on which products to be relisted"),
       'rel_prod' : fields.many2many('product.product','shop_prod_rel','shop_id','prod_id','List of Expired Products'),
       'schedule_time':fields.datetime('Schedule Time'),
       'list_durtn' : fields.many2one('duration.time','Duration',required=True,help="Duration Of the Product on Ebay"),
       'template_id': fields.many2one('ebayerp.template','Template',required=True,help="Selected Template Configuration will be applied to the Listing Products"),
       'ebay_current_time':fields.datetime('Ebay Current Time'),
       'type': fields.selection([('Chinese','Auction'),('FixedPriceItem','Fixed Price'),('LeadGeneration','Classified Ad')],'Type',required=True,help="Type in which Products to be listed"),
       'start_price':fields.many2one('product.pricelist','Start Price',help="Selected Pricelist will be applied to the Listing Products"),
       'reserve_price':fields.many2one('product.pricelist','Reserve Price',help="Selected Pricelist will be applied to the Listing Products"),
       'buy_it_nw':fields.many2one('product.pricelist','Buy It Now Price',help="Selected Pricelist will be applied to the Listing Products"),
       'condtn':fields.selection([('1000','New'),('1500','New other (see details)'),('2000','Manufacturer refurbished'),('2500','Seller refurbished'),('3000','Used'),('7000','For parts or not working')],'Condition'),
       'inst_list_chk' : fields.boolean('Start listing immediately',help="Will Active Product Immediately on Ebay"),
    }
    _defaults = {
        'type': 'Chinese',
        'inst_list_chk':True,
        'start_price':1,
        'reserve_price':1,
        'buy_it_nw':1
    }
#    _sql_constraints = [
#        ('shop_uniq_completed', 'unique(shop_id)', 'This shop is already created !'),
#    ]
ebayerp_relist()

class ebayerp_relist(ebayerp_osv.ebayerp_osv):
    _name = "ebayerp.relist"
    _inherit = "ebayerp.relist"
ebayerp_relist()

class ebayerp_manage(osv.osv):
    _name = "ebayerp.manage"
    def create(self,cr,uid,vals,context={}):
        ids = super(ebayerp_manage, self).create(cr, uid, vals, context=context)
        shop_id = vals.get('shop_id',False)
        if shop_id:
            shop_name = self.pool.get('sale.shop').browse(cr, uid, shop_id).name
            if ids:
                search_shop_exists = self.search(cr,uid,[('shop_id','=',shop_id),('id','!=',ids)])
                if search_shop_exists:
                    if shop_name:
                        raise osv.except_osv(_('Warning !'), _("This %s Shop already exists")%(shop_name))
        
        return ids
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
                shop_id = shop_id
                shop_name = self.pool.get('sale.shop').browse(cr, uid, shop_id).name
                search_shop_exists = self.search(cr,uid,[('shop_id','=',shop_id),('id','!=',ids)])
                if search_shop_exists:
                    if shop_name:
                        raise osv.except_osv(_('Warning !'), _("This %s Shop already exists")%(shop_name))
        return super(ebayerp_manage, self).write(cr, uid, ids, vals, context=context)
####################################function for importing products################################3
    def import_ebay_products(self, cr, uid, ids, context=None):
        increment = 0
        siteid = ''
        shop_id = self.browse(cr,uid,ids[0]).shop_id.id
        shop_name = self.browse(cr,uid,ids[0]).shop_id.name
        inst_lnk = self.pool.get('sale.shop').browse(cr, uid, shop_id).instance_id
        site_id = self.pool.get('sale.shop').browse(cr, uid, shop_id).site_id
        if site_id:
            siteid =  site_id.site_id
        else:
            raise osv.except_osv(_('Warning !'), _("Please Select Site ID in %s shop")%(shop_name))
        FMT = '%Y-%m-%d %H:%M:%S'
        now_tm = datetime.now()
        current_now = str(now_tm)[:19]
        now_utc = datetime.now(timezone('UTC'))
        now_utc1 = str(now_utc)[:19]
        ########################Timezone Logic########################
        timezone_time = self.pool.get('res.users').browse(cr,uid,uid).context_tz
        if timezone_time:
            current_timezone = now_utc.astimezone(timezone(timezone_time))
            current_timezone = str(current_timezone)[:19]
        else:
           current_timezone = current_now
        ###############################################################
        difft_time = datetime.strptime(now_utc1, FMT) - datetime.strptime(current_timezone, FMT)
        currnt_diff = datetime.strptime(current_now, FMT) - datetime.strptime(current_timezone, FMT)
        try:
            currentTimeTo = self.call(cr, uid, inst_lnk, 'GeteBayOfficialTime',siteid)
            currentTimeTo = time.strptime(currentTimeTo, "%Y-%m-%d %H:%M:%S")
            currentTimeTo = time.strftime("%Y-%m-%dT%H:%M:%S.000Z",currentTimeTo)
        except Exception, e:
            raise osv.except_osv(_('Error !'),e)
            return False
        currentTimeFrom1 = self.browse(cr,uid,ids[0]).last_ebay_catalog_import_date
        if not currentTimeFrom1:
#            currentTimeFrom = currentTimeTo
            currentTime = datetime.strptime(currentTimeTo, "%Y-%m-%dT%H:%M:%S.000Z")
            now = currentTime - timedelta(days=119)
            currentTimeFrom = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        else:
            currentTimeFrom = datetime.strptime(currentTimeFrom1, FMT) - currnt_diff
            currentTimeFrom = currentTimeFrom + difft_time
        print"currentTimeFrom",currentTimeFrom
        results = self.call(cr, uid, inst_lnk, 'GetSellerList',currentTimeFrom,currentTimeTo,siteid)
        print"results",results
        ack = results.get('Ack',False)
        if ack =='Success':
            if results.get('Item',False):
                product_id = False
                for result in results["Item"]:
                    custom_label = False
                    result_item = self.call(cr, uid, inst_lnk, 'GetItem',result['ItemID'],siteid)
                    if result_item:
                        product_id = self.pool.get('ebayerp.instance').createProduct(cr,uid,ids[0],shop_id,result_item[0]['ItemID'],custom_label,result_item[0],context)
                        if product_id:
                            product_name = self.pool.get('product.product').browse(cr,uid,product_id).name_template
                            message = _('%s has been included in OpenERP' % (product_name))
                            increment += 1
                            self.log(cr, uid, increment, message)
            else:
                message = _('No more products to import')
                self.log(cr, uid, ids[0], message)
        elif ack =='Failure':
            if results.get('LongMessage',False):
               long_message = results['LongMessage']
               for each_messsge in long_message:
                   severity_code = each_messsge[0]['SeverityCode']
                   if severity_code == 'Error':
                       Longmessage = each_messsge[0]['LongMessage']
                       long_message = ('Error : %s') % (Longmessage)
                       increment += 1
                       self.log(cr, uid,increment, long_message)
        elif ack =='Warning':
            if results.get('LongMessage',False):
               long_message = results['LongMessage']
               for each_messsge in long_message:
                   severity_code = each_messsge[0]['SeverityCode']
                   if severity_code == 'Warning':
                       Longmessage = each_messsge[0]['LongMessage']
                       long_message = ('Warning : %s') % (Longmessage)
                       increment += 1
                       self.log(cr, uid,increment, long_message)
        else:
            message = _('No more products to import')
            self.log(cr, uid, ids[0], message)
        self.write(cr,uid,ids[0],{'last_ebay_catalog_import_date':current_now})
#        cr.execute("UPDATE ebayerp_manage SET last_ebay_catalog_import_date=%s where id=%d"%(current_now,ids[0],))
#        cr.commit()
        return True
###########################################function for getting products in the orders#########################
    def import_product(self, cr, uid, shop_id, itemId, context=None):
        logger.notifyChannel('init', netsvc.LOG_WARNING, 'sale.py itemId %s'%(itemId,))
        search_shop = self.search(cr,uid,[('shop_id','=',shop_id)])
        shop_id = self.browse(cr,uid,search_shop[0]).shop_id.id
        siteid = ''
        inst_lnk = self.pool.get('sale.shop').browse(cr, uid, shop_id).instance_id
        site_id = self.pool.get('sale.shop').browse(cr, uid, shop_id).site_id
        shop_name = self.pool.get('sale.shop').browse(cr, uid, shop_id).name
        if site_id:
            siteid = site_id.site_id
        else:
            raise osv.except_osv(_('Warning !'), _("Please Select Site ID in %s shop")%(shop_name))
        logger.notifyChannel('init', netsvc.LOG_WARNING, 'import product inst_lnk: %s'%(inst_lnk,))
        result = False
        try:
            result = self.call(cr, uid, inst_lnk, 'GetItem',itemId,siteid)
        except Exception, e:
            raise osv.except_osv(_('Error !'),e)
            return False    
        logger.notifyChannel('init', netsvc.LOG_WARNING, 'results############ %s'%(result,))
        return result
#######################################function for exporting inventory from openerp to ebay##################
    def export_inventory(self, cr, uid, ids, context=None):
        increment = 1
        siteid = ''
        shop_id = self.browse(cr,uid,ids[0]).shop_id.id
        shop_name = self.browse(cr,uid,ids[0]).shop_id.name
        inst_lnk = self.pool.get('sale.shop').browse(cr, uid, shop_id).instance_id
        site_id = self.pool.get('sale.shop').browse(cr, uid, shop_id).site_id
        if site_id:
            siteid = site_id.site_id
        else:
            raise osv.except_osv(_('Warning !'), _("Please Select Site ID in %s shop")%(shop_name))
        now_tm = datetime.now()
        current_now = str(now_tm)[:19]
        type='Fixed Price'
        prodtempl_obj = self.pool.get('product.template')
        listing_obj = self.pool.get('product.listing')
        try:
            currentTime = self.call(cr, uid, inst_lnk, 'GeteBayOfficialTime',siteid)
            currentTimeEbay = time.strptime(currentTime, "%Y-%m-%d %H:%M:%S")
            currentTimeEbay = time.strftime("%Y-%m-%dT%H:%M:%S.000Z",currentTimeEbay)
        except Exception, e:
            raise osv.except_osv(_('Error !'),e)
            return False
        result = False
        listing_ids = listing_obj.search(cr,uid,[('name','!=',''),('shop_id','=',shop_id),('prod_list','!=',False),('ebay_end_time','>',currentTime),('type','=',type)])
        warehouse_id = self.pool.get('sale.shop').browse(cr,uid,shop_id).warehouse_id
        location_id = warehouse_id.lot_input_id
        location_id_id = location_id.id
        for listing_id in listing_ids:
            prod = listing_obj.browse(cr,uid,listing_id).prod_list
            prod_id = prod.id
            prodtempl = prodtempl_obj.browse(cr,uid,prod.product_tmpl_id.id)
            product_id_location = self.pool.get('product.listing.templates')._my_value(cr, uid,location_id_id,prod_id,context={})
            product_split = str(product_id_location).split('.')
            value = product_split[0]
            if value != '0':
                result = self.call(cr, uid, inst_lnk, 'ReviseInventoryStatus',listing_obj.browse(cr,uid,listing_id).name,float(prodtempl.list_price * prod.price_margin + prod.price_extra),value,siteid)
                ack = result.get('Ack',False)
                if ack =='Failure':
                    if result.get('LongMessage',False):
                       long_message = result['LongMessage']
                       for each_messsge in long_message:
                           severity_code = each_messsge[0]['SeverityCode']
                           if severity_code == 'Error':
                               Longmessage = each_messsge[0]['LongMessage']
                               long_message = ('Error : %s: %s') % (prod.name,Longmessage)
                               increment += 1
                               self.log(cr, uid,increment, long_message)
                elif ack =='Warning':
                    if result.get('LongMessage',False):
                       long_message = result['LongMessage']
                       for each_messsge in long_message:
                           severity_code = each_messsge[0]['SeverityCode']
                           if severity_code == 'Warning':
                               Longmessage = each_messsge[0]['LongMessage']
                               long_message = ('Warning : %s: %s:') %  (prod.name,Longmessage)
                               increment += 1
                               self.log(cr, uid,increment,long_message)
                else:
                    increment += 1
                    self.log(cr, uid, increment, '%s : Stock level exported successfully. \n' % (prod.name))

            else:
                increment += 1
                self.log(cr, uid, increment, '%s: Inventory cannot be updated because its quantity is zero. \n' % (prod.name))
        self.write(cr,uid,ids[0],{'last_inventory_export_date':current_now})
#        cr.execute("UPDATE ebayerp_manage SET last_inventory_export_date=%s where id=%d"%(current_now,ids[0],))
#        cr.commit()
        return True
#################################################function for importing orders################################
    def import_orders(self, cr, uid, ids, context=None):
        shop_id = self.browse(cr,uid,ids[0]).shop_id.id
        inst_lnk = self.pool.get('sale.shop').browse(cr, uid, shop_id).instance_id
        siteid = ''
        site_id = self.pool.get('sale.shop').browse(cr, uid, shop_id).site_id
        shop_name = self.pool.get('sale.shop').browse(cr, uid, shop_id).name
        if site_id:
            siteid = site_id.site_id
        else:
            raise osv.except_osv(_('Warning !'), _("Please Select Site ID in %s shop")%(shop_name))
        now_tm = datetime.now()
        current_now = str(now_tm)[:19]
        FMT = '%Y-%m-%d %H:%M:%S'
        now_utc = datetime.now(timezone('UTC'))
        now_utc1 = str(now_utc)[:19]
        #########################Timezone Logic########################
        timezone_time = self.pool.get('res.users').browse(cr,uid,uid).context_tz
        if timezone_time:
            current_timezone = now_utc.astimezone(timezone(timezone_time))
            current_timezone = str(current_timezone)[:19]
        else:
           current_timezone = current_now
        ###############################################################
        difft_time = datetime.strptime(now_utc1, FMT) - datetime.strptime(current_timezone, FMT)
        currnt_diff = datetime.strptime(current_now, FMT) - datetime.strptime(current_timezone, FMT)
        try:
            currentTimeTo = self.call(cr, uid, inst_lnk, 'GeteBayOfficialTime',siteid)
            currentTimeTo = time.strptime(currentTimeTo, "%Y-%m-%d %H:%M:%S")
            currentTimeTo = time.strftime("%Y-%m-%dT%H:%M:%S.000Z",currentTimeTo)
        except Exception, e:
            raise osv.except_osv(_('Error !'),e)
            return False
        currentTimeFrom1 = self.browse(cr,uid,ids[0]).last_ebay_order_import_date
        if not currentTimeFrom1:
            currentTime = datetime.strptime(currentTimeTo, "%Y-%m-%dT%H:%M:%S.000Z")
            now = currentTime - timedelta(days=29)
            currentTimeFrom = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        else:
            currentTimeFrom = datetime.strptime(currentTimeFrom1, FMT) - currnt_diff
            currentTimeFrom = currentTimeFrom + difft_time
        pageNumber = 1
        resultFinal = []
#        results = self.call(cr, uid, inst_lnk, 'GetSellerTransactions',currentTimeFrom,currentTimeTo,pageNumber)
#        if results:
        while True:
            results = self.call(cr, uid, inst_lnk, 'GetSellerTransactions',currentTimeFrom,currentTimeTo,pageNumber,siteid)
            has_more_trans = results[-1]
            del results[-1]
            resultFinal = resultFinal + results
            if has_more_trans['HasMoreTransactions'] == 'false':
                break
            pageNumber = pageNumber + 1
        if resultFinal:
            orderid = self.pool.get('ebayerp.instance').createOrder(cr,uid,inst_lnk.id,shop_id,resultFinal,context)
        else:
            message = _('No Orders In Paid Status Exist')
            self.log(cr, uid, ids[0], message)
        self.write(cr,uid,ids[0],{'last_ebay_order_import_date':current_now})
        return True
############################################for updating order status#########################
    def update_orders(self, cr, uid, ids, ctx=None):
        increment = 0
        shop_id = self.browse(cr,uid,ids[0]).shop_id.id
        inst_lnk = self.pool.get('sale.shop').browse(cr, uid, shop_id).instance_id
        siteid = ''
        site_id = self.pool.get('sale.shop').browse(cr, uid, shop_id).site_id
        shop_name = self.pool.get('sale.shop').browse(cr, uid, shop_id).name
        if site_id:
            siteid = site_id.site_id
        else:
            raise osv.except_osv(_('Warning !'), _("Please Select Site ID in %s shop")%(shop_name))
#####################################last update time######################
        FMT = '%Y-%m-%d %H:%M:%S'
        now_tm = datetime.now()
        current_now = str(now_tm)[:19]
        difft_time = datetime.utcnow() - datetime.now()
        saleorder_obj = self.pool.get('sale.order')
        last_ebay_update_order_export_date1 = self.browse(cr,uid,ids[0]).last_update_order_export_date
        if not last_ebay_update_order_export_date1:
            saleorder_ids = saleorder_obj.search(cr,uid,[('shop_id','=',shop_id),('state','=','done'),('ebay_order_id','!=',False)])
        else:
            last_ebay_update_order_export_date = datetime.strptime(last_ebay_update_order_export_date1,FMT) - difft_time
            saleorder_ids = saleorder_obj.search(cr,uid,[('write_date','>',last_ebay_update_order_export_date),('shop_id','=',shop_id),('state','=','done'),(('ebay_order_id','!=',False))])
        try:
            currentTime = self.call(cr, uid, inst_lnk, 'GeteBayOfficialTime',siteid)
        except Exception, e:
            raise osv.except_osv(_('Error !'),e)
            return False
        if saleorder_ids:
            for saleorder_id in saleorder_ids:
                productlisting_obj = self.pool.get('product.listing')
                ebay_order_id = saleorder_obj.browse(cr,uid,saleorder_id).ebay_order_id
                order_data = {}
                trans_split = ebay_order_id.split("-")
                order_data['ItemID'] = trans_split[0]
                order_data['TransactionID'] = trans_split[1]
                listing_ids = productlisting_obj.search(cr,uid,[('name','=',order_data['ItemID'])])
                listing_type = productlisting_obj.browse(cr,uid,listing_ids[0]).type
                if listing_type =='Fixed Price':
                    listing_type_new = "FixedPriceItem"
                elif listing_type =='Auction':
                    listing_type_new = "Chinese"
                order_data['ListingType'] = listing_type_new
                order_data['Paid'] = saleorder_obj.browse(cr,uid,saleorder_id).invoiced
                order_data['shipped'] = saleorder_obj.browse(cr,uid,saleorder_id).shipped
                if order_data['shipped']:
                    picking_ids = saleorder_obj.browse(cr,uid,saleorder_id).picking_ids
                    if picking_ids:
                        order_data['ShipmentTrackingNumber'] = picking_ids[0].carrier_tracking_ref
                        order_data['ShippingCarrierUsed'] = picking_ids[0].carrier_id.name
                        results = self.call(cr, uid, inst_lnk, 'CompleteSale',order_data,siteid)
                        ack = results.get('Ack',False)
                        if ack =='Failure':
                            if results.get('LongMessage',False):
                                long_message = results['LongMessage']
                                for each_messsge in long_message:
                                    severity_code = each_messsge[0]['SeverityCode']
                                    if severity_code == 'Error':
                                        Longmessage = each_messsge[0]['LongMessage']
                                        long_message = ('Error : %s: %s') % (saleorder_obj.browse(cr,uid,saleorder_id).name,Longmessage)
                                        increment += 1
                                        self.log(cr, uid,increment, long_message)
                        elif ack =='Warning':
                            if results.get('LongMessage',False):
                                long_message = results['LongMessage']
                                for each_messsge in long_message:
                                    severity_code = each_messsge[0]['SeverityCode']
                                    if severity_code == 'Warning':
                                        Longmessage = each_messsge[0]['LongMessage']
                                        long_message = ('Warning : %s: %s') % (saleorder_obj.browse(cr,uid,saleorder_id).name,Longmessage)
                                        increment += 1
                                        self.log(cr, uid,increment, long_message)
                        else:
                           message = _('%s status updated successfully' % (saleorder_obj.browse(cr,uid,saleorder_id).name))
                           increment += 1
                           self.log(cr, uid, increment, message)
                           self.write(cr,uid,ids[0],{'last_update_order_export_date':current_now})
    #                       cr.execute("UPDATE ebayerp_manage SET last_update_order_export_date=%s where id=%d"%(current_now,ids[0],))
    #                       cr.commit()

                else:
                    message = _('No More Orders to Update')
                    self.log(cr, uid, increment, message)
                    self.write(cr,uid,ids[0],{'last_update_order_export_date':current_now})
        else:
            message = _('No More Orders to Update')
            self.log(cr, uid, increment, message)
            self.write(cr,uid,ids[0],{'last_update_order_export_date':current_now})
#          
        return True
    _rec_name = 'shop_id'
    _columns = {
        'shop_id' : fields.many2one('sale.shop','Ebay Shop',required=True,help="Selected Pricelist will be applied to the Listing Products"),
        'last_ebay_catalog_import_date' : fields.datetime('Last Catalog Import Time',help="Product was last Imported On"),
        'last_ebay_order_import_date' : fields.datetime('Last Order Import  Time',help="Order was last Updated On"),
        'last_inventory_export_date': fields.datetime('Last Inventory Export Time',help="Product Stock last Updated On "),
        'last_update_order_export_date' : fields.datetime('Last Order Update  Time',help="Order Status was last Updated On")
    }
ebayerp_manage()

class ebayerp_manage(ebayerp_osv.ebayerp_osv):
    _name = "ebayerp.manage"
    _inherit = "ebayerp.manage"

ebayerp_manage()
