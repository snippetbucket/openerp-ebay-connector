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
import datetime
from datetime import date, timedelta
import os
from PIL import Image, ImageEnhance,ImageDraw
from tools.translate import _
import base64, urllib
import netsvc
logger = netsvc.Logger()
from base64 import b64decode
import binascii


class sale_shop(osv.osv):
    _name = "sale.shop"
    _inherit = "sale.shop"

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if not context:
            context = {}
        #ctx_view_id = context.get('default_view_id', False)
        #if ctx_view_id:
        #    mod_obj = self.pool.get('ir.model.data')
        #    model,view_id = mod_obj.get_object_reference(cr, uid, 'engineer', ctx_view_id)
        result = super(osv.osv, self).fields_view_get(cr, uid, view_id, view_type, context=context, toolbar=toolbar, submenu=submenu)
        return result

    def store_image(self,cr,uid,store_image_binary,path,flag=False):
        if store_image_binary and path:
            image = binascii.b2a_base64(str(b64decode(store_image_binary)))
            png_file_open = open(path,'wb')
            png_file = png_file_open.write(b64decode(image))
            if flag == False:
                png_file_new = Image.open(path)
            else:
                png_file_new = path
            return png_file_new
    def shipping_details(self,cr,uid,template_object,product_id,listing_type,shop_id,start_price,reserve_price,buy_it_now_price,quantity):
        if listing_type == 'Fixed Price':
            listing_type = 'FixedPriceItem'
        elif listing_type == 'Auction':
            listing_type = 'Chinese'
        elif listing_type == 'ClassifiedAd':
            listing_type = 'LeadGeneration'
        template_id = template_object.id
        ship_ser1 =''
        ship_ser2 = ''
        ship_ser3 = ''
        ship_ser4 = ''
        ship_ser_1 = ''
        ship_ser_2 = ''
        ship_ser_3 = ''
        ship_ser_4 = ''
        ship_ser_calc1 = ''
        get_it_fast = ''
        free_ship_serv = ''
        int_ship_type = ''
        add_info = ''
        add_info = template_object.add_inst
        if add_info == False:
            add_info = ''
        ship_type = self.pool.get('ebayerp.template').browse(cr,uid,template_id).ship_type
        inter_chk = self.pool.get('ebayerp.template').browse(cr,uid,template_id).inter_chk
        if ship_type == 'Flat':
            ship1 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).serv1.ship_ser
            if ship1 == False:
                raise osv.except_osv(_('Warning!'), _("Please select Primary shipping service"))
            free_ship = self.pool.get('ebayerp.template').browse(cr,uid,template_id).free_ship
            if free_ship == False:
                cost1= self.pool.get('ebayerp.template').browse(cr,uid,template_id).cost
                add_1= self.pool.get('ebayerp.template').browse(cr,uid,template_id).each_add
                if add_1 == False:
                    add_1 = 0
                if cost1 == False:
                    raise osv.except_osv(_('Warning!'), _("Please enter shipping cost for Primary service"))
                ship_ser1+= """<ShippingServiceOptions>
                <FreeShipping>%s</FreeShipping>
                <ShippingService>%s</ShippingService>
                <ShippingServiceAdditionalCost>%s</ShippingServiceAdditionalCost>
                <ShippingServiceCost>%s</ShippingServiceCost>
                <ShippingServicePriority>1</ShippingServicePriority>
                </ShippingServiceOptions>""" %(free_ship,ship1,add_1,cost1)
            else:
                ship_ser1+= """<ShippingServiceOptions>
                <FreeShipping>%s</FreeShipping>
                <ShippingService>%s</ShippingService>
                <ShippingServiceAdditionalCost>0</ShippingServiceAdditionalCost>
                <ShippingServiceCost>0</ShippingServiceCost>
                <ShippingServicePriority>1</ShippingServicePriority>
                </ShippingServiceOptions>""" %(free_ship,ship1)
            chk_ship2 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).serv2_chk
            if chk_ship2 == True:
                ship2 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).serv2.ship_ser
                if not ship2:
                    raise osv.except_osv(_('Warning!'), _("Please select 2nd shipping service"))
                cost2= self.pool.get('ebayerp.template').browse(cr,uid,template_id).cost2
                add_2= self.pool.get('ebayerp.template').browse(cr,uid,template_id).each_add2
                if add_2 == False:
                    add_2 = 0
                if cost2 == False:
                    raise osv.except_osv(_('Warning!'), _("Please enter shipping cost for 2nd service"))
                ship_ser2+= """<ShippingServiceOptions>
                <ShippingService>%s</ShippingService>
                <ShippingServiceAdditionalCost>%s</ShippingServiceAdditionalCost>
                <ShippingServiceCost>%s</ShippingServiceCost>
                <ShippingServicePriority>2</ShippingServicePriority>
                </ShippingServiceOptions>""" %(ship2,add_2,cost2)
            chk_ship3 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).serv3_chk
            if chk_ship3 == True:
                ship3 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).serv3.ship_ser
                if not ship3:
                    raise osv.except_osv(_('Warning!'), _("Please select 3rd shipping service"))
                cost3= self.pool.get('ebayerp.template').browse(cr,uid,template_id).cost3
                add_3= self.pool.get('ebayerp.template').browse(cr,uid,template_id).each_add3
                if add_3 == False:
                    add_3 = 0
                if cost3 == False:
                    raise osv.except_osv(_('Warning!'), _("Please enter shipping cost for 3rd service "))
                ship_ser3+= """<ShippingServiceOptions>
                <ShippingService>%s</ShippingService>
                <ShippingServiceAdditionalCost>%s</ShippingServiceAdditionalCost>
                <ShippingServiceCost>%s</ShippingServiceCost>
                <ShippingServicePriority>3</ShippingServicePriority>
                </ShippingServiceOptions>""" %(ship3,add_3,cost3)
            chk_ship4 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).serv4_chk
            if chk_ship4 == True:
                ship4 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).serv4.ship_ser
                if not ship4:
                    raise osv.except_osv(_('Warning!'), _("Please select 4th shipping service"))
                cost4= self.pool.get('ebayerp.template').browse(cr,uid,template_id).cost4
                add_4= self.pool.get('ebayerp.template').browse(cr,uid,template_id).each_add4
                if add_4 == False:
                    add_4 = 0
                if cost4 == False:
                    raise osv.except_osv(_('Warning!'), _("Please enter shipping cost for 4th service "))
                ship_ser4+= """<ShippingServiceOptions>
                <ShippingService>%s</ShippingService>
                <ShippingServiceAdditionalCost>%s</ShippingServiceAdditionalCost>
                <ShippingServiceCost>%s</ShippingServiceCost>
                <ShippingServicePriority>4</ShippingServicePriority>
                </ShippingServiceOptions>""" %(ship4,add_4,cost4)
        elif ship_type == 'Calculated':
            ship1_calc = self.pool.get('ebayerp.template').browse(cr,uid,template_id).serv1.ship_ser
            if not ship1_calc:
                raise osv.except_osv(_('Warning!'), _("Please select Primary shipping service"))
            free_ship = self.pool.get('ebayerp.template').browse(cr,uid,template_id).free_ship
            ship_ser_1+= """<ShippingServiceOptions>
            <FreeShipping>%s</FreeShipping>
            <ShippingService>%s</ShippingService>
            <ShippingServicePriority>1</ShippingServicePriority>
            </ShippingServiceOptions>""" %(free_ship,ship1_calc)
            chk_ship_calc2 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).serv2_chk
            if chk_ship_calc2:
                ship2_calc = self.pool.get('ebayerp.template').browse(cr,uid,template_id).serv2.ship_ser
                if not ship2_calc:
                    raise osv.except_osv(_('Warning!'), _("Please select 2nd shipping service"))
                ship_ser_2+= """<ShippingServiceOptions>
                <ShippingService>%s</ShippingService>
                <ShippingServicePriority>2</ShippingServicePriority>
                </ShippingServiceOptions>""" %(ship2_calc)
            chk_ship_calc3 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).serv3_chk
            if chk_ship_calc3:
                ship3_calc = self.pool.get('ebayerp.template').browse(cr,uid,template_id).serv3.ship_ser
                if not ship3_calc:
                    raise osv.except_osv(_('Warning!'), _("Please select 3rd shipping service"))
                ship_ser_3+= """<ShippingServiceOptions>
                <ShippingService>%s</ShippingService>
                <ShippingServicePriority>3</ShippingServicePriority>
                </ShippingServiceOptions>""" %(ship3_calc)
            chk_ship_calc4 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).serv4_chk
            if chk_ship_calc4:
                ship4_calc = self.pool.get('ebayerp.template').browse(cr,uid,template_id).serv4.ship_ser
                if not ship4_calc:
                    raise osv.except_osv(_('Warning!'), _("Please select 4th shipping service"))
                ship_ser_4+= """<ShippingServiceOptions>
                <ShippingService>%s</ShippingService>
                <ShippingServicePriority>4</ShippingServicePriority>
                </ShippingServiceOptions>""" %(ship4_calc)
            max_weight = self.pool.get('ebayerp.template').browse(cr,uid,template_id).intr_max_weight
            if not max_weight:
                    raise osv.except_osv(_('Warning!'), _("Please enter maximum weight for international service"))
            min_weight = self.pool.get('ebayerp.template').browse(cr,uid,template_id).intr_min_weight
            if not min_weight:
                    raise osv.except_osv(_('Warning!'), _("Please enter minimum weight for international service"))
            gross_weight = self.pool.get('product.product').browse(cr,uid,product_id).weight
            net_weight = self.pool.get('product.product').browse(cr,uid,product_id).weight_net
            if gross_weight == 0.0:
                min_weight = min_weight
            else:
                min_weight =  gross_weight
            if net_weight == 0.0:
                max_weight = max_weight
            else:
                max_weight =  net_weight
            irrg_pack = self.pool.get('ebayerp.template').browse(cr,uid,template_id).intr_irreg_pack
            pack_type = self.pool.get('ebayerp.template').browse(cr,uid,template_id).intr_pack_type
            hand_cost = self.pool.get('ebayerp.template').browse(cr,uid,template_id).handling_cost
            ship_ser_calc1 = """<CalculatedShippingRate>
                <PackagingHandlingCosts>%s</PackagingHandlingCosts>
                <ShippingIrregular>%s</ShippingIrregular>
                <ShippingPackage>%s</ShippingPackage>
                <WeightMajor>%s</WeightMajor>
                <WeightMinor>%s</WeightMinor>
                </CalculatedShippingRate>"""%(hand_cost,irrg_pack,pack_type,max_weight,min_weight)
        elif ship_type == 'LocalDelivery':
           free_ship_serv += """<ShippingServiceOptions>
       <ShippingService>LocalDelivery</ShippingService>
       <ShippingServiceCost currencyID="USD">0.0</ShippingServiceCost>
       <ShippingServiceAdditionalCost>0.0</ShippingServiceAdditionalCost>
       <ShippingServicePriority>1</ShippingServicePriority>
     </ShippingServiceOptions>"""
#############################international shipping functions######################################
        ship_loc1 =''
        intr_ship_ser1 = ''
        ship_loc2 = ''
        intr_ship_ser2 = ''
        ship_loc3 = ''
        intr_ship_ser3 = ''
        ship_loc4 = ''
        intr_ship_ser4 = ''
        ship_loc5 = ''
        ship_loc1_calc = ''
        ship_loc2_calc = ''
        ship_loc3_calc = ''
        ship_loc4_calc = ''
        ship_loc5_calc = ''
        intr_ship_ser5 = ''
        comb_ships_locs1 = ''
        comb_ships_locs2 = ''
        comb_ships_locs3 = ''
        comb_ships_locs4 = ''
        comb_ships_locs5 = ''
        inter_shipping_combo = ''
        intr_ship_ser1_calc = ''
        intr_ship_ser2_calc = ''
        intr_ship_ser3_calc = ''
        intr_ship_ser4_calc = ''
        intr_ship_ser5_calc = ''
###############Primary service##########################
        if inter_chk == True:
            ship_to1 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).custom_loc
            if not ship_to1:
                raise osv.except_osv(_('Warning!'), _("Please enter Ship to service "))
            int_ship_type = self.pool.get('ebayerp.template').browse(cr,uid,template_id).int_ship_type
            if int_ship_type == 'Flat':
                intr_ship1 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).intr_serv.ship_ser
                if not intr_ship1:
                    raise osv.except_osv(_('Warning!'), _("Please select Primary International shipping service"))
                int_cost1= self.pool.get('ebayerp.template').browse(cr,uid,template_id).cost_int
                if int_cost1 == False:
                    raise osv.except_osv(_('Warning!'), _("Please enter shipping cost for 1st International service "))
                int_add_1= self.pool.get('ebayerp.template').browse(cr,uid,template_id).add_int
                if int_add_1 == False:
                    int_add_1 = 0
                if ship_to1 == 'Worldwide':
                    ship_loc1 = """<ShipToLocation>%s</ShipToLocation>""" %(ship_to1)
                elif ship_to1 == 'Canada':
                    ship_loc1 = """<ShipToLocation>CA</ShipToLocation>"""
                elif ship_to1 == 'customloc':
                    ship_locs1 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).add_loc_tab
                    if not ship_locs1:
                        raise osv.except_osv(_('Warning!'), _("Please select atleast one custom location for 1st service"))
                    else:
                        for cust_locs in ship_locs1:
                            intr_loc_code = cust_locs.ship_code
                            ship_loc1+= """<ShipToLocation>%s</ShipToLocation>""" %(intr_loc_code)
                intr_ship_ser1+= """<InternationalShippingServiceOption>
                                    <ShippingService>%s</ShippingService>
                                    <ShippingServiceAdditionalCost>%s</ShippingServiceAdditionalCost>
                                    <ShippingServiceCost>%s</ShippingServiceCost>
                                    <ShippingServicePriority>1</ShippingServicePriority>
                                 """ %(intr_ship1,int_add_1,int_cost1)
                comb_ships_locs1 = intr_ship_ser1.encode("utf-8") + ship_loc1.encode("utf-8") + """</InternationalShippingServiceOption>"""
####################For 2nd Service####################
                intr_serv2_chk = self.pool.get('ebayerp.template').browse(cr,uid,template_id).serv2_int_chk
                if intr_serv2_chk == True:
                    ship_to2 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).custom_loc2
                    if not ship_to2:
                        raise osv.except_osv(_('Warning!'), _("Please select 2nd Ship to service"))
                    intr_ship2 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).intr_serv2.ship_ser
                    if not intr_ship2:
                        raise osv.except_osv(_('Warning!'), _("Please select 2nd International shipping service"))
                    int_cost2= self.pool.get('ebayerp.template').browse(cr,uid,template_id).cost_int2
                    if int_cost2 == False:
                        raise osv.except_osv(_('Warning!'), _("Please enter shipping cost for 1st International service "))
                    int_add_2= self.pool.get('ebayerp.template').browse(cr,uid,template_id).add_int2
                    if int_add_2 == False:
                        int_add_2 = 0
                    if ship_to2 == 'Worldwide':
                        ship_loc2 = """<ShipToLocation>%s</ShipToLocation>""" %(ship_to2)
                    elif ship_to2 == 'Canada':
                        ship_loc2 = """<ShipToLocation>CA</ShipToLocation>"""
                    elif ship_to2 == 'customloc':
                        ship_locs2 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).add_loc_tab2
                        if not ship_locs2:
                            raise osv.except_osv(_('Warning!'), _("Please select atleast one custom location for 2nd shipping service"))
                        else:
                            for cust_locs2 in ship_locs2:
                                intr_loc_code2 = cust_locs2.ship_code
                                ship_loc2+= """<ShipToLocation>%s</ShipToLocation>""" %(intr_loc_code2)
                    intr_ship_ser2+= """<InternationalShippingServiceOption>
                                        <ShippingService>%s</ShippingService>
                                        <ShippingServiceAdditionalCost>%s</ShippingServiceAdditionalCost>
                                        <ShippingServiceCost>%s</ShippingServiceCost>
                                        <ShippingServicePriority>2</ShippingServicePriority>
                                     """ %(intr_ship2,int_add_2,int_cost2)
                    comb_ships_locs2 = intr_ship_ser2.encode("utf-8") + ship_loc2.encode("utf-8") + """</InternationalShippingServiceOption>"""
##################For 3rd Service#######################
                intr_serv3_chk = self.pool.get('ebayerp.template').browse(cr,uid,template_id).serv3_int_chk
                if intr_serv3_chk == True:
                    ship_to3 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).custom_loc3
                    if not ship_to3:
                        raise osv.except_osv(_('Warning!'), _("Please select 3rd Ship to service"))
                    intr_ship3 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).intr_serv3.ship_ser
                    if not intr_ship3:
                        raise osv.except_osv(_('Warning!'), _("Please select 3rd shipping service"))
                    int_cost3= self.pool.get('ebayerp.template').browse(cr,uid,template_id).cost_int3
                    if int_cost3 == False:
                        raise osv.except_osv(_('Warning!'), _("Please enter shipping cost for 1st International service "))
                    int_add_3= self.pool.get('ebayerp.template').browse(cr,uid,template_id).add_int3
                    if int_cost3 == False:
                        int_add_3 = 0
                    if ship_to3 == 'Worldwide':
                        ship_loc3 = """<ShipToLocation>%s</ShipToLocation>""" %(ship_to3)
                    elif ship_to3 == 'Canada':
                        ship_loc3 = """<ShipToLocation>CA</ShipToLocation>"""
                    elif ship_to3 == 'customloc':
                        ship_locs3 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).add_loc_tab3
                        if not ship_locs3:
                            raise osv.except_osv(_('Warning!'), _("Please select atleast one custom location for 3rd shipping service"))
                        else:
                            for cust_locs3 in ship_locs3:
                                intr_loc_code3 = cust_locs3.ship_code
                                ship_loc3+= """<ShipToLocation>%s</ShipToLocation>""" %(intr_loc_code3)
                    intr_ship_ser3+= """<InternationalShippingServiceOption>
                                        <ShippingService>%s</ShippingService>
                                        <ShippingServiceAdditionalCost>%s</ShippingServiceAdditionalCost>
                                        <ShippingServiceCost>%s</ShippingServiceCost>
                                        <ShippingServicePriority>3</ShippingServicePriority>
                                     """ %(intr_ship3,int_add_3,int_cost3)
                    comb_ships_locs3 = intr_ship_ser3.encode("utf-8") + ship_loc3.encode("utf-8") + """</InternationalShippingServiceOption>"""
############################4th Service#####################
                intr_serv4_chk = self.pool.get('ebayerp.template').browse(cr,uid,template_id).serv4_int_chk
                if intr_serv4_chk == True:
                    ship_to4 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).custom_loc4
                    if not ship_to4:
                        raise osv.except_osv(_('Warning!'), _("Please select 4th Ship to service"))
                    intr_ship4 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).intr_serv4.ship_ser
                    if not intr_ship4:
                        raise osv.except_osv(_('Warning!'), _("Please select 4th International shipping service"))
                    int_cost4= self.pool.get('ebayerp.template').browse(cr,uid,template_id).cost_int4
                    if int_cost4 == False:
                        raise osv.except_osv(_('Warning!'), _("Please enter shipping cost for 4th International service "))
                    int_add_4= self.pool.get('ebayerp.template').browse(cr,uid,template_id).add_int4
                    if int_cost4 == False:
                        int_cost4 = 0
                    if ship_to4 == 'Worldwide':
                        ship_loc4 = """<ShipToLocation>%s</ShipToLocation>""" %(ship_to4)
                    elif ship_to4 == 'Canada':
                        ship_loc4 = """<ShipToLocation>CA</ShipToLocation>"""
                    elif ship_to4 == 'customloc':
                        ship_locs4 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).add_loc_tab4
                        if not ship_locs4:
                            raise osv.except_osv(_('Warning!'), _("Please select atleast one custom location for 4th shipping service"))
                        else:
                            for cust_locs4 in ship_locs4:
                                intr_loc_code4 = cust_locs4.ship_code
                                ship_loc4+= """<ShipToLocation>%s</ShipToLocation>""" %(intr_loc_code4)
                    intr_ship_ser4+= """<InternationalShippingServiceOption>
                                        <ShippingService>%s</ShippingService>
                                        <ShippingServiceAdditionalCost>%s</ShippingServiceAdditionalCost>
                                        <ShippingServiceCost>%s</ShippingServiceCost>
                                        <ShippingServicePriority>4</ShippingServicePriority>
                                     """ %(intr_ship4,int_add_4,int_cost4)
                    comb_ships_locs4 = intr_ship_ser4.encode("utf-8") + ship_loc4.encode("utf-8") + """</InternationalShippingServiceOption>"""
############################5th Service#####################
                intr_serv5_chk = self.pool.get('ebayerp.template').browse(cr,uid,template_id).serv5_int_chk
                if intr_serv5_chk == True:
                    ship_to5 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).custom_loc5
                    if not ship_to5:
                        raise osv.except_osv(_('Warning!'), _("Please select 5th Ship to service"))
                    intr_ship5 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).intr_serv5.ship_ser
                    if  not intr_ship5:
                        raise osv.except_osv(_('Warning!'), _("Please select 5th International shipping service"))
                    int_cost5= self.pool.get('ebayerp.template').browse(cr,uid,template_id).cost_int5
                    if int_cost5 == False:
                        raise osv.except_osv(_('Warning!'), _("Please enter shipping cost for 5th International service "))
                    int_add_5= self.pool.get('ebayerp.template').browse(cr,uid,template_id).add_int5
                    if int_add_5 == False:
                        int_add_5 = 0
                    if ship_to5 == 'Worldwide':
                        ship_loc5 = """<ShipToLocation>%s</ShipToLocation>""" %(ship_to5)
                    elif ship_to5 == 'Canada':
                        ship_loc5 = """<ShipToLocation>CA</ShipToLocation>"""
                    elif ship_to5 == 'customloc':
                        ship_locs5 = self.pool.get('ebayerp.template').browse(cr,uid,template_id).add_loc_tab5
                        if not ship_locs5:
                            raise osv.except_osv(_('Warning!'), _("Please select atleast one custom location for 4th shipping service"))
                        else:
                            for cust_locs5 in ship_locs5:
                                intr_loc_code5 = cust_locs5.ship_code
                                ship_loc5+= """<ShipToLocation>%s</ShipToLocation>""" %(intr_loc_code5)
                    intr_ship_ser5+= """<InternationalShippingServiceOption>
                                        <ShippingService>%s</ShippingService>
                                        <ShippingServiceAdditionalCost>%s</ShippingServiceAdditionalCost>
                                        <ShippingServiceCost>%s</ShippingServiceCost>
                                        <ShippingServicePriority>5</ShippingServicePriority>
                                     """ %(intr_ship5,int_add_5,int_cost5)
                    comb_ships_locs5 = intr_ship_ser5.encode("utf-8") + ship_loc5.encode("utf-8") + """</InternationalShippingServiceOption>"""
            elif int_ship_type == 'Calculated':
                ship_to1_calc = self.pool.get('ebayerp.template').browse(cr,uid,template_id).custom_loc
                if not ship_to1_calc:
                        raise osv.except_osv(_('Warning!'), _("Please select Primary Ship to service"))
                intr_ship1_calc = self.pool.get('ebayerp.template').browse(cr,uid,template_id).intr_serv.ship_ser
                if not intr_ship1_calc:
                    raise osv.except_osv(_('Warning!'), _("Please select Primary International shipping service"))
                if ship_to1_calc == 'Worldwide':
                    ship_loc1_calc = """<ShipToLocation>%s</ShipToLocation>""" %(ship_to1_calc)
                elif ship_to1_calc == 'Canada':
                    ship_loc1_calc = """<ShipToLocation>CA</ShipToLocation>"""
                elif ship_to1_calc == 'customloc':
                    ship_locs1_calc = self.pool.get('ebayerp.template').browse(cr,uid,template_id).add_loc_tab
                    if not ship_locs1_calc:
                        raise osv.except_osv(_('Warning!'), _("Please select atleast one custom location for 1st service"))
                    else:
                        for cust_locs_calc in ship_locs1_calc:
                            intr_loc_code_calc = cust_locs_calc.ship_code
                            print"intr_loc_code_calc",intr_loc_code_calc
                            ship_loc1_calc+= """<ShipToLocation>%s</ShipToLocation>""" %(intr_loc_code_calc)
                intr_ship_ser1_calc+= """<InternationalShippingServiceOption>
                                    <ShippingService>%s</ShippingService>
                                    <ShippingServicePriority>1</ShippingServicePriority>
                                 """ %(intr_ship1_calc)
                comb_ships_locs1 = intr_ship_ser1_calc.encode("utf-8") + ship_loc1_calc.encode("utf-8") + """</InternationalShippingServiceOption>"""
############################2nd Service######################################
                intr_serv2_chk_calc = self.pool.get('ebayerp.template').browse(cr,uid,template_id).serv2_int_chk
                if intr_serv2_chk_calc == True:
                    ship_to2_calc = self.pool.get('ebayerp.template').browse(cr,uid,template_id).custom_loc2
                    if not ship_to2_calc:
                        raise osv.except_osv(_('Warning!'), _("Please select 2nd Ship to service"))
                    intr_ship2_calc = self.pool.get('ebayerp.template').browse(cr,uid,template_id).intr_serv2.ship_ser
                    if not intr_ship2_calc:
                        raise osv.except_osv(_('Warning!'), _("Please select 2nd International shipping service"))
                    if ship_to2_calc == 'Worldwide':
                        ship_loc2_calc = """<ShipToLocation>%s</ShipToLocation>""" %(ship_to2_calc)
                    elif ship_to2_calc == 'Canada':
                        ship_loc2_calc = """<ShipToLocation>CA</ShipToLocation>"""
                    elif ship_to2_calc == 'customloc':
                        ship_locs2_calc = self.pool.get('ebayerp.template').browse(cr,uid,template_id).add_loc_tab2
                        if not ship_locs2_calc:
                            raise osv.except_osv(_('Warning!'), _("Please select atleast one custom location for 2nd service"))
                        else:
                            for cust_locs_calc2 in ship_locs2_calc:
                                intr_loc_code_calc2 = cust_locs_calc2.ship_code
                                ship_loc2_calc+= """<ShipToLocation>%s</ShipToLocation>""" %(intr_loc_code_calc2)
                    intr_ship_ser2_calc+= """<InternationalShippingServiceOption>
                                        <ShippingService>%s</ShippingService>
                                        <ShippingServicePriority>2</ShippingServicePriority>
                                     """ %(intr_ship2_calc)
                    comb_ships_locs2 = intr_ship_ser2_calc.encode("utf-8") + ship_loc2_calc.encode("utf-8") + """</InternationalShippingServiceOption>"""
################ 3rd Service######################
                intr_serv3_chk_calc = self.pool.get('ebayerp.template').browse(cr,uid,template_id).serv3_int_chk
                if intr_serv3_chk_calc == True:
                    ship_to3_calc = self.pool.get('ebayerp.template').browse(cr,uid,template_id).custom_loc3
                    if not ship_to3_calc:
                        raise osv.except_osv(_('Warning!'), _("Please select 3rd Ship to service"))
                    intr_ship3_calc = self.pool.get('ebayerp.template').browse(cr,uid,template_id).intr_serv3.ship_ser
                    if not intr_ship3_calc:
                        raise osv.except_osv(_('Warning!'), _("Please select 3rd International shipping service"))
                    if ship_to3_calc == 'Worldwide':
                        ship_loc3_calc = """<ShipToLocation>%s</ShipToLocation>""" %(ship_to3_calc)
                    elif ship_to3_calc == 'Canada':
                        ship_loc3_calc = """<ShipToLocation>CA</ShipToLocation>"""
                    elif ship_to3_calc == 'customloc':
                        ship_locs3_calc = self.pool.get('ebayerp.template').browse(cr,uid,template_id).add_loc_tab3
                        if not ship_locs3_calc:
                            raise osv.except_osv(_('Warning!'), _("Please select atleast one custom location for 3rd service"))
                        else:
                            for cust_locs_calc3 in ship_locs3_calc:
                                intr_loc_code_calc3 = cust_locs_calc3.ship_code
                                ship_loc3_calc+= """<ShipToLocation>%s</ShipToLocation>""" %(intr_loc_code_calc3)
                    intr_ship_ser3_calc+= """<InternationalShippingServiceOption>
                                        <ShippingService>%s</ShippingService>
                                        <ShippingServicePriority>3</ShippingServicePriority>
                                     """ %(intr_ship3_calc)
                    comb_ships_locs3 = intr_ship_ser3_calc.encode("utf-8") + ship_loc3_calc.encode("utf-8") + """</InternationalShippingServiceOption>"""
###############4th Service######################################################################################
                intr_serv4_chk_calc = self.pool.get('ebayerp.template').browse(cr,uid,template_id).serv4_int_chk
                if intr_serv4_chk_calc == True:
                    ship_to4_calc = self.pool.get('ebayerp.template').browse(cr,uid,template_id).custom_loc4
                    if not ship_to4_calc:
                        raise osv.except_osv(_('Warning!'), _("Please select 4th Ship to service"))
                    intr_ship4_calc = self.pool.get('ebayerp.template').browse(cr,uid,template_id).intr_serv4.ship_ser
                    if not intr_ship4_calc:
                        raise osv.except_osv(_('Warning!'), _("Please select 4th International shipping service"))
                    if ship_to4_calc == 'Worldwide':
                        ship_loc4_calc = """<ShipToLocation>%s</ShipToLocation>""" %(ship_to4_calc)
                    elif ship_to4_calc == 'Canada':
                        ship_loc4_calc = """<ShipToLocation>CA</ShipToLocation>"""
                    elif ship_to4_calc == 'customloc':
                        ship_locs4_calc = self.pool.get('ebayerp.template').browse(cr,uid,template_id).add_loc_tab4
                        if not ship_locs4_calc:
                            raise osv.except_osv(_('Warning!'), _("Please select atleast one custom location for 4th service"))
                        else:
                            for cust_locs_calc4 in ship_locs4_calc:
                                intr_loc_code_calc4 = cust_locs_calc4.ship_code
                                ship_loc4_calc+= """<ShipToLocation>%s</ShipToLocation>""" %(intr_loc_code_calc4)
                    intr_ship_ser4_calc+= """<InternationalShippingServiceOption>
                                        <ShippingService>%s</ShippingService>
                                        <ShippingServicePriority>4</ShippingServicePriority>
                                     """ %(intr_ship4_calc)
                    comb_ships_locs4 = intr_ship_ser4_calc.encode("utf-8") + ship_loc4_calc.encode("utf-8") + """</InternationalShippingServiceOption>"""
#########################5th Service###########################3
                intr_serv5_chk_calc = self.pool.get('ebayerp.template').browse(cr,uid,template_id).serv5_int_chk
                if intr_serv5_chk_calc == True:
                    ship_to5_calc = self.pool.get('ebayerp.template').browse(cr,uid,template_id).custom_loc5
                    if not ship_to5_calc:
                        raise osv.except_osv(_('Warning!'), _("Please select 5th Ship to service"))
                    intr_ship5_calc = self.pool.get('ebayerp.template').browse(cr,uid,template_id).intr_serv5.ship_ser
                    if not intr_ship5_calc:
                        raise osv.except_osv(_('Warning!'), _("Please select 5th International shipping service"))
                    if ship_to5_calc == 'Worldwide':
                        ship_loc5_calc = """<ShipToLocation>%s</ShipToLocation>""" %(ship_to5_calc)
                    elif ship_to5_calc == 'Canada':
                        ship_loc5_calc = """<ShipToLocation>CA</ShipToLocation>"""
                    elif ship_to5_calc == 'customloc':
                        ship_locs5_calc = self.pool.get('ebayerp.template').browse(cr,uid,template_id).add_loc_tab5
                        if not ship_locs5_calc:
                            raise osv.except_osv(_('Warning!'), _("Please select atleast one custom location for 5th service"))
                        else:
                            for cust_locs_calc5 in ship_locs5_calc:
                                intr_loc_code_calc5 = cust_locs_calc5.ship_code
                                ship_loc5_calc+= """<ShipToLocation>%s</ShipToLocation>""" %(intr_loc_code_calc5)
                    intr_ship_ser5_calc+= """<InternationalShippingServiceOption>
                                        <ShippingService>%s</ShippingService>
                                        <ShippingServicePriority>5</ShippingServicePriority>
                                     """ %(intr_ship5_calc)
                    comb_ships_locs5 = intr_ship_ser5_calc.encode("utf-8") + ship_loc5_calc.encode("utf-8") + """</InternationalShippingServiceOption>"""
                max_weight_intr = self.pool.get('ebayerp.template').browse(cr,uid,template_id).intr_max_weight
                min_weight_intr = self.pool.get('ebayerp.template').browse(cr,uid,template_id).intr_min_weight
                gross_weight = self.pool.get('product.product').browse(cr,uid,product_id).weight
                net_weight = self.pool.get('product.product').browse(cr,uid,product_id).weight_net
                if gross_weight == 0.0:
                    min_weight_intr = min_weight_intr
                else:
                    min_weight_intr =  gross_weight

                if net_weight == 0.0:
                    max_weight_intr = max_weight_intr
                else:
                    max_weight_intr =  net_weight
                irrg_pack_intr = self.pool.get('ebayerp.template').browse(cr,uid,template_id).intr_irreg_pack
                intr_pack_type = self.pool.get('ebayerp.template').browse(cr,uid,template_id).intr_pack_type
                hand_cost_intr = self.pool.get('ebayerp.template').browse(cr,uid,template_id).intr_handling_cost
                if ship_type == 'Calculated':
                    ship_ser_calc1 = """<CalculatedShippingRate>
                <PackagingHandlingCosts>%s</PackagingHandlingCosts>
                <ShippingIrregular>%s</ShippingIrregular>
                <ShippingPackage>%s</ShippingPackage>
                <WeightMajor>%s</WeightMajor>
                <WeightMinor>%s</WeightMinor>
                </CalculatedShippingRate>"""%(hand_cost,irrg_pack,pack_type,max_weight,min_weight)
                else:
                    ship_ser_calc1 = """<CalculatedShippingRate>
                        <InternationalPackagingHandlingCosts>%s</InternationalPackagingHandlingCosts>
                        <ShippingIrregular>%s</ShippingIrregular>
                        <ShippingPackage>%s</ShippingPackage>
                        <WeightMajor>%s</WeightMajor>
                        <WeightMinor>%s</WeightMinor>
                        </CalculatedShippingRate>"""%(hand_cost_intr,irrg_pack_intr,intr_pack_type,max_weight_intr,min_weight_intr)
        inter_shipping_combo = comb_ships_locs1.encode("utf-8") + comb_ships_locs2.encode("utf-8") + comb_ships_locs3.encode("utf-8") + comb_ships_locs4.encode("utf-8") + comb_ships_locs5.encode("utf-8")
        if ship_type == 'Calculated' and int_ship_type == 'Flat':
            ship_type = 'CalculatedDomesticFlatInternational'
        elif ship_type == 'Flat' and int_ship_type == 'Calculated':
            ship_type = 'FlatDomesticCalculatedInternational'
        if ship_type == 'Free':
            inter_shipping_combo = ''
        hand_time = self.pool.get('ebayerp.template').browse(cr,uid,template_id).hand_time
        if not hand_time:
            raise osv.except_osv(_('Warning!'), _("Please select Handling time"))
        if hand_time:
            handl = """<DispatchTimeMax>%s</DispatchTimeMax>"""%(hand_time)
        get_fast = self.pool.get('ebayerp.template').browse(cr,uid,template_id).get_it_fast
        if get_fast == True:
            get_it_fast = """<GetItFast>%s</GetItFast>"""%(get_fast)
        exclude_locatn = ''
        addtional_loc_cm = ''
        if inter_chk == True:
            add_loc_chk = self.pool.get('ebayerp.template').browse(cr,uid,template_id).act_add_loc
            if add_loc_chk == True:
                add_loc_cust = self.pool.get('ebayerp.template').browse(cr,uid,template_id).add_loc
                if not add_loc_cust:
                    raise osv.except_osv(_('Warning!'), _("Please select atleast one custom location for addtional location"))
                if add_loc_cust == 'Worldwide':
                    addtional_loc_cm+="""<ShipToLocations>%s</ShipToLocations>"""%(add_loc_cust)
                elif add_loc_cust == 'unitedstates':
                    ship_locs_cm = self.pool.get('ebayerp.template').browse(cr,uid,template_id).add_loc_tab_cm
                    for cust_locs_cm in ship_locs_cm:
                        intr_loc_code_cm = cust_locs_cm.ship_code
                        addtional_loc_cm+= """<ShipToLocations>%s</ShipToLocations>""" %(intr_loc_code_cm)
#############################for passing start price ,reserve price and buy it now price to the api##########################################
        
        payment_method = shop_id.pay_mthd
        paypal_email = shop_id.email_add
        private_listing = ''
        buyer_info = template_object.check
        if buyer_info == True:
            buyer_pay_pal = template_object.pay_pal_accnt
            if buyer_pay_pal:
                linked_paypal = """<LinkedPayPalAccount>%s</LinkedPayPalAccount>"""%(buyer_pay_pal)
            else:
                linked_paypal = """<LinkedPayPalAccount>%s</LinkedPayPalAccount>"""%(False)
            buyer_pri_ship = template_object.pri_ship
            if buyer_pri_ship:
                pri_ship = """ <ShipToRegistrationCountry>%s</ShipToRegistrationCountry> """%(buyer_pri_ship)
            else:
                pri_ship = """ <ShipToRegistrationCountry>%s</ShipToRegistrationCountry> """%(False)
            buyer_have_rec = template_object.have_rec
            if buyer_have_rec:
                buyer_unpaid_str = template_object.unpaid_str
                buyer_unpaid_str_wthn = template_object.unpaid_str_wthn
                unpaidstr = """<MaximumUnpaidItemStrikesInfo>
                <Count>%s</Count>
                <Period>%s</Period>
                </MaximumUnpaidItemStrikesInfo>"""%(buyer_unpaid_str,buyer_unpaid_str_wthn)
            else:
                unpaidstr = ''
            buyer_hv_policy_vio = template_object.hv_policy_vio
            if buyer_hv_policy_vio:
                buyer_policy_vio = template_object.policy_vio
                buyer_policy_vio_wthn = template_object.policy_vio_wthn
                policy_vio = """<MaximumBuyerPolicyViolations>
        <Count>%s</Count>
        <Period>%s</Period>
      </MaximumBuyerPolicyViolations>"""%(buyer_policy_vio,buyer_policy_vio_wthn)
            else:
                policy_vio = ''
            buyer_hv_feed_scr = template_object.hv_feed_scr
            if buyer_hv_feed_scr:
                buyer_feed_scr = template_object.feed_scr
                feed_scr = """<MinimumFeedbackScore>%s</MinimumFeedbackScore>"""%(buyer_feed_scr)
            else:
                feed_scr =''
            hv_bid = template_object.hv_bid
            if hv_bid:
                buyer_bid = template_object.bid
            else:
                buyer_bid = ''
            only_feed_scr = template_object.only_feed_scr
            if only_feed_scr:
                buyer_feed_scr_lwr = template_object.feed_scr_lwr
            else:
                buyer_feed_scr_lwr=''
            if hv_bid and only_feed_scr:
                maximum_item_requirements = """<MaximumItemRequirements> MaximumItemRequirementsType
           <MaximumItemCount>%s</MaximumItemCount>
           <MinimumFeedbackScore>%s</MinimumFeedbackScore>
         </MaximumItemRequirements>"""%(buyer_bid,buyer_feed_scr_lwr)
            else:
                maximum_item_requirements = ''
            buyerrequirement_str = "<BuyerRequirementDetails>" + linked_paypal.encode('utf-8') + pri_ship.encode('utf-8')+ unpaidstr.encode('utf-8')+ policy_vio.encode('utf-8')+ feed_scr.encode('utf-8') + maximum_item_requirements.encode('utf-8') + "</BuyerRequirementDetails>"
        else:
            buyerrequirement_str =''
        buyer_priv_list = template_object.priv_list
        if buyer_priv_list:
            private_listing = """ <PrivateListing>%s</PrivateListing>"""%(buyer_priv_list)
        else:
            private_listing = ''
        return_policy = template_object.retur_pol
        return_policy_string = ''
        if return_policy == 'ReturnsAccepted':
             add_det = template_object.add_det
             if not add_det:
                 add_det = ''
             retur_days = template_object.retur_days
             refund_giv_as = template_object.refund_giv_as
             paid_by = template_object.paid_by
             return_policy_string += """
<ReturnsAcceptedOption>%s</ReturnsAcceptedOption>
  <RefundOption>%s</RefundOption>
  <ReturnsWithinOption>%s</ReturnsWithinOption>
  <Description>%s</Description>
  <ShippingCostPaidByOption>%s</ShippingCostPaidByOption>"""%(return_policy,refund_giv_as,retur_days,add_det,paid_by)
        else:
            return_policy_string += """
<ReturnsAcceptedOption>%s</ReturnsAcceptedOption>"""%(return_policy)
        return_policy_details = ''
        return_policy_details = """<ReturnPolicy>""" + return_policy_string.encode("utf-8") + """ </ReturnPolicy>"""
        new_related_fields = ''
        related_fields = ''
        if start_price:
            start_price ="""<StartPrice>%s</StartPrice>"""%(start_price)
        else:
            start_price =''
        if quantity:
            quantity ="""<Quantity>%s</Quantity>"""%(quantity)
        else:
            quantity = ''
        if reserve_price:
            reserve_price ="""<ReservePrice currencyID="USD">%s</ReservePrice>"""%(reserve_price)
        else:
            reserve_price = ''
        if buy_it_now_price:
            buy_it_now_price ="""<BuyItNowPrice currencyID="USD">%s</BuyItNowPrice>"""%(buy_it_now_price)
        else:
            buy_it_now_price = ''
        if listing_type == 'LeadGeneration':
            new_related_fields += "<ListingSubtype2>ClassifiedAd</ListingSubtype2>"
            new_related_fields = new_related_fields + start_price.encode("utf-8")+quantity.encode("utf-8")
        elif listing_type == 'Chinese':
            related_fields += """
            <PaymentMethods>%s</PaymentMethods>
            <PayPalEmailAddress>%s</PayPalEmailAddress>
    """ % (payment_method,paypal_email)
            ship_fields = ''
            quantity ="""<Quantity>1</Quantity>"""
            ship_fields += """<ShippingDetails>
            <ShippingType>%s</ShippingType>
            <PaymentInstructions>%s</PaymentInstructions>
            """% (ship_type,add_info)
            shipping_options = ship_ser1.encode("utf-8") + ship_ser2.encode("utf-8") + ship_ser3.encode("utf-8") + ship_ser4.encode("utf-8") + ship_ser_1.encode("utf-8") + ship_ser_2.encode("utf-8") +ship_ser_3.encode("utf-8") + ship_ser_4.encode("utf-8") + ship_ser_calc1.encode("utf-8") + free_ship_serv.encode("utf-8")
            shipping_tag = start_price.encode("utf-8")+quantity.encode("utf-8")+reserve_price.encode("utf-8") +buy_it_now_price.encode("utf-8")+related_fields.encode("utf-8") + ship_fields.encode("utf-8") + shipping_options.encode("utf-8") + inter_shipping_combo.encode("utf-8") + exclude_locatn.encode("utf-8") + """</ShippingDetails>"""
            new_related_fields = shipping_tag.encode("utf-8") +  return_policy_details.encode("utf-8") + buyerrequirement_str.encode("utf-8") + private_listing.encode("utf-8")+ addtional_loc_cm.encode("utf-8") + get_it_fast.encode("utf-8") + handl.encode("utf-8")
        elif listing_type == 'FixedPriceItem':
            related_fields += """
            <PaymentMethods>%s</PaymentMethods>
            <PayPalEmailAddress>%s</PayPalEmailAddress>
     """ % (payment_method,paypal_email)
            ship_fields = ''
            ship_fields += """<ShippingDetails>
            <ShippingType>%s</ShippingType>
            <PaymentInstructions>%s</PaymentInstructions>
    """% (ship_type,add_info)
            shipping_options = ship_ser1.encode("utf-8") + ship_ser2.encode("utf-8") + ship_ser3.encode("utf-8") + ship_ser4.encode("utf-8") + ship_ser_1.encode("utf-8") + ship_ser_2.encode("utf-8") +ship_ser_3.encode("utf-8") + ship_ser_4.encode("utf-8") + ship_ser_calc1.encode("utf-8") + free_ship_serv.encode("utf-8")
            shipping_tag = start_price.encode("utf-8")+quantity.encode("utf-8")+related_fields.encode("utf-8") + ship_fields.encode("utf-8") + shipping_options.encode("utf-8") + inter_shipping_combo.encode("utf-8") + exclude_locatn.encode("utf-8") + """</ShippingDetails>"""
            new_related_fields = shipping_tag.encode("utf-8")  +  return_policy_details.encode("utf-8") + buyerrequirement_str.encode("utf-8")+ private_listing.encode("utf-8") + addtional_loc_cm.encode("utf-8") + get_it_fast.encode("utf-8") + handl.encode("utf-8")
        else:
            new_related_fields = ''
        return new_related_fields

    def write(self, cr, uid, ids, vals, context=None):
        if ids:
            ids = super(sale_shop, self).write(cr, uid, ids, vals, context=context)
            if 'order_policy' in vals:
                if vals['order_policy'] == 'prepaid':
                    vals.update({'invoice_quantity': 'order'})
                elif vals['order_policy'] == 'picking':
                    vals.update({'invoice_quantity': 'procurement'})
            return ids

    def create(self, cr, uid, vals, context={}):
        print "::::::::::vals",vals
        vals['company_id'] = vals['company_id'][0]
        vals['site_id'] = vals['site_id'][0]
        vals['warehouse_id'] = vals['warehouse_id'][0]
        id = super(sale_shop, self).create(cr, uid, vals, context=context)
        if id:
            if 'order_policy' in vals:
                if vals['order_policy'] == 'prepaid':
                    vals.update({'invoice_quantity': 'order'})
                if vals['order_policy'] == 'picking':
                    vals.update({'invoice_quantity': 'procurement'})
            return id

    _columns = {
        'instance_id' : fields.many2one('ebayerp.instance','Instance',readonly=True,help="Current shop is related with this Instance"),
#        'last_inventory_export_date': fields.datetime('Last Inventory Export Time'),
#        'last_update_order_export_date' : fields.datetime('Last Order Update  Time'),
        'is_tax_included': fields.boolean('Prices Include Tax?', help="Requires sale_tax_include module to be installed"),
        'journal_id': fields.many2one('account.journal','Journal/Payment Mode'),
        #TODO all the following settings are deprecated and replaced by the finer grained base.sale.payment.type settings!
        'picking_policy': fields.selection([('direct', 'Partial Delivery'), ('one', 'Complete Delivery')],
                                           'Packing Policy', help="""If you don't have enough stock available to deliver all at once, do you accept partial shipments or not?"""),
        'order_policy': fields.selection([
            ('prepaid', 'Payment Before Delivery'),
            ('manual', 'Shipping & Manual Invoice'),
            ('postpaid', 'Invoice on Order After Delivery'),
            ('picking', 'Invoice from the Packing'),
        ], 'Shipping Policy', help="""The Shipping Policy is used to synchronise invoice and delivery operations.
  - The 'Pay before delivery' choice will first generate the invoice and then generate the packing order after the payment of this invoice.
  - The 'Shipping & Manual Invoice' will create the packing order directly and wait for the user to manually click on the 'Invoice' button to generate the draft invoice.
  - The 'Invoice on Order After Delivery' choice will generate the draft invoice based on sale order after all packing lists have been finished.
  - The 'Invoice from the packing' choice is used to create an invoice during the packing process."""),
        'invoice_quantity': fields.selection([('order', 'Ordered Quantities'), ('procurement', 'Shipped Quantities')], 'Invoice on', help="The sale order will automatically create the invoice proposition (draft invoice). Ordered and delivered quantities may not be the same. You have to choose if you invoice based on ordered or shipped quantities. If the product is a service, shipped quantities means hours spent on the associated tasks."),
        'invoice_generation_policy': fields.selection([('none', 'None'), ('draft', 'Draft'), ('valid', 'Validated')], 'Invoice Generation Policy', help="Should orders create an invoice after import?"),
        'picking_generation_policy': fields.selection([('none', 'None'), ('draft', 'Draft'), ('valid', 'Validated')], 'Picking Generation Policy', help="Should orders create a picking after import?"),
        'ebay_shop' : fields.boolean('Ebay Shop',readonly=True),
        'auto_import_ebay' : fields.boolean('Auto Import'),
        'url':fields.char('URL',size=31),
        'acnt':fields.char('Account name',size=32),
        'pay_mthd': fields.selection([('PayPal', 'PayPal')],'Payment Methods',help="Method of Payment"),
        'email_add' : fields.char('Email Address', size=126,help="Seller Email Address"),
        'partner_id' : fields.many2one('res.partner','Customer'),
        'post_code':fields.char('Postal Code',size=64,help="Enter the Postal Code for Item Location"),
        'site_id' : fields.many2one('site.details','Site'),
    }
    _defaults = {
       # 'payment_default_id': lambda * a: 1, #required field that would cause trouble if not set when importing
        'picking_policy': lambda * a: 'one',
        'order_policy': lambda * a: 'prepaid',
        'invoice_quantity': lambda * a: 'order',
        'invoice_generation_policy': lambda * a: 'valid',
        'picking_generation_policy': lambda * a: 'draft',
    }

    def call(self, cr, uid, referential, method, *arguments):
        if method == 'GetToken':
            tk = Token(referential.dev_id, referential.app_id, referential.cert_id, referential.auth_token, referential.server_url)
            result = tk.Get()
        elif method == 'GeteBayOfficialTime':
            eTime = eBayTime(referential.dev_id, referential.app_id, referential.cert_id, referential.auth_token, referential.server_url)
            result = eTime.Get()
            return result

        elif method == 'GetOrders':
            gOrders = GetOrders(referential.dev_id, referential.app_id, referential.cert_id, referential.auth_token, referential.server_url)
            result = gOrders.Get(arguments[0],arguments[1],arguments[2])
            return result

        elif method == 'GetItemTransactions':
            gItemTrans = GetItemTransactions(referential.dev_id, referential.app_id, referential.cert_id, referential.auth_token, referential.server_url)
            result = gItemTrans.Get(arguments[0],arfguments[1])

        elif method == 'GetSellerTransactions':
            gSellerTrans = GetSellerTransactions(referential.dev_id, referential.app_id, referential.cert_id, referential.auth_token, referential.server_url)
            result = gSellerTrans.Get(arguments[0],arguments[1],arguments[2],arguments[3])
            return result

        elif method == 'GetItem':
            gItem = GetItem(referential.dev_id, referential.app_id, referential.cert_id, referential.auth_token, referential.server_url)
            result = gItem.Get(arguments[0],arguments[1])
            return result

        elif method == 'GetSellerList':
            gItem = GetSellerList(referential.dev_id, referential.app_id, referential.cert_id, referential.auth_token, referential.server_url)
            result = gItem.Get(arguments[0],arguments[1],arguments[2])
            return result

        elif method == 'CompleteSale':
            gCompleteSale = CompleteSale(referential.dev_id, referential.app_id, referential.cert_id, referential.auth_token, referential.server_url)
            result = gCompleteSale.Get(arguments[0],arguments[1])
            return result
        
        elif method == 'ReviseInventoryStatus':
            revInvStatus = ReviseInventoryStatus(referential.dev_id, referential.app_id, referential.cert_id, referential.auth_token, referential.server_url)
            result = revInvStatus.Get(arguments[0],arguments[1], arguments[2],arguments[3])
            return result

        elif method == 'RelistItem':
           relist = RelistItem(referential.dev_id, referential.app_id, referential.cert_id, referential.auth_token, referential.server_url)
           result = relist.Get(arguments[0],arguments[1],arguments[2],arguments[3],arguments[4],arguments[5],arguments[6],arguments[7],arguments[8],arguments[9],arguments[10],arguments[11],cr,uid)
           print"result",result
           return result

        elif method == 'GetCategories':
            categories = GetCategories(referential.dev_id, referential.app_id, referential.cert_id, referential.auth_token, referential.server_url)
            result = categories.Get(arguments[0],arguments[1])
            return result

        elif method == 'GetCategory2CS':
            categories = GetCategory2CS(referential.dev_id, referential.app_id, referential.cert_id, referential.auth_token, referential.server_url)
            result = categories.Get(arguments[0],arguments[1])
            return result

        elif method == 'GetAttributesCS':
            attribute = GetAttributesCS(referential.dev_id, referential.app_id, referential.cert_id, referential.auth_token, referential.server_url)
            result = attribute.Get(arguments[0],arguments[1])
            return result

        elif method == 'GetCategoryFeatures':
            itemspecfics = GetCategoryFeatures(referential.dev_id, referential.app_id, referential.cert_id, referential.auth_token, referential.server_url)
            result = itemspecfics.Get(arguments[0],arguments[1])
            return result
        
        elif method == 'AddItem':
            item = AddItem(referential.dev_id, referential.app_id, referential.cert_id, referential.auth_token, referential.server_url)
            result = item.Get(arguments[0],arguments[1],arguments[2],arguments[3],arguments[4],arguments[5],arguments[6],arguments[7],arguments[8],arguments[9],arguments[10],cr,uid)
            print"this is the additem output",result
            return result

        elif method == 'ReviseItem':
            revise_item = ReviseItem(referential.dev_id, referential.app_id, referential.cert_id, referential.auth_token, referential.server_url)
            result = revise_item.Get(arguments[0],arguments[1],arguments[2],arguments[3],arguments[4],arguments[5],arguments[6],arguments[7],arguments[8],cr,uid)
            print"this is the reviseitem output",result
            return result

        elif method == 'EndItem':
            end_item = EndItem(referential.dev_id, referential.app_id, referential.cert_id, referential.auth_token, referential.server_url)
            result = end_item.Get(arguments[0],arguments[1],arguments[2])
            return result

        elif method == 'GeteBayDetails':
            getebaydet = GeteBayDetails(referential.dev_id, referential.app_id, referential.cert_id, referential.auth_token, referential.server_url)
            result = getebaydet.Get(arguments[0])
            return result
        
        elif method == 'UploadSiteHostedPictures':
           upload = UploadSiteHostedPictures(referential.dev_id, referential.app_id, referential.cert_id, referential.auth_token, referential.server_url)
           result = upload.Get(arguments[0],arguments[1])
           return result
       
        elif method == 'GetProducts':
           get_products = GetProducts(referential.dev_id, referential.app_id, referential.cert_id, referential.auth_token, referential.server_url)
           result = get_products.Get(arguments[0],arguments[1],arguments[2],arguments[3],arguments[4])
           return result
sale_shop()

class sale_order(osv.osv):
    _name = 'sale.order'
    _inherit = 'sale.order'
    def _default_journal(self, cr, uid, context={}):
       accountjournal_obj = self.pool.get('account.journal')
       accountjournal_ids = accountjournal_obj.search(cr,uid,[('name','=','Sales Journal')])
       if accountjournal_ids:
           return accountjournal_ids[0]
       else:
#            raise wizard.except_wizard(_('Error !'), _('Sales journal not defined.'))
           return False
    _columns = {
        'ebay_order_id' : fields.char('Ebay Order ID', size=256),
        'journal_id': fields.many2one('account.journal', 'Journal',readonly=True),
   }
    _defaults = {
       'journal_id': _default_journal,
    }
sale_order()
