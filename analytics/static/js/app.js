
define(
[
    'jquery',
    'd3',
    'd3pie',
    'd3tip',
    'nv',
    'elasticsearch'
],
function($, d3, D3pie, d3tip, nv, elasticsearch) {
    'use strict';

    var statuses = ['operational', 'error'];

    var elasticSearchHost = function() {
            return {
                host: {
                    protocol: $(location).attr('protocol'),
                    host: $(location).attr('hostname')
                }
            };
        };

    var statsPage = function() {
        installationsCount();
        environmentsCount();
        distributionOfInstallations();
        nodesDistributionChart();
        hypervisorDistributionChart();
        osesDistributionChart();
    };

    var installationsCount = function() {
        var client = new elasticsearch.Client(elasticSearchHost());
         client.count({
            index: 'fuel',
            type: 'structure',
            body: {
               query: {match_all: {}}
            }
            }).then(function(resp) {
                $('#installations-count').html(resp.count);
            });
    };

    var environmentsCount = function() {
        var client = new elasticsearch.Client(elasticSearchHost());
         client.search({
            index: 'fuel',
            type: 'structure',
            body: {
               aggs: {
                    clusters: {
                        nested: {
                            path: 'clusters'
                        },
                       aggs: {
                           statuses: {
                                terms: {field: 'status'}
                            }
                        }
                    }
                }
            }
            }).then(function(resp) {
                var rawData = resp.aggregations.clusters.statuses.buckets,
                    total = resp.aggregations.clusters.doc_count,
                    colors = {
                        error: '#FF7372',
                        operational: '#51851A',
                        new: '#999999',
                        deployment: '#2783C0',
                        remove: '#000000',
                        update: '#775575',
                        update_error: '#F5007B',
                        stopped: '#FFB014'
                    },
                    chartData = [];
                $.each(rawData, function(key, value) {
                    chartData.push({label: value.key, value: value.doc_count, color: colors[value.key]});
                });
                $('#environments-count').html(total);
                var data = [{
                    key: 'Distribution of environments by statuses',
                    values: chartData
                    }];

                nv.addGraph(function() {
                    var chart = nv.models.discreteBarChart()
                        .x(function(d) { return d.label;})
                        .y(function(d) { return d.value;})
                        .margin({top: 30})
                        .transitionDuration(350);

                    chart.xAxis
                        .axisLabel('Statuses');

                    chart.yAxis
                        .axisLabel('Environments')
                        .axisLabelDistance(50)
                        .tickFormat(d3.format('d'));

                    chart.tooltipContent(function(key, x, y) {
                        return '<h3>Status: "' + x + '"</h3>' + '<p>' + parseInt(y) + ' environments</p>';
                    });

                    d3.select('#clusters-distribution svg')
                        .datum(data)
                        .call(chart);

                    nv.utils.windowResize(chart.update);

                    return chart;
                });
            });
    };

    var distributionOfInstallations = function() {
        var client = new elasticsearch.Client(elasticSearchHost());
         client.search({
            index: 'fuel',
            size: 0,
            body: {
                 aggs: {
                    envs_distribution: {
                        histogram: {
                            field: 'clusters_num',
                            interval: 1
                        }
                    }
                }
            }
            }).then(function(resp) {
                var rawData = resp.aggregations.envs_distribution.buckets,
                    chartData = [];
                $.each(rawData, function(key, value) {
                    chartData.push({label: value.key, value: value.doc_count});
                });
                var data = [{
                    color: '#1DA489',
                    values: chartData
                    }];

                nv.addGraph(function() {
                    var chart = nv.models.multiBarChart()
                        .x(function(d) { return d.label;})
                        .y(function(d) { return d.value;})
                        .margin({top: 30})
                        .transitionDuration(350)
                        .reduceXTicks(false)   //If 'false', every single x-axis tick label will be rendered.
                        .rotateLabels(0)      //Angle to rotate x-axis labels.
                        .showControls(false)   //Allow user to switch between 'Grouped' and 'Stacked' mode.
                        .showLegend(false)
                        .groupSpacing(0.5);    //Distance between each group of bars.

                    chart.xAxis
                        .axisLabel('Environments count');

                    chart.yAxis
                        .axisLabel('Installations')
                        .axisLabelDistance(50)
                        .tickFormat(d3.format('d'));

                    chart.tooltipContent(function(key, x, y) {
                        return '<h3>' + parseInt(y) + ' installations</h3>' + '<p>with ' + x + ' environments</p>';
                    });

                    d3.select('#env-distribution svg')
                        .datum(data)
                        .call(chart);

                    nv.utils.windowResize(chart.update);

                    return chart;
                });
            });
    };

    var nodesDistributionChart = function() {
        var client = new elasticsearch.Client(elasticSearchHost()),
            ranges = [
                  {from: 1, to: 5},
                  {from: 5, to: 10},
                  {from: 10, to: 20},
                  {from: 20, to: 50},
                  {from: 50, to: 100},
                  {from: 100}
            ];

        client.search({
            index: 'fuel',
            type: 'structure',
            size: 0,
            body: {
                aggs: {
                    clusters: {
                        nested: {
                            path: 'clusters'
                        },
                        aggs: {
                            statuses: {
                                filter: {
                                    terms:   {status: statuses}
                                },
                                aggs: {
                                    nodes_ranges: {
                                        range: {
                                            field: 'nodes_num',
                                            ranges: ranges
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            }).then(function(resp) {
                var rawData = resp.aggregations.clusters.statuses.nodes_ranges.buckets,
                    total = resp.aggregations.clusters.statuses.doc_count,
                    chartData = [];
                $('#count-nodes-distribution').html(total);
                $.each(rawData, function(key, value) {
                    var labelText = '',
                        labelData = value.key.split('-');
                    $.each(labelData, function(key, value) {
                        if (value) {
                            if (key == labelData.length - 1) labelText += (value == '*' ? '+' : '-' + parseInt(value));
                        } else {
                            labelText += parseInt(value);
                        }
                    });
                    chartData.push({label: labelText, value: value.doc_count});
                });

                var data = [{
                    key: 'Environment size distribution by number of nodes',
                    color: '#1DA489',
                    values: chartData
                    }];

                nv.addGraph(function() {
                    var chart = nv.models.multiBarChart()
                        .x(function(d) { return d.label;})
                        .y(function(d) { return d.value;})
                        .margin({top: 30})
                        .transitionDuration(350)
                        .reduceXTicks(false)   //If 'false', every single x-axis tick label will be rendered.
                        .rotateLabels(0)      //Angle to rotate x-axis labels.
                        .showControls(false)   //Allow user to switch between 'Grouped' and 'Stacked' mode.
                        .groupSpacing(0.2);    //Distance between each group of bars.

                    chart.xAxis
                        .axisLabel('Number of nodes');

                    chart.yAxis
                        .axisLabel('Environments')
                        .axisLabelDistance(50)
                        .tickFormat(d3.format('d'));

                    chart.tooltipContent(function(key, x, y) {
                        return '<h3>' + x + ' nodes</h3>' + '<p>' + parseInt(y) + '</p>';
                    });

                    d3.select('#nodes-distribution svg')
                        .datum(data)
                        .call(chart);

                    nv.utils.windowResize(chart.update);

                    return chart;
                });
            });
    };

    var hypervisorDistributionChart = function() {
        var client = new elasticsearch.Client(elasticSearchHost());
        client.search({
            size: 0,
            index: 'fuel',
            type: 'structure',
            body: {
                aggs: {
                    clusters: {
                        nested: {
                            path: 'clusters'
                        },
                        aggs: {
                            statuses: {
                                filter: {
                                    terms:   {status: statuses}
                                },
                                aggs: {
                                    attributes: {
                                        nested: {
                                            path: 'clusters.attributes'
                                        },
                                        aggs: {
                                            libvirt_types: {
                                                terms: {
                                                    field: 'libvirt_type'
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            }).then(function(resp) {
                var rawData = resp.aggregations.clusters.statuses.attributes.libvirt_types.buckets,
                    total = resp.aggregations.clusters.statuses.attributes.doc_count,
                    totalСounted = 0,
                    chartData = [];
                $.each(rawData, function(key, value) {
                    chartData.push({label: value.key, value: value.doc_count});
                    totalСounted  += value.doc_count;
                });
                var unknownHypervisorsCount = total - totalСounted;
                if (unknownHypervisorsCount) {
                    chartData.push({label: 'unknown', value: unknownHypervisorsCount});
                }
                $('#count-releases-distribution').html(total);
                new D3pie("releases-distribution", {
                    header: {
                        title: {
                            text: 'Distribution of deployed hypervisor',
                            fontSize: 15
                        },
                        location: 'top-left',
                        titleSubtitlePadding: 9
                    },
                    size: {
                        canvasWidth: 400,
                        canvasHeight: 300,
                        pieInnerRadius: '40%',
                        pieOuterRadius: '60%'
                    },
                    labels: {
                        outer: {
                            format: 'label-value2',
                            pieDistance: 10
                        },
                        mainLabel: {
                            fontSize: 14
                        },
                        percentage: {
                            color: '#ffffff',
                            decimalPlaces: 2
                        },
                        value: {
                            color: '#adadad',
                            fontSize: 11
                        },
                        lines: {
                            enabled: true
                        }
                    },
                    data: {
                        content: chartData
                    },
                    tooltips: {
                        enabled: true,
                        type: 'placeholder',
                        string: '{label}: {value}, {percentage}%',
                        styles: {
                            borderRadius: 3,
                            fontSize: 12,
                            padding: 6
                        }
                    }
                });
            });
    };

    var osesDistributionChart = function() {
        var client = new elasticsearch.Client(elasticSearchHost());
        client.search({
            size: 0,
            index: 'fuel',
            type: 'structure',
            body: {
                aggs: {
                    clusters: {
                        nested: {
                            path: 'clusters'
                        },
                        aggs: {
                            statuses: {
                                filter: {
                                    terms:   {status: statuses}
                                },
                                aggs: {
                                    release: {
                                        nested: {
                                            path: 'clusters.release'
                                        },

                                        aggs: {
                                            oses: {
                                                terms: {
                                                    field: 'os'
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            }).then(function(resp) {
                var rawData = resp.aggregations.clusters.statuses.release.oses.buckets,
                    total =  resp.aggregations.clusters.statuses.doc_count,
                    chartData = [];
                $('#count-distribution-of-oses').html(total);
                $.each(rawData, function(key, value) {
                    chartData.push({label: value.key, value: value.doc_count});
                });
                new D3pie("distribution-of-oses", {
                    header: {
                        title: {
                            text: 'Distribution of deployed operating system',
                            fontSize: 15
                        },
                        location: 'top-left',
                        titleSubtitlePadding: 9
                    },
                    size: {
                        canvasWidth: 400,
                        canvasHeight: 300,
                        pieInnerRadius: '40%',
                        pieOuterRadius: '60%'
                    },
                    labels: {
                        outer: {
                            format: 'label-value2',
                            pieDistance: 10
                        },
                        mainLabel: {
                            fontSize: 14
                        },
                        percentage: {
                            color: '#ffffff',
                            decimalPlaces: 2
                        },
                        value: {
                            color: '#adadad',
                            fontSize: 11
                        },
                        lines: {
                            enabled: true
                        }
                    },
                    data: {
                        content: chartData
                    },
                    tooltips: {
                        enabled: true,
                        type: 'placeholder',
                        string: '{label}: {value}, {percentage}%',
                        styles: {
                            borderRadius: 3,
                            fontSize: 12,
                            padding: 6
                        }
                    }
                });
            });
    };

    return statsPage();
});
