var tailwind = { config: {} };
var document = { 
    documentElement: { classList: { add: function(){} } },
    body: { getAttribute: function(){ return null; } },
    getElementById: function(){ return { classList: { add: function(){}, remove: function(){} }, innerText: '', style: {} }; },
    addEventListener: function(event, cb) { if(event === 'DOMContentLoaded') cb(); },
    querySelectorAll: function() { return []; }
};
var localStorage = { getItem: function(){ return null; } };
var window = {};
var lucide = { createIcons: function(){} };
var fetch = async function() { return { json: async function() { return []; } }; };
var setInterval = function(){};
var LightweightCharts = { createChart: function(){ return { addCandlestickSeries: function(){ return { setData: function(){} }; } }; } };
var TradingView = { widget: function(config){ console.log("TV Widget created:", config); return {}; } };


