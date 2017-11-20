
TOOL_VERSION = "10"
# used to pair included cartridge and determine slipstream requirements
CARTRIDGE_VERSION = "2"
SKIP_METADATA_CHECK_ON_UPGRADE = True
RERUN_MIGRATIONS_ON_UPGRADE = True

BOOTSTRAP_META = """<?xml version="1.0" encoding="UTF-8"?>
<metadata xmlns="http://www.demandware.com/xml/impex/metadata/2006-10-31">
    <type-extension type-id="OrganizationPreferences">
        <custom-attribute-definitions>
            <attribute-definition attribute-id="dwreMigrateCurrentVersion">
                <display-name xml:lang="x-default">DWRE Migrate Current Version</display-name>
                <description xml:lang="x-default">DO NOT MODIFY THIS VALUE UNLESS YOU UNDERSTAND THE CONSEQUENCES. PERFORM A SITE BACKUP BEFORE MANUAL MODIFICATION</description>
                <type>string</type>
                <mandatory-flag>false</mandatory-flag>
                <externally-managed-flag>true</externally-managed-flag>
                <min-length>0</min-length>
            </attribute-definition>
            <attribute-definition attribute-id="dwreMigrateToolVersion">
                <display-name xml:lang="x-default">DWRE Migrate Tool Version</display-name>
                <description xml:lang="x-default">DO NOT MODIFY THIS VALUE UNLESS YOU UNDERSTAND THE CONSEQUENCES. PERFORM A SITE BACKUP BEFORE MANUAL MODIFICATION</description>
                <type>string</type>
                <mandatory-flag>false</mandatory-flag>
                <externally-managed-flag>true</externally-managed-flag>
                <min-length>0</min-length>
                <default-value>1</default-value>
            </attribute-definition>
            <attribute-definition attribute-id="dwreMigrateVersionPath">
                <display-name xml:lang="x-default">DWRE Migrate Version Path</display-name>
                <description xml:lang="x-default">DO NOT MODIFY THIS VALUE UNLESS YOU UNDERSTAND THE CONSEQUENCES. PERFORM A SITE BACKUP BEFORE MANUAL MODIFICATION</description>
                <type>text</type>
                <mandatory-flag>false</mandatory-flag>
                <externally-managed-flag>true</externally-managed-flag>
            </attribute-definition>
            <attribute-definition attribute-id="dwreMigrateHotfixes">
                <display-name xml:lang="x-default">DWRE Migrate Hotfixes Applied</display-name>
                <description xml:lang="x-default">DO NOT MODIFY THIS VALUE UNLESS YOU UNDERSTAND THE CONSEQUENCES. PERFORM A SITE BACKUP BEFORE MANUAL MODIFICATION</description>
                <type>text</type>
                <mandatory-flag>false</mandatory-flag>
                <externally-managed-flag>true</externally-managed-flag>
            </attribute-definition>
        </custom-attribute-definitions>
        <group-definitions>
            <attribute-group group-id="dwreMigrate">
                <display-name xml:lang="x-default">DWREMigrate</display-name>
                <attribute attribute-id="dwreMigrateCurrentVersion"/>
                <attribute attribute-id="dwreMigrateToolVersion"/>
                <attribute attribute-id="dwreMigrateVersionPath"/>
                <attribute attribute-id="dwreMigrateHotfixes"/>
            </attribute-group>
        </group-definitions>
    </type-extension>
</metadata>
"""

PREFERENCES = """<?xml version="1.0" encoding="UTF-8"?>
<preferences xmlns="http://www.demandware.com/xml/impex/preferences/2007-03-31">
    <custom-preferences>
        <all-instances>
            <preference preference-id="dwreMigrateToolVersion">{0}</preference>
        </all-instances>
        <development>
            <preference preference-id="dwreMigrateToolVersion">{0}</preference>
        </development>
        <staging>
            <preference preference-id="dwreMigrateToolVersion">{0}</preference>
        </staging>
        <production>
            <preference preference-id="dwreMigrateToolVersion">{0}</preference>
        </production>
    </custom-preferences>
</preferences>
""".format(TOOL_VERSION)

WHITELIST = """<?xml version="1.0" encoding="UTF-8"?>
<csrf-whitelists xmlns="http://www.demandware.com/xml/impex/csrfwhitelists/2017-02-09">
</csrf-whitelists>
"""

VERSION = """###########################################
# Generated file, do not edit.
# Copyright (c) 2015 by Demandware, Inc.
###########################################
15.5.2
"""

