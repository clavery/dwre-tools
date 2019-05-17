from __future__ import print_function

from lxml import etree as ET
import os
import re
import json

from colorama import Fore, Back, Style
from jsonschema import validate as validate_jsonschema
import jsonschema
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
    "customer-list" : "customerlist2.xsd",
    "customerpaymentinstrument" : "customerpaymentinstrument.xsd",
    "custom-objects" : "customobject.xsd",
    "csrf-whitelists" : "csrfwhitelists.xsd",
    "extensions" : "bmext.xsd",
    "feeds" : "feed.xsd",
    "form" : "form.xsd",
    "geolocations" : "geolocation.xsd",
    "gift-certificates" : "giftcertificate.xsd",
    "inventory" : "inventory.xsd",
    "library" : "library.xsd",
    "locales" : "locales.xsd",
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
    "migrations" : "dwre-migrate.xsd",
    "services" : "services.xsd",
    "shipping" : "shipping.xsd",
    "site" : "site.xsd",
    "slot-configurations" : "slot.xsd",
    "sitemap-configuration" : "sitemapconfiguration.xsd",
    "sort" : "sort.xsd",
    "sourcecodes" : "sourcecode.xsd",
    "stores" : "store.xsd",
    "tax" : "tax.xsd",
    "url-rules" : "urlrules.xsd",
    "xml" : "xml.xsd",
    "jobs" : "jobs.xsd",
    "page-meta-tags" : "pagemetatag.xsd",
}

NSMAP = {
    "http://www.demandware.com/xml/impex/search/2007-02-28" : "search.xsd",
    "http://www.demandware.com/xml/impex/search2/2010-02-19" : "search2.xsd",
}

JSON_SCHEMAS = [
    "attributedefinition.json",
    "attributedefinitiongroup.json",
    "common.json",
    "componenttype.json",
    "componenttypeexclusion.json",
    "contentassetcomponentconfig.json",
    "contentassetcomponentdata.json",
    "contentassetpageconfig.json",
    "customeditortype.json",
    "editordefinition.json",
    "image.json",
    "pagetype.json",
    "regiondefinition.json",
    "visibilityrule.json",
]

def load_json_schema_ref_resolver():
    store = {}
    for schema in JSON_SCHEMAS:
        store[schema] = json.load(open(os.path.join(dwre_tools.__path__[0], 'schemas/' + schema)))
    return jsonschema.RefResolver(base_uri='', referrer='', store=store)

def validate_xml(xml, throw=True):
    """Validates XML against DWRE schemas"""

    root_el = xml.getroot()
    root_tag = root_el.tag[root_el.tag.find('}')+1:]
    schema_name = None
    if None in root_el.nsmap:
        schema_name = NSMAP.get(root_el.nsmap[None], SCHEMA_MAP.get(root_tag))
    elif root_tag in SCHEMA_MAP:
        schema_name = SCHEMA_MAP.get(root_tag)

    if not schema_name:
        return

    schema = ET.XMLSchema(file=os.path.join(dwre_tools.__path__[0], 'schemas', schema_name))
    schema.validate(xml)
    if throw:
        schema.assertValid(xml)
    return schema


SCHEMALINE_RE = re.compile(r'^(.*?:\d+:\d+:)')
def validate_file(full_filename):
    print("%s"  % full_filename, end=' ')
    try:
        xml = ET.parse(full_filename)
        schema = validate_xml(xml, throw=False)
        if schema is None:
            print(Fore.YELLOW + "no schema [WARNING]" + Fore.RESET)
            return True
        elif schema.error_log:
            print(Fore.RED + "[ERROR]" + Fore.RESET)
            for e in schema.error_log:
                print(SCHEMALINE_RE.sub(Fore.CYAN + '\\1' + Fore.RESET, str(e)))
            return False
        else:
            print(Fore.GREEN + "[OK]" + Fore.RESET)
            return True
    except ET.XMLSchemaParseError as e:
        print(Fore.YELLOW + "bad schema [WARNING]" + Fore.RESET)
        return True
    except ET.XMLSyntaxError as e:
        print(Fore.RED + "[ERROR]" + Fore.RESET)
        print(e)
        return False

def validate_json_schemas(directory):
    results = []
    ref_resolver = load_json_schema_ref_resolver()
    for (dirpath, dirnames, filenames) in os.walk(directory):
        for fname in filenames:
            (root, ext) = os.path.splitext(fname)

            if ext == ".json":
                full_filename = os.path.join(dirpath, fname)
                result = validate_json_schema(full_filename, ref_resolver=ref_resolver)
                results.append(result)

    return all(results)

def validate_json_schema(full_filename, ref_resolver=None):
    if not ref_resolver:
        ref_resolver = load_json_schema_ref_resolver()
    try:
        if os.path.normpath("experience/components") in os.path.normpath(full_filename):
            print("%s"  % full_filename, end=' ')
            # validate component
            component_schema = json.load(open(os.path.join(dwre_tools.__path__[0], 'schemas/componenttype.json')))
            with open(full_filename, "r") as f:
                instance = json.load(f) # TODO: check json failure
                validate_jsonschema(instance=instance, schema=component_schema,
                                    resolver=ref_resolver)
            print(Fore.GREEN + "[OK]" + Fore.RESET)
            return True
        elif os.path.normpath("experience/pages") in os.path.normpath(full_filename):
            print("%s"  % full_filename, end=' ')
            # validate component
            component_schema = json.load(open(os.path.join(dwre_tools.__path__[0], 'schemas/pagetype.json')))
            with open(full_filename, "r") as f:
                instance = json.load(f) # TODO: check json failure
                validate_jsonschema(instance=instance, schema=component_schema,
                                    resolver=ref_resolver)
            print(Fore.GREEN + "[OK]" + Fore.RESET)
            return True
        return True
    except json.decoder.JSONDecodeError as e:
        print(Fore.RED + "[ERROR] Cannot Decode JSON" + Fore.RESET)
        print(e.msg)
        return False
    except jsonschema.exceptions.ValidationError as e:
        print(Fore.RED + "[ERROR] jsonschema validation error" + Fore.RESET)
        print(e.message)
        return False

def validate_directory(directory):
    results = []
    for (dirpath, dirnames, filenames) in os.walk(directory):
        for fname in filenames:
            (root, ext) = os.path.splitext(fname)

            if ext == ".xml":
                full_filename = os.path.join(dirpath, fname)
                result = validate_file(full_filename)
                results.append(result)

    return all(results)

def validate_command(target):
    if os.path.isdir(target):
        validate_directory(target)
        validate_json_schemas(target)
    elif os.path.isfile(target):
        (root, ext) = os.path.splitext(target)
        if ext == ".json":
            validate_json_schema(target)
        else:
            validate_file(target)
    else:
        raise IOError("file not found")

