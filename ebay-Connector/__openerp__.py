#########################################################################
#                                                                       #
# Copyright (C) 2011 Bista Solutions  www.bistasolutions.com            #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################
{
    "name" : "Ebay e-commerce",
    "version" : "1.0",
    "depends" : ["base","product","sale","base_sale_multichannels","product_images_olbs","delivery",'account','stock'],
    "author" : "Bista Solutions",
    "description": """ Ebay E-commerce Management
	Contact us at sales@bistasolutions.com for any queries related to this module
	Check our YouTube channel for videos on how to you this module http://youtube.com/opensourcebista
""",
    "website" : "http://www.bistasolutions.com/",
    "category" : "Generic Modules",
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
            
        #    'security/ir.model.access.csv',
            'wizard/create_ebay_shop.xml',
            'wizard/many2many_filter.xml',
            'wizard/many2many_filter_relist.xml',
            'wizard/catalog_en.xml',
            'sale_view.xml',
            'template_view.xml',
            
            'ebayerp_view.xml',
            'category_attribute.xml',
            'ebayerp_menu.xml',
            'global_setting_view.xml',
            'duration_data.xml',
            'partner_view.xml',
            'product_view.xml',
            'magento_sale.xml',
            'ecomm_sett.xml',
            
                    ],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

