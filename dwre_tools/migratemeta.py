
TOOL_VERSION = u"5"

BOOTSTRAP_META = """<?xml version="1.0" encoding="UTF-8"?>
<metadata xmlns="http://www.demandware.com/xml/impex/metadata/2006-10-31">
    <type-extension type-id="OrganizationPreferences">
        <custom-attribute-definitions>
            <attribute-definition attribute-id="dwreMigrateCurrentVersion">
                <display-name xml:lang="x-default">DWRE Migrate Current Version</display-name>
                <description>DO NOT MODIFY THIS VALUE UNLESS YOU UNDERSTAND THE CONSEQUENCES. PERFORM A SITE BACKUP BEFORE MANUAL MODIFICATION</description>
                <type>string</type>
                <site-specific-flag>false</site-specific-flag>
                <mandatory-flag>false</mandatory-flag>
                <externally-managed-flag>true</externally-managed-flag>
                <min-length>0</min-length>
            </attribute-definition>
            <attribute-definition attribute-id="dwreMigrateToolVersion">
                <display-name xml:lang="x-default">DWRE Migrate Tool Version</display-name>
                <description>DO NOT MODIFY THIS VALUE UNLESS YOU UNDERSTAND THE CONSEQUENCES. PERFORM A SITE BACKUP BEFORE MANUAL MODIFICATION</description>
                <type>string</type>
                <site-specific-flag>false</site-specific-flag>
                <mandatory-flag>false</mandatory-flag>
                <externally-managed-flag>true</externally-managed-flag>
                <min-length>0</min-length>
                <default-value>1</default-value>
            </attribute-definition>
        </custom-attribute-definitions>
        <group-definitions>
            <attribute-group group-id="dwreMigrate">
                <display-name xml:lang="x-default">DWREMigrate</display-name>
                <attribute attribute-id="dwreMigrateCurrentVersion"/>
                <attribute attribute-id="dwreMigrateToolVersion"/>
            </attribute-group>
        </group-definitions>
    </type-extension>
</metadata>
"""

PREFERENCES = """<?xml version="1.0" encoding="UTF-8"?>
<preferences xmlns="http://www.demandware.com/xml/impex/preferences/2007-03-31">
    <custom-preferences>
        <all-instances>
            <preference preference-id="dwreMigrateToolVersion">%s</preference>
        </all-instances>
    </custom-preferences>
</preferences>
""" % (TOOL_VERSION)

VERSION = """###########################################
# Generated file, do not edit.
# Copyright (c) 2015 by Demandware, Inc.
###########################################
15.5.2
"""

