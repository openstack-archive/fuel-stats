requirejs.config({
    baseUrl: "js",
    urlArgs: '_=' + (new Date()).getTime(),
    paths: {
        jquery: 'jquery-2.1.1.min',
        elasticsearch: 'elasticsearch.min',
        d3: 'd3.v3.min',
        d3pie: 'd3pie.min',
        d3tip: 'd3.tip.v0.6.3',
        nv: 'nv.d3.min',
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