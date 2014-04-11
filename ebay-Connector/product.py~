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
from mx import DateTime
import time
from datetime import date
import datetime
from datetime import date, timedelta, datetime
import ebayerp_osv
import pooler
from tools import config
from tools.translate import _
import tools
import netsvc
from time import gmtime, strftime
logger = netsvc.Logger()
import base64, urllib
import os

class product_images(osv.osv):
    _inherit = "product.images"
    def get_image(self, cr, uid, id):
      print"get_image"
      img = ''
      each = self.read(cr, uid, id, ['link', 'filename', 'image','full_url','chk_ebay_link'])
      if each['link'] == True:
          if each['link']:
           (filename, header) = urllib.urlretrieve(each['filename'])
           f = open(filename , 'rb')
           img = base64.encodestring(f.read())
           f.close()
      if each['full_url']:
          if each['full_url']:
               (filename, header) = urllib.urlretrieve(each['full_url'])
               f = open(filename , 'rb')
               img_ebay = base64.encodestring(f.read())
               f.close()
               if img_ebay:
                       cr.execute("UPDATE product_images SET preview_ebay='%s' where id=%d"%(img_ebay,id,))
               f.close()
      else:
          img = each['image']
      return img
    def write(self,cr,uid,ids,vals,context={}):
       if ids:
           filename = vals.get('filename_ebay',False)
           filename_database = self.browse(cr,uid,ids[0]).filename_ebay
           if filename == filename_database:
                vals.update({'change_or_no_change': 'no_change'})
           else:
               vals.update({'change_or_no_change': 'change','last_updated_changes':time.strftime('%Y-%m-%d %H:%M:%S')})
           id =  super(product_images, self).write(cr, uid, ids,vals, context)
           return id
    
    
    def create(self,cr,uid,vals,context={}):
       id =  super(product_images, self).create(cr, uid, vals, context)
       filename = vals.get('filename_ebay',False)
       vals.update({'change_or_no_change': 'change','last_updated_changes':time.strftime('%Y-%m-%d %H:%M:%S')})
       return id
    _columns = {
        'chk_ebay_link' : fields.boolean('Ebay'),
        'chk_mag' : fields.boolean('Magento'),
        'link':fields.boolean('Magento Link?', help="Images can be linked from files on your file system or remote (Preferred)"),
        'filename_ebay':fields.binary('Main Image', filters='*.png,*.jpg,*.gif'),
        'filename':fields.char('Magento File Location', size=250),
        'change_or_no_change':fields.selection([('change', 'Change'),('no_change', 'No Change')],'Changes'),
        'last_updated_changes': fields.datetime('Last Updated'),
        'full_url':fields.char('Full URL', size=256),
        'preview_ebay':fields.binary('Preview of Ebay Image'),
    }
    _defaults = {
        'link': lambda *a: False,
        'change_or_no_change': 'change',
        }
product_images()

class product_product(osv.osv):
    _inherit = "product.product"
    _columns = {
        'ebay_condtn':fields.many2one('condition.class','Ebay Product Condition'),
#        'ebay_condtn':fields.selection([('1000','New'),('1500','New other (see details)'),('1750','New with defects'),('2000','Manufacturer refurbished'),('2500','Seller refurbished'),('2750','Like New'),('3000','Used'),('4000','Very Good'),('5000','Good'),('6000','Acceptable '),('7000','For parts or not working'),('None','None')],'Ebay Product Condition',required=True),
        'bold_tl_prod':fields.boolean('Bold title'),
        'catlog_select':fields.selection([('isbn','ISBN'),('upc','UPC')],'Select Type of code To list catalog product'),
       'code_type':fields.char('UPC/ISBN',size=20),
       'details_url':fields.text('Details URL'),
       'product_reference_id': fields.char('Product reference ID',size=64),
       'stock_photo_url':fields.text('Stock Photo URL'),
    }
   
product_product()

class product_listing(osv.osv):
    _name = "product.listing"

    def unlink(self, cr, uid, ids, context=None):
       raise osv.except_osv(_('Warning !'), _("You cannot Delete the Active Products"))
   
    def update_listing(self,cr,uid,ids,context={}):
        increment = 0
        if type(ids) == type(int()):
            ids = [ids]
        if type(ids) == type(long()):
            ids = [ids]
        product_obj = self.browse(cr,uid,ids[0]).prod_list
        if product_obj:
            product_id = product_obj.id
            product_name = product_obj.name_template
            ebay_item_id = self.browse(cr,uid,ids[0]).name
            inst_lnk = self.browse(cr, uid, ids, context)[0].shop_id.instance_id
            shop_lnk = self.browse(cr, uid, ids, context)[0].shop_id
            if shop_lnk:
                shop_name = shop_lnk.name
                postal_code = shop_lnk.post_code
                if not postal_code:
        #            raise osv.except_osv(_('Warning !'), _("Please Enter the Postal Code in %s shop")%(shop_name))
                    list_message = _("Please Enter the Postal Code in %s shop") % shop_name
                    self.log(cr, uid, ids[0], list_message)
                    return
                payment_method = shop_lnk.pay_mthd
                if not payment_method:
        #            raise osv.except_osv(_('Warning !'), _("Please Enter the Payment Method in %s shop")%(shop_name))
                    list_message = _("Please Enter the Payment Method in %s shop") % shop_name
                    self.log(cr, uid, ids[0], list_message)
                    return
                paypal_email = shop_lnk.email_add
                if not paypal_email:
        #            raise osv.except_osv(_('Warning !'), _("Please Enter the Email Address in %s shop")%(shop_name))
                    list_message = _("Please Enter the Email Address in %s shop") % shop_name
                    self.log(cr, uid, ids[0], list_message)
                    return
                site_id = shop_lnk.site_id
                if site_id:
                    siteid = site_id.site_id
    #        if not site_id:
    #            list_message = _("Please Select Site ID in %s shop") % shop_name
    #            self.log(cr, uid, ids[0], list_message)
    #            return
    #            raise osv.except_osv(_('Warning !'), _("Please Select Site ID in %s shop")%(shop_name))
            related_template = self.browse(cr,uid,ids[0]).related_template
            if related_template:
                template_name = related_template.name
                template_cat = related_template.category_id1
                template_cat2 = related_template.category_id2
                product_cat =self.pool.get('product.product').browse(cr,uid,product_id).cat1
                product_cat2 =self.pool.get('product.product').browse(cr,uid,product_id).cat2
                if not product_cat:
                    if not template_cat:
                        list_message = _("Please Select Primary Category in Product or Template")
                        self.log(cr, uid, ids[0], list_message)
                        return
        #                raise osv.except_osv(_('Warning!'), _("Please select the category in Product or Template"))
                    else:
                        site_id_template_cat = template_cat.site_id
                        if site_id_template_cat != site_id:
        #                    raise osv.except_osv(_('Warning!'), _("Please select the Proper Primary Category in %s Template because Site ID of Category and Shop Differs")%(template_name))
                            list_message = _("Please Select the Proper Primary Category in %s Template because Site ID of Category and Shop Differs")%(template_name)
                            self.log(cr, uid, ids[0], list_message)
                            return
                else:
                    site_id_cat = product_cat.site_id
                    if site_id_cat != site_id:
        #                raise osv.except_osv(_('Warning!'), _("Please select the Proper Primary Category in %s Product because Site ID of Category and Shop Differs")%(product_name))
                        list_message = _("Please select the Proper Primary Category in %s Product because Site ID of Category and Shop Differs")%(product_name)
                        self.log(cr, uid, ids[0], list_message)
                        return

                if not product_cat2:
                    if template_cat2:
        #                raise osv.except_osv(_('Warning!'), _("Please select the category in Product or Template"))
                        site_id_template_cat2 = template_cat2.site_id
                        if site_id_template_cat2 != site_id:
        #                    raise osv.except_osv(_('Warning!'), _("Please select the Proper Secondary Category in %s Template because Site ID of Category and Shop Differs")%(template_name))
                            list_message = _("Please Select the Proper Secondary Category in %s Template because Site ID of Category and Shop Differs")%(template_name)
                            self.log(cr, uid, ids[0], list_message)
                            return
                else:
                    site_id_cat2 = product_cat2.site_id
                    if site_id_cat2 != site_id:
        #                raise osv.except_osv(_('Warning!'), _("Please select the Proper Primary Category in %s Product because Site ID of Category and Shop Differs")%(product_name))
                        list_message = _("Please Select the Proper Primary Category in %s Product because Site ID of Category and Shop Differs")%(product_name)
                        self.log(cr, uid, ids[0], list_message)
                        return
##################################################For Subtitle  ###############################
                product_search = self.pool.get('placeholder.holder').search(cr,uid,[('plc_hld','=',product_id)])
                plc_holder_chk = self.pool.get('placeholder.holder').search(cr,uid,[('plc_hld_temp','=',related_template.id)])
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
                subtitle = related_template.subtitle
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
##################################################For Description  ################################
                description_field = related_template.description
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
##########################################Replacing Title#######################################
                title = related_template.temp_name
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
                results = self.pool.get('sale.shop').call(cr, uid, inst_lnk, 'ReviseItem', ids,product_id, ebay_item_id,title_final,description_final,subtitle_final,postal_code,increment,siteid)
                ack = results.get('Ack',False)
                if ack =='Failure':
                    if results.get('LongMessage',False):
                           long_message = results['LongMessage']
                           for each_messsge in long_message:
                               severity_code = each_messsge[0]['SeverityCode']
                               if severity_code == 'Error':
                                   Longmessage = each_messsge[0]['LongMessage']
                                   product_long_message = ('Error : This %s product cannot be Updated because:') % (product_name)+ ' ' + Longmessage
                                   increment += 1
                                   self.log(cr, uid,increment, product_long_message)
                elif ack =='Warning':
                    if results.get('LongMessage',False):
                       long_message = results['LongMessage']
                       for each_messsge in long_message:
                           severity_code = each_messsge[0]['SeverityCode']
                           if severity_code == 'Warning':
                               Longmessage = each_messsge[0]['LongMessage']
                               product_long_message = ('Warning : %s:') % (product_name)+ ' ' + Longmessage
                               increment += 1
                               self.log(cr, uid,increment, product_long_message)
                elif ack =='Success':
                    self.log(cr, uid, increment, 'This %s is updated. \n' % (product_name))
#                vals_rd  = self.pool.get('product.listing').write(cr,uid,ids[0],{'ebay_name':title_final})
                cr.execute("UPDATE product_listing SET ebay_name='%s' where id=%d"%(title_final,ids[0],))
                cr.commit()
        return True
####################################################################################
    def cancel_listing_btn(self,cr,uid,ids,context={}):
        inst_lnk = self.browse(cr, uid, ids[0]).shop_id.instance_id
        site_id = self.browse(cr, uid, ids[0]).shop_id.site_id
        if site_id:
            siteid = site_id.site_id
        ebay_item_id = self.browse(cr,uid,ids[0]).name
        cancel_listing = self.browse(cr,uid,ids[0]).cancel_listing
        utc_tm = datetime.utcnow()
        utc_trunk = str(utc_tm)[:19]
        difft_time = datetime.utcnow() - datetime.now()
        if cancel_listing == True:
            ending_reason = self.browse(cr,uid,ids[0]).ending_reason
            if not ending_reason:
                self.log(cr, uid, ids[0], 'Please Select the Ending Reason \n')
                return
            try:
                if inst_lnk:
                    results = self.call(cr, uid, inst_lnk, 'EndItem',ebay_item_id,ending_reason,siteid)
                    self.log(cr, uid, ids[0], '%s has been Cancelled. \n' % (ebay_item_id))
            except Exception, e:
                raise osv.except_osv(_('Error !'),e)
                return False
            if results:
                if len(ids):
                    FMT = '%Y-%m-%d %H:%M:%S'
                    endtime = results.get('EndTime',False)
                    if endtime:
                        end_tm = self.pool.get('ebayerp.instance').openerpFormatDate(endtime)
                        endtime = datetime.strptime(end_tm, FMT) - difft_time
                        ebay_end_tm2 = str(endtime)[:19]
                        ebay_end_tm = ebay_end_tm2
#                        ebay_end_time = self.write(cr, uid, ids[0],{'ebay_end_time': ebay_end_tm,'is_cancel':True})
                        cr.execute("UPDATE product_listing SET ebay_end_time='%s',is_cancel='True' where id=%d"%(ebay_end_tm,ids[0],))
                        cr.commit()
    #                        deactive  = self.write(cr,uid,product_search,{'is_cancel':True})
        return True
    def _get_time_remain_funtion(self, cr, uid, ids, field_name, arg, context):
        res = {}
        if ids:
            difft_time = datetime.utcnow() - datetime.now()
            for each_ids in self.browse(cr, uid, ids, context):
                each_id = each_ids.id
                cur_record_end_time = self.browse(cr,uid,each_id).ebay_end_time
                gmt_tm = time.strftime("%Y-%m-%d %H:%M:%S", gmtime())
                new_gmt_time = datetime.strptime(gmt_tm, "%Y-%m-%d %H:%M:%S" )
                trunc_time = str(new_gmt_time)[:19]
                time_remain1 = datetime.strptime(cur_record_end_time, "%Y-%m-%d %H:%M:%S" ) - datetime.strptime(trunc_time, "%Y-%m-%d %H:%M:%S" )
                time_remain = time_remain1 + difft_time
                timeremain_str = str(time_remain)
                time_split = timeremain_str.split('.')
                if time_split:
                    timeremain = time_split[0]
                locate = timeremain
                locate_first = locate[0]
                if locate_first == '-':
                    locate_val = 'Inactive'
                    cr.execute("UPDATE product_listing SET state='%s' where id=%d"%(locate_val,each_ids.id,))
                    cr.commit()
                else:
                    locate_val = 'Active'
                    cr.execute("UPDATE product_listing SET state='%s' where id=%d"%(locate_val,each_ids.id,))
                    cr.commit()
                res[each_ids.id] =  {
                                'time_remain_function': locate,
                                'state':locate_val,
                                }
        return res

    _columns = {
        'name': fields.char('Item ID', size=64),
        'prod_list':fields.many2one('product.product', string='Product Name',readonly= True),
        'shop_id':fields.many2one('sale.shop', string='Shop Name'),
        'ebay_end_time':fields.datetime('End Time',size=64),
        'start_time':fields.datetime('Start Time',size=64),
        'is_cancel':fields.boolean('Is Cancelled',readonly=True),
        'cancel_listing' : fields.boolean('Cancel Listing'),
        'ending_reason': fields.selection([('Incorrect','The start price or reserve price is incorrect'),('LostOrBroken','The item was lost or broken'),('NotAvailable','The item is no longer available for sale'),('OtherListingError','The listing contained an error'),('SellToHighBidder','The listing has qualifying bids')],'Ending Reason'),
        'type': fields.char('Type',size=64),
        'related_template':fields.many2one('ebayerp.template','Template'),
        'listing_duration' : fields.char('Listing Duration',size=64),
        'time_remain' : fields.char('Time Remaining',size=64),
        'time_remain_function': fields.function(_get_time_remain_funtion, method=True, string='Remaining Time', type='char', multi='_get_time_remain_funtion'),
        'product_listing_id': fields.one2many('current.details', 'current_details_ids','Product listing id'),
        'state':fields.selection([('Active','Active'),('Inactive','Expired')],'Status',readonly=True),
        'condtn':fields.selection([('1000','New'),('1500','New other (see details)'),('2000','Manufacturer refurbished'),('2500','Seller refurbished'),('3000','Used'),('7000','For parts or not working')],'Condition'),
        'ebay_name':fields.char('Ebay Title',size=256),
        'time_rem':fields.char('Time Remain',size=256),
    }
    _defaults = {
        'state': 'Active',
    }
product_listing()

class product_listing(ebayerp_osv.ebayerp_osv):
    _name = 'product.listing'
    _inherit = 'product.listing'
product_listing()

class current_details(osv.osv):
    _name = "current.details"
    _columns = {
        'name': fields.char('Name', size=64),
        'ebay_current_time':fields.datetime('Current Details',size=64),
        'current_details_ids':fields.many2one('product.listing','Ebay current details'),
    }
current_details()

###########################Class for product PlaceHolders#########################
class placeholder_holder(osv.osv):
   _name = "placeholder.holder"
   _columns = {
      'name': fields.char('Name', size=50),
      'value': fields.char('Value', size=256),
      'plc_hld': fields.many2one('product.product', string='Place holder'),
      'plc_hld_temp': fields.many2one('ebayerp.template', string='Place holder'),
      }
placeholder_holder()

class product_product(osv.osv):
    _inherit = "product.product"
    def create(self,cr,uid,vals,context={}):
        id  = super(product_product, self).create(cr, uid, vals, context=context)
        if id:
            category_id1 = vals.get('cat1',False)
            category_id2 = vals.get('cat2',False)
            if category_id1 != False and category_id2 != False:
                if category_id1 == category_id2:
                    raise osv.except_osv(_('Warning !'), _("Please Select Two Different Categories"))
            return id

    def write(self,cr,uid,ids,vals,context={}):
        if ids:
            if type(ids) == type(int()):
                    ids = [ids]
            if type(ids) == type(long()):
                    ids = [ids]
            if 'cat1' in vals:
                category_id1 = vals.get('cat1',False)
            else:
                category_id1 = self.browse(cr, uid, ids[0]).cat1.id
            if 'cat2' in vals:
                category_id2 = vals.get('cat2',False)
            else:
                category_id2 = self.browse(cr, uid, ids[0]).cat2.id
            if category_id1 != False and category_id2 != False:
                if category_id1 == category_id2:
                    raise osv.except_osv(_('Warning !'), _("Please Select Two Different Categories"))
        return super(product_product, self).write(cr, uid, ids, vals, context=context)


    def onchange_clear_attributes(self, cr, uid, ids,cat1 ,cat2,category_name,context=None):
        result ={}
        domain = {}
        if category_name == 'category1':
            if ids:
                cat1_database = self.browse(cr,uid,ids[0]).cat1
                if cat1:
                    if cat1 != cat1_database.id:
                        result['product_reference_id'] = ''
                        result['details_url'] = ''
                        result['stock_photo_url'] = ''
        if cat1:
            condition_ids =  self.pool.get('condition.class').search(cr,uid,[('category_id','=',cat1)])
            condition_enabled =  self.pool.get('category.master').browse(cr,uid,cat1).condition_enabled
            if condition_enabled == False:
                if cat2:
                    condition_enabled =  self.pool.get('category.master').browse(cr,uid,cat2).condition_enabled
                    if condition_enabled == True:
                        condition_ids =  self.pool.get('condition.class').search(cr,uid,[('category_id','=',cat2)])
                        domain['ebay_condtn'] = [('id', 'in', condition_ids)]
                    else:
                        domain['ebay_condtn'] = [('id', 'in', [])]
                else:
                    domain['ebay_condtn'] = [('id', 'in', [])]
            else:
                domain['ebay_condtn'] = [('id', 'in', condition_ids)]

            if condition_ids:
                result['ebay_condtn'] = condition_ids[0]
            else:
                result['ebay_condtn'] = False
            item_specifics = self.pool.get('category.master').browse(cr,uid,cat1).item_specifics
            catlg_enbld = self.pool.get('category.master').browse(cr,uid,cat1).catlog_enabled
            if catlg_enbld == True:
                result['catalog_en'] = 'checked'
            else:
                if cat2:
                    catlg_enbld = self.pool.get('category.master').browse(cr,uid,cat2).catlog_enabled
                    if catlg_enbld == True:
                        result['catalog_en'] = 'checked'
                    else:
                        result['catalog_en'] = 'unchecked'
                else:
                    result['catalog_en'] = 'unchecked'
            if item_specifics == True:
                result['item_specifics_enabled_prod1'] = 'checked'
            else:
                if cat2:
                    item_specifics = self.pool.get('category.master').browse(cr,uid,cat2).item_specifics
                    if item_specifics == True:
                        result['item_specifics_enabled_prod1'] = 'checked'
                    else:
                        result['item_specifics_enabled_prod1'] = 'unchecked'
                        if ids:
                            custom_attributes = self.browse(cr,uid,ids[0]).custom_item_specifics_prod_cat_gene
                            if custom_attributes:
                                for each_specifics in custom_attributes:
                                    each_specifics_id = each_specifics.id
                                    if each_specifics_id:
                                        delete = cr.execute('delete from custom_item_specifics where id=%s',(each_specifics_id,))
                else:
                    result['item_specifics_enabled_prod1'] = 'unchecked'
                    
                    if ids:
                        custom_attributes = self.browse(cr,uid,ids[0]).custom_item_specifics_prod_cat_gene
                        if custom_attributes:
                            for each_specifics in custom_attributes:
                                each_specifics_id = each_specifics.id
                                if each_specifics_id:
                                    delete = cr.execute('delete from custom_item_specifics where id=%s',(each_specifics_id,))
        elif cat2:
            item_specifics = self.pool.get('category.master').browse(cr,uid,cat2).item_specifics
            catlg_enbld = self.pool.get('category.master').browse(cr,uid,cat2).catlog_enabled
            if catlg_enbld == True:
                result['catalog_en'] = 'checked'
            else:
                result['catalog_en'] = 'unchecked'
            if item_specifics == True:
                result['item_specifics_enabled_prod1'] = 'checked'
            else:
                result['item_specifics_enabled_prod1'] = 'unchecked'
                if ids:
                    custom_attributes = self.browse(cr,uid,ids[0]).custom_item_specifics_prod_cat_gene
                    if custom_attributes:
                        for each_specifics in custom_attributes:
                            each_specifics_id = each_specifics.id
                            print"each_specifics_id",each_specifics_id
                            ##delete from the attribute matching
                            if each_specifics_id:
                                delete = cr.execute('delete from custom_item_specifics where id=%s',(each_specifics_id,))
        else:
            result['item_specifics_enabled_prod1'] = 'unchecked'
            result['catalog_en'] = 'unchecked'
            result['product_reference_id'] = ''
            result['details_url'] = ''
            result['stock_photo_url'] = ''
            result['ebay_condtn'] = False
            domain['ebay_condtn'] = [('id', 'in', [])]
            if ids:
                custom_attributes = self.browse(cr,uid,ids[0]).custom_item_specifics_prod_cat_gene
                if custom_attributes:
                    for each_specifics in custom_attributes:
                        each_specifics_id = each_specifics.id
                        if each_specifics_id:
                            delete = cr.execute('delete from custom_item_specifics where id=%s',(each_specifics_id,))
        if len(ids):
            attribute_matching = self.browse(cr,uid,ids[0]).match_att_cat1
            if attribute_matching:
                for each_attribute in attribute_matching:
                    attribute_matching_id = each_attribute.id
                    ##delete from the attribute matching
                    if attribute_matching_id:
                        delete = cr.execute('delete from attribute_matching where id=%s',(attribute_matching_id,))
        return {'value':result,'domain':domain}
        
    def onchange_clear_attributes_cat2(self, cr, uid, ids,cat2,cat1,category_name,context=None):
        result ={}
        domain = {}
        if category_name == 'category2':
            if ids:
                cat2_database = self.browse(cr,uid,ids[0]).cat2
                if cat2:
                    if cat2 != cat2_database.id:
                        result['product_reference_id'] = ''
                        result['details_url'] = ''
                        result['stock_photo_url'] = ''
                else:
                    result['product_reference_id'] = ''
                    result['details_url'] = ''
                    result['stock_photo_url'] = ''
        if cat1:
            condition_ids =  self.pool.get('condition.class').search(cr,uid,[('category_id','=',cat1)])
            condition_enabled =  self.pool.get('category.master').browse(cr,uid,cat1).condition_enabled
            if condition_enabled == False:
                if cat2:
                    condition_enabled =  self.pool.get('category.master').browse(cr,uid,cat2).condition_enabled
                    if condition_enabled == True:
                        condition_ids =  self.pool.get('condition.class').search(cr,uid,[('category_id','=',cat2)])
                        domain['ebay_condtn'] = [('id', 'in', condition_ids)]
                    else:
                        domain['ebay_condtn'] = [('id', 'in', [])]
                else:
                    domain['ebay_condtn'] = [('id', 'in', [])]
            else:
                domain['ebay_condtn'] = [('id', 'in', condition_ids)]
            if condition_ids:
                result['ebay_condtn'] = condition_ids[0]
            else:
                result['ebay_condtn'] = False
            item_specifics = self.pool.get('category.master').browse(cr,uid,cat1).item_specifics
            catlg_enbld = self.pool.get('category.master').browse(cr,uid,cat1).catlog_enabled
            if catlg_enbld == True:
                result['catalog_en'] = 'checked'
            else:
                if cat2:
                    catlg_enbld = self.pool.get('category.master').browse(cr,uid,cat2).catlog_enabled
                    if catlg_enbld == True:
                        result['catalog_en'] = 'checked'
                    else:
                        result['catalog_en'] = 'unchecked'
                else:
                    result['catalog_en'] = 'unchecked'
            if item_specifics == True:
                result['item_specifics_enabled_prod1'] = 'checked'
            else:
                if cat2:
                    item_specifics = self.pool.get('category.master').browse(cr,uid,cat2).item_specifics
                    if item_specifics == True:
                        result['item_specifics_enabled_prod1'] = 'checked'
                    else:
                        result['item_specifics_enabled_prod1'] = 'unchecked'
                        if ids:
                            custom_attributes = self.browse(cr,uid,ids[0]).custom_item_specifics_prod_cat_gene
                            if custom_attributes:
                                for each_specifics in custom_attributes:
                                    each_specifics_id = each_specifics.id
                                    ##delete from the attribute matching
                                    if each_specifics_id:
                                        delete = cr.execute('delete from custom_item_specifics where id=%s',(each_specifics_id,))
                else:
                    result['item_specifics_enabled_prod1'] = 'unchecked'
                    if ids:
                        custom_attributes = self.browse(cr,uid,ids[0]).custom_item_specifics_prod_cat_gene
                        if custom_attributes:
                            for each_specifics in custom_attributes:
                                each_specifics_id = each_specifics.id
                                ##delete from the attribute matching
                                if each_specifics_id:
                                    delete = cr.execute('delete from custom_item_specifics where id=%s',(each_specifics_id,))
        elif cat2:
            item_specifics = self.pool.get('category.master').browse(cr,uid,cat2).item_specifics
            catlg_enbld = self.pool.get('category.master').browse(cr,uid,cat2).catlog_enabled
            if catlg_enbld == True:
                result['catalog_en'] = 'checked'
            else:
                result['catalog_en'] = 'unchecked'
            if item_specifics == True:
                result['item_specifics_enabled_prod1'] = 'checked'
            else:
                result['item_specifics_enabled_prod1'] = 'unchecked'
                if ids:
                    custom_attributes = self.browse(cr,uid,ids[0]).custom_item_specifics_prod_cat_gene
                    if custom_attributes:
                        for each_specifics in custom_attributes:
                            each_specifics_id = each_specifics.id
                            ##delete from the attribute matching
                            if each_specifics_id:
                                delete = cr.execute('delete from custom_item_specifics where id=%s',(each_specifics_id,))
        else:
            result['item_specifics_enabled_prod1'] = 'unchecked'
            result['catalog_en'] = 'unchecked'
            result['product_reference_id'] = ''
            result['details_url'] = ''
            result['stock_photo_url'] = ''
            result['ebay_condtn'] = False
            domain['ebay_condtn'] = [('id', 'in', [])]
            if ids:
                custom_attributes = self.browse(cr,uid,ids[0]).custom_item_specifics_prod_cat_gene
                if custom_attributes:
                    for each_specifics in custom_attributes:
                        each_specifics_id = each_specifics.id
                        ##delete from the attribute matching
                        if each_specifics_id:
                            delete = cr.execute('delete from custom_item_specifics where id=%s',(each_specifics_id,))
        if len(ids):
            attribute_matching = self.browse(cr,uid,ids[0]).match_att_cat2
            if attribute_matching:
                for each_attribute in attribute_matching:
                    attribute_matching_id = each_attribute.id
                    ##delete from the attribute matching
                    if attribute_matching_id:
                        delete = cr.execute('delete from attribute_matching where id=%s',(attribute_matching_id,))
        return {'value':result,'domain':domain}
    def onchange_details_url(self,cr,uid,ids,details_url,context=None):
        result = {}
        if details_url:
            if ids:
                details_url_database = self.browse(cr,uid,ids[0]).details_url
                if details_url_database != details_url:
                    result['product_refernce_id']=''
                    result['stock_photo_url'] =''
                    result['details_url'] = ''
        else:
            result['product_reference_id'] = ''
            result['stock_photo_url'] = ''
            
        return{'value':result}
    _columns = {
        'prods_list': fields.one2many('product.listing', 'prod_list','Shop Id',readonly = True),
        'cat1': fields.many2one('category.master','Category1'),
        'cat2': fields.many2one('category.master','Category2'),
        'match_att_cat1': fields.one2many('attribute.matching','product_cat1_match','Matching Attribute'),
        'match_att_cat2': fields.one2many('attribute.matching','product_cat2_match','Matching Attribute'),
        'plcs_holds': fields.one2many('placeholder.holder', 'plc_hld','Place Holder'),
        'related_template': fields.many2one('ebayerp.template'),
        'start_price': fields.char('Start Price',size=64),
        'reserve_price':fields.char('Reserve Price',size=64),
        'buy_it_now_price':fields.char('Buy It Now Price',size=64),
        'ebay_sku':fields.char('Ebay Product Sku',size=64),
        'exported_to_ebay': fields.boolean('Exported To Ebay',help="Specifies to List an Product to Ebay or not"),
        'catalog_en':fields.selection([('checked','Checked'),('unchecked','Unchecked')],'Item specifics Enabled'),
        'custom_item_specifics_prod_cat_gene': fields.one2many('custom.item.specifics','product_cat_gen','Custom Item Specifics'),
        'item_specifics_enabled_prod1':fields.selection([('checked','Checked'),('unchecked','Unchecked')],'Item specifics Enabled'),
        'ebay_breadth':fields.char('Breadth',size=10),
        'ebay_width':fields.char('Width',size=10),
        'ebay_height':fields.char('Height',size=10),
        'category_name': fields.char('CategoryName',size=64)
    }
    _defaults = {
        'exported_to_ebay': lambda *a:True,
        'item_specifics_enabled_prod1':'unchecked',
        'catalog_en':'unchecked',
        'product_reference_id':''
    }
product_product()
