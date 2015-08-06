requirejs.config({
    baseUrl: "js",
    waitSeconds: 60,
    urlArgs: '_=' + (new Date()).getTime(),
    paths: {
        jquery: 'libs/jquery/js/jquery',
        elasticsearch: 'libs/elasticsearch/js/elasticsearch',
        d3: 'libs/d3/js/d3',
        d3pie: 'libs/d3pie/js/d3pie',
        d3tip: 'libs/d3-tip/js/index',
        nv: 'libs/nvd3/js/nv.d3',
        app: 'app'
    },
    shim: {
        d3tip: {
            deps: ['d3'],
            exports: 'd3tip'
        },
        d3pie: {
            deps: ['d3'],
            exports: 'd3pie'
        },
        nv: {
            deps: ['d3'],
            exports: 'nv'
        }
    }
});

require(['app']);
