from unittest import TestCase
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

import re
import shutil
import tempfile
import os
from os.path import join as J

import requests
import responses

import dwre_tools
from dwre_tools.bmtools import login_business_manager, get_list_data_units, get_current_versions
from dwre_tools.bmtools import wait_for_import

TEST_DATA = os.path.join(dwre_tools.__path__[0], '..', 'testdata')


class TestBMTools(TestCase):
    def setUp(self):
        self.env = {
            "server": "www.example.com",
            "username": "test",
            "password": "user"
        }

    @responses.activate
    def test_login_business_manager(self):
        responses.add(responses.POST, re.compile('.*ViewApplication-ProcessLogin.*'),
                      body="'csrf_token','abc'", status=200)

        session = requests.session()
        login_business_manager(self.env, session)

        assert len(responses.calls) == 1
        assert 'csrf_token' in session.params and session.params['csrf_token'] == 'abc'

    @responses.activate
    def test_login_business_manager_bad_password(self):
        responses.add(responses.POST, re.compile('.*ViewApplication-ProcessLogin.*'),
                      body="Invalid login or password", status=200)

        session = requests.session()

        with self.assertRaises(RuntimeError):
            login_business_manager(self.env, session)

        assert len(responses.calls) == 1

    @responses.activate
    def test_get_list_data_units(self):
        """Test parsing the export units from a snippet body of the
        site import/export page"""
        responses.add(responses.GET, re.compile('.*ViewSiteImpex-Status.*'),
                      body=DATA_UNITS_BODY, status=200)

        session = requests.session()
        data_units = get_list_data_units(self.env, session)

        assert len(responses.calls) == 1
        assert data_units
        assert 'GlobalDataExport_all_' in [i['id'] for i in data_units]

    @responses.activate
    def test_get_current_versions(self):
        """Test parsing the export units from a snippet body of the
        site import/export page"""
        r = dict(
            toolVersion='1',
            migrationVersion='abc123',
            cartridgeVersion='2',
            migrationPath='foobar,abc123',
            dwreMigrateHotfixes='hotfix1,hotfix1'
        )
        responses.add(responses.GET, re.compile('.*DWREMigrate-Versions.*'),
                      json=r, status=200)

        session = requests.session()
        (tool_version, migration_version, current_migration_path,
                cartridge_version, hotfixes) = get_current_versions(self.env, session)

        assert len(responses.calls) == 1
        assert tool_version == '1'
        assert len(current_migration_path) == 2
        assert 'hotfix1' in hotfixes

    @responses.activate
    @patch('time.sleep')
    def test_wait_for_import(self, new_time_sleep):
        def request_callback(request):
            request_callback.num_requests += 1
            if request_callback.num_requests == 3:
                return (200, {}, IMPORT_BODY)
            else:
                return (200, {}, "<div>dummy data</div>")

        request_callback.num_requests = 0
        responses.add_callback(responses.GET, re.compile('.*ViewSiteImpex-Status.*'),
                               callback=request_callback) 
        responses.add(responses.GET, re.compile('.*ViewSiteImpex-Monitor.*'),
                      body="finished successfully", status=200)

        session = requests.session()
        wait_for_import(self.env, session, 'dwremigrate_20171120T1319_foo.zip')

        # 3 calls for waiting and 1 final to get the result of the import
        # = 4 total remote calls
        assert len(responses.calls) == 4
        # assert sleep was called with 1 second interval
        # use mock to speed test up
        new_time_sleep.assert_called_with(1)


IMPORT_BODY = """
<td class="table_detail e s top" nowrap="nowrap">

<a href="https://www.example.com/on/demandware.store/Sites-Site/default/ViewSiteImpex-Monitor?JobConfigurationUUID=548b03e87a9400d30bfbe66256&amp;csrf_token=pUIjZEEkO8Nrne7s62TmstSGvYqyimLaHxsIo_IRvhoP_d6gNNJdRHgQWeKef6plHhHXzfrtd-Ie4ynYc0cmoPIXc2YrdfPv9E9pbsjxxVp_OvXb8rxOZQvj3Gfp9tT1XQCyYt17EmpThyJWkixPx4tCC8_BBMBshryBpQPrW5vvbtGhcds" class="selection_link">
Site Import (dwremigrate_20171120T1319_foo.zip)
</a>

</td>
"""

DATA_UNITS_BODY = """

var exportUnitJSON1 = [
{


id: "FullSiteExport_all_",
text: "Sites",
description: "All site data",
uiProvider: "exportUnit",
leaf: false,
checked: false,
iconCls: "tree_filefolder_icon"

, children: [

{


id: "FullSiteExport_RossSimons",
text: "RossSimons",
description: 'All data of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: false,
checked: false,
iconCls: "tree_filefolder_icon",
children: [
{


id: "SiteExport_RossSimons_ABTestExport",
text: "A/B Tests",
description: 'A/B tests of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "SiteExport_RossSimons_FeedExport",
text: "Active Data Feeds",
description: 'Active data feeds of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "SiteExport_RossSimons_CacheSettingsExport",
text: "Cache Settings",
description: 'Cache settings of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "SiteExport_RossSimons_PromotionExport",
text: "Campaigns and Promotions",
description: 'Campaigns and promotions of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "SiteExport_RossSimons_ContentExport",
text: "Content",
description: 'Content of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "SiteExport_RossSimons_CouponExport",
text: "Coupons",
description: 'Coupons of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "SiteExport_RossSimons_CustomerCDNSettingsExport",
text: "Customer CDN Settings",
description: 'Customer CDN settings of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "SiteExport_RossSimons_CustomerGroupExport",
text: "Customer Groups",
description: 'Customer groups of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "SiteExport_RossSimons_SiteCustomObjectExport",
text: "Custom Objects",
description: 'Custom objects of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "SiteExport_RossSimons_DynamicFileResourcesExport",
text: "Dynamic File Resources",
description: 'Dynamic file resources of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "SiteExport_RossSimons_DCExtensionsExport",
text: "Distributed Commerce Extensions",
description: 'Distributed Commerce extensions configuration of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "SiteExport_RossSimons_SiteOcapiSettingsExport",
text: "OCAPI Settings",
description: 'OCAPI settings of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "SiteExport_RossSimons_PaymentMethodExport",
text: "Payment Methods",
description: 'Payment methods of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "SiteExport_RossSimons_PaymentProcessorExport",
text: "Payment Processors",
description: 'Payment processors of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "SiteExport_RossSimons_RedirectUrlExport",
text: "Redirect URLs",
description: 'Redirect URLs of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "SiteExport_RossSimons_SearchExport",
text: "Search Settings",
description: 'Search settings of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "SiteExport_RossSimons_ShippingExport",
text: "Shipping",
description: 'Shipping settings of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "SiteExport_RossSimons_SitesExport",
text: "Site Descriptor",
description: 'Site.xml file of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "SiteExport_RossSimons_SitePreferencesExport",
text: "Site Preferences",
description: 'Preferences of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "SiteExport_RossSimons_SiteUrlExport",
text: "Site URLs",
description: 'Site URLs of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},





{


id: "SiteExport_RossSimons_SitemapConfigurationExport",
text: "Sitemap Settings",
description: 'Sitemap settings of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},

{


id: "SiteExport_RossSimons_SlotExport",
text: "Slots",
description: 'Slots of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "SiteExport_RossSimons_SortExport",
text: "Sorting Rules",
description: 'Sorting rules of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "SiteExport_RossSimons_SourceCodeExport",
text: "Source Codes",
description: 'Source codes of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "SiteExport_RossSimons_StoreExport",
text: "Stores",
description: 'Stores of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "SiteExport_RossSimons_TaxExport",
text: "Tax",
description: 'Tax data of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "SiteExport_RossSimons_StorefrontUrlExport",
text: "URL Rules",
description: 'URL Rules of site \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
}
]
}


]

},
{


id: "FullLibraryExport_all_",
text: "Libraries",
description: "All shared libraries",
uiProvider: "exportUnit",
leaf: false,
checked: false,
iconCls: "tree_filefolder_icon"

, children: [

{


id: "FullLibraryExport_RossSimonsSharedLibrary",
text: "RossSimonsSharedLibrary",
description: 'Library \"RossSimonsSharedLibrary\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
}


]

}
]




var exportUnitJSON2 = [
{


id: "SiteContentExport_all_",
text: "Library Static Resources",
description: "All content images",
uiProvider: "exportUnit",
leaf: false,
checked: false,
iconCls: "tree_filefolder_icon"

, children: [

{


id: "SiteContentExport_RossSimons",
text: "RossSimons",
description: 'Content images of private site library \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
}


]

},
{


id: "FullCatalogExport_all_",
text: "Catalogs",
description: "All catalogs",
uiProvider: "exportUnit",
leaf: false,
checked: false,
iconCls: "tree_filefolder_icon"

, children: [

{


id: "FullCatalogExport_lbh-master",
text: "lbh-master",
description: 'Catalog \"lbh-master\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
}
,

{


id: "FullCatalogExport_ross-simons-storefront",
text: "ross-simons-storefront",
description: 'Catalog \"ross-simons-storefront\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
}


]

},
{


id: "CatalogContentExport_all_",
text: "Catalog Static Resources",
description: "All product images",
uiProvider: "exportUnit",
leaf: false,
checked: false,
iconCls: "tree_filefolder_icon"

, children: [

{


id: "CatalogContentExport_lbh-master",
text: "lbh-master",
description: 'Product images of catalog \"lbh-master\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
}
,

{


id: "CatalogContentExport_ross-simons-storefront",
text: "ross-simons-storefront",
description: 'Product images of catalog \"ross-simons-storefront\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
}


]

},
{


id: "PriceBookExport_all_",
text: "Price Books",
description: "All price books",
uiProvider: "exportUnit",
leaf: false,
checked: false,
iconCls: "tree_filefolder_icon"

,children: [

{


id: "PriceBookExport_ross-simons-list-prices",
text: "ross-simons-list-prices",
description: 'Price book "ross-simons-list-prices"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
}
,

{


id: "PriceBookExport_ross-simons-sale-prices",
text: "ross-simons-sale-prices",
description: 'Price book "ross-simons-sale-prices"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
}


]

},
{


id: "InventoryListExport_all_",
text: "Inventory Lists",
description: "All inventory lists",
uiProvider: "exportUnit",
leaf: false,
checked: false,
iconCls: "tree_filefolder_icon"

,children: [

{


id: "InventoryListExport_lbh-inventory",
text: "lbh-inventory",
description: 'Inventory list "lbh-inventory"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
}


]

},
{


id: "CustomerListExport_all_",
text: "Customer Lists",
description: "All customer lists",
uiProvider: "exportUnit",
leaf: false,
checked: false,
iconCls: "tree_filefolder_icon"

,children: [

{


id: "CustomerListExport_RossSimons",
text: "RossSimons",
description: 'Customer list \"RossSimons\"',
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
}


]

},
{


id: "GlobalDataExport_all_",
text: "Global Data",
description: "All global data",
uiProvider: "exportUnit",
leaf: false,
checked: false,
iconCls: "tree_filefolder_icon",
children: [
{


id: "LocalesExport",
text: "Locales",
description: "Locales",
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "GlobalPreferencesExport",
text: "Preferences",
description: "Global preferences",
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "GlobalCustomObjectExport",
text: "Global Custom Objects",
description: "Global custom objects",
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},

{


id: "JobsExport",
text: "Job Schedules",
description: "Scheduled job definitions",
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},

{


id: "SchedulesExport",
text: "Job Schedules (deprecated)",
description: "Deprecated scheduled job definitions",
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "MetaDataExport",
text: "Meta Data",
description: "System object type extensions and custom object type extensions",
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "GlobalStaticFilesExport",
text: "Static Resources",
description: "Global static resources",
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "UserExport",
text: "Users",
description: "Users of the organization",
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "AccessRoleExport",
text: "Access Roles",
description: "Access roles of the organization",
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "GeolocationExport",
text: "Geolocations",
description: "Geolocations of the organization",
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: 'CustomQuotaExport',
text: "Custom Quota Settings",
description: "Custom quota settings of the instance",
uiProvider: 'exportUnit',
leaf: true,
iconCls: 'tree_file_icon',
checked: false
},
{


id: 'OAuthProvidersExport',
text: "OAuth Providers",
description: "OAuth providers",
uiProvider: 'exportUnit',
leaf: true,
iconCls: 'tree_file_icon',
checked: false
},
{


id: "GlobalOcapiSettingsExport",
text: "OCAPI Settings",
description: "Global OCAPI settings",
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "GlobalWebdavClientPermissionExport",
text: "WebDAV Client Permissions",
description: "Global WebDAV Client Permissions",
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "ServicesExport",
text: "Services",
description: "Service definitions from the service framework",
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "CSCSettingsExport",
text: "CSC Settings",
description: "Settings for Customer Service Center customization",
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "PageMetaTags",
text: "Page Meta Tags",
description: "Page meta tag definitions",
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "PriceAdjustmentLimitsExport",
text: "Price Adjustment Limits",
description: "Price adjustment limits for all roles",
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
},
{


id: "CSRFWhitelistExport",
text: "CSRF Whitelists",
description: "CSRF Whitelists",
uiProvider: "exportUnit",
leaf: true,
iconCls: "tree_file_icon",
checked: false
}
]
}
]
 // too big for one file
var exportUnitJSON = exportUnitJSON1 == null ? null : exportUnitJSON1.concat(exportUnitJSON2);

/**
* Construct the UI tree based on the static JSON.
*/
</script>
<!-- End: Unit selection -->
"""
