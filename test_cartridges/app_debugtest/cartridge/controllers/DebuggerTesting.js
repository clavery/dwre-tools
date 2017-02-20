'use strict';

/**
 * TODO: Controller Description
 *
 * @module controllers/DebuggerTesting
 */

var ArrayList = require('dw/util/ArrayList');
var ISML = require('dw/template/ISML');
var Resource = require('dw/web/Resource');
var Transaction = require('dw/system/Transaction');
var URLUtils = require('dw/web/URLUtils');
var OrderMgr = require('dw/order/OrderMgr');


var app = require('/app_storefront_controllers/cartridge/scripts/app');
var guard = require('/app_storefront_controllers/cartridge/scripts/guard');


function test() {

  var a = "joe";
  var bar = "test";

  var b = 1 + 2;
}


/**
 * TODO: Doc
 */
function start() {
  var t = "foo";

  var myMap = new dw.util.HashMap();

  var order = OrderMgr.getOrder(request.httpParameterMap.orderNo.value);

  myMap.put("yo", t);
  test();
  myMap.put("bob", "something");

  var b = t;

  response.writer.print("this is a test " + t);
}


/*
* Exposed methods.
*/

/** // TODO: method documentation
 * @see {@link module:controllers/DebuggerTesting~start} */
exports.Start = guard.ensure(['get'], start);

