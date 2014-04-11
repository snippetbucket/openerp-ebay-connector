# coding: utf-8
from osv import osv, fields
import time
import datetime
import xmlrpclib
import netsvc
logger = netsvc.Logger()
import urllib2
import base64
from base_external_referentials import external_osv
from tools.translate import _
import pooler
import httplib, ConfigParser, urlparse
from xml.dom.minidom import parse, parseString
import os

class Session:
    # Plug the following values into ebay.ini (not here)
    Developer = "YOUR_DEVELOPER_KEY"
    Certificate = "YOUR_CERTIFICATE"
    Token = "YOUR_TOKEN"
    ServerURL = "https://api.sandbox.ebay.com/ws/api.dll"

    def Initialize(self, Developer, Application, Certificate, Token, ServerURL):
        config = ConfigParser.ConfigParser()
        config.read("ebay.ini")
        """self.Developer = config.get("Developer Keys", "Developer")
        self.Application = config.get("Developer Keys", "Application")
        self.Certificate = config.get("Developer Keys", "Certificate")
        self.Token = config.get("Authentication", "Token")
        self.ServerURL = config.get("Server", "URL")"""
        self.Developer = Developer
        self.Application = Application
        self.Certificate = Certificate
        self.Token = Token
        self.ServerURL = ServerURL
        urldat = urlparse.urlparse(self.ServerURL)
        self.Server = urldat[1]   # e.g., api.sandbox.ebay.com
        self.Command = urldat[2]  # e.g., /ws/api.dll
########## Call
class Call:
    RequestData = "<xml />"  # just a stub
    DetailLevel = "0"
    SiteID = "0"
    def MakeCall(self, CallName):
        conn = httplib.HTTPSConnection(self.Session.Server)
        if CallName =='UploadSiteHostedPictures':
            conn.request("POST", self.Session.Command, self.RequestData, self.GenerateHeaders_upload_picture(self.Session, CallName,len(self.RequestData)))
        else:
            conn.request("POST", self.Session.Command, self.RequestData, self.GenerateHeaders(self.Session, CallName))
        response = conn.getresponse()
        data = response.read()
        conn.close()
        responseDOM = parseString(data)
        # check for any <Error> tags and print
        # TODO: Return a real exception and log when this happens
        tag = responseDOM.getElementsByTagName('Error')
        if (tag.count!=0):
            for error in tag:
                print "\n",error.toprettyxml("  ")
        return responseDOM

    def GenerateHeaders(self, Session, CallName):
        headers = {"X-EBAY-API-COMPATIBILITY-LEVEL": "713",
                   "X-EBAY-API-SESSION-CERTIFICATE": Session.Developer + ";" + Session.Application + ";" + Session.Certificate,
                   "X-EBAY-API-DEV-NAME": Session.Developer,
                   "X-EBAY-API-APP-NAME": Session.Application,
                   "X-EBAY-API-CERT-NAME": Session.Certificate,
                   "X-EBAY-API-CALL-NAME": CallName,
                   "X-EBAY-API-SITEID": self.SiteID,
                   "X-EBAY-API-DETAIL-LEVEL": self.DetailLevel,
                   "Content-Type": "text/xml"}
        return headers
    
    def GenerateHeaders_upload_picture(self, Session, CallName,length):
        headers = {
                  "Content-Type": "multipart/form-data; boundary=MIME_boundary",
                  "Content-Length":length,
                  "X-EBAY-API-COMPATIBILITY-LEVEL": "747",
                  "X-EBAY-API-DEV-NAME": Session.Developer,
                  "X-EBAY-API-APP-NAME": Session.Application,
                  "X-EBAY-API-CERT-NAME": Session.Certificate,
                  "X-EBAY-API-CALL-NAME": CallName,
                  "X-EBAY-API-SITEID": self.SiteID,
                 
                  }
        return headers

########## GetToken
class Token:
    Session = Session()

    def __init__(self, DevID, AppID, CertID, Token, ServerURL):
        self.Session.Initialize(DevID, AppID, CertID, Token, ServerURL)
        self.RequestUserId = 'TESTUSER_aasim.ansari'
        self.RequestPassword = 'Makaami_5kaam'

    def Get(self,siteid):
        api = Call()
        api.Session = self.Session
        api.SiteID = siteid
        api.DetailLevel = "0"
        api.RequestData = """<?xml version='1.0' encoding='utf-8'?>
<request>
    <RequestToken></RequestToken>
    <RequestUserId>%(userid)s</RequestUserId>
    <RequestPassword>%(password)s</RequestPassword>
    <DetailLevel>%(detail)s</DetailLevel>
    <ErrorLevel>1</ErrorLevel>
    <SiteId>0</SiteId>
    <Verb>GetToken</Verb>
</request>"""
        api.RequestData = api.RequestData % { 'detail': api.DetailLevel,
                                              'userid': self.RequestUserId,
                                              'password': self.RequestPassword}
#        print api.RequestData
        self.Xml = api.MakeCall("GetToken")

class eBayTime:
    Session = Session()

    def __init__(self, DevID, AppID, CertID, Token, ServerURL):
        self.Session.Initialize(DevID, AppID, CertID, Token, ServerURL)

    def Get(self):
        api = Call()
        api.Session = self.Session
        api.RequestData = """<?xml version="1.0" encoding="utf-8"?>
<request>
    <RequestToken>%(token)s</RequestToken>
    <ErrorLevel>1</ErrorLevel>
    <DetailLevel>0</DetailLevel>
    <Verb>GeteBayOfficialTime</Verb>
    <SiteId>0</SiteId>
</request>"""
        api.RequestData = api.RequestData % { 'token': self.Session.Token,
                                              'detail': api.DetailLevel }

        responseDOM = api.MakeCall("GeteBayOfficialTime")
        timeElement = responseDOM.getElementsByTagName('EBayTime')
        if (timeElement != []):
            return timeElement[0].childNodes[0].data
        responseDOM.unlink()

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)
class GetSellerList:
    Session = Session()
    DevID = ''
    AppID = ''
    CertID = ''
    Token = ''
    ServerURL = ''

    def __init__(self, DevID, AppID, CertID, Token, ServerURL):
        self.DevID = DevID
        self.AppID = AppID
        self.CertID = CertID
        self.Token = Token
        self.ServerURL = ServerURL
        self.Session.Initialize(DevID, AppID, CertID, Token, ServerURL)

    def geterrors(self, nodelist):
      transDetails = []
      info = {}
      for cNode in nodelist.childNodes:
          if cNode.nodeName == 'LongMessage':
              if cNode.childNodes:
                info[cNode.nodeName] = cNode.childNodes[0].data
          if cNode.nodeName == 'SeverityCode':
              if cNode.childNodes:
                info[cNode.nodeName] = cNode.childNodes[0].data
      transDetails.append(info)
      return transDetails

    def Get(self, timeFrom, timeTo,site_id):
        api = Call()
        api.Session = self.Session
        api.SiteID = site_id
        api.RequestData = """<?xml version="1.0" encoding="utf-8"?>
<GetSellerListRequest xmlns="urn:ebay:apis:eBLBaseComponents">
  <DetailLevel>ItemReturnDescription</DetailLevel>
  <RequesterCredentials>
    <eBayAuthToken>%(token)s</eBayAuthToken>
  </RequesterCredentials>
  <ErrorLanguage>en_US</ErrorLanguage>
  <WarningLevel>High</WarningLevel>
  <StartTimeFrom>%(startTime)s</StartTimeFrom>
  <StartTimeTo>%(endTime)s</StartTimeTo>
  <IncludeWatchCount>true</IncludeWatchCount>
  <Pagination>
    <EntriesPerPage>200</EntriesPerPage>
  </Pagination>
  </GetSellerListRequest>​​​"""
        api.RequestData = api.RequestData % { 'token': self.Session.Token.encode("utf-8"),
                                              'startTime': timeFrom,
                                              'endTime': timeTo }
        responseDOM = api.MakeCall("GetSellerList")
        print"responseDom",responseDOM.toprettyxml()
        Dictionary={}
        if responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Success':
            ack = responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data
            Dictionary.update({'Ack': ack})
            gItem = GetItem(self.DevID, self.AppID, self.CertID, self.Token, self.ServerURL)
            Dictionary.update({'Item':gItem.getItemInfo(responseDOM.getElementsByTagName('Item'))})
        elif responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Warning':
            ack = responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data
            Dictionary.update({'Ack': ack})
            many_errors = []
            for each_error in  responseDOM.getElementsByTagName('Errors'):
                errors = self.geterrors(each_error)
                many_errors.append(errors)
            logger.notifyChannel('init', netsvc.LOG_WARNING, 'LongMessage %s' % (many_errors))
            Dictionary.update({'LongMessage': many_errors})
        elif responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Failure':
            ack = responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data
            Dictionary.update({'Ack': ack})
            many_errors = []
            for each_error in  responseDOM.getElementsByTagName('Errors'):
                errors = self.geterrors(each_error)
                many_errors.append(errors)
            logger.notifyChannel('init', netsvc.LOG_WARNING, 'LongMessage %s' % (many_errors))
            Dictionary.update({'LongMessage': many_errors})
       # force garbage collection of the DOM object
        responseDOM.unlink()
        return Dictionary

class GetItemTransactions:
    Session = Session()

    def __init__(self, DevID, AppID, CertID, Token, ServerURL):
        self.Session.Initialize(DevID, AppID, CertID, Token, ServerURL)

    def Get(self, ItemId,siteid):
        api = Call()
        api.Session = self.Session
        api.SiteID = siteid
        api.RequestData = """<?xml version="1.0" encoding="utf-8"?>
<GetItemTransactionsRequest xmlns="urn:ebay:apis:eBLBaseComponents">
<Version>681</Version>
<ItemID>%(item_id)s</ItemID>
<RequesterCredentials>
<eBayAuthToken>%(token)s</eBayAuthToken>
</RequesterCredentials>
</GetItemTransactionsRequest>​​"""

        api.RequestData = api.RequestData % { 'token': self.Session.Token.encode("utf-8"),
                                              'item_id': ItemId }
        responseDOM = api.MakeCall("GetItemTransactions")
#        print "GetItemTransactions Output: ",responseDOM.toprettyxml()
        # force garbage collection of the DOM object
        responseDOM.unlink()

class GetSellerTransactions:
    Session = Session()

    def __init__(self, DevID, AppID, CertID, Token, ServerURL):
        self.Session.Initialize(DevID, AppID, CertID, Token, ServerURL)
    def geterrors(self, nodelist):
       transDetails = []
       info = {}
       for cNode in nodelist.childNodes:
           if cNode.nodeName == 'LongMessage':
               if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
           if cNode.nodeName == 'SeverityCode':
               if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
       transDetails.append(info)
       return transDetails
    def getBuyerInfo(self, node):
        cNodes = node.childNodes
        info = {}
        for cNode in cNodes:
            if cNode.nodeName == 'EIASToken':
                if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
            elif cNode.nodeName == 'Email':
                if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
            elif cNode.nodeName == 'UserID':
                if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
            elif cNode.nodeName == 'RegistrationDate':
                if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
            elif cNode.nodeName == 'UserIDLastChanged':
                if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
            elif cNode.nodeName == 'BuyerInfo':
                if cNode.childNodes[0].childNodes:
                    for gcNode in cNode.childNodes[0].childNodes:
                        if gcNode.nodeName == 'Name':
                            if gcNode.childNodes:
                                info[gcNode.nodeName] = gcNode.childNodes[0].data
                        elif gcNode.nodeName == 'Street1':
                            info[gcNode.nodeName] = gcNode.childNodes and gcNode.childNodes[0].data or ''
                        elif gcNode.nodeName == 'CityName':
                            info[gcNode.nodeName] = gcNode.childNodes and gcNode.childNodes[0].data or ''
                        elif gcNode.nodeName == 'StateOrProvince':
                            info[gcNode.nodeName] = gcNode.childNodes and gcNode.childNodes[0].data or ''
                        elif gcNode.nodeName == 'CountryName':
                            info[gcNode.nodeName] = gcNode.childNodes and gcNode.childNodes[0].data or ''
                        elif gcNode.nodeName == 'Phone':
                            info[gcNode.nodeName] = gcNode.childNodes and gcNode.childNodes[0].data or ''
                        elif gcNode.nodeName == 'PostalCode':
                            info[gcNode.nodeName] = gcNode.childNodes and gcNode.childNodes[0].data or ''
                        elif gcNode.nodeName == 'AddressID':
                            info[gcNode.nodeName] = gcNode.childNodes and gcNode.childNodes[0].data or ''
                        elif gcNode.nodeName == 'AddressOwner':
                            info[gcNode.nodeName] = gcNode.childNodes and gcNode.childNodes[0].data or ''
                        elif gcNode.nodeName == 'AddressUsage':
                            info[gcNode.nodeName] = gcNode.childNodes and gcNode.childNodes[0].data or ''
        return info

    def getSellingManagerProductDetailsInfo(self, node):
        info = {}
        for cNode in node.childNodes:
            if cNode.nodeName == 'CustomLabel':
                if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
        return info

    def getItemInfo(self, node):
        info = {}
        for cNode in node.childNodes:
            if cNode.nodeName == 'ItemID':
                if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
            elif cNode.nodeName == 'SKU':
                if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
            elif cNode.nodeName == 'ListingType':
                if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
            elif cNode.nodeName == 'PaymentMethods':
                if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
            elif cNode.nodeName == 'Quantity':
                if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
            elif cNode.nodeName == 'SellingStatus':
                for ssNode in cNode.childNodes:
                    if ssNode.nodeName == 'CurrentPrice':
                        if ssNode.childNodes:
                            info[ssNode.nodeName] = ssNode.childNodes[0].data
                    elif ssNode.nodeName == 'QuantitySold':
                        if ssNode.childNodes:
                            info[ssNode.nodeName] = ssNode.childNodes[0].data
                    elif ssNode.nodeName == 'ListingStatus':
                        if ssNode.childNodes:
                            info[ssNode.nodeName] = ssNode.childNodes[0].data
            elif cNode.nodeName == 'ConditionDisplayName':
                if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
            elif cNode.nodeName == 'ConditionID':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
        return info

    def getStatusInfo(self, node):
        info = {}
        for cNode in node.childNodes:
            if cNode.nodeName == 'eBayPaymentStatus':
                if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
                    paymentstat = info[cNode.nodeName]
            elif cNode.nodeName == 'CheckoutStatus':
                if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
            elif cNode.nodeName == 'PaymentMethodUsed':
                if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
            elif cNode.nodeName == 'CompleteStatus':
                if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
            elif cNode.nodeName == 'BuyerSelectedShipping':
                if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
            elif cNode.nodeName == 'PaymentHoldStatus':
                if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
            elif cNode.nodeName == 'IntegratedMerchantCreditCardEnabled':
                if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
        return info

    def getShippingServiceInfo(self, node):
        info = {}
        for cNode in node.childNodes:
            if cNode.nodeName == 'ShippingService':
                if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
            elif cNode.nodeName == 'ShippingServiceCost':
                if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
        return info

    def getShipDetailsInfo(self, node):
        info = {}
        for cNode in node.childNodes:
            if cNode.nodeName == 'SalesTax':
                for gcNode in cNode.childNodes:
                    if gcNode.childNodes:
                        info[gcNode.nodeName] = gcNode.childNodes[0].data
        return info

    def getTransaction(self, nodelist):
        transDetails = []
        for node in nodelist:
            info = {}
            info['Item'] = {}
            for cNode in node.childNodes:
                if cNode.nodeName == 'AmountPaid':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'AdjustmentAmount':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'ConvertedAdjustmentAmount':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'Buyer':
                    if cNode.childNodes:
                        info['Buyer'] = self.getBuyerInfo(cNode)
                elif cNode.nodeName == 'ShippingDetails':
                    if cNode.childNodes:
                        info['ShippingDetails'] = self.getShipDetailsInfo(cNode)
                elif cNode.nodeName == 'ConvertedAmountPaid':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'ConvertedTransactionPrice':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'CreatedDate':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'DepositType':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'Item':
                    info['Item'].update(self.getItemInfo(cNode))
                    #ebayTransactionId = ebayTransactionId + info['Item']['ItemID']
                elif cNode.nodeName == 'SellingManagerProductDetails':
                    if cNode.childNodes:
                        info['Item'].update(self.getSellingManagerProductDetailsInfo(cNode))
                elif cNode.nodeName == 'QuantityPurchased':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'Status':
                    if cNode.childNodes:
                        info['Status'] = self.getStatusInfo(cNode)
                elif cNode.nodeName == 'TransactionID':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'TransactionPrice':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'ShippingServiceSelected':
                    info['ShippingServiceSelected'] = self.getShippingServiceInfo(cNode)
                elif cNode.nodeName == 'TransactionSiteID':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                    #ebayTransactionId = ebayTransactionId + '-' + cNode.childNodes[0].data
                elif cNode.nodeName == 'ActualShippingCost':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'ActualHandlingCost':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'PaidTime':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'ShippedTime':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'OrderLineItemID': # ItemID-TransactionID
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
            transDetails.append(info)
        return transDetails

    def Get(self, timeFrom, timeTo, pageNo,siteid):
        api = Call()
        api.Session = self.Session
        api.SiteID = siteid
        api.RequestData = """<?xml version="1.0" encoding="utf-8"?>
<GetSellerTransactionsRequest xmlns="urn:ebay:apis:eBLBaseComponents">
<DetailLevel>ReturnAll</DetailLevel>
<RequesterCredentials>
<eBayAuthToken>%(token)s</eBayAuthToken>
</RequesterCredentials>
<Version>713</Version>
<ModTimeFrom>%(startTime)s</ModTimeFrom>
<ModTimeTo>%(endTime)s</ModTimeTo>
<Platform>eBay</Platform>
<Pagination>
    <EntriesPerPage>100</EntriesPerPage>
    <PageNumber>%(pageNo)s</PageNumber>
</Pagination>
</GetSellerTransactionsRequest>​"""
        api.RequestData = api.RequestData % { 'token': self.Session.Token.encode("utf-8"),
                                              'startTime' :  timeFrom,
                                              'endTime' :  timeTo,
                                              'pageNo' : pageNo,
                                            }
        responseDOM = api.MakeCall("GetSellerTransactions")
        transInfo={}
        if responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Failure':
            raise osv.except_osv(_('Error!'), _((responseDOM.getElementsByTagName('Errors')[0].childNodes[0].childNodes[0].data)))
        transInfo = self.getTransaction(responseDOM.getElementsByTagName('Transaction'))
        transInfo = transInfo + [{'HasMoreTransactions':responseDOM.getElementsByTagName('HasMoreTransactions')[0].childNodes[0].data}]
        # force garbage collection of the DOM object
        responseDOM.unlink()
        return transInfo

class GetOrders:
    Session = Session()
    def __init__(self, DevID, AppID, CertID, Token, ServerURL):
        self.Session.Initialize(DevID, AppID, CertID, Token, ServerURL)

    def getOrders(self, nodelist):
        transDetails = []
        for node in nodelist:
            info = {}
    def Get(self, timeFrom, timeTo,siteid):
        api = Call()
        api.Session = self.Session
        api.SiteID = siteid
        api.RequestData = """<?xml version="1.0" encoding="utf-8"?>
<GetOrdersRequest xmlns="urn:ebay:apis:eBLBaseComponents">
<RequesterCredentials>
<eBayAuthToken>%(token)s</eBayAuthToken>
</RequesterCredentials>
<CreateTimeFrom>%(startTime)s</CreateTimeFrom>
<CreateTimeTo>%(endTime)s</CreateTimeTo>
<OrderRole>Seller</OrderRole>
<OrderStatus>Completed</OrderStatus>
</GetOrdersRequest>​​"""

        api.RequestData = api.RequestData % { 'token': self.Session.Token.encode("utf-8"),
                                              'startTime' :  timeFrom,
                                              'endTime' :  timeTo,
                                            }
        responseDOM = api.MakeCall("GetOrders")
        ordersInfo = self.getOrders(responseDOM.getElementsByTagName('Order'))
        responseDOM.unlink()
        return ordersInfo

class CompleteSale:
    Session = Session()
    def __init__(self, DevID, AppID, CertID, Token, ServerURL):
        self.Session.Initialize(DevID, AppID, CertID, Token, ServerURL)

    def getOrders(self, nodelist):
        transDetails = []
        for node in nodelist:
            info = {}

    def geterrors(self, nodelist):
      transDetails = []
      info = {}
      for cNode in nodelist.childNodes:
          if cNode.nodeName == 'LongMessage':
              if cNode.childNodes:
                info[cNode.nodeName] = cNode.childNodes[0].data
          if cNode.nodeName == 'SeverityCode':
              if cNode.childNodes:
                info[cNode.nodeName] = cNode.childNodes[0].data
      transDetails.append(info)
      return transDetails

    def Get(self, order_data,siteid):

        api = Call()
        api.Session = self.Session
        api.SiteID = siteid
        if order_data['shipped']:
            shipment = """<Shipment>
      <ShipmentTrackingDetails>
        <ShipmentTrackingNumber>%s</ShipmentTrackingNumber>
        <ShippingCarrierUsed>%s</ShippingCarrierUsed>
      </ShipmentTrackingDetails>
    </Shipment><Shipped>true</Shipped>""" % (order_data['ShipmentTrackingNumber'],order_data['ShippingCarrierUsed'])
            time.sleep(10)
        else:
            shipment = ""
        api.RequestData = """<?xml version="1.0" encoding="utf-8"?>
<CompleteSaleRequest xmlns="urn:ebay:apis:eBLBaseComponents">
<RequesterCredentials>
<eBayAuthToken>%(token)s</eBayAuthToken>
</RequesterCredentials>
<ItemID>%(item_id)s</ItemID>
<TransactionID>%(ebay_order_id)s</TransactionID>""" + shipment.encode("utf-8")+ """
<Paid>%(paid)s</Paid>
<ListingType>%(listing_type)s</ListingType>
<OrderID>%(order_id)s</OrderID>
<OrderLineItemID>%(order_line_item_id)s</OrderLineItemID>
<Version>713</Version>
</CompleteSaleRequest>​​​"""
        api.RequestData = api.RequestData % { 'token': self.Session.Token.encode("utf-8"),
                                              'item_id' :  order_data['ItemID'].encode("utf-8"),
                                              'ebay_order_id' :  order_data['TransactionID'].encode("utf-8"),
                                              'paid' :  order_data['Paid'],
                                              'listing_type' :  order_data['ListingType'].encode("utf-8"),
                                              'order_id' :  order_data['ItemID'].encode("utf-8") + '-' + order_data['TransactionID'].encode("utf-8"),
                                              'order_line_item_id' :  order_data['ItemID'].encode("utf-8") + '-' + order_data['TransactionID'].encode("utf-8"),
                                            }

        responseDOM = api.MakeCall("CompleteSale")
        Dictionary = {}
        print "responseDOM: ", responseDOM.toprettyxml()
        if responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Success':
            ack = responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data
            Dictionary.update({'Ack': ack})
        elif responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Warning':
            ack = responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data
            Dictionary.update({'Ack': ack})
            many_errors = []
            for each_error in  responseDOM.getElementsByTagName('Errors'):
                errors = self.geterrors(each_error)
                many_errors.append(errors)
            logger.notifyChannel('init', netsvc.LOG_WARNING, 'LongMessage %s' % (many_errors))
            Dictionary.update({'LongMessage': many_errors})
        elif responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Failure':
            ack = responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data
            Dictionary.update({'Ack': ack})
            many_errors = []
            for each_error in  responseDOM.getElementsByTagName('Errors'):
                errors = self.geterrors(each_error)
                many_errors.append(errors)
            logger.notifyChannel('init', netsvc.LOG_WARNING, 'LongMessage %s' % (many_errors))
            Dictionary.update({'LongMessage': many_errors})
        responseDOM.unlink()
        return Dictionary

class GetItem:
    Session = Session()

    def __init__(self, DevID, AppID, CertID, Token, ServerURL):
        self.Session.Initialize(DevID, AppID, CertID, Token, ServerURL)

    def getCategoryName(self, node):
        info = {}
        for cNode in node.childNodes:
            if cNode.nodeName == 'CategoryName':
                if cNode.childNodes:
                    return cNode.childNodes[0].data
    def getPictureDetails(self, node):
       for cNode in node.childNodes:
           if cNode.nodeName == 'PictureURL':
               if cNode.childNodes:
                   return cNode.childNodes[0].data
    def getListingDetails(self, node, nodeNames):
        info = {}
        for cNode in node.childNodes:
            if cNode.nodeName in nodeNames:
                if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
        return info

    def getSellingStatus(self, node):
        info = []
        for cNode in node.childNodes:
            if cNode.nodeName == 'ConvertedCurrentPrice':
                if cNode.childNodes:
                    return cNode.childNodes[0].data
        return info

    def getItemShipDetailsInfo(self, node):
        info = {}
        for cNode in node.childNodes:
            if cNode.nodeName == 'CalculatedShippingRate':
                for newNode in cNode.childNodes:
                    if newNode.nodeName == 'WeightMajor':
                        if newNode.childNodes:
                            info[newNode.nodeName] = newNode.childNodes[0].data
                        if newNode.hasAttribute('unit'):
                            info[newNode.nodeName] += ":" + newNode.getAttribute('unit')
                    elif newNode.nodeName == 'WeightMinor':
                        if newNode.childNodes:
                            info[newNode.nodeName] = newNode.childNodes[0].data
                        if newNode.hasAttribute('unit'):
                            info[newNode.nodeName] += ":" + newNode.getAttribute('unit')
        return info

    def getItemInfo(self, nodelist):
        data = []
        for node in nodelist:
            info = {}
            for cNode in node.childNodes:
                if cNode.nodeName == 'ItemID':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'ListingDetails':
                    listingInfo = self.getListingDetails(cNode, ['StartTime','EndTime','ConvertedBuyItNowPrice','ConvertedStartPrice','ConvertedReservePrice'])
                    info = dict(info.items() + listingInfo.items())
                elif cNode.nodeName == 'ListingDuration':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'ListingType':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'PrimaryCategory':
                    if cNode.childNodes:
                        info['CategoryName'] = self.getCategoryName(cNode)
                elif cNode.nodeName == 'Title':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'Quantity':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'Description':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'StartPrice':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'SellingStatus':
                    info['ConvertedCurrentPrice'] = self.getSellingStatus(cNode)
                elif cNode.nodeName == 'SKU':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'ShippingDetails':
                    info[cNode.nodeName] = self.getItemShipDetailsInfo(cNode)
                elif cNode.nodeName == 'ConditionDisplayName':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'ConditionID':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'PictureDetails':
                   if cNode.childNodes:
                       info['PictureDetails'] = self.getPictureDetails(cNode)
            data.append(info)
        return data

    def Get(self, itemId,siteid):
        api = Call()
        api.Session = self.Session
        api.SiteID = siteid
        api.RequestData = """<?xml version="1.0" encoding="utf-8"?>
<GetItemRequest xmlns="urn:ebay:apis:eBLBaseComponents">
<DetailLevel>ReturnAll</DetailLevel>
<RequesterCredentials>
<eBayAuthToken>%(token)s</eBayAuthToken>
</RequesterCredentials>
<ItemID>%(item_id)s</ItemID>
</GetItemRequest>"""
        api.RequestData = api.RequestData % { 'token': self.Session.Token.encode("utf-8"),
                                              'item_id' :  itemId,
                                            }
        responseDOM = api.MakeCall("GetItem")
#        print "responseDOM: ", responseDOM.toprettyxml()
        itemInfo = self.getItemInfo(responseDOM.getElementsByTagName('Item'))
        responseDOM.unlink()
        return itemInfo

class ReviseInventoryStatus:
    Session = Session()

    def __init__(self, DevID, AppID, CertID, Token, ServerURL):
        self.Session.Initialize(DevID, AppID, CertID, Token, ServerURL)

    def geterrors(self, nodelist):
      transDetails = []
      info = {}
      for cNode in nodelist.childNodes:
          if cNode.nodeName == 'LongMessage':
              if cNode.childNodes:
                info[cNode.nodeName] = cNode.childNodes[0].data
          if cNode.nodeName == 'SeverityCode':
              if cNode.childNodes:
                info[cNode.nodeName] = cNode.childNodes[0].data
      transDetails.append(info)
      return transDetails

    def Get(self, itemId, startPrice, quantity,siteid):
        if quantity == 0.0:
            quantity = 0
        api = Call()
        api.Session = self.Session
        api.SiteID = siteid
        api.RequestData = """<?xml version="1.0" encoding="utf-8"?>
<ReviseInventoryStatusRequest xmlns="urn:ebay:apis:eBLBaseComponents">
<RequesterCredentials>
<eBayAuthToken>%(token)s</eBayAuthToken>
</RequesterCredentials>
<InventoryStatus ComplexType="InventoryStatusType">
<ItemID>%(item_id)s</ItemID>
<StartPrice>%(item_price)s</StartPrice>
<Quantity>%(item_qty)s</Quantity>
</InventoryStatus>
</ReviseInventoryStatusRequest>"""
        api.RequestData = api.RequestData % { 'token': self.Session.Token.encode("utf-8"),
                                              'item_id' :  str(itemId).encode("utf-8"),
                                              'item_price' : str(startPrice).encode("utf-8"),
                                              'item_qty' : str(quantity).encode("utf-8"),
                                            }

        responseDOM = api.MakeCall("ReviseInventoryStatus")
        Dictionary = {}
        if responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Success':
            ack = responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data
            Dictionary.update({'Ack': ack})
        elif responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Warning':
            ack = responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data
            Dictionary.update({'Ack': ack})
            many_errors = []
            for each_error in  responseDOM.getElementsByTagName('Errors'):
                errors = self.geterrors(each_error)
                many_errors.append(errors)
            logger.notifyChannel('init', netsvc.LOG_WARNING, 'LongMessage %s' % (many_errors))
            Dictionary.update({'LongMessage': many_errors})
        elif responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Failure':
            ack = responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data
            Dictionary.update({'Ack': ack})
            many_errors = []
            for each_error in  responseDOM.getElementsByTagName('Errors'):
                errors = self.geterrors(each_error)
                many_errors.append(errors)
            logger.notifyChannel('init', netsvc.LOG_WARNING, 'LongMessage %s' % (many_errors))
            Dictionary.update({'LongMessage': many_errors})
        responseDOM.unlink()
        return Dictionary
###########################################################################################
class RelistItem:
    Session = Session()
    def __init__(self, DevID, AppID, CertID, Token, ServerURL):
       self.Session.Initialize(DevID, AppID, CertID, Token, ServerURL)

    def geterrors(self, nodelist):
       transDetails = []
       info = {}
       for cNode in nodelist.childNodes:
           if cNode.nodeName == 'LongMessage':
               if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
           if cNode.nodeName == 'SeverityCode':
               if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
       transDetails.append(info)
       return transDetails

    def Get(self,ids,product_id,ItemId,title,desc,listing_type,scheduled_time,duration,sku,subtitle,postal,siteid,cr=None,uid=None):
        api = Call()
        api.Session = self.Session
        api.DetailLevel = "0"
        api.SiteID = siteid
        attribute_ids = []
        attribute_names = []
        value_ids = []
        attribute_ids_prod = []
        attribute_names_prod = []
        value_ids_prod = []
        attribute_ids_dict = {}
        attribute_ids2 = []
        attribute_names2 = []
        value_ids2 = []
        attribute_ids_prod2 = []
        attribute_names_prod2 = []
        value_ids_prod2 = []
        attribute_ids_dict2 = {}
        cat2_id = ''
        bold_tag = ''
        category = ''
        condition_enabled =''
        condtn_desc = ''
        condtn_desc_prod = ''
        Itemspecifics =''
        condition_enabled_cat2 = ''
##################for the  category1 ####################################
        title_cd = "<![CDATA[" + title + "]]>"
        subtitle_cd = "<![CDATA[" + subtitle + "]]>"
        des_cd = "<![CDATA[" + desc + "]]>"
        product_cat = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).cat1.id
        template_cat = pooler.get_pool(cr.dbname).get('ebayerp.relist').browse(cr,uid,ids[0]).template_id.category_id1.id
        if product_cat:
            cat1_id = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,product_cat).ebay_category_id
            condition_enabled = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,product_cat).condition_enabled
            attribute_set_id_cat1 = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,product_cat).attribute_set_id
            product_match_atts = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).match_att_cat1
            for match_att in product_match_atts:
                attribute_obj = match_att.attribute_name
                attribute_id_prod = attribute_obj.attribute_id
                attribute_name_prod = attribute_obj.name
                value_id_prod = match_att.attribute_values_id.att_val_id
                if value_id_prod == None:
                    new_dict = {}
                    new_key = match_att.text_field
                    new_val = '-3'
                    new_dict[new_key] = new_val
                    value_id_prod = new_dict
                attribute_ids_dict[attribute_name_prod] = attribute_id_prod
                attribute_ids_prod.append(attribute_id_prod)
                attribute_names_prod.append(attribute_name_prod)
                value_ids_prod.append(value_id_prod)
        elif template_cat:
            cat1_id = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,template_cat).ebay_category_id
            condition_enabled = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,template_cat).condition_enabled
            attribute_set_id_cat1 = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,template_cat).attribute_set_id
            template_id = pooler.get_pool(cr.dbname).get('ebayerp.relist').browse(cr,uid,ids[0]).template_id.id
            matching_attributes = pooler.get_pool(cr.dbname).get('ebayerp.template').browse(cr,uid,template_id).match_attribute_ids
            for matching_att in matching_attributes:
                attribute_obj = matching_att.attribute_name
                attribute_id = attribute_obj.attribute_id
                attribute_name = attribute_obj.name
                value_id = matching_att.attribute_values_id.att_val_id
                if value_id == None:
                        new_dict = {}
                        new_key = matching_att.text_field
                        new_val = '-3'
                        new_dict[new_key] = new_val
                        value_id = new_dict
                attribute_ids.append(attribute_id)
                attribute_names.append(attribute_name)
                value_ids.append(value_id)
                if attribute_name not in attribute_ids_dict.iterkeys():
                    attribute_ids_dict[attribute_name] = attribute_id
        else:
            raise osv.except_osv(_('Warning!'), _("Please select the category in Product or Template"))
############################for getting template matching attribute from ebayerp.template master#############
        template_id = pooler.get_pool(cr.dbname).get('ebayerp.relist').browse(cr,uid,ids[0]).template_id.id
        template_object = pooler.get_pool(cr.dbname).get('ebayerp.relist').browse(cr,uid,ids[0]).template_id
#####################condition######################
        condtn_record = pooler.get_pool(cr.dbname).get('ebayerp.template').browse(cr,uid,template_id).condtn
        if condtn_record:
            condtn_desc =  condtn_record.condition_id
        condtn_prod_record = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).ebay_condtn
        if condtn_prod_record:
            condtn_desc_prod = condtn_prod_record.condition_id
#        if condtn_desc == False and condtn_desc_prod == False:
#            raise osv.except_osv(_('Warning'), _("Please select condition either at the  template or product level"))
        if template_cat and product_cat:
            if product_cat == template_cat:
                matching_attributes = pooler.get_pool(cr.dbname).get('ebayerp.template').browse(cr,uid,template_id).match_attribute_ids
                for matching_att in matching_attributes:
                    attribute_obj = matching_att.attribute_name
                    attribute_id = attribute_obj.attribute_id
                    attribute_name = attribute_obj.name
                    value_id = matching_att.attribute_values_id.att_val_id
                    if value_id == None:
                            new_dict = {}
                            new_key = matching_att.text_field
                            new_val = '-3'
                            new_dict[new_key] = new_val
                            value_id = new_dict
                    attribute_ids.append(attribute_id)
                    attribute_names.append(attribute_name)
                    value_ids.append(value_id)
                    if attribute_name not in attribute_ids_dict.iterkeys():
                        attribute_ids_dict[attribute_name] = attribute_id
        product_dict = {}
        template_dict = {}
        position_prod = 0
        position_template = 0
############################## to create product matching attribute dictionary####
        for val in attribute_names_prod:
                product_dict[val] = value_ids_prod[position_prod]
                position_prod = position_prod + 1
#########################template matching attribute dictionary###########
        for value in attribute_names:
                template_dict[value] = value_ids[position_template]
                position_template = position_template + 1
###################################for appending attributes in template to product onetomany fields#######
        if (template_cat and product_cat == template_cat) or template_cat:
                for keys in template_dict.iterkeys():
                    if keys not in product_dict.iterkeys():
                        dict_val = template_dict[keys]
                        if type(dict_val)==type(dict()):
                            for dic_key in dict_val.iterkeys():
                                keyval = dic_key
                                val = dict_val[dic_key]
                                product_dict[keyval] =  val
                                attribute_ids_dict[keyval] = attribute_ids_dict.pop(keys)
                        else:
                            value = template_dict[keys]
                            product_dict[keys] = value
###################for second category############################
        product_cat2 = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).cat2.id
        template_cat2 = pooler.get_pool(cr.dbname).get('ebayerp.relist').browse(cr,uid,ids[0]).template_id.category_id2.id
        if product_cat2:
            attribute_set_id_cat2 = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,product_cat2).attribute_set_id
            cat2_id = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,product_cat2).ebay_category_id
            condition_enabled_cat2 = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,product_cat2).condition_enabled
            product_obj = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id)
            matching_att_cat2 = product_obj.match_att_cat2
            for matching_att in matching_att_cat2:
                attribute_obj = matching_att.attribute_name
                attribute_id_prod = attribute_obj.attribute_id
                attribute_name_prod = attribute_obj.name
                value_id_prod = matching_att.attribute_values_id.att_val_id
                if value_id_prod == None:
                    new_dict = {}
                    new_key = matching_att.text_field
                    new_val = '-3'
                    new_dict[new_key] = new_val
                    value_id_prod = new_dict
                attribute_ids_dict2[attribute_name_prod] = attribute_id_prod
                attribute_ids_prod2.append(attribute_id_prod)
                attribute_names_prod2.append(attribute_name_prod)
                value_ids_prod2.append(value_id_prod)
        elif template_cat2:
            attribute_set_id_cat2 = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,template_cat2).attribute_set_id
            cat2_id = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,template_cat2).ebay_category_id
            condition_enabled_cat2 = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,template_cat2).condition_enabled
            template_obj = pooler.get_pool(cr.dbname).get('ebayerp.relist').browse(cr,uid,ids[0]).template_id
            template_match_att = template_obj.match_attribute_cat2
            for matching_att in template_match_att:
                attribute_obj = matching_att.attribute_name
                attribute_id = attribute_obj.attribute_id
                attribute_name = attribute_obj.name
                value_id = matching_att.attribute_values_id.att_val_id
                if value_id == None:
                        new_dict = {}
                        new_key = matching_att.text_field
                        new_val = '-3'
                        new_dict[new_key] = new_val
                        value_id = new_dict
                attribute_ids2.append(attribute_id)
                attribute_names2.append(attribute_name)
                value_ids2.append(value_id)
                if attribute_name not in attribute_ids_dict2.iterkeys():
                    attribute_ids_dict2[attribute_name] = attribute_id
######################################for gettting template attribute values####################
        template_obj = pooler.get_pool(cr.dbname).get('ebayerp.relist').browse(cr,uid,ids[0]).template_id
        template_match_att = template_obj.match_attribute_cat2
        if template_cat2 and product_cat2:
            if product_cat2 == template_cat2:
                for matching_att in template_match_att:
                    attribute_obj = matching_att.attribute_name
                    attribute_id = attribute_obj.attribute_id
                    attribute_name = attribute_obj.name
                    value_id = matching_att.attribute_values_id.att_val_id
                    if value_id == None:
                            new_dict = {}
                            new_key = matching_att.text_field
                            new_val = '-3'
                            new_dict[new_key] = new_val
                            value_id = new_dict
                    attribute_ids2.append(attribute_id)
                    attribute_names2.append(attribute_name)
                    value_ids2.append(value_id)
                    if attribute_name not in attribute_ids_dict2.iterkeys():
                        attribute_ids_dict2[attribute_name] = attribute_id
#########################################################################
        product_dict2 = {}
        template_dict2 = {}
        position_prod2 = 0
        position_template2 = 0
############################## to create product matching attribute dictionary####
        for val in attribute_names_prod2:
                product_dict2[val] = value_ids_prod2[position_prod2]
                position_prod2 = position_prod2 + 1
#########################template matching attribute dictionary###########
        for value in attribute_names2:
                template_dict2[value] = value_ids2[position_template2]
                position_template2 = position_template2 + 1
###################################for appending attributes in template to product onetomany fields#######
        if (template_cat2 and product_cat2 == template_cat2) or template_cat2:
                for keys in template_dict2.iterkeys():
                    if keys not in product_dict2.iterkeys():
                        dict_val = template_dict2[keys]
                        if type(dict_val)==type(dict()):
                            for dic_key in dict_val.iterkeys():
                                keyval = dic_key
                                val = dict_val[dic_key]
                                #popval = product_dict.pop(keys)
                                product_dict2[keyval] =  val
                                attribute_ids_dict2[keyval] = attribute_ids_dict2.pop(keys)
                        else:
                            value = template_dict2[keys]
                            product_dict2[keys] = value
#####################################Passing the <AttributeSetArray> to the api########################
        att_ids = []
        attribute_set_array = ''
        new_att_set_array = ''
        att_set_array2 = ''
        attribute_set_array2 = ''
        double_value = []
        AttributeSetArray = ''
        double_value2 = []
        full_urls = []
        for keys in product_dict.iterkeys():
            dict_val = product_dict[keys]
            if type(dict_val)==type(dict()):
                for dic_key in dict_val.iterkeys():
                    keyval = dic_key
                    value = dict_val[dic_key]
                    product_dict[keyval] = product_dict.pop(keys)
                    product_dict[keyval] =  value
                    double_value.append(keyval)
                    attribute_ids_dict[keyval] = attribute_ids_dict.pop(keys)
                    keys = keyval
                    if keys in attribute_ids_dict.iterkeys():
                            att_id = attribute_ids_dict[keys]
                            att_ids.append(att_id)
                            attribute_set_array += """
                           <Attribute attributeID="%s">
                              <Value>
                                <ValueLiteral>%s</ValueLiteral>
                                <ValueID>%s</ValueID>
                              </Value>
                            </Attribute>""" % (att_id,keys,value)
            else:
                if len(double_value):
                    if keys in double_value:
                        print"Double value",keys
                    else:
                        value = product_dict[keys]
                        double_value.append(keys)
                        if keys in attribute_ids_dict.iterkeys():
                                att_id = attribute_ids_dict[keys]
                        att_ids.append(att_id)
                        attribute_set_array += """
                       <Attribute attributeID="%s">
                          <Value>
                            <ValueLiteral>%s</ValueLiteral>
                            <ValueID>%s</ValueID>
                          </Value>
                        </Attribute>""" % (att_id,keys,value)
                else:
                    value = product_dict[keys]
                    double_value.append(keys)
                    if keys in attribute_ids_dict.iterkeys():
                            att_id = attribute_ids_dict[keys]
                    att_ids.append(att_id)
                    attribute_set_array += """
                   <Attribute attributeID="%s">
                      <Value>
                        <ValueLiteral>%s</ValueLiteral>
                        <ValueID>%s</ValueID>
                      </Value>
                    </Attribute>""" % (att_id,keys,value)
        AttributeSet = """<AttributeSet attributeSetID="%s">""" %(attribute_set_id_cat1)
        if attribute_set_array:
            new_att_set_array = AttributeSet.encode("utf-8") + attribute_set_array.encode("utf-8") + """</AttributeSet>"""
        if cat1_id:
            category = """<PrimaryCategory><CategoryID>%s</CategoryID></PrimaryCategory>"""%(cat1_id)
        if cat2_id:
            category += """<SecondaryCategory><CategoryID>%s</CategoryID></SecondaryCategory>"""%(cat2_id)
        if product_dict2:
            for keys in product_dict2.iterkeys():
                dict_val = product_dict2[keys]
                if type(dict_val)==type(dict()):
                    for dic_key in dict_val.iterkeys():
                        keyval = dic_key
                        value = dict_val[dic_key]
                        product_dict2[keyval] = product_dict2.pop(keys)
                        product_dict2[keyval] =  value
                        double_value2.append(keyval)
                        attribute_ids_dict2[keyval] = attribute_ids_dict2.pop(keys)
                        keys = keyval
                        if keys in attribute_ids_dict2.iterkeys():
                            att_id = attribute_ids_dict2[keys]
                            att_ids.append(att_id)
                            attribute_set_array2 += """
                           <Attribute attributeID="%s">
                              <Value>
                                <ValueLiteral>%s</ValueLiteral>
                                <ValueID>%s</ValueID>
                              </Value>
                            </Attribute>""" % (att_id,keys,value)
                else:
                    if len(double_value2):
                        if keys in double_value2:
                            print"Double value",keys
                        else:
                            value = product_dict2[keys]
                            double_value2.append(keys)
                            if keys in attribute_ids_dict2.iterkeys():
                                    att_id = attribute_ids_dict2[keys]
                            att_ids.append(att_id)
                            attribute_set_array2 += """
                           <Attribute attributeID="%s">
                              <Value>
                                <ValueLiteral>%s</ValueLiteral>
                                <ValueID>%s</ValueID>
                              </Value>
                            </Attribute>""" % (att_id,keys,value)
                    else:
                        value = product_dict2[keys]
                        double_value2.append(keys)
                        if keys in attribute_ids_dict2.iterkeys():
                                att_id = attribute_ids_dict2[keys]
                        att_ids.append(att_id)
                        attribute_set_array2 += """
                       <Attribute attributeID="%s">
                          <Value>
                            <ValueLiteral>%s</ValueLiteral>
                            <ValueID>%s</ValueID>
                          </Value>
                        </Attribute>""" % (att_id,keys,value)
            AttributeSet = """<AttributeSet attributeSetID="%s">""" %(attribute_set_id_cat2)
            if attribute_set_array2:
                att_set_array2 = AttributeSet.encode("utf-8") + attribute_set_array2.encode("utf-8") + """</AttributeSet>"""
                new_att_set_array += att_set_array2.encode("utf-8")
        if new_att_set_array:
            AttributeSetArray = "<AttributeSetArray>" + new_att_set_array.encode("utf-8") + "</AttributeSetArray>"  
###########################for the default attributes#######################
        
        item_specifics_dict_prod = {}
        item_specifics_dict_template = {}
        if product_cat:
            item_specifics = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,product_cat).item_specifics
            if item_specifics == True:
                product_item_specifics = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).custom_item_specifics_prod_cat_gene
                for each_item_specifics in product_item_specifics:
                    item_specifics_name = each_item_specifics.custom_name
                    item_specifics_value = each_item_specifics.custom_value
                    item_specifics_dict_prod[item_specifics_name] = item_specifics_value
        if product_cat2:
            item_specifics = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,product_cat2).item_specifics
            if item_specifics == True:
                product_item_specifics = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).custom_item_specifics_prod_cat_gene
                for each_item_specifics in product_item_specifics:
                    item_specifics_name = each_item_specifics.custom_name
                    if not item_specifics_dict_prod.has_key(item_specifics_name):
                        item_specifics_value = each_item_specifics.custom_value
                        item_specifics_dict_prod[item_specifics_name] = item_specifics_value
        if template_cat or template_cat2:
            if ((product_cat == template_cat) and product_cat != False and template_cat != False) or ((product_cat2 == template_cat2) and product_cat2 != False and template_cat2 != False):
                template_item_specifics = pooler.get_pool(cr.dbname).get('ebayerp.template').browse(cr,uid,template_id).custom_item_specifics_generic
                for each_item_specifics in template_item_specifics:
                    item_specifics_name = each_item_specifics.custom_name
                    item_specifics_value = each_item_specifics.custom_value
                    item_specifics_dict_template[item_specifics_name] = item_specifics_value
            else:
                template_item_specifics = pooler.get_pool(cr.dbname).get('ebayerp.template').browse(cr,uid,template_id).custom_item_specifics_generic
                for each_item_specifics in template_item_specifics:
                    item_specifics_name = each_item_specifics.custom_name
                    item_specifics_value = each_item_specifics.custom_value
                    item_specifics_dict_template[item_specifics_name] = item_specifics_value
        for each_key in item_specifics_dict_template.iterkeys():
            if each_key not in item_specifics_dict_prod.iterkeys():
                    value = item_specifics_dict_template[each_key]
                    item_specifics_dict_prod[each_key] = value
        code_list = ''
        product_reference_id = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).product_reference_id
        if product_reference_id:
            code_list+= """ <ProductListingDetails>
                            <IncludePrefilledItemInformation>true</IncludePrefilledItemInformation>
                      <IncludeStockPhotoURL>true</IncludeStockPhotoURL>
                                <ListIfNoProduct>true</ListIfNoProduct>
                                 <ProductReferenceID>%s</ProductReferenceID>
                              </ProductListingDetails>""" %(product_reference_id)
            stock_photo_url = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).stock_photo_url
            if stock_photo_url != 'NULL':
                full_urls.append(stock_photo_url)
        if item_specifics_dict_prod:
            name_val_str = ''
            for each_key in item_specifics_dict_prod:
                value = item_specifics_dict_prod[each_key]
                name_val_str+= """<NameValueList>
                                <Name>%s</Name>
                                <Value>%s</Value>
                              </NameValueList>""" %(each_key,value)
#            Itemspecifics =''
            Itemspecifics = "<ItemSpecifics>"+ name_val_str.encode('utf-8')+ "</ItemSpecifics>"
#        else:
#            Itemspecifics = ''
        shop_id = pooler.get_pool(cr.dbname).get('ebayerp.relist').browse(cr,uid,ids[0]).shop_id
        inst_obj = shop_id.instance_id
        site_name = ''
        site = ''
        site_id = shop_id.site_id
        if site_id:
            site_name = site_id.name
        site = """<Site>%s</Site>"""%(site_name)
        product_images = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).image_ids
        images = ''
        for each_image in product_images:
            uploading_image = ''
            each_image_id = each_image.id
            filename_ebay = each_image.filename_ebay
            if filename_ebay:
                uploading_image = pooler.get_pool(cr.dbname).get('sale.shop').store_image(cr,uid,filename_ebay,'/opt/openerp_603/openerp-server-6.0.3/bin/addons/ebayconnect_new_generic/images/ebay_product.png',True)
            if uploading_image:
                results = pooler.get_pool(cr.dbname).get('sale.shop').call(cr, uid, inst_obj, 'UploadSiteHostedPictures',uploading_image,siteid)
                increment = 0
                ack = results.get('Ack',False)
                if ack =='Failure':
                    if results.get('LongMessage',False):
                           long_message = results['LongMessage']
                           for each_messsge in long_message:
                               severity_code = each_messsge[0]['SeverityCode']
                               if severity_code == 'Error':
                                   Longmessage = each_messsge[0]['LongMessage']
                                   product_long_message = ('Error : %s') % (Longmessage)
                                   increment += 1
                                   pooler.get_pool(cr.dbname).get('sale.shop').log(cr, uid,increment, product_long_message)
                elif ack =='Warning':
                    full_url_array = results.get('FullURL',False)
                    if full_url_array:
                        full_url = (full_url_array[0]['FullURL'])
                        cr.execute("UPDATE product_images SET change_or_no_change ='no_change',full_url='%s'where id = %s"%(str(full_url),each_image_id,))
                        full_urls.append(full_url)
                    if results.get('LongMessage',False):
                        long_message = results['LongMessage']
                        for each_messsge in long_message:
                           severity_code = each_messsge[0]['SeverityCode']
                           if severity_code == 'Warning':
                               Longmessage = each_messsge[0]['LongMessage']
                               product_long_message = ('Warning : %s:') % (Longmessage)
                               increment += 1
                               pooler.get_pool(cr.dbname).get('sale.shop').log(cr, uid,increment, product_long_message)
                else:
                    full_url_array = results.get('FullURL',False)
                    if full_url_array:
                        full_url = (full_url_array[0]['FullURL'])
                        cr.execute("UPDATE product_images SET change_or_no_change ='no_change',full_url='%s'where id = %s"%(str(full_url),each_image_id,))
                        full_urls.append(full_url)
        for each_url in full_urls:
            images += """<PictureURL>%s</PictureURL>"""%(each_url)
        images_url = ''
        images_url = """<PictureDetails>""" + images + """</PictureDetails>"""
        new_condition = ''
        if not condtn_desc_prod :
            new_condition = condtn_desc
        else:
            new_condition = condtn_desc_prod
        condition = ''
        if listing_type == 'LeadGeneration' :
            condition = ''
        elif condition_enabled:
            if condition_enabled == False:
                if condition_enabled_cat2:
                    if condition_enabled_cat2 == False:
                        condition = ''
                    else:
                        condition =  """<ConditionID>%s</ConditionID>"""%(new_condition)
            else:
                condition =  """<ConditionID>%s</ConditionID>"""%(new_condition)
        else:
            condition =  """<ConditionID>%s</ConditionID>"""%(new_condition)
        start_pricelist = pooler.get_pool(cr.dbname).get('ebayerp.relist').browse(cr,uid,ids[0]).start_price.id
        reserve_pricelist = pooler.get_pool(cr.dbname).get('ebayerp.relist').browse(cr,uid,ids[0]).reserve_price.id
        buy_it_now = pooler.get_pool(cr.dbname).get('ebayerp.relist').browse(cr,uid,ids[0]).buy_it_nw.id
        get_reserve_price = pooler.get_pool(cr.dbname).get('product.pricelist').price_get(cr,uid,[reserve_pricelist],product_id,1,None,None)
        reserve_price = get_reserve_price[reserve_pricelist]
        get_start_price = pooler.get_pool(cr.dbname).get('product.pricelist').price_get(cr,uid,[start_pricelist],product_id,1,None,None)
        start_price = get_start_price[start_pricelist]
        get_buy_it_now = pooler.get_pool(cr.dbname).get('product.pricelist').price_get(cr,uid,[buy_it_now],product_id,1,None,None)
        buy_it_now_price = get_buy_it_now[buy_it_now]
        warehouse_id = shop_id.warehouse_id.id
        location_id = pooler.get_pool(cr.dbname).get('stock.warehouse').browse(cr,uid,warehouse_id).lot_stock_id.id
        function_call = pooler.get_pool(cr.dbname).get('product.listing.templates')._my_value(cr, uid,location_id,product_id,context={})
        quantity = str(function_call).split('.')
        shipping_details = ''
        shipping_details = pooler.get_pool(cr.dbname).get('sale.shop').shipping_details(cr,uid,template_object,product_id,listing_type,shop_id,start_price,reserve_price,buy_it_now_price,quantity[0])
        bold_tl = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).bold_tl_prod
        bold_tl_tm = pooler.get_pool(cr.dbname).get('ebayerp.template').browse(cr,uid,template_id).bold_tl
        if bold_tl == True:
            bold_tag = """<ListingEnhancement>BoldTitle</ListingEnhancement>"""
        elif bold_tl_tm == True:
            bold_tag = """<ListingEnhancement>BoldTitle</ListingEnhancement>"""
        sku_string = ''
        if sku:
            sku_string = "<SKU>%s</SKU>"%(sku)
####################################################################
        api.RequestData = """<?xml version="1.0" encoding="utf-8"?>
<RelistItemRequest xmlns="urn:ebay:apis:eBLBaseComponents">
<RequesterCredentials>
<eBayAuthToken>%(token)s</eBayAuthToken>
</RequesterCredentials>
<Item>
    <Title>%(title_name)s</Title>
    """ + sku_string.encode('utf-8') + """
    <ItemID>%(item_id)s</ItemID>
    """+ condition.encode("utf-8") + """
    """ + category.encode("utf-8") + """
    """ + Itemspecifics.encode("utf-8") + """
     """ + AttributeSetArray.encode('utf-8') + """
    """ + code_list.encode("utf-8") + """
    <Description>%(description)s</Description>
    """ + bold_tag.encode("utf-8") + """
     """ +images_url.encode("utf-8") + """
     """ + shipping_details.encode("utf-8") + """
    <CategoryMappingAllowed>true</CategoryMappingAllowed>
    <Country>US</Country>
    <Currency>USD</Currency>
    <ScheduleTime>%(scheduled_time)s</ScheduleTime>
    <ListingDuration>%(duration)s</ListingDuration>
    <ListingType>%(type)s</ListingType>
    <SubTitle>%(subtitle)s</SubTitle>
    <PostalCode>%(postal)s</PostalCode>
     """ + site.encode("utf-8") + """
  </Item>
</RelistItemRequest>"""
        api.RequestData = api.RequestData % { 'token': self.Session.Token.encode("utf-8"),
                                            'title_name': title_cd.encode("utf-8"),
                                            'description': des_cd.encode("utf-8"),
                                            'scheduled_time': scheduled_time,
                                            'duration': duration.encode("utf-8"),
                                            'type': listing_type.encode("utf-8"),
#                                            'sku': sku.encode("utf-8"),
                                            'subtitle': subtitle_cd.encode("utf-8"),
                                            'postal': postal.encode("utf-8"),
                                             'item_id': ItemId.encode("utf-8"),
                                             }
        print"api.RequestData",api.RequestData
        responseDOM = api.MakeCall("RelistItem")
        print "relist item api Output: ",responseDOM.toprettyxml()
        Dictionary = {}
        if responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Success':
            ack = responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data
            Dictionary.update({'Ack': ack})
            item_id = responseDOM.getElementsByTagName('ItemID')[0].childNodes[0].data
            Dictionary.update({'ItemID': item_id})
            start_time = responseDOM.getElementsByTagName('StartTime')[0].childNodes[0].data
            Dictionary.update({'StartTime': start_time})
            end_time = responseDOM.getElementsByTagName('EndTime')[0].childNodes[0].data
            Dictionary.update({'EndTime': end_time})
        elif responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Warning':
            ack = responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data
            Dictionary.update({'Ack': ack})
            item_id = responseDOM.getElementsByTagName('ItemID')[0].childNodes[0].data
            Dictionary.update({'ItemID': item_id})
            start_time = responseDOM.getElementsByTagName('StartTime')[0].childNodes[0].data
            Dictionary.update({'StartTime': start_time})
            end_time = responseDOM.getElementsByTagName('EndTime')[0].childNodes[0].data
            Dictionary.update({'EndTime': end_time})
            many_errors = []
            for each_error in  responseDOM.getElementsByTagName('Errors'):
               errors = self.geterrors(each_error)
               many_errors.append(errors)
            Dictionary.update({'LongMessage': many_errors})
        elif responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Failure':
           ack = responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data
           Dictionary.update({'Ack': ack})
           many_errors = []
           for each_error in  responseDOM.getElementsByTagName('Errors'):
               errors = self.geterrors(each_error)
               many_errors.append(errors)
           Dictionary.update({'LongMessage': many_errors})
        responseDOM.unlink()
        return Dictionary
#######################################################################################################
class GetCategories:
    Session = Session()
    def __init__(self, DevID, AppID, CertID, Token, ServerURL):
        self.Session.Initialize(DevID, AppID, CertID, Token, ServerURL)
    def getCategoryArray(self, nodelist):
        categoryarray = []
        info = {}
        for node in nodelist:
            for cNode in node.childNodes:
                if cNode.nodeName == 'Category':
                    for ssNode in cNode.childNodes:
                        if ssNode.nodeName == 'LeafCategory':
                            if ssNode.childNodes:
                                info[ssNode.nodeName] = ssNode.childNodes[0].data
                break
            categoryarray.append(info)
        return categoryarray

    def Get(self,category_id,siteid):
        api = Call()
        api.Session = self.Session
        api.SiteID = siteid
        api.DetailLevel = "ReturnAll"
        api.RequestData = """<?xml version="1.0" encoding="utf-8"?>
<GetCategoriesRequest xmlns="urn:ebay:apis:eBLBaseComponents">
<CategorySiteID>0</CategorySiteID>
<DetailLevel>%(detail)s</DetailLevel>
 <LevelLimit>2</LevelLimit>
<CategoryParent>%(category_id)s</CategoryParent>
<RequesterCredentials>
<eBayAuthToken>%(token)s</eBayAuthToken>
</RequesterCredentials>
</GetCategoriesRequest>​​"""

        api.RequestData = api.RequestData % { 'token': self.Session.Token.encode("utf-8"),
                                                                'detail': api.DetailLevel,
                                                        'category_id':category_id}

        responseDOM = api.MakeCall("GetCategories")
        print "GetCategories Output: ",responseDOM.toprettyxml()
        getcategory_array = self.getCategoryArray(responseDOM.getElementsByTagName('CategoryArray'))
        # force garbage collection of the DOM object
        responseDOM.unlink()
        return getcategory_array
class GetCategory2CS:
    Session = Session()

    def __init__(self, DevID, AppID, CertID, Token, ServerURL):
        self.Session.Initialize(DevID, AppID, CertID, Token, ServerURL)

    def Get(self,categoryid,siteid):
        api = Call()
        api.Session = self.Session
        api.SiteID = siteid
        api.DetailLevel = "ReturnAll"
        api.RequestData = """<?xml version="1.0" encoding="utf-8"?>
  <GetCategory2CSRequest xmlns="urn:ebay:apis:eBLBaseComponents">
  <CategoryID>%(category_id)s</CategoryID>
  <DetailLevel>%(detail)s</DetailLevel>
  <RequesterCredentials>
  <eBayAuthToken>%(token)s</eBayAuthToken>
  </RequesterCredentials>
  <WarningLevel>High</WarningLevel>
</GetCategory2CSRequest>​​"""
        api.RequestData = api.RequestData % { 'token': self.Session.Token.encode("utf-8"),
                                              'detail': api.DetailLevel,
                                              'category_id' : categoryid}
        Dictionary = {}
        responseDOM = api.MakeCall("GetCategory2CS")
        timeElement = responseDOM.getElementsByTagName('AttributeSetID')
        if (timeElement != []):
            Dictionary.update({'AttributeSetID': timeElement[0].childNodes[0].data})
        catalog_enabld = responseDOM.getElementsByTagName('CatalogEnabled')
        if (catalog_enabld != []):
            Dictionary.update({'CatalogEnabled': catalog_enabld[0].childNodes[0].data})
        responseDOM.unlink()
        return Dictionary
class GetAttributesCS:
    Session = Session()
    def __init__(self, DevID, AppID, CertID, Token, ServerURL):
        self.Session.Initialize(DevID, AppID, CertID, Token, ServerURL)

    def Get(self,attributeid,siteid):
        api = Call()
        api.Session = self.Session
        api.DetailLevel = "ReturnAll"
        api.SiteID = siteid
        api.RequestData = """<?xml version="1.0" encoding="utf-8"?>
  <GetAttributesCSRequest xmlns="urn:ebay:apis:eBLBaseComponents">
  <RequesterCredentials>
  <eBayAuthToken>%(token)s</eBayAuthToken>
  </RequesterCredentials>
  <ErrorLanguage>0</ErrorLanguage>
  <DetailLevel>%(detail)s</DetailLevel>
  <AttributeSetID>%(attribute_set_id)s</AttributeSetID>
</GetAttributesCSRequest> ​​"""
        api.RequestData = api.RequestData % { 'token': self.Session.Token.encode("utf-8"),
                                              'detail': api.DetailLevel,
                                              'attribute_set_id' : attributeid
                                                                    }

        responseDOM = api.MakeCall("GetAttributesCS")
        timeElement = responseDOM.getElementsByTagName('AttributeData')
        if (timeElement != []):
            return timeElement[0].childNodes[0].data
        attbiute = timeElement.getElementsByTagName('eBay')
        if (attbiute != []):
            return attbiute[0].childNodes[0].data
        responseDOM.unlink()
##############for custom attributes####################
class GetCategoryFeatures:
    Session = Session()
    def __init__(self, DevID, AppID, CertID, Token, ServerURL):
        self.Session.Initialize(DevID, AppID, CertID, Token, ServerURL)
    def condition_vals(self,node):
        cNodes = node.childNodes
        condition_details = []
        info = {}
        for cNode in cNodes:
            if cNode.nodeName == 'ID':
                if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
            elif cNode.nodeName == 'DisplayName':
                if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
        condition_details.append(info)
        return condition_details
    def getConditionValues(self,nodelist):
        condition_details = []
#        print"nodelist",nodelist
#        nodelist = nodelist[0]
#        print"nodelist",nodelist
#        del nodelist[-1]
        for cNode in nodelist:
            print"CNode",cNode
            info = {}
            for cNode in cNode.childNodes:
#               if cNode.nodeName == 'Condition':
#                   if cNode.childNodes:
#                        info['ConditionValues'] = self.condition_vals(cNode)
#               for ssNode in cNode.childNodes:
               if cNode.nodeName == 'ID':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data

               elif cNode.nodeName == 'DisplayName':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
            condition_details.append(info)
#        print"condition_details",condition_details
        return condition_details
        
    def Get(self,category_id,siteid):
        api = Call()
        api.Session = self.Session
        api.SiteID = siteid
        api.DetailLevel = "ReturnAll"
        api.RequestData = """<?xml version="1.0" encoding="utf-8"?>
  <GetCategoryFeaturesRequest xmlns="urn:ebay:apis:eBLBaseComponents">
  <CategoryID>%(categoryid)s</CategoryID>
  <DetailLevel>%(detail)s</DetailLevel>
  <ViewAllNodes>true</ViewAllNodes>
  <RequesterCredentials>
  <eBayAuthToken>%(token)s</eBayAuthToken>
  </RequesterCredentials>
</GetCategoryFeaturesRequest>​​"""

        api.RequestData = api.RequestData % { 'token': self.Session.Token.encode("utf-8"),
                                              'detail': api.DetailLevel,
                                              'categoryid' : category_id
                                                                    }
        responseDOM = api.MakeCall("GetCategoryFeatures")
        print "GetCategoryFeatures Output: ",responseDOM.toprettyxml()
        Dictionary = {}
        item_spc = responseDOM.getElementsByTagName('ItemSpecificsEnabled')[0].childNodes[0].data
        Dictionary.update({'ItemSpecificsEnabled': item_spc})
        class_ad_en = responseDOM.getElementsByTagName('AdFormatEnabled')[0].childNodes[0].data
        Dictionary.update({'AdFormatEnabled': class_ad_en})
        condition_enabled = responseDOM.getElementsByTagName('ConditionEnabled')[0].childNodes[0].data
        Dictionary.update({'ConditionEnabled': condition_enabled})
#        condition_values = responseDOM.getElementsByTagName('ConditionValues')
        condition_values = self.getConditionValues(responseDOM.getElementsByTagName('Condition'))
        Dictionary.update({'ConditionValues': condition_values})
        responseDOM.unlink()
        return Dictionary

##################################for additem api ##################################
class AddItem:
    Session = Session()
    def __init__(self, DevID, AppID, CertID, Token, ServerURL):
        self.Session.Initialize(DevID, AppID, CertID, Token, ServerURL)

    def geterrors(self, nodelist):
       transDetails = []
       info = {}
       for cNode in nodelist.childNodes:
           if cNode.nodeName == 'LongMessage':
               if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
           if cNode.nodeName == 'SeverityCode':
               if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
       transDetails.append(info)
       return transDetails

    def Get(self, ids,product_id,title,desc,listing_type,scheduled_time,duration,sku,subtitle,postal,siteid,cr=None,uid=None):
        api = Call()
        api.Session = self.Session
        api.SiteID = siteid
        api.DetailLevel = "0"
        attribute_ids = []
        attribute_names = []
        value_ids = []
        attribute_ids_dict = {}
        attribute_ids_prod = []
        attribute_names_prod = []
        value_ids_prod = []
        attribute_ids2 = []
        attribute_names2 = []
        value_ids2 = []
        attribute_ids_prod2 = []
        attribute_names_prod2 = []
        value_ids_prod2 = []
        attribute_ids_dict2 = {}
        cat2_id = ''
        bold_tag = ''
        category = ''
        condition_enabled =''
        condtn_desc = ''
        condtn_desc_prod = ''
        Itemspecifics =''
        condition_enabled_cat2 = ''
#############for the first category#################
        title_cd = "<![CDATA[" + title + "]]>"
        subtitle_cd = "<![CDATA[" + subtitle + "]]>"
        des_cd = "<![CDATA[" + desc + "]]>"
        product_cat = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).cat1.id
        template_cat = pooler.get_pool(cr.dbname).get('product.listing.templates').browse(cr,uid,ids[0]).template_id.category_id1.id
        if product_cat:
            cat1_id = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,product_cat).ebay_category_id
            condition_enabled = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,product_cat).condition_enabled
            attribute_set_id_cat1 = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,product_cat).attribute_set_id
            product_match_atts = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).match_att_cat1
            for match_att in product_match_atts:
                attribute_obj = match_att.attribute_name
                attribute_id_prod = attribute_obj.attribute_id
                attribute_name_prod = attribute_obj.name
                value_id_prod = match_att.attribute_values_id.att_val_id
                if value_id_prod == None:
                    new_dict = {}
                    new_key = match_att.text_field
                    new_val = '-3'
                    new_dict[new_key] = new_val
                    value_id_prod = new_dict
                attribute_ids_dict[attribute_name_prod] = attribute_id_prod
                attribute_ids_prod.append(attribute_id_prod)
                attribute_names_prod.append(attribute_name_prod)
                value_ids_prod.append(value_id_prod)
        elif template_cat:
            cat1_id = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,template_cat).ebay_category_id
            condition_enabled = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,template_cat).condition_enabled
            attribute_set_id_cat1 = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,template_cat).attribute_set_id
            template_id = pooler.get_pool(cr.dbname).get('product.listing.templates').browse(cr,uid,ids[0]).template_id.id
            matching_attributes = pooler.get_pool(cr.dbname).get('ebayerp.template').browse(cr,uid,template_id).match_attribute_ids
            for matching_att in matching_attributes:
                attribute_obj = matching_att.attribute_name
                attribute_id = attribute_obj.attribute_id
                attribute_name = attribute_obj.name
                value_id = matching_att.attribute_values_id.att_val_id
                if value_id == None:
                        new_dict = {}
                        new_key = matching_att.text_field
                        new_val = '-3'
                        new_dict[new_key] = new_val
                        value_id = new_dict
                attribute_ids.append(attribute_id)
                attribute_names.append(attribute_name)
                value_ids.append(value_id)
                if attribute_name not in attribute_ids_dict.iterkeys():
                    attribute_ids_dict[attribute_name] = attribute_id
#        else:
#            raise osv.except_osv(_('Warning!'), _("Please select the category in Product or Template"))
############################for getting template matching attribute from ebayerp.template master#############
        template_id = pooler.get_pool(cr.dbname).get('product.listing.templates').browse(cr,uid,ids[0]).template_id.id
        template_object = pooler.get_pool(cr.dbname).get('product.listing.templates').browse(cr,uid,ids[0]).template_id
#####################condition######################
        condtn_record = pooler.get_pool(cr.dbname).get('ebayerp.template').browse(cr,uid,template_id).condtn
        if condtn_record:
            condtn_desc =  condtn_record.condition_id
        condtn_prod_record = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).ebay_condtn
        if condtn_prod_record:
            condtn_desc_prod = condtn_prod_record.condition_id
        if template_cat and product_cat:
            if product_cat == template_cat:
                matching_attributes = pooler.get_pool(cr.dbname).get('ebayerp.template').browse(cr,uid,template_id).match_attribute_ids
                for matching_att in matching_attributes:
                    attribute_obj = matching_att.attribute_name
                    attribute_id = attribute_obj.attribute_id
                    attribute_name = attribute_obj.name
                    value_id = matching_att.attribute_values_id.att_val_id
                    if value_id == None:
                            new_dict = {}
                            new_key = matching_att.text_field
                            new_val = '-3'
                            new_dict[new_key] = new_val
                            value_id = new_dict
                    attribute_ids.append(attribute_id)
                    attribute_names.append(attribute_name)
                    value_ids.append(value_id)
                    if attribute_name not in attribute_ids_dict.iterkeys():
                        attribute_ids_dict[attribute_name] = attribute_id
        product_dict = {}
        template_dict = {}
        position_prod = 0
        position_template = 0
############################## to create product matching attribute dictionary####
        for val in attribute_names_prod:
                product_dict[val] = value_ids_prod[position_prod]
                position_prod = position_prod + 1     
#########################template matching attribute dictionary###########
        for value in attribute_names:
                template_dict[value] = value_ids[position_template]
                position_template = position_template + 1
###################################for appending attributes in template to product onetomany fields#######
        if (template_cat and product_cat == template_cat) or template_cat:
                for keys in template_dict.iterkeys():
                    if keys not in product_dict.iterkeys():
                        dict_val = template_dict[keys]
                        if type(dict_val)==type(dict()):
                            for dic_key in dict_val.iterkeys():
                                keyval = dic_key
                                val = dict_val[dic_key]
                                product_dict[keyval] =  val
                                attribute_ids_dict[keyval] = attribute_ids_dict.pop(keys)
                        else:
                            value = template_dict[keys]
                            product_dict[keys] = value
###################for second category############################
        product_cat2 = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).cat2.id
        template_cat2 = pooler.get_pool(cr.dbname).get('product.listing.templates').browse(cr,uid,ids[0]).template_id.category_id2.id
        if product_cat2:
            attribute_set_id_cat2 = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,product_cat2).attribute_set_id
            cat2_id = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,product_cat2).ebay_category_id
            condition_enabled_cat2 = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,product_cat2).condition_enabled
            product_obj = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id)
            matching_att_cat2 = product_obj.match_att_cat2
            for matching_att in matching_att_cat2:
                attribute_obj = matching_att.attribute_name
                attribute_id_prod = attribute_obj.attribute_id
                attribute_name_prod = attribute_obj.name
                value_id_prod = matching_att.attribute_values_id.att_val_id
                if value_id_prod == None:
                    new_dict = {}
                    new_key = matching_att.text_field
                    new_val = '-3'
                    new_dict[new_key] = new_val
                    value_id_prod = new_dict
                attribute_ids_dict2[attribute_name_prod] = attribute_id_prod
                attribute_ids_prod2.append(attribute_id_prod)
                attribute_names_prod2.append(attribute_name_prod)
                value_ids_prod2.append(value_id_prod)
        elif template_cat2:
            attribute_set_id_cat2 = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,template_cat2).attribute_set_id
            cat2_id = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,template_cat2).ebay_category_id
            condition_enabled_cat2 = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,template_cat2).condition_enabled
            template_obj = pooler.get_pool(cr.dbname).get('product.listing.templates').browse(cr,uid,ids[0]).template_id
            template_match_att = template_obj.match_attribute_cat2
            for matching_att in template_match_att:
                attribute_obj = matching_att.attribute_name
                attribute_id = attribute_obj.attribute_id
                attribute_name = attribute_obj.name
                value_id = matching_att.attribute_values_id.att_val_id
                if value_id == None:
                        new_dict = {}
                        new_key = matching_att.text_field
                        new_val = '-3'
                        new_dict[new_key] = new_val
                        value_id = new_dict
                attribute_ids2.append(attribute_id)
                attribute_names2.append(attribute_name)
                value_ids2.append(value_id)
                if attribute_name not in attribute_ids_dict2.iterkeys():
                    attribute_ids_dict2[attribute_name] = attribute_id
######################################for gettting template attribute values####################
        template_obj = pooler.get_pool(cr.dbname).get('product.listing.templates').browse(cr,uid,ids[0]).template_id
        template_match_att = template_obj.match_attribute_cat2
        if template_cat2 and product_cat2:
            if product_cat2 == template_cat2:
                for matching_att in template_match_att:
                    attribute_obj = matching_att.attribute_name
                    attribute_id = attribute_obj.attribute_id
                    attribute_name = attribute_obj.name
                    value_id = matching_att.attribute_values_id.att_val_id
                    if value_id == None:
                            new_dict = {}
                            new_key = matching_att.text_field
                            new_val = '-3'
                            new_dict[new_key] = new_val
                            value_id = new_dict
                    attribute_ids2.append(attribute_id)
                    attribute_names2.append(attribute_name)
                    value_ids2.append(value_id)
                    if attribute_name not in attribute_ids_dict2.iterkeys():
                        attribute_ids_dict2[attribute_name] = attribute_id
#########################################################################
        product_dict2 = {}
        template_dict2 = {}
        position_prod2 = 0
        position_template2 = 0
############################## to create product matching attribute dictionary####
        for val in attribute_names_prod2:
                product_dict2[val] = value_ids_prod2[position_prod2]
                position_prod2 = position_prod2 + 1
#########################template matching attribute dictionary###########
        for value in attribute_names2:
                template_dict2[value] = value_ids2[position_template2]
                position_template2 = position_template2 + 1
###################################for appending attributes in template to product onetomany fields#######
        if (template_cat2 and product_cat2 == template_cat2) or template_cat2:
                for keys in template_dict2.iterkeys():
                    if keys not in product_dict2.iterkeys():
                        dict_val = template_dict2[keys]
                        if type(dict_val)==type(dict()):
                            for dic_key in dict_val.iterkeys():
                                keyval = dic_key
                                val = dict_val[dic_key]
                                #popval = product_dict.pop(keys)
                                product_dict2[keyval] =  val
                                attribute_ids_dict2[keyval] = attribute_ids_dict2.pop(keys)
                        else:
                            value = template_dict2[keys]
                            product_dict2[keys] = value
#####################################Passing the <AttributeSetArray> to the api########################
        att_ids = []
        attribute_set_array = ''
        new_att_set_array = ''
        att_set_array2 = ''
        attribute_set_array2 = ''
        double_value = []
        AttributeSetArray = ''
        double_value2 = []
        for keys in product_dict.iterkeys():
            dict_val = product_dict[keys]
            if type(dict_val)==type(dict()):
                for dic_key in dict_val.iterkeys():
                    keyval = dic_key
                    value = dict_val[dic_key]
                    product_dict[keyval] = product_dict.pop(keys)
                    product_dict[keyval] =  value
                    double_value.append(keyval)
                    attribute_ids_dict[keyval] = attribute_ids_dict.pop(keys)
                    keys = keyval
                    if keys in attribute_ids_dict.iterkeys():
                            att_id = attribute_ids_dict[keys]
                            att_ids.append(att_id)
                            attribute_set_array += """
                           <Attribute attributeID="%s">
                              <Value>
                                <ValueLiteral>%s</ValueLiteral>
                                <ValueID>%s</ValueID>
                              </Value>
                            </Attribute>""" % (att_id,keys,value)
            else:
                if len(double_value):
                    if keys in double_value:
                        print"Double value",keys
                    else:
                        value = product_dict[keys]
                        double_value.append(keys)
                        if keys in attribute_ids_dict.iterkeys():
                                att_id = attribute_ids_dict[keys]
                        att_ids.append(att_id)
                        attribute_set_array += """
                       <Attribute attributeID="%s">
                          <Value>
                            <ValueLiteral>%s</ValueLiteral>
                            <ValueID>%s</ValueID>
                          </Value>
                        </Attribute>""" % (att_id,keys,value)
                else:
                    value = product_dict[keys]
                    double_value.append(keys)
                    if keys in attribute_ids_dict.iterkeys():
                            att_id = attribute_ids_dict[keys]
                    att_ids.append(att_id)
                    attribute_set_array += """
                   <Attribute attributeID="%s">
                      <Value>
                        <ValueLiteral>%s</ValueLiteral>
                        <ValueID>%s</ValueID>
                      </Value>
                    </Attribute>""" % (att_id,keys,value)
        AttributeSet = """<AttributeSet attributeSetID="%s">""" %(attribute_set_id_cat1)
        if attribute_set_array:
            new_att_set_array = AttributeSet.encode("utf-8") + attribute_set_array.encode("utf-8") + """</AttributeSet>"""
        if cat1_id:
            category = """<PrimaryCategory><CategoryID>%s</CategoryID></PrimaryCategory>"""%(cat1_id)
        if cat2_id:
            category += """<SecondaryCategory><CategoryID>%s</CategoryID></SecondaryCategory>"""%(cat2_id)
        if product_dict2:
            for keys in product_dict2.iterkeys():
                dict_val = product_dict2[keys]
                if type(dict_val)==type(dict()):
                    for dic_key in dict_val.iterkeys():
                        keyval = dic_key
                        value = dict_val[dic_key]
                        product_dict2[keyval] = product_dict2.pop(keys)
                        product_dict2[keyval] =  value
                        double_value2.append(keyval)
                        attribute_ids_dict2[keyval] = attribute_ids_dict2.pop(keys)
                        keys = keyval
                        if keys in attribute_ids_dict2.iterkeys():
                            att_id = attribute_ids_dict2[keys]
                            att_ids.append(att_id)
                            attribute_set_array2 += """
                           <Attribute attributeID="%s">
                              <Value>
                                <ValueLiteral>%s</ValueLiteral>
                                <ValueID>%s</ValueID>
                              </Value>
                            </Attribute>""" % (att_id,keys,value)
                else:
                    if len(double_value2):
                        if keys in double_value2:
                            print"Double value",keys
                        else:
                            value = product_dict2[keys]
                            double_value2.append(keys)
                            if keys in attribute_ids_dict2.iterkeys():
                                    att_id = attribute_ids_dict2[keys]
                            att_ids.append(att_id)
                            attribute_set_array2 += """
                           <Attribute attributeID="%s">
                              <Value>
                                <ValueLiteral>%s</ValueLiteral>
                                <ValueID>%s</ValueID>
                              </Value>
                            </Attribute>""" % (att_id,keys,value)
                    else:
                        value = product_dict2[keys]
                        double_value2.append(keys)
                        if keys in attribute_ids_dict2.iterkeys():
                                att_id = attribute_ids_dict2[keys]
                        att_ids.append(att_id)
                        attribute_set_array2 += """
                       <Attribute attributeID="%s">
                          <Value>
                            <ValueLiteral>%s</ValueLiteral>
                            <ValueID>%s</ValueID>
                          </Value>
                        </Attribute>""" % (att_id,keys,value)
            AttributeSet = """<AttributeSet attributeSetID="%s">""" %(attribute_set_id_cat2)
            if attribute_set_array2:
                att_set_array2 = AttributeSet.encode("utf-8") + attribute_set_array2.encode("utf-8") + """</AttributeSet>"""
                new_att_set_array += att_set_array2.encode("utf-8")
        if new_att_set_array:
            AttributeSetArray = "<AttributeSetArray>" + new_att_set_array.encode("utf-8") + "</AttributeSetArray>"  
###############################For images##########################
        shop_id = pooler.get_pool(cr.dbname).get('product.listing.templates').browse(cr,uid,ids[0]).shop_id
        inst_obj = shop_id.instance_id
        site_name = ''
        site = ''
        site_id = shop_id.site_id
        if site_id:
            site_name = site_id.name
        site = """<Site>%s</Site>"""%(site_name)
        product_images = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).image_ids
        full_urls = []
        images = ''
        for each_image in product_images:
            uploading_image = ''
            each_image_id = each_image.id
            filename_ebay = each_image.filename_ebay
            if filename_ebay:
                    uploading_image = pooler.get_pool(cr.dbname).get('sale.shop').store_image(cr,uid,filename_ebay,'/opt/openerp_603/openerp-server-6.0.3/bin/addons/ebayconnect_new_generic/images/ebay_product.png',True)
            if uploading_image:        
                results = pooler.get_pool(cr.dbname).get('sale.shop').call(cr, uid, inst_obj, 'UploadSiteHostedPictures',uploading_image,siteid)
                increment = 0
                ack = results.get('Ack',False)
                if ack =='Failure':
                    if results.get('LongMessage',False):
                           long_message = results['LongMessage']
                           for each_messsge in long_message:
                               severity_code = each_messsge[0]['SeverityCode']
                               if severity_code == 'Error':
                                   Longmessage = each_messsge[0]['LongMessage']
                                   product_long_message = ('Error : %s') % (Longmessage)
                                   increment += 1
                                   pooler.get_pool(cr.dbname).get('sale.shop').log(cr, uid,increment, product_long_message)
                elif ack =='Warning':
                    full_url_array = results.get('FullURL',False)
                    if full_url_array:
                        full_url = (full_url_array[0]['FullURL'])
                        cr.execute("UPDATE product_images SET change_or_no_change ='no_change',full_url='%s'where id = %s"%(str(full_url),each_image_id,))
                        full_urls.append(full_url)
                    if results.get('LongMessage',False):
                        long_message = results['LongMessage']
                        for each_messsge in long_message:
                           severity_code = each_messsge[0]['SeverityCode']
                           if severity_code == 'Warning':
                               Longmessage = each_messsge[0]['LongMessage']
                               product_long_message = ('Warning : %s:') % (Longmessage)
                               increment += 1
                               pooler.get_pool(cr.dbname).get('sale.shop').log(cr, uid,increment, product_long_message)
                else:
                    full_url_array = results.get('FullURL',False)
                    if full_url_array:
                        full_url = (full_url_array[0]['FullURL'])
                        cr.execute("UPDATE product_images SET change_or_no_change ='no_change',full_url='%s'where id = %s"%(str(full_url),each_image_id,))
                        full_urls.append(full_url)
        code_list = ''
        product_reference_id = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).product_reference_id
        if product_reference_id:
            code_list+= """ <ProductListingDetails>
                            <IncludePrefilledItemInformation>true</IncludePrefilledItemInformation>
                            <IncludeStockPhotoURL>true</IncludeStockPhotoURL>
                                <ListIfNoProduct>true</ListIfNoProduct>
                                 <ProductReferenceID>%s</ProductReferenceID>
                              </ProductListingDetails>""" %(product_reference_id)
            stock_photo_url = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).stock_photo_url
            if stock_photo_url != 'NULL':
                full_urls.append(stock_photo_url)
        for each_url in full_urls:
            images += """<PictureURL>%s</PictureURL>"""%(each_url)
        images_url = ''
        images_url = """<PictureDetails>""" + images  + """</PictureDetails>"""
####################code for custom item specifics a######################################################################3
        item_specifics_dict_prod = {}
        item_specifics_dict_template = {}
        if product_cat:
            item_specifics = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,product_cat).item_specifics
            if item_specifics == True:
                product_item_specifics = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).custom_item_specifics_prod_cat_gene
                for each_item_specifics in product_item_specifics:
                    item_specifics_name = each_item_specifics.custom_name
                    item_specifics_value = each_item_specifics.custom_value
                    item_specifics_dict_prod[item_specifics_name] = item_specifics_value
        if product_cat2:
            item_specifics = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,product_cat2).item_specifics
            if item_specifics == True:
                product_item_specifics = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).custom_item_specifics_prod_cat_gene
                for each_item_specifics in product_item_specifics:
                    item_specifics_name = each_item_specifics.custom_name
                    if not item_specifics_dict_prod.has_key(item_specifics_name):
                        item_specifics_value = each_item_specifics.custom_value
                        item_specifics_dict_prod[item_specifics_name] = item_specifics_value
        if template_cat or template_cat2:
            if ((product_cat == template_cat) and product_cat != False and template_cat != False) or ((product_cat2 == template_cat2) and product_cat2 != False and template_cat2 != False):
                template_item_specifics = pooler.get_pool(cr.dbname).get('ebayerp.template').browse(cr,uid,template_id).custom_item_specifics_generic
                for each_item_specifics in template_item_specifics:
                    item_specifics_name = each_item_specifics.custom_name
                    item_specifics_value = each_item_specifics.custom_value
                    item_specifics_dict_template[item_specifics_name] = item_specifics_value
            else:
                template_item_specifics = pooler.get_pool(cr.dbname).get('ebayerp.template').browse(cr,uid,template_id).custom_item_specifics_generic
                for each_item_specifics in template_item_specifics:
                    item_specifics_name = each_item_specifics.custom_name
                    item_specifics_value = each_item_specifics.custom_value
                    item_specifics_dict_template[item_specifics_name] = item_specifics_value
        for each_key in item_specifics_dict_template.iterkeys():
            if each_key not in item_specifics_dict_prod.iterkeys():
                    value = item_specifics_dict_template[each_key]
                    item_specifics_dict_prod[each_key] = value
        if item_specifics_dict_prod:
            name_val_str = ''
            for each_key in item_specifics_dict_prod:
                value = item_specifics_dict_prod[each_key]

                name_val_str+= """<NameValueList>
                                <Name>%s</Name>
                                <Value>%s</Value>
                              </NameValueList>""" %(each_key,value)
#            Itemspecifics =''
            Itemspecifics = "<ItemSpecifics>"+ name_val_str.encode('utf-8')+ "</ItemSpecifics>"
#        else:
#            Itemspecifics = ''
        new_condition = ''
        if not condtn_desc_prod :
            new_condition = condtn_desc
        else:
            new_condition = condtn_desc_prod
        condition = ''
        if listing_type == 'LeadGeneration':
            condition = ''
        elif condition_enabled:
            if condition_enabled == False:
                if condition_enabled_cat2:
                    if condition_enabled_cat2 == False:
                        condition = ''
                    else:
                        condition =  """<ConditionID>%s</ConditionID>"""%(new_condition)
            else:
                condition =  """<ConditionID>%s</ConditionID>"""%(new_condition)
        else:
            condition =  """<ConditionID>%s</ConditionID>"""%(new_condition)
        start_price =  pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).start_price
        reserve_price = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).reserve_price
        buy_it_now_price = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).buy_it_now_price
        warehouse_id = shop_id.warehouse_id.id
        location_id = pooler.get_pool(cr.dbname).get('stock.warehouse').browse(cr,uid,warehouse_id).lot_stock_id.id
        function_call = pooler.get_pool(cr.dbname).get('product.listing.templates')._my_value(cr, uid,location_id,product_id,context={})
        quantity = str(function_call).split('.')
        shipping_details =''
        shipping_details = pooler.get_pool(cr.dbname).get('sale.shop').shipping_details(cr,uid,template_object,product_id,listing_type,shop_id,start_price,reserve_price,buy_it_now_price,quantity[0])
        bold_tag = ''
        bold_tl = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).bold_tl_prod
        bold_tl_tm = pooler.get_pool(cr.dbname).get('ebayerp.template').browse(cr,uid,template_id).bold_tl
        if bold_tl == True:
            bold_tag = """<ListingEnhancement>BoldTitle</ListingEnhancement>"""
        elif bold_tl_tm == True:
            bold_tag = """<ListingEnhancement>BoldTitle</ListingEnhancement>"""
        sku_string = ''
        if sku:
            sku_string = "<SKU>%s</SKU>"%(sku)
####################
        api.RequestData = """<?xml version="1.0" encoding="utf-8"?>
    <AddItemRequest xmlns="urn:ebay:apis:eBLBaseComponents">
    <Item>
    <Title>%(title_name)s</Title>
    """ + sku_string.encode('utf-8') + """
    """+ condition.encode("utf-8") + """"
    """ + category.encode("utf-8") + """
    """ + Itemspecifics.encode("utf-8") + """
     """ + AttributeSetArray.encode('utf-8') + """
    """ + code_list.encode("utf-8") + """
    <Description>%(description)s</Description>
    """ + bold_tag.encode("utf-8") + """
    """ +images_url.encode("utf-8") + """
    """ + shipping_details.encode("utf-8") + """
    <CategoryMappingAllowed>true</CategoryMappingAllowed>
    <Country>US</Country>
    <Currency>USD</Currency>
    <ScheduleTime>%(scheduled_time)s</ScheduleTime>
    <ListingDuration>%(duration)s</ListingDuration>
    <ListingType>%(type)s</ListingType>
    <SubTitle>%(subtitle)s</SubTitle>
    <PostalCode>%(postal)s</PostalCode>
    """ + site.encode("utf-8") + """
  </Item>
  <RequesterCredentials>
  <eBayAuthToken>%(token)s</eBayAuthToken>
  </RequesterCredentials>
</AddItemRequest>​​"""
        api.RequestData = api.RequestData % {'token': self.Session.Token.encode("utf-8"),
                                            'title_name': title_cd.encode("utf-8"),
                                            'description': des_cd.encode("utf-8"),
                                            'scheduled_time': scheduled_time,
                                            'duration': duration.encode("utf-8"),
                                            'type': listing_type.encode("utf-8"),
#                                            'sku': sku.encode("utf-8"),
                                            'postal': postal.encode("utf-8"),
                                            'subtitle': subtitle_cd.encode("utf-8"),
                                            
                                            }
        print"apirequest data",api.RequestData
        responseDOM = api.MakeCall("AddItem")
        print "Additem api Output: ",responseDOM.toprettyxml()
#############################for getting the values of itemid,start_time & end_time
        Dictionary = {}
        if responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Success':
            ack = responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data
            Dictionary.update({'Ack': ack})
            item_id = responseDOM.getElementsByTagName('ItemID')[0].childNodes[0].data
            Dictionary.update({'ItemID': item_id})
            start_time = responseDOM.getElementsByTagName('StartTime')[0].childNodes[0].data
            Dictionary.update({'StartTime': start_time})
            end_time = responseDOM.getElementsByTagName('EndTime')[0].childNodes[0].data
            Dictionary.update({'EndTime': end_time})
        elif responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Warning':
            ack = responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data
            Dictionary.update({'Ack': ack})
            item_id = responseDOM.getElementsByTagName('ItemID')[0].childNodes[0].data
            Dictionary.update({'ItemID': item_id})
            start_time = responseDOM.getElementsByTagName('StartTime')[0].childNodes[0].data
            Dictionary.update({'StartTime': start_time})
            end_time = responseDOM.getElementsByTagName('EndTime')[0].childNodes[0].data
            Dictionary.update({'EndTime': end_time})
            many_errors = []
            for each_error in  responseDOM.getElementsByTagName('Errors'):
               errors = self.geterrors(each_error)
               many_errors.append(errors)
            logger.notifyChannel('init', netsvc.LOG_WARNING, 'LongMessage %s' % (many_errors))
            Dictionary.update({'LongMessage': many_errors})
        elif responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Failure':
           ack = responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data
           Dictionary.update({'Ack': ack})
           many_errors = []
           for each_error in  responseDOM.getElementsByTagName('Errors'):
               errors = self.geterrors(each_error)
               many_errors.append(errors)
           Dictionary.update({'LongMessage': many_errors})
        responseDOM.unlink()
        return Dictionary
 #############################for update listing using reviseitem api (through active listing)##########
class ReviseItem:
    Session = Session()
    def __init__(self, DevID, AppID, CertID, Token, ServerURL):
        self.Session.Initialize(DevID, AppID, CertID, Token, ServerURL)

    def geterrors(self, nodelist):
       transDetails = []
       info = {}
       for cNode in nodelist.childNodes:
           if cNode.nodeName == 'LongMessage':
               if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
           if cNode.nodeName == 'SeverityCode':
               if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
       transDetails.append(info)
       return transDetails

    def Get(self, ids, product_id,item_id,title,description,subtitle,postal,increment,siteid,cr=None,uid=None):
        api = Call()
        api.Session = self.Session
        api.SiteID = siteid
        api.DetailLevel = "ReturnAll"
        attribute_ids = []
        attribute_names = []
        value_ids = []
        attribute_ids_prod = []
        attribute_names_prod = []
        value_ids_prod = []
        attribute_ids_dict = {}
        attribute_ids2 = []
        attribute_names2 = []
        value_ids2 = []
        attribute_ids_prod2 = []
        attribute_names_prod2 = []
        value_ids_prod2 = []
        attribute_ids_dict2 = {}
        cat2_id=''
        bold_tag = ''
        category = ''
        Dictionary ={}
        condtn_desc = ''
        condtn_desc_prod = ''
        condition_enabled =''
        Itemspecifics =''
        condition_enabled_cat2 = ''
######################## for category 1 ########################
        title_cd = "<![CDATA[" + title + "]]>"
        subtitle_cd = "<![CDATA[" + subtitle + "]]>"
        description_cd = "<![CDATA[" + description + "]]>"
        template_obj = pooler.get_pool(cr.dbname).get('product.listing').browse(cr,uid,ids[0]).related_template
        template_id = template_obj.id
        product_cat = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).cat1.id
        template_cat = pooler.get_pool(cr.dbname).get('product.listing').browse(cr,uid,ids[0]).related_template.category_id1.id
        if product_cat:
            cat1_id = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,product_cat).ebay_category_id
            condition_enabled = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,product_cat).condition_enabled
            attribute_set_id_cat1 = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,product_cat).attribute_set_id
            product_match_atts = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).match_att_cat1
            for match_att in product_match_atts:
                attribute_obj = match_att.attribute_name
                attribute_id_prod = attribute_obj.attribute_id
                attribute_name_prod = attribute_obj.name
                value_id_prod = match_att.attribute_values_id.att_val_id
                if value_id_prod == None:
                    new_dict = {}
                    new_key = match_att.text_field
                    new_val = '-3'
                    new_dict[new_key] = new_val
                    value_id_prod = new_dict
                attribute_ids_dict[attribute_name_prod] = attribute_id_prod
                attribute_ids_prod.append(attribute_id_prod)
                attribute_names_prod.append(attribute_name_prod)
                value_ids_prod.append(value_id_prod)
        elif template_cat:
            cat1_id = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,template_cat).ebay_category_id
            condition_enabled = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,template_cat).condition_enabled
            attribute_set_id_cat1 = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,template_cat).attribute_set_id
            matching_attributes = template_obj.match_attribute_ids
            for matching_att in matching_attributes:
                attribute_obj = matching_att.attribute_name
                attribute_id = attribute_obj.attribute_id
                attribute_name = attribute_obj.name
                value_id = matching_att.attribute_values_id.att_val_id
                if value_id == None:
                        new_dict = {}
                        new_key = matching_att.text_field
                        new_val = '-3'
                        new_dict[new_key] = new_val
                        value_id = new_dict
                attribute_ids.append(attribute_id)
                attribute_names.append(attribute_name)
                value_ids.append(value_id)
                if attribute_name not in attribute_ids_dict.iterkeys():
                    attribute_ids_dict[attribute_name] = attribute_id
        else:
            return Dictionary
######################################for gettting template attribute values####################
        if template_cat and product_cat:
            if product_cat == template_cat:
                template_match_att = template_obj.match_attribute_ids
                for matching_att in template_match_att:
                    attribute_obj = matching_att.attribute_name
                    attribute_id = attribute_obj.attribute_id
                    attribute_name = attribute_obj.name
                    value_id = matching_att.attribute_values_id.att_val_id
                    if value_id == None:
                            new_dict = {}
                            new_key = matching_att.text_field
                            new_val = '-3'
                            new_dict[new_key] = new_val
                            value_id = new_dict
                    attribute_ids.append(attribute_id)
                    attribute_names.append(attribute_name)
                    value_ids.append(value_id)
                    if attribute_name not in attribute_ids_dict.iterkeys():
                        attribute_ids_dict[attribute_name] = attribute_id
#########################################################################
        product_dict = {}
        template_dict = {}
        position_prod = 0
        position_template = 0
############################## to create product matching attribute dictionary####
        for val in attribute_names_prod:
                product_dict[val] = value_ids_prod[position_prod]
                position_prod = position_prod + 1
#########################template matching attribute dictionary###########
        for value in attribute_names:
                template_dict[value] = value_ids[position_template]
                position_template = position_template + 1
###################################for appending attributes in template to product onetomany fields#######
        if (template_cat and product_cat == template_cat) or template_cat:
            for keys in template_dict.iterkeys():
                if keys not in product_dict.iterkeys():
                    dict_val = template_dict[keys]
                    if type(dict_val)==type(dict()):
                        for dic_key in dict_val.iterkeys():
                            keyval = dic_key
                            val = dict_val[dic_key]
                            #popval = product_dict.pop(keys)
                            product_dict[keyval] =  val
                            attribute_ids_dict[keyval] = attribute_ids_dict.pop(keys)
                    else:
                        value = template_dict[keys]
                        product_dict[keys] = value
############################for second category###############################
        product_cat2 = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).cat2.id
        template_cat2 = pooler.get_pool(cr.dbname).get('product.listing').browse(cr,uid,ids[0]).related_template.category_id2.id
        if product_cat2:
            attribute_set_id_cat2 = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,product_cat2).attribute_set_id
            cat2_id = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,product_cat2).ebay_category_id
            condition_enabled_cat2 = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,product_cat2).condition_enabled
            product_obj = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id)
            matching_att_cat2 = product_obj.match_att_cat2
            for matching_att in matching_att_cat2:
                attribute_obj = matching_att.attribute_name
                attribute_id_prod = attribute_obj.attribute_id
                attribute_name_prod = attribute_obj.name
                value_id_prod = matching_att.attribute_values_id.att_val_id
                if value_id_prod == None:
                    new_dict = {}
                    new_key = matching_att.text_field
                    new_val = '-3'
                    new_dict[new_key] = new_val
                    value_id_prod = new_dict
                attribute_ids_dict2[attribute_name_prod] = attribute_id_prod
                attribute_ids_prod2.append(attribute_id_prod)
                attribute_names_prod2.append(attribute_name_prod)
                value_ids_prod2.append(value_id_prod)
        elif template_cat2:
            attribute_set_id_cat2 = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,template_cat2).attribute_set_id
            cat2_id = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,template_cat2).ebay_category_id
            condition_enabled_cat2 = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,template_cat2).condition_enabled
######################################for gettting template attribute values####################
            template_match_att = template_obj.match_attribute_cat2
            for matching_att in template_match_att:
                attribute_obj = matching_att.attribute_name
                attribute_id = attribute_obj.attribute_id
                attribute_name = attribute_obj.name
                value_id = matching_att.attribute_values_id.att_val_id
                if value_id == None:
                        new_dict = {}
                        new_key = matching_att.text_field
                        new_val = '-3'
                        new_dict[new_key] = new_val
                        value_id = new_dict
                attribute_ids2.append(attribute_id)
                attribute_names2.append(attribute_name)
                value_ids2.append(value_id)
                if attribute_name not in attribute_ids_dict2.iterkeys():
                    attribute_ids_dict2[attribute_name] = attribute_id
        template_match_att = template_obj.match_attribute_cat2
        if template_cat2 and product_cat2:
            if product_cat2 == template_cat2:            
                for matching_att in template_match_att:
                    attribute_obj = matching_att.attribute_name
                    attribute_id = attribute_obj.attribute_id
                    attribute_name = attribute_obj.name
                    value_id = matching_att.attribute_values_id.att_val_id
                    if value_id == None:
                            new_dict = {}
                            new_key = matching_att.text_field
                            new_val = '-3'
                            new_dict[new_key] = new_val
                            value_id = new_dict
                    attribute_ids2.append(attribute_id)
                    attribute_names2.append(attribute_name)
                    value_ids2.append(value_id)
                    if attribute_name not in attribute_ids_dict2.iterkeys():
                        attribute_ids_dict2[attribute_name] = attribute_id
#########################################################################
        product_dict2 = {}
        template_dict2 = {}
        position_prod2 = 0
        position_template2 = 0
############################## to create product matching attribute dictionary####
        for val in attribute_names_prod2:
                product_dict2[val] = value_ids_prod2[position_prod2]
                position_prod2 = position_prod2 + 1
#########################template matching attribute dictionary###########
        for value in attribute_names2:
                template_dict2[value] = value_ids2[position_template2]
                position_template2 = position_template2 + 1
###################################for appending attributes in template to product onetomany fields#######
        if (template_cat2 and product_cat2 == template_cat2) or template_cat2:
            for keys in template_dict2.iterkeys():
                if keys not in product_dict2.iterkeys():
                    dict_val = template_dict2[keys]
                    if type(dict_val)==type(dict()):
                        for dic_key in dict_val.iterkeys():
                            keyval = dic_key
                            val = dict_val[dic_key]
                            #popval = product_dict.pop(keys)
                            product_dict2[keyval] =  val
                            attribute_ids_dict2[keyval] = attribute_ids_dict2.pop(keys)
                    else:
                        value = template_dict2[keys]
                        product_dict2[keys] = value
######################################Passing the <AttributeSetArray> to the api>
        att_ids = []
        attribute_set_array = ''
        new_att_set_array = ''
        att_set_array2 = ''
        attribute_set_array2 = ''
        double_value = []
        AttributeSetArray = ''
        double_value2 = []
        for keys in product_dict.iterkeys():
            dict_val = product_dict[keys]
            if type(dict_val)==type(dict()):
                for dic_key in dict_val.iterkeys():
                    keyval = dic_key
                    value = dict_val[dic_key]
                    product_dict[keyval] = product_dict.pop(keys)
                    product_dict[keyval] =  value
                    double_value.append(keyval)
                    attribute_ids_dict[keyval] = attribute_ids_dict.pop(keys)
                    keys = keyval
                    if keys in attribute_ids_dict.iterkeys():
                            att_id = attribute_ids_dict[keys]
                            att_ids.append(att_id)
                            attribute_set_array += """
                           <Attribute attributeID="%s">
                              <Value>
                                <ValueLiteral>%s</ValueLiteral>
                                <ValueID>%s</ValueID>
                              </Value>
                            </Attribute>""" % (att_id,keys,value)
            else:
                if len(double_value):
                    if keys in double_value:
                        print"Double value",keys
                    else:
                        value = product_dict[keys]
                        double_value.append(keys)
                        if keys in attribute_ids_dict.iterkeys():
                                att_id = attribute_ids_dict[keys]
                        att_ids.append(att_id)
                        attribute_set_array += """
                       <Attribute attributeID="%s">
                          <Value>
                            <ValueLiteral>%s</ValueLiteral>
                            <ValueID>%s</ValueID>
                          </Value>
                        </Attribute>""" % (att_id,keys,value)
                else:
                    value = product_dict[keys]
                    double_value.append(keys)
                    if keys in attribute_ids_dict.iterkeys():
                            att_id = attribute_ids_dict[keys]
                    att_ids.append(att_id)
                    attribute_set_array += """
                   <Attribute attributeID="%s">
                      <Value>
                        <ValueLiteral>%s</ValueLiteral>
                        <ValueID>%s</ValueID>
                      </Value>
                    </Attribute>""" % (att_id,keys,value)
        AttributeSet = """<AttributeSet attributeSetID="%s">""" %(attribute_set_id_cat1)
        if attribute_set_array:
            new_att_set_array = AttributeSet.encode("utf-8") + attribute_set_array.encode("utf-8") + """</AttributeSet>"""
        if cat1_id:
            category = """<PrimaryCategory><CategoryID>%s</CategoryID></PrimaryCategory>"""%(cat1_id)
        if cat2_id:
            category += """<SecondaryCategory><CategoryID>%s</CategoryID></SecondaryCategory>"""%(cat2_id)
        if product_dict2:
            for keys in product_dict2.iterkeys():
                dict_val = product_dict2[keys]
                if type(dict_val)==type(dict()):
                    for dic_key in dict_val.iterkeys():
                        keyval = dic_key
                        value = dict_val[dic_key]
                        product_dict2[keyval] = product_dict2.pop(keys)
                        product_dict2[keyval] =  value
                        double_value2.append(keyval)
                        attribute_ids_dict2[keyval] = attribute_ids_dict2.pop(keys)
                        keys = keyval
                        if keys in attribute_ids_dict2.iterkeys():
                            att_id = attribute_ids_dict2[keys]
                            att_ids.append(att_id)
                            attribute_set_array2 += """
                           <Attribute attributeID="%s">
                              <Value>
                                <ValueLiteral>%s</ValueLiteral>
                                <ValueID>%s</ValueID>
                              </Value>
                            </Attribute>""" % (att_id,keys,value)
                else:
                    if len(double_value2):
                        if keys in double_value2:
                            print"Double value",keys
                        else:
                            value = product_dict2[keys]
                            double_value2.append(keys)
                            if keys in attribute_ids_dict2.iterkeys():
                                    att_id = attribute_ids_dict2[keys]
                            att_ids.append(att_id)
                            attribute_set_array2 += """
                           <Attribute attributeID="%s">
                              <Value>
                                <ValueLiteral>%s</ValueLiteral>
                                <ValueID>%s</ValueID>
                              </Value>
                            </Attribute>""" % (att_id,keys,value)
                    else:
                        value = product_dict2[keys]
                        double_value2.append(keys)
                        if keys in attribute_ids_dict2.iterkeys():
                                att_id = attribute_ids_dict2[keys]
                        att_ids.append(att_id)
                        attribute_set_array2 += """
                       <Attribute attributeID="%s">
                          <Value>
                            <ValueLiteral>%s</ValueLiteral>
                            <ValueID>%s</ValueID>
                          </Value>
                        </Attribute>""" % (att_id,keys,value)
            AttributeSet = """<AttributeSet attributeSetID="%s">""" %(attribute_set_id_cat2)
            if attribute_set_array2:
                att_set_array2 = AttributeSet.encode("utf-8") + attribute_set_array2.encode("utf-8") + """</AttributeSet>"""
                new_att_set_array += att_set_array2.encode("utf-8")
        if new_att_set_array:
            AttributeSetArray = "<AttributeSetArray>" + new_att_set_array.encode("utf-8") + "</AttributeSetArray>"  
####################################Condition#######################################
        condtn_record = pooler.get_pool(cr.dbname).get('ebayerp.template').browse(cr,uid,template_id).condtn
        if condtn_record:
            condtn_desc =  condtn_record.condition_id
        condtn_prod_record = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).ebay_condtn
        if condtn_prod_record:
            condtn_desc_prod = condtn_prod_record.condition_id
################For Images#############################
        shop_id = pooler.get_pool(cr.dbname).get('product.listing').browse(cr,uid,ids[0]).shop_id
        inst_obj = shop_id.instance_id
        token = inst_obj.auth_token
        product_images = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).image_ids
        full_urls = []
        images = ''
        code_list = ''
        delete_field = ''
        product_reference_id = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).product_reference_id
        if product_reference_id:
            code_list+= """ <ProductListingDetails>
                            <IncludePrefilledItemInformation>true</IncludePrefilledItemInformation>
                                <ListIfNoProduct>true</ListIfNoProduct>
                                 <ProductReferenceID>%s</ProductReferenceID>
                                 <IncludeStockPhotoURL>true</IncludeStockPhotoURL>
                              </ProductListingDetails>
                              """ %(product_reference_id)
            stock_photo_url = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).stock_photo_url
            if stock_photo_url != 'NULL':
                full_urls.append(stock_photo_url)
        else:
            delete_field = "<DeletedField>Item.ProductListingDetails</DeletedField>"
        for each_image in product_images:
            uploading_image = ''
            each_image_id = each_image.id
            change_or_no_change = each_image.change_or_no_change
            filename_ebay = each_image.filename_ebay
            if filename_ebay:
                product_image_id = each_image.id
                if change_or_no_change == 'change':
                    uploading_image = pooler.get_pool(cr.dbname).get('sale.shop').store_image(cr,uid,filename_ebay,'/opt/openerp_603/openerp-server-6.0.3/bin/addons/ebayconnect_new_generic/images/ebay_product.png',True)
                    cr.execute("update product_images set change_or_no_change='no_change' where id=%s"%(product_image_id,))
                else:
                    full_url = each_image.full_url
                    if full_url:
                        full_urls.append(full_url)
            if uploading_image:
                results = pooler.get_pool(cr.dbname).get('sale.shop').call(cr, uid, inst_obj, 'UploadSiteHostedPictures',uploading_image,siteid)
                ack = results.get('Ack',False)
                if ack =='Failure':
                    if results.get('LongMessage',False):
                           long_message = results['LongMessage']
                           for each_messsge in long_message:
                               severity_code = each_messsge[0]['SeverityCode']
                               if severity_code == 'Error':
                                   Longmessage = each_messsge[0]['LongMessage']
                                   product_long_message = ('Error : %s') % (Longmessage)
                                   increment += 1
                                   pooler.get_pool(cr.dbname).get('sale.shop').log(cr, uid,increment, product_long_message)
                elif ack =='Warning':
                    full_url_array = results.get('FullURL',False)
                    if full_url_array:
                        full_url = (full_url_array[0]['FullURL'])
                        full_urls.append(full_url)
                        cr.execute("UPDATE product_images SET change_or_no_change ='no_change',full_url='%s'where id = %s"%(str(full_url),each_image_id,))
                    if results.get('LongMessage',False):
                        long_message = results['LongMessage']
                        for each_messsge in long_message:
                           severity_code = each_messsge[0]['SeverityCode']
                           if severity_code == 'Warning':
                               Longmessage = each_messsge[0]['LongMessage']
                               product_long_message = ('Warning : %s:') % (Longmessage)
                               increment += 1
                               pooler.get_pool(cr.dbname).get('sale.shop').log(cr, uid,increment, product_long_message)
                else:
                    full_url_array = results.get('FullURL',False)
                    if full_url_array:
                        full_url = (full_url_array[0]['FullURL'])
                        full_urls.append(full_url)
                        cr.execute("UPDATE product_images SET change_or_no_change ='no_change',full_url='%s'where id = %s"%(str(full_url),each_image_id,))
        for each_url in full_urls:
            images += """<PictureURL>%s</PictureURL>"""%(each_url)
        images_url = ''
        images_url = """<PictureDetails>""" + images + """</PictureDetails>"""
##################################################################################
        item_specifics_dict_prod = {}
        item_specifics_dict_template = {}
        if product_cat:
            item_specifics = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,product_cat).item_specifics
            if item_specifics == True:
                product_item_specifics = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).custom_item_specifics_prod_cat_gene
                for each_item_specifics in product_item_specifics:
                    item_specifics_name = each_item_specifics.custom_name
                    item_specifics_value = each_item_specifics.custom_value
                    item_specifics_dict_prod[item_specifics_name] = item_specifics_value
        if product_cat2:
            item_specifics = pooler.get_pool(cr.dbname).get('category.master').browse(cr,uid,product_cat2).item_specifics
            if item_specifics == True:
                product_item_specifics = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).custom_item_specifics_prod_cat_gene
                for each_item_specifics in product_item_specifics:
                    item_specifics_name = each_item_specifics.custom_name
                    if not item_specifics_dict_prod.has_key(item_specifics_name):
                        item_specifics_value = each_item_specifics.custom_value
                        item_specifics_dict_prod[item_specifics_name] = item_specifics_value
        if template_cat or template_cat2:
            if product_cat or product_cat2:
                if ((product_cat == template_cat) and product_cat != False and template_cat != False) or ((product_cat2 == template_cat2) and product_cat2 != False and template_cat2 != False):
                    template_item_specifics = pooler.get_pool(cr.dbname).get('ebayerp.template').browse(cr,uid,template_id).custom_item_specifics_generic
                    for each_item_specifics in template_item_specifics:
                        item_specifics_name = each_item_specifics.custom_name
                        item_specifics_value = each_item_specifics.custom_value
                        item_specifics_dict_template[item_specifics_name] = item_specifics_value
            else:
                template_item_specifics = pooler.get_pool(cr.dbname).get('ebayerp.template').browse(cr,uid,template_id).custom_item_specifics_generic
                for each_item_specifics in template_item_specifics:
                    item_specifics_name = each_item_specifics.custom_name
                    item_specifics_value = each_item_specifics.custom_value
                    item_specifics_dict_template[item_specifics_name] = item_specifics_value 
                       
        for each_key in item_specifics_dict_template.iterkeys():
            if each_key not in item_specifics_dict_prod.iterkeys():
                    value = item_specifics_dict_template[each_key]
                    item_specifics_dict_prod[each_key] = value
        if item_specifics_dict_prod:
            name_val_str = ''
            for each_key in item_specifics_dict_prod:
                value = item_specifics_dict_prod[each_key]
                name_val_str+= """<NameValueList>
                                <Name>%s</Name>
                                <Value>%s</Value>
                              </NameValueList>""" %(each_key,value)
#            Itemspecifics =''
            Itemspecifics = "<ItemSpecifics>"+ name_val_str.encode('utf-8')+ "</ItemSpecifics>"
#        else:
#            Itemspecifics = ''
        
#            if not Itemspecifics:
#                delete_field += "<DeletedField>Item.ItemSpecifics</DeletedField>"
        if not full_urls and not product_reference_id:
            delete_field += """<DeletedField>Item.PictureDetails.PictureURL</DeletedField>"""
        listing_type = pooler.get_pool(cr.dbname).get('product.listing').browse(cr,uid,ids[0]).type
        new_condition = ''
        if not condtn_desc_prod:
            new_condition = condtn_desc
        else:
            new_condition = condtn_desc_prod
        condition = ''
        if listing_type == 'Classified Ad':
            condition = ''
        elif condition_enabled:
            if condition_enabled == False:
                if condition_enabled_cat2:
                    if condition_enabled_cat2 == False:
                        condition = ''
                    else:
                        condition =  """<ConditionID>%s</ConditionID>"""%(new_condition)
            else:
                condition =  """<ConditionID>%s</ConditionID>"""%(new_condition)
        else:
            condition =  """<ConditionID>%s</ConditionID>"""%(new_condition)
        shipping_details = pooler.get_pool(cr.dbname).get('sale.shop').shipping_details(cr,uid,template_obj,product_id,listing_type,shop_id,'','','','')
        bold_tag = ''
        bold_tl = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).bold_tl_prod
        bold_tl_tm = pooler.get_pool(cr.dbname).get('ebayerp.template').browse(cr,uid,template_id).bold_tl
        if bold_tl == True:
            bold_tag = """<ListingEnhancement>BoldTitle</ListingEnhancement>"""
        elif bold_tl_tm == True:
            bold_tag = """<ListingEnhancement>BoldTitle</ListingEnhancement>"""
        ebay_sku = pooler.get_pool(cr.dbname).get('product.product').browse(cr,uid,product_id).ebay_sku
        sku_string = ''
        if ebay_sku:
            sku_string = "<SKU>%s</SKU>"%(ebay_sku)
        else:
            delete_field += "<DeletedField>Item.SKU</DeletedField>"
######################################for gettting template attribute values of category2####################
        api.RequestData = """<?xml version="1.0" encoding="utf-8"?>
  <ReviseItemRequest xmlns="urn:ebay:apis:eBLBaseComponents">
  """ + delete_field.encode("utf-8") +"""
  <Item>
    <ItemID>%(item_id)s</ItemID>
    <Title>%(title)s</Title>
    """ + sku_string.encode('utf-8') + """
    """+ condition.encode("utf-8") + """
    """ + category.encode("utf-8") + """
    """ + Itemspecifics.encode("utf-8") + """
    <Description>%(description)s</Description>
    """ + bold_tag.encode("utf-8") + """
    <CategoryMappingAllowed>true</CategoryMappingAllowed>
    """ + AttributeSetArray.encode('utf-8') + """
    """ + code_list.encode("utf-8") + """
    <SubTitle>%(subtitle)s</SubTitle>
    <PostalCode>%(postal)s</PostalCode>
   """+ images_url.encode("utf-8") + """
   """ + shipping_details.encode("utf-8") + """
  </Item>

  <RequesterCredentials>
    <eBayAuthToken>""" + token.encode("utf-8")+"""</eBayAuthToken>
  </RequesterCredentials>
</ReviseItemRequest>​​"""
        print "api.RequestData",api.RequestData
        api.RequestData = api.RequestData % { 
                                              'item_id' : item_id.encode("utf-8"),
                                              'title' : title_cd.encode("utf-8"),
                                              'postal': postal.encode("utf-8"),
                                              'description': description_cd.encode("utf-8"),
                                              'subtitle': subtitle_cd.encode("utf-8")
                                              }
        responseDOM = api.MakeCall("ReviseItem")
        print "Reviseitem api output: ",responseDOM.toprettyxml()
        if responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Success':
            ack = responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data
            Dictionary.update({'Ack': ack})
            item_id = responseDOM.getElementsByTagName('ItemID')[0].childNodes[0].data
            logger.notifyChannel('init', netsvc.LOG_WARNING, 'item_id %s' % (item_id))
            Dictionary.update({'ItemID': item_id})
        elif responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Warning':
            ack = responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data
            Dictionary.update({'Ack': ack})
            item_id = responseDOM.getElementsByTagName('ItemID')[0].childNodes[0].data
            Dictionary.update({'ItemID': item_id})
            many_errors = []
            for each_error in  responseDOM.getElementsByTagName('Errors'):
               errors = self.geterrors(each_error)
               many_errors.append(errors)
            Dictionary.update({'LongMessage': many_errors})
        elif responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Failure':
           ack = responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data
           Dictionary.update({'Ack': ack})
           many_errors = []
           for each_error in  responseDOM.getElementsByTagName('Errors'):
               errors = self.geterrors(each_error)
               many_errors.append(errors)
           Dictionary.update({'LongMessage': many_errors})
        responseDOM.unlink()
        return Dictionary
#############################code for cancel listing using enditem api ##################3
class EndItem:
    Session = Session()
    def __init__(self, DevID, AppID, CertID, Token, ServerURL):
        self.Session.Initialize(DevID, AppID, CertID, Token, ServerURL)
    def Get(self,item_id,ending_reason,siteid):
        api = Call()
        api.Session = self.Session
        api.SiteID = siteid
        api.DetailLevel = "ReturnAll"
        api.RequestData = """<?xml version="1.0" encoding="utf-8"?>
  <EndItemRequest xmlns="urn:ebay:apis:eBLBaseComponents">
  <EndingReason>%(ending_reason)s</EndingReason>
  <RequesterCredentials>
    <eBayAuthToken>%(token)s</eBayAuthToken>
  </RequesterCredentials>
  <ItemID>%(item_id)s</ItemID>
</EndItemRequest>​​"""
        api.RequestData = api.RequestData % { 'token': self.Session.Token.encode("utf-8"),
                                              'item_id':item_id.encode("utf-8"),
                                              'ending_reason':ending_reason.encode("utf-8")
                                              }
        responseDOM = api.MakeCall("EndItem")
        print "End Time Output: ",responseDOM.toprettyxml()
#################################for getting the values of endtime#################
        Dictionary = {}
        if responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Success':
            end_time = responseDOM.getElementsByTagName('EndTime')[0].childNodes[0].data
            Dictionary.update({'EndTime': end_time})
        elif responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Warning':
            end_time = responseDOM.getElementsByTagName('EndTime')[0].childNodes[0].data
            Dictionary.update({'EndTime': end_time})
        elif responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Failure':
            long_message = responseDOM.getElementsByTagName('LongMessage')[0].childNodes[0].data
            raise osv.except_osv(_('Warning!'), _("%s")% (long_message))
        responseDOM.unlink()
        return Dictionary
######################################################################################
class GeteBayDetails:
    Session = Session()
    def __init__(self, DevID, AppID, CertID, Token, ServerURL):
        self.Session.Initialize(DevID, AppID, CertID, Token, ServerURL)
    def getshipserv(self, nodelist):
        transDetails = []
        for node in nodelist:
            info = {}
            flag = 0
            for cNode in node.childNodes:
                if cNode.nodeName == 'Description':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'ShippingService':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'ShippingTimeMax':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'ServiceType':
                    if flag == 0:
                        if cNode.childNodes:
                            info[cNode.nodeName] = cNode.childNodes[0].data
                            flag = 1
                    else :
                        cNode.nodeName = 'ServiceType1'
                        if cNode.childNodes:
                            info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'ShippingPackage':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'InternationalService':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'ShippingCarrier':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'SurchargeApplicable':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'DimensionsRequired':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
            transDetails.append(info)
        return transDetails

    def getlocdetails(self, nodelist):
        locDetails = []
        for node in nodelist:
            info1 = {}
            for cNode in node.childNodes:
                if cNode.nodeName == 'Description':
                    if cNode.childNodes:
                        info1[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'Location':
                    if cNode.childNodes:
                        info1[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'Region':
                    if cNode.childNodes:
                        info1[cNode.nodeName] = cNode.childNodes[0].data
            locDetails.append(info1)
        return locDetails

    def getlocations(self, nodelist):
        locations = []
        for node in nodelist:
            info2 = {}
            for cNode in node.childNodes:
                if cNode.nodeName == 'ShippingLocation':
                    if cNode.childNodes:
                        info2[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'Description':
                    if cNode.childNodes:
                        info2[cNode.nodeName] = cNode.childNodes[0].data
            locations.append(info2)
        return locations
    def getsitedetails(self, nodelist):
        sitedetails = []
        for node in nodelist:
            info = {}
            for cNode in node.childNodes:
                if cNode.nodeName == 'Site':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'SiteID':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
            sitedetails.append(info)
        return sitedetails

    def Get(self,siteid):
        api = Call()
        api.Session = self.Session
        api.SiteID = siteid
        api.DetailLevel = "ReturnAll"
        api.RequestData = """<?xml version="1.0" encoding="utf-8"?>
  <GeteBayDetailsRequest xmlns="urn:ebay:apis:eBLBaseComponents">
  <DetailName>ExcludeShippingLocationDetails</DetailName>
  <DetailName>ShippingServiceDetails</DetailName>
  <DetailName>ShippingLocationDetails</DetailName>
  <DetailName>SiteDetails</DetailName>
  <RequesterCredentials>
    <eBayAuthToken>%(token)s</eBayAuthToken>
  </RequesterCredentials>
  <WarningLevel>High</WarningLevel>
</GeteBayDetailsRequest>"""
        api.RequestData = api.RequestData % { 'token': self.Session.Token.encode("utf-8")}
        responseDOM = api.MakeCall("GeteBayDetails")
        Dictionary = {}
        ack_response = responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data
        if  ack_response == 'Success' or ack_response == 'Warning':
            getshipInfo = self.getshipserv(responseDOM.getElementsByTagName('ShippingServiceDetails'))
            getcountryInfo = self.getlocdetails(responseDOM.getElementsByTagName('ExcludeShippingLocationDetails'))
            getlocationInfo = self.getlocations(responseDOM.getElementsByTagName('ShippingLocationDetails'))
            sitedetails = self.getsitedetails(responseDOM.getElementsByTagName('SiteDetails'))
            Dictionary.update({'ShippingLocationDetails': getlocationInfo})
            Dictionary.update({'ShippingServiceDetails': getshipInfo})
            Dictionary.update({'ExcludeShippingLocationDetails': getcountryInfo})
            Dictionary.update({'SiteDetails': sitedetails})
        else:
            raise osv.except_osv(_('Error!'), _((responseDOM.getElementsByTagName('Errors')[0].childNodes[0].childNodes[0].data)))
        return Dictionary

class UploadSiteHostedPictures:
    Session = Session()
    def __init__(self, DevID, AppID, CertID, Token, ServerURL):
        self.Session.Initialize(DevID, AppID, CertID, Token, ServerURL)
    def geturl(self,nodelist):
        url = []
        for node in nodelist:
            info1 = {}
            for cNode in node.childNodes:
                if cNode.nodeName == 'FullURL':
                    if cNode.childNodes:
                        info1[cNode.nodeName] = cNode.childNodes[0].data
            url.append(info1)
        return url
    def geterrors(self, nodelist):
       transDetails = []
       info = {}
       for cNode in nodelist.childNodes:
           if cNode.nodeName == 'LongMessage':
               if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
           if cNode.nodeName == 'SeverityCode':
               if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
       transDetails.append(info)
       return transDetails
    def Get(self,filename,siteid):
        api = Call()
        api.Session = self.Session
        api.SiteID = siteid
        uploading_image = open(filename,'rb')
        multiPartImageData = uploading_image.read()
        uploading_image.close()
        string1 = "--MIME_boundary"
        string2 = "Content-Disposition: form-data; name=\"XML Payload\""
        string3 = "Content-Type: text/xml;charset=utf-8"
        string4 = string1 + '\r\n' + string2 +'\r\n' + string3
        string5 = string4 + '\r\n'+'\r\n'
        string6 = string5 + "<?xml version='1.0' encoding='utf-8'?>"+'\r\n'
        string7=  string6 + "<UploadSiteHostedPicturesRequest xmlns=\"urn:ebay:apis:eBLBaseComponents\">"+'\r\n'
        string8 = string7 + "<Version>747</Version>"+'\r\n'
        string9 = string8 + "<PictureName>my_pic</PictureName>"+'\r\n'
        string10 = string9 + "<RequesterCredentials><eBayAuthToken>" + self.Session.Token.encode("utf-8") + "</eBayAuthToken></RequesterCredentials>"+'\r\n'
        string11 = string10 + "</UploadSiteHostedPicturesRequest>"+'\r\n'
        string12 = string11 + "--MIME_boundary" +'\r\n'
        string13 = string12 + "Content-Disposition: form-data; name='dummy'; filename='dummy'" +'\r\n'
        string14 = string13 + "Content-Transfer-Encoding: binary" + '\r\n'
        string15 = string14 + "Content-Type: application/octet-stream" + '\r\n'+'\r\n'
        string16 = string15 + multiPartImageData + '\r\n'
        string17 = string16 + "--MIME_boundary--" + '\r\n'
        api.RequestData = string17
        responseDOM = api.MakeCall("UploadSiteHostedPictures")
        print "uploadsitehosted pictures api call: ",responseDOM.toprettyxml()
        Dictionary={}
        if responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Success':
            ack = responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data
            Dictionary.update({'Ack': ack})
            full_url = self.geturl(responseDOM.getElementsByTagName('SiteHostedPictureDetails'))
            Dictionary.update({'FullURL':full_url})
        elif responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Warning':
            ack = responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data
            Dictionary.update({'Ack': ack})
            full_url = self.geturl(responseDOM.getElementsByTagName('SiteHostedPictureDetails'))
            Dictionary.update({'FullURL':full_url})
            many_errors = []
            for each_error in  responseDOM.getElementsByTagName('Errors'):
               errors = self.geterrors(each_error)
               many_errors.append(errors)
            logger.notifyChannel('init', netsvc.LOG_WARNING, 'LongMessage %s' % (many_errors))
            Dictionary.update({'LongMessage': many_errors})
        elif responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Failure':
            ack = responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data
            Dictionary.update({'Ack': ack})
            many_errors = []
            for each_error in  responseDOM.getElementsByTagName('Errors'):
               errors = self.geterrors(each_error)
               many_errors.append(errors)
            logger.notifyChannel('init', netsvc.LOG_WARNING, 'LongMessage %s' % (many_errors))
            Dictionary.update({'LongMessage': many_errors})
        responseDOM.unlink()
        return Dictionary
 ########################Getproducts api call ###########
class GetProducts:
    Session = Session()
    def __init__(self, DevID, AppID, CertID, Token, ServerURL):
        self.Session.Initialize(DevID, AppID, CertID, Token, ServerURL)

    def geterrors(self, nodelist):
       transDetails = []
       info = {}
       for cNode in nodelist.childNodes:
           if cNode.nodeName == 'LongMessage':
               if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
           if cNode.nodeName == 'SeverityCode':
               if cNode.childNodes:
                    info[cNode.nodeName] = cNode.childNodes[0].data
       transDetails.append(info)
       return transDetails
    def getProduct(self, nodelist):
        productDetails = []
        for node in nodelist:
            info = {}
            for cNode in node.childNodes:
                if cNode.nodeName == 'Title':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'DetailsURL':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'ProductReferenceID':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'StockPhotoURL':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
            productDetails.append(info)
        return productDetails
            
    def Get(self,attribute_set_id,search_by,query_keyword,pageno,siteid):
        api = Call()
        api.Session = self.Session
        api.SiteID = siteid
        api.DetailLevel = "ReturnAll"
        external_productid = ''
        if search_by == 'UPC':
            external_productid = """<ExternalProductID> ExternalProductIDType
                                      <Type>UPC</Type>
                                      <Value>%s</Value>
                                    </ExternalProductID>"""%(query_keyword)
        elif query_keyword:
            external_productid = """<QueryKeywords>%s</QueryKeywords>"""%(query_keyword)
        api.RequestData = """<?xml version="1.0" encoding="utf-8"?>
                      <GetProductsRequest xmlns="urn:ebay:apis:eBLBaseComponents">
                      <RequesterCredentials>
                        <eBayAuthToken>%(token)s</eBayAuthToken>
                      </RequesterCredentials>
                    <ProductSearch><AvailableItemsOnly>True</AvailableItemsOnly>
                    """+external_productid.encode("utf-8") +"""
                    <Pagination>
                        <EntriesPerPage>25</EntriesPerPage>
                        <PageNumber>%(pageno)s</PageNumber>
                    </Pagination>
                    <CharacteristicSetIDs>
                    <ID>%(attribute_set_id)s</ID></CharacteristicSetIDs>
                    </ProductSearch></GetProductsRequest>​​"""
        api.RequestData = api.RequestData % { 'token': self.Session.Token.encode("utf-8"),
                                              'attribute_set_id':attribute_set_id,
                                              'pageno':pageno,
                                              }
        print"api requestdata",api.RequestData
        responseDOM = api.MakeCall("GetProducts")
#        print "Getproducts api call output: ",responseDOM.toprettyxml()
#################################for getting the values of endtime#################
        Dictionary = {}
        if responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Success':
            ack = responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data
            Dictionary.update({'Ack': ack})
            product_info = self.getProduct(responseDOM.getElementsByTagName('Product'))
            Dictionary.update({'Product': product_info})
            hasmore =  responseDOM.getElementsByTagName('HasMore')[0].childNodes[0].data
            Dictionary.update({'HasMore': hasmore})
        elif responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data == 'Failure':
            ack = responseDOM.getElementsByTagName('Ack')[0].childNodes[0].data
            Dictionary.update({'Ack': ack})
            many_errors = []
            for each_error in  responseDOM.getElementsByTagName('Errors'):
               errors = self.geterrors(each_error)
               many_errors.append(errors)
            Dictionary.update({'LongMessage': many_errors})
        responseDOM.unlink()
        return Dictionary

class ebayerp_osv(external_osv.external_osv):
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
