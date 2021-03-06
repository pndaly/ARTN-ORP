/* eslint-disable no-unused-vars */
'use strict';

var Utils = {

  isNumeric: function(number){
    return !isNaN(parseFloat(number) && isFinite(number));
  },

  semesterStart: function(datetime){
    if(datetime.month() < 3 ){
      return datetime.subtract(1, 'years').month(9).date(1);
    }else if(datetime.month() < 9){
        return datetime.month(3).date(1);
    }else{
      return datetime.month(9).date(1);
    }
  },

  semesterEnd: function(datetime){
    if(datetime.month() < 3){
      return datetime.month(3).date(1).subtract(1, 'days');
    }else if(datetime.month() < 9){
        return datetime.month(9).date(1).subtract(1, 'days');
    }else{
        return datetime.add(1, 'years').month(3).date(1).subtract(1, 'days');
    }
  },

  sexagesimalRaToDecimal: function(ra) {
    // algorithm: ra_decimal = 15 * ( hh + mm/60 + ss/(60 * 60) )
    /*                 (    hh     ):(     mm            ):  (   ss  ) */
    var m = ra.match('^([0-9]?[0-9]):([0-5]?[0-9][.0-9]*):?([.0-9]+)?$');
    if(m){
      var hh = parseInt(m[1], 10);
      var mm = parseFloat(m[2]);
      var ss = m[3] ? parseFloat(m[3]) : 0.0;
      if (hh >= 0 && hh <= 23 && mm >= 0 && mm < 60 && ss >= 0 && ss < 60){
        ra = (15.0 * (hh + mm / 60.0 + ss / (3600.0))).toFixed(10);
      }
    }
    return ra;
  },

  sexagesimalDecToDecimal: function(dec){
    // algorithm: dec_decimal = sign * ( dd + mm/60 + ss/(60 * 60) )
    /*                  ( +/-   ) (    dd     ):(     mm            ): (   ss   ) */
    var m = dec.match('^([+-])?([0-9]?[0-9]):([0-5]?[0-9][.0-9]*):?([.0-9]+)?$');
    if(m){
      var sign = m[1] === '-' ? -1 : 1;
      var dd = parseInt(m[2], 10);
      var mm = parseFloat(m[3]);
      var ss = m[4] ? parseFloat(m[4]) : 0.0;
      if (dd >= 0 && dd <= 90 && mm >= 0 && mm <= 59 && ss >= 0 && ss <= 59){
        dec = (sign * (dd + mm / 60.0 + ss / 3600.0)).toFixed(10);
      }
    }
    return dec;
  }
};

var QueryString = function () {
  var qString = {};
  var query = window.location.search.substring(1);
  var vars = query.split('&');
  for (var i = 0; i < vars.length; i++) {
    var pair = vars[i].split('=');
    if (typeof qString[pair[0]] === 'undefined') {
      qString[pair[0]] = decodeURIComponent(pair[1]);
    } else if (typeof qString[pair[0]] === 'string') {
      var arr = [qString[pair[0]], decodeURIComponent(pair[1])];
      qString[pair[0]] = arr;
    } else {
      qString[pair[0]].push(decodeURIComponent(pair[1]));
    }
  }
    return qString;
}();
