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
class res_partner(osv.osv):
    _name = "res.partner"
    _inherit = "res.partner"
    _columns = {
        'ebay_eias_token' : fields.char('EIAS Token',size=256),
        'ebay_reg_date' : fields.char('Registration Date',size=64),
        'ebay_user_id' : fields.char('User ID',size=64),
        'ebay_user_id_last_changed' : fields.char('User ID Last Changed',size=64),
        'ebay_user_emaid_id' : fields.char('Email',size=100),
#        'ebay_shop_ids' : fields.one2many('sale.shop','partner_id','Ebay Shops',readonly=True)
           'ebay_shop_ids' : fields.many2many('sale.shop','partner_shop_id','partner_id','shop_id','Ebay Shops',readonly=True)
    }

res_partner()

class res_partner_address(osv.osv):
    _name = "res.partner.address"
    _inherit = "res.partner.address"
    _columns = {
        'ebay_address_id' : fields.char('Address ID',size=64),
    }

res_partner_address()

#class res_users(osv.osv):
##    _name = "res.users"
#    _inherit = "res.users"
#    _columns = {
#        'server_offset' : fields.char('US server offset',size=3),
#    }
#
#res_users()

class delivery_carrier(osv.osv):
    _inherit = "delivery.carrier"

    _columns = {
        'ebay_code': fields.char('Ebay Carrier Code', size=64, required=False),
    }

delivery_carrier()
