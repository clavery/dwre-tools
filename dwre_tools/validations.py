from lxml import etree as ET
import os
import re

from colorama import Fore, Back, Style
import dwre_tools

SCHEMA_MAP = {
    "abtest" : "abtest.xsd",
    "bmext" : "bmext.xsd",
    "cache-settings" : "cachesettings.xsd",
    "catalog" : "catalog.xsd",
    "coupons" : "coupon.xsd",
    "coupon-redemptions" : "couponredemption.xsd",
    "customers" : "customer.xsd",
    "customer-groups" : "customergroup.xsd",
    "customer-lists" : "customerlist.xsd",
    "customerpaymentinstrument" : "customerpaymentinstrument.xsd",
    "custom-objects" : "customobject.xsd",
    "feeds" : "feed.xsd",
    "form" : "form.xsd",
    "geolocations" : "geolocation.xsd",
    "gift-certificates" : "giftcertificate.xsd",
    "inventory" : "inventory.xsd",
    "library" : "library.xsd",
    "metadata" : "metadata.xsd",
    "oauth" : "oauth.xsd",
    "orders" : "order.xsd",
    "payment-settings" : "paymentmethod.xsd",
    "payment-processors" : "paymentprocessor.xsd",
    "preferences" : "preferences.xsd",
    "pricebooks" : "pricebook.xsd",
    "product-lists" : "productlist.xsd",
    "promotions" : "promotion.xsd",
    "redirect-urls" : "redirecturl.xsd",
    "schedules" : "schedules.xsd",
    "search" : "search.xsd",
    "search2" : "search2.xsd",
    "migrations" : "dwre-migrate.xsd",
    "services" : "services.xsd",
    "shipping" : "shipping.xsd",
    "site" : "site.xsd",
    "slot-configurations" : "slot.xsd",
    "sort" : "sort.xsd",
    "sourcecodes" : "sourcecode.xsd",
    "stores" : "store.xsd",
    "tax" : "tax.xsd",
    "url-rules" : "urlrules.xsd",
    "xml" : "xml.xsd"
}


def validate_xml(xml, throw=True):
    root_el = xml.getroot()
    root_tag = root_el.tag[root_el.tag.find('}')+1:]
    if root_tag not in SCHEMA_MAP:
        return
    schema_name = SCHEMA_MAP[root_tag]
    schema = ET.XMLSchema(file=os.path.join(dwre_tools.__path__[0], 'schemas', schema_name))
    schema.validate(xml)
    if throw:
        schema.assertValid(xml)
    return schema


SCHEMALINE_RE = re.compile(r'^(.*?:\d+:\d+:)')
def validate_file(full_filename):
    print "%s"  % full_filename,
    try:
        xml = ET.parse(full_filename)
        schema = validate_xml(xml, throw=False)
        if schema is None:
            print Fore.YELLOW + "no schema [WARNING]" + Fore.RESET
            return True
        elif schema.error_log:
            print Fore.RED + "[ERROR]" + Fore.RESET
            for e in schema.error_log:
                print SCHEMALINE_RE.sub(Fore.BLUE + '\\1' + Fore.RESET, str(e))
            return False
        else:
            print Fore.GREEN + "[OK]" + Fore.RESET
            return True
    except ET.XMLSyntaxError as e:
        print Fore.RED + "[ERROR]" + Fore.RESET
        print e
        return False


def validate_directory(directory):
    results = []
    for (dirpath, dirnames, filenames) in os.walk(directory):
        for fname in filenames:
            (root, ext) = os.path.splitext(fname)

            if ext != ".xml":
                continue

            full_filename = os.path.join(dirpath, fname)
            result = validate_file(full_filename)
            results.append(result)

    return all(results)



def validate_command(target):
    if os.path.isdir(target):
        validate_directory(target)
    elif os.path.isfile(target):
        validate_file(target)
    else:
        raise IOError("file not found")

