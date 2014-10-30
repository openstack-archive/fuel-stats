
define(
[
    'jquery',
    'd3',
    'd3pie',
    'd3tip',
    'nv',
    'elasticsearch'
],
function(jquery, d3, d3pie, d3tip, nv, elasticsearch) {
    'use strict';

    var elasticSearchHost = function() {
        return {
            host: {
                protocol: $(location).attr('protocol'),
                host: $(location).attr('hostname')
            }
        };
    }

    var statsPage = function() {
        activityChart();
        nodesDistributionChart();
        virtualizationDistributionChart();
        osesDistributionChart();
    }

    var nodesDistributionChart = function() {
        var client = new elasticsearch.Client(elasticSearchHost());
        client.search({
            size: 0,
            body: {
                "aggs": {
                    "nodes_ranges": {
                        "range": {
                            "field": "allocated_nodes_num",
                            "ranges": [
                                {"to": 5},
                                {"from": 5, "to": 10},
                                {"from": 10, "to": 30},
                                {"from": 30}
                            ]
                        }
                    }
                }
            }
            }).then(function (resp) {
                var rawData = resp.aggregations.nodes_ranges.buckets,
                    chartData = [];
                $.each(rawData, function(key, value) {
                    chartData.push({label: value.key, value: value.doc_count})
                });
                var pie = new d3pie("nodes-distribution", {
                    size: {
                        "canvasWidth": 400,
                        "canvasHeight": 300,
                        "pieInnerRadius": "40%",
                        "pieOuterRadius": "60%"
                    },
                    labels: {
                        "outer": {
                            "pieDistance": 10
                        },
                        "mainLabel": {
                            "fontSize": 14
                        },
                        "percentage": {
                            "color": "#ffffff",
                            "decimalPlaces": 2
                        }
                    },
                    data: {
                        content: chartData
                    }
                });
            });
        // BAR CHART Request for Nodes distribution
        // body: {
        //     "aggs": {
        //         "nodes_distribution": {
        //             "histogram": {
        //                 "field": "allocated_nodes_num",
        //                 "interval": 1
        //             }
        //         }
        //     }
        // }
        // }).then(function (resp) {
        //     var data = resp.aggregations.nodes_distribution.buckets;
        //     console.log(data);
        // });
    }

    var activityChart = function() {
        var data = [
        {
        key: 'Users becames inactive',
        color: '#d62728',
        values: [
          {
            "label" : "sep 2014" ,
            "value" : 0
          },
          {
            "label" : "aug 2014" ,
            "value" : -17
          },
          {
            "label" : "jul 2014" ,
            "value" : -6
          },
          {
            "label" : "jun 2014" ,
            "value" : -2
          },
          {
            "label" : "may 2014" ,
            "value" : -10
          },
          {
            "label" : "apr 2014" ,
            "value" : -5
          },
          {
            "label" : "mar 2014" ,
            "value" : 0
          },
          {
            "label" : "feb 2014" ,
            "value" : -1
          },
          {
            "label" : "jan 2014" ,
            "value" : 0
          }
        ]
        },
        {
        key: 'New user activation',
        color: '#1f77b4',
        values: [
          {
            "label" : "sep 2014" ,
            "value" : 80
          },
          { 
            "label" : "aug 2014" ,
            "value" : 20
          }, 
          { 
            "label" : "jul 2014" ,
            "value" : 34
          },
          { 
            "label" : "jun 2014" ,
            "value" : 20
          },
          {
            "label" : "may 2014" ,
            "value" : 10
          },
          {
            "label" : "apr 2014" ,
            "value" : 2
          },
          {
            "label" : "mar 2014" ,
            "value" : 1
          },
          {
            "label" : "feb 2014" ,
            "value" : 2
          },
          {
            "label" : "jan 2014" ,
            "value" : 0
          }
        ]
        }];

        nv.addGraph(function() {
            var chart = nv.models.multiBarHorizontalChart()
                .x(function(d) { return d.label })
                .y(function(d) { return d.value })
                .margin({top: 30, right: 20, bottom: 50, left: 175})
                .valueFormat(d3.format('d'))
                .showValues(true)           //Show bar value next to each bar.
                .tooltips(true)             //Show tooltips on hover.
                .transitionDuration(350)
                .showControls(true);        //Allow user to switch between "Grouped" and "Stacked" mode.

            chart.yAxis
                .tickFormat(d3.format('d'));

            d3.select('#activity-chart svg')
                .datum(data)
                .call(chart);

            nv.utils.windowResize(chart.update);

            return chart;
        });
    }

    var virtualizationDistributionChart = function() {
        var client = new elasticsearch.Client(elasticSearchHost());
        client.search({
            size: 0,
            body: {
                "aggs": {
                    "clusters": {
                        "nested": {
                            "path": "clusters"
                        },
                        "aggs": {
                            "attributes": {
                                "nested": {
                                    "path": "clusters.attributes"
                                },
                                "aggs": {
                                    "libvirt_types": {
                                        "terms": {
                                            "field": "libvirt_type"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            }).then(function (resp) {
                var rawData = resp.aggregations.clusters.attributes.libvirt_types.buckets,
                    chartData = [];
                $.each(rawData, function(key, value) {
                    chartData.push({label: value.key, value: value.doc_count})
                });
                var data = [{
                    "key": "Number of Environments",
                    "color": "#1DA489",
                    "values": chartData
                    }];
                nv.addGraph(function() {
                    var chart = nv.models.multiBarHorizontalChart()
                        .x(function(d) { return d.label })
                        .y(function(d) { return d.value })
                        .valueFormat(d3.format('d'))
                        .margin({top: 40, right: 20, bottom: 0, left: 50})
                        .showValues(true)           //Show bar value next to each bar.
                        .tooltips(true)             //Show tooltips on hover.
                        .transitionDuration(350)
                        .showControls(false);        //Allow user to switch between "Grouped" and "Stacked" mode.

                    chart.yAxis
                        .tickFormat(d3.format(',.2f'));

                    nv.utils.windowResize(chart.update);

                    d3.select('#releases-distribution svg')
                        .datum(data)
                        .call(chart);
                    return chart;
                  });
            });
    }

    var osesDistributionChart = function() {
        var client = new elasticsearch.Client(elasticSearchHost());
        client.search({
            size: 0,
            body: {
                "aggs": {
                    "clusters": {
                        "nested": {
                            "path": "clusters"
                        },
                        "aggs": {
                            "release": {
                                "nested": {
                                    "path": "clusters.release"
                                },
                                "aggs": {
                                    "oses": {
                                        "terms": {
                                            "field": "os"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            }).then(function (resp) {
                var rawData = resp.aggregations.clusters.release.oses.buckets,
                    chartData = [];
                $.each(rawData, function(key, value) {
                    chartData.push({label: value.key, value: value.doc_count})
                });
                var pie = new d3pie("distribution-of-oses", {
                    size: {
                        "canvasWidth": 400,
                        "canvasHeight": 300,
                        "pieInnerRadius": "40%",
                        "pieOuterRadius": "60%"
                    },
                    labels: {
                        "outer": {
                            "pieDistance": 10
                        },
                        "mainLabel": {
                            "fontSize": 14
                        },
                        "percentage": {
                            "color": "#ffffff",
                            "decimalPlaces": 2
                        }
                    },
                    data: {
                        "sortOrder": "random",
                        content: chartData
                    }
                });
            });
    };

    return statsPage();

});
