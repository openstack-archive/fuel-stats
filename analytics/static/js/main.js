requirejs.config({
    baseUrl: "js",
    urlArgs: '_=' + (new Date()).getTime(),
    paths: {
        jquery: 'libs/jquery',
        elasticsearch: 'libs/elasticsearch',
        d3: 'libs/d3',
        d3pie: 'libs/d3pie',
        d3tip: 'libs/index',
        nv: 'libs/nv.d3',
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