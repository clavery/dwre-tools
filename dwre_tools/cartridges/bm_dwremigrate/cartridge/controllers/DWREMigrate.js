/**
 * Implements the server-side component of the DWRE tools
 * specifically the migration requirements
 *
 * @module controllers/DWREMigrate
 */

var ISML = require('dw/template/ISML');
var Transaction = require('dw/system/Transaction');
var System = require('dw/system/System');

const CARTRIDGE_VERSION = "2";

function overview() {
    if (!session.userAuthenticated) {
        return;
    }

    var preferences = System.getPreferences();

    var dwreMigrateCurrentVersion = null;
    var dwreMigrateToolVersion = null;
    var dwreMigrateHotfixes = null;
    var dwreMigrateVersionPath = [];

    if ("dwreMigrateToolVersion" in preferences.getCustom()) {
        dwreMigrateToolVersion = preferences.getCustom()["dwreMigrateToolVersion"];
    }
    if ("dwreMigrateCurrentVersion" in preferences.getCustom()) {
        dwreMigrateCurrentVersion = preferences.getCustom()["dwreMigrateCurrentVersion"];
    }
    if ("dwreMigrateVersionPath" in preferences.getCustom()) {
        dwreMigrateVersionPath = preferences.getCustom()["dwreMigrateVersionPath"].split(',');
    }
    if ("dwreMigrateHotfixes" in preferences.getCustom()) {
        dwreMigrateHotfixes = preferences.getCustom()["dwreMigrateHotfixes"].split(',');
    }

    ISML.renderTemplate('dwremigrate/overview', {
        cartridgeVersion: CARTRIDGE_VERSION,
        dwreMigrateToolVersion: dwreMigrateToolVersion,
        dwreMigrateCurrentVersion: dwreMigrateCurrentVersion,
        dwreMigrateVersionPath: dwreMigrateVersionPath,
        dwreMigrateHotfixes: dwreMigrateHotfixes
    });
}
overview.public = true;
exports.Overview = overview;

function versions() {
    if (!session.userAuthenticated) {
        return;
    }
    var preferences = System.getPreferences();	
    var prefTypeDef = preferences.describe();

    var dwreMigrateCurrentVersion = null;
    var dwreMigrateToolVersion = null;
    var dwreMigrateVersionPath = null;

    if ("dwreMigrateToolVersion" in preferences.getCustom()) {
        dwreMigrateToolVersion = preferences.getCustom()["dwreMigrateToolVersion"];
    }
    if ("dwreMigrateCurrentVersion" in preferences.getCustom()) {
        dwreMigrateCurrentVersion = preferences.getCustom()["dwreMigrateCurrentVersion"];
    }
    if ("dwreMigrateVersionPath" in preferences.getCustom()) {
        dwreMigrateVersionPath = preferences.getCustom()["dwreMigrateVersionPath"];
    }

    var resp = {
        cartridgeVersion: CARTRIDGE_VERSION,
        // legacy 
        "missingToolVersion" : dwreMigrateToolVersion === null,
        "toolVersion" : dwreMigrateToolVersion,
        "migrationVersion" : dwreMigrateCurrentVersion,
        "migrationPath" : dwreMigrateVersionPath
    };

    var migrateAttributeGroup = prefTypeDef.getAttributeGroup('dwreMigrate');
    for (var i=0; i < migrateAttributeGroup.attributeDefinitions.length; i++) {
        var def = migrateAttributeGroup.attributeDefinitions[i];
        if (def.ID in preferences.custom && !(def.ID in resp)) {
            resp[def.ID] = preferences.custom[def.ID];
        }
    }

    response.setContentType('application/json');
    response.writer.println(JSON.stringify(resp, null, 2));
}
versions.public = true;
exports.Versions = versions;


function updateVersion() {
    if (!session.userAuthenticated) {
        return;
    }
    var preferences = System.getPreferences();
    var prefTypeDef = preferences.describe();
    var resp;

    var params = request.httpParameterMap;

    var dwreMigrateCurrentVersion = null;
    var dwreMigrateToolVersion = null;

    if ("dwreMigrateToolVersion" in preferences.getCustom()) {
        dwreMigrateToolVersion = preferences.getCustom()["dwreMigrateToolVersion"];
    }
    if ("dwreMigrateCurrentVersion" in preferences.getCustom()) {
        dwreMigrateCurrentVersion = preferences.getCustom()["dwreMigrateCurrentVersion"];
    }

    if (dwreMigrateToolVersion === null) {
        response.setStatus(400);
        resp = {
            "error" : "tools not boostrapped"
        };
    }

    Transaction.wrap(function() {
        preferences.custom.dwreMigrateCurrentVersion = params.NewVersion.stringValue;

        if (params.NewVersionPath.submitted) {
            preferences.custom.dwreMigrateVersionPath = params.NewVersionPath.stringValue;
        }

        var migrateAttributeGroup = prefTypeDef.getAttributeGroup('dwreMigrate');
        for (var i=0; i < migrateAttributeGroup.attributeDefinitions.length; i++) {
            var def = migrateAttributeGroup.attributeDefinitions[i];
            if (params.get(def.ID).submitted) {
                preferences.custom[def.ID] = params.get(def.ID).value;
            }
        }
    });

    resp = {
        "message" : "updated"
    };

    response.setContentType('application/json');
    response.writer.println(JSON.stringify(resp, null, 2));
}
updateVersion.public = true;
exports.UpdateVersion = updateVersion;


function updateIndexes() {
    let Pipeline = require('dw/system/Pipeline');
    let pdict = Pipeline.execute('DWREMigrateLegacy-UpdateIndexes', { });
    var t = pdict;
}
updateIndexes.public = true;
exports.UpdateIndexes = updateIndexes;
