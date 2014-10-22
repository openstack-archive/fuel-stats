
//$(function() {

define(
[
    'd3',
    'd3pie',
    'd3tip',
    'nv'
],
function(d3, d3pie, d3tip, nv) {
    'use strict';
    
    var statsPage = function() {
        activityChart();
        nodesDistributionChart();
        virtualizationDistributionChart();
        pieChart();
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
          } , 
          { 
            "label" : "aug 2014" ,
            "value" : -17
          } , 
          { 
            "label" : "jul 2014" ,
            "value" : -6
          } , 
          { 
            "label" : "jun 2014" ,
            "value" : -2
          } , 
          {
            "label" : "may 2014" ,
            "value" : -10
          } , 
          { 
            "label" : "apr 2014" ,
            "value" : -5
          } , 
          { 
            "label" : "mar 2014" ,
            "value" : 0
          } , 
          {
            "label" : "feb 2014" ,
            "value" : -1
          } , 
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
          } , 
          { 
            "label" : "aug 2014" ,
            "value" : 20
          } , 
          { 
            "label" : "jul 2014" ,
            "value" : 34
          } , 
          { 
            "label" : "jun 2014" ,
            "value" : 20
          } , 
          {
            "label" : "may 2014" ,
            "value" : 10
          } , 
          { 
            "label" : "apr 2014" ,
            "value" : 2
          } , 
          { 
            "label" : "mar 2014" ,
            "value" : 1
          } , 
          {
            "label" : "feb 2014" ,
            "value" : 2
          } , 
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

    var nodesDistributionChart = function() {
         var pie = new d3pie("nodes-distribution", {
            size: {
                "canvasWidth": 400,
                "canvasHeight": 300,
                "pieInnerRadius": "43%",
                "pieOuterRadius": "70%"
            },
            labels: {
                "outer": {
                    "pieDistance": 10
                },
                "inner": {
                    "hideWhenLessThanPercentage": 3
                },
                "mainLabel": {
                    "fontSize": 11
                },
                "percentage": {
                    "color": "#ffffff",
                    "decimalPlaces": 2
                },
                "value": {
                    "color": "#adadad",
                    "fontSize": 11
                },
                "lines": {
                    "enabled": true
                }
            },
            data: {
                content: [
                    { label: "1-10 nodes", value: 264131 },
                    { label: "10-50 nodes", value: 218812 },
                    { label: "> 50 nodes", value: 157618 },
                ]
            }
        });
    }

    var virtualizationDistributionChart = function() {
        var data = [{
            "key": "Number of Installations",
            "color": "#1DA489",
            "values": [{
                        'label': "KVM",
                        'value': 56
                    }, {
                        'label': "QEMU",
                        'value': 68
                    }, {
                        'label': "vCenter",
                        'value': 42
                    }]
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
    }

    var pieChart = function() {
        var pie = new d3pie("distribution-of-oses", {
            size: {
                "canvasWidth": 400,
                "canvasHeight": 300,
                "pieInnerRadius": "43%",
                "pieOuterRadius": "70%"
            },
            data: {
                content: [
                    { label: "Ubuntu", value: 264131 },
                    { label: "Centos", value: 218812 }
                ]
            }
        });
    };

    // Nodes distribution elasticsearch requiest
    /*
    var client = new elasticsearch.Client();
    client.search({
        size: 0,
        body: {
            "aggs": {
                     "nodes_distribution": {
                        "histogram": {
                            "field": "allocated_nodes_num",
                            "interval": 1
                        }
                    }
            }
        }
    }).then(function (resp) {
        var data = resp.aggregations.nodes_distribution.buckets,
            margin = {top: 40, right: 20, bottom: 50, left: 30},
            width = 300 - margin.left - margin.right,
            height = 240 - margin.top - margin.bottom,
            paddingBottom = 3,
            x = d3.scale.ordinal()
                .rangeRoundBands([0, width], .3),
            y = d3.scale.linear()
                .range([height, 0]),
            xAxis = function() {
                return d3.svg.axis()
                    .scale(x)
                    .orient("bottom")
            },
            yAxis  = function() {
                return d3.svg.axis()
                    .scale(y)
                    .orient("left")
                    .ticks(2)
            },
            tip = d3.tip()
                .attr('class', 'd3-tip')
                .html(function(d) {
                    return "<strong>Number of Installation:</strong> <span>" + d.doc_count + "</span>";
                }),
            svg = d3.select("#nodes-distribution").append("svg")
                .attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom)
                .append("g")
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
        svg.call(tip);

        x.domain(data.map(function(d) { return d.key; }));
        y.domain([0, d3.max(data, function(d) { return d.doc_count; })]);

        svg.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + height + ")")
            .call(xAxis())
            .append("text")
            .attr("x", 150 )
            .attr("y", 30 )
            .style("text-anchor", "middle")
            .text("Number of Nodes in the Environment");

        svg.append("g")
            .attr("class", "y axis")
            .call(yAxis())
            .append("text")
            .attr("y", -15)
            .attr("x", 100)
            .style("text-anchor", "end") 
            .text("Number of Installation");

        svg.append("g")         
            .attr("class", "grid")
            .attr("transform", "translate(0," + height + ")")
            .call(xAxis()
                .tickSize(-height, 0, 0)
                .tickFormat(""));

        svg.append("g")         
            .attr("class", "grid")
            .call(yAxis()
                .tickSize(-width, 0, 0)
                .tickFormat(""));

        svg.selectAll(".bar")
            .data(data)
            .enter().append("rect")
            .attr("class", "bar")
            .attr("x", function(d) { return x(d.key); })
            .attr("width", x.rangeBand())
            .attr("y", function(d) { return y(d.doc_count); })
            .attr("height", function(d) { return height - y(d.doc_count) - paddingBottom; })
            .on('mouseover', tip.show)
            .on('mouseout', tip.hide);
    */

    return statsPage();

});
