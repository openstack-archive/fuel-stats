
define(
[
    'jquery',
    'd3',
    'd3pie',
    'd3tip',
    'nv'
],
function($, d3, D3pie, d3tip, nv) {
    'use strict';

    var releases = [
        {name: 'All', filter: ''},
        {name: '6.0 Technical Preview', filter: '6.0-techpreview'},
        {name: '6.0 GA', filter: '6.0'},
        {name: '6.1', filter: '6.1'},
        {name: '7.0', filter: '7.0'},
        {name: '8.0', filter: '8.0'},
        {name: '9.0', filter: '9.0'}
    ];
    var currentRelease = releases[0].filter;

    var releaseFilter = $('#release-filter');
    releases.forEach(function(release) {
        releaseFilter.append($('<option/>', {text: release.name, value: release.filter}));
    });
    releaseFilter.on('change', function(e) {
        var newRelease = $(e.currentTarget).val();
        currentRelease = newRelease;
        statsPage();
    });

    var statsPage = function() {
        var url = '/api/v1/json/report/installations';
        var data = {};

        if (currentRelease) {
            data['release'] = currentRelease;
        }

        jQuery.get(url, data, function(resp) {
            installationsCount(resp);
            environmentsCount(resp);
            distributionOfInstallations(resp);
            nodesDistributionChart(resp);
            hypervisorDistributionChart(resp);
            osesDistributionChart(resp);
        });

    };

    var installationsCount = function(resp) {
        $('#installations-count').html(resp.installations.count);
    };

    var environmentsCount = function(resp) {
        $('#environments-count').html(resp.environments.count);

        var colors = [
            {status: 'new', code: '#999999'},
            {status: 'operational', code: '#51851A'},
            {status: 'error', code: '#FF7372'},
            {status: 'deployment', code: '#2783C0'},
            {status: 'remove', code: '#000000'},
            {status: 'stopped', code: '#FFB014'},
            {status: 'update', code: '#775575'},
            {status: 'update_error', code: '#F5007B'}
        ];
        var chartData = [];

        $.each(colors, function(index, color) {
            var in_status = resp.environments.statuses[color.status];
            if (in_status) {
                chartData.push({label: color.status, value: in_status, color: color.code});
            }
        });

        var data = [{
            key: 'Distribution of environments by statuses',
            values: chartData
            }];

        nv.addGraph(function() {
            var chart = nv.models.discreteBarChart()
                .x(function(d) { return d.label;})
                .y(function(d) { return d.value;})
                .margin({top: 30, bottom: 60})
                .staggerLabels(true)
                .transitionDuration(350);

            chart.xAxis
                .axisLabel('Statuses');

            chart.yAxis
                .axisLabel('Environments')
                .axisLabelDistance(30)
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
    };

    var distributionOfInstallations = function(resp) {
        var chartData = [];
        $.each(resp.installations.environments_num, function(key, value) {
            chartData.push({label: key, value: value});
        });
        var data = [{
            color: '#1DA489',
            values: chartData
            }];

        nv.addGraph(function() {
            var chart = nv.models.multiBarChart()
                .x(function(d) { return d.label;})
                .y(function(d) { return d.value;})
                .margin({top: 30, bottom: 60})
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
                .axisLabelDistance(30)
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
    };

    var nodesDistributionChart = function(resp) {
        var total = resp.environments.operable_envs_count;
        var ranges = [
            {from: 1, to: 5, count: 0},
            {from: 5, to: 10, count: 0},
            {from: 10, to: 20, count: 0},
            {from: 20, to: 50, count: 0},
            {from: 50, to: 100, count: 0},
            {from: 100, to: null, count: 0}
        ];
        var chartData = [];

        $('#count-nodes-distribution').html(total);
        $.each(resp.environments.nodes_num, function(nodes_num, count) {
            $.each(ranges, function(index, range) {
                var num = parseInt(nodes_num);
                if (
                    num >= range.from &&
                    (num < range.to || range.to == null)
                ) {
                    range.count += count;
                }
            });
        });

        $.each(ranges, function(index, range) {
            var labelText = range.from + (range.to == null ? '+' : '-' + range.to);
            chartData.push({label: labelText, value: range.count});
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
                .axisLabelDistance(30)
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
    };

    var hypervisorDistributionChart = function(resp) {
        var totalСounted = 0,
            total = resp.environments.operable_envs_count,
            chartData = [];
        $.each(resp.environments.hypervisors_num, function(hypervisor, count) {
            chartData.push({label: hypervisor, value: count});
            totalСounted  += count;
        });
        var unknownHypervisorsCount = total - totalСounted;
        if (unknownHypervisorsCount) {
            chartData.push({label: 'unknown', value: unknownHypervisorsCount});
        }
        $('#count-releases-distribution').html(total);
        $('#releases-distribution').html('');
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
                canvasWidth: 330,
                canvasHeight: 300,
                pieInnerRadius: '40%',
                pieOuterRadius: '55%'
            },
            labels: {
                outer: {
                    format: 'label-value2',
                    pieDistance: 10
                },
                inner: {
                    format: "percentage",
                    hideWhenLessThanPercentage: 5
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
                string: '{label}: {value} pcs, {percentage}%',
                styles: {
                    borderRadius: 3,
                    fontSize: 12,
                    padding: 6
                }
            }
        });
    };

    var osesDistributionChart = function(resp) {
        var total =  resp.environments.operable_envs_count,
            chartData = [];
        $('#count-distribution-of-oses').html(total);
        $.each(resp.environments.oses_num, function(os, count) {
            chartData.push({label: os, value: count});
        });
        $('#distribution-of-oses').html('');
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
                canvasWidth: 330,
                canvasHeight: 300,
                pieInnerRadius: '40%',
                pieOuterRadius: '55%'
            },
            labels: {
                outer: {
                    format: 'label-value2',
                    pieDistance: 10
                },
                inner: {
                    format: "percentage",
                    hideWhenLessThanPercentage: 5
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
                string: '{label}: {value} pcs, {percentage}%',
                styles: {
                    borderRadius: 3,
                    fontSize: 12,
                    padding: 6
                }
            }
        });
    };

    return statsPage();
});
