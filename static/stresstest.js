$(document).ajaxError(function(e, xhr, settings, exception) {
    if (xhr.status == 404) {
        drawViz2(currentI - 1);
    }
});

var run_data = []
var currentI = 20;

function drawCharts(url) {
    $.getJSON(url, _draw);
    setTimeout(function() {drawCharts(url)}, 45000);
}

function _draw(data) {
    var dts = [];
    var x_label = "Interval";
    var y_label = "Requests";
    var dt = new google.visualization.DataTable();
    dt.addColumn("string", x_label);
    for (i = 0, l = data.length; i < l; i++) {
        dt.addColumn("number", y_label + " " + data[i].title + " " + data[i].start);
    }
    var rows = _get_rows(data);
    dt.addRows(rows);

    var options = {title: "Stress Test"};

    var chart = new google.visualization.LineChart(document.getElementById("visualization"));
    chart.draw(dt, options);
}

function _get_rows(data) {
    var i, j, l = data.length, current_row = null, max_interval = null;
    var rows = [];
    var first_row = ["0"];
    for (i = 0; i < l; i++) {
        first_row.push(0);
    }
    rows.push(first_row);

    for (i = 0; i < l; i++) {
        if (max_interval == null || data[i].data.length > max_interval) {
            max_interval = data[i].data.length;
        }
    }

    for (i = 0; i < max_interval; i++) {
        current_row = ["" + (i + 1)];
        for (j = 0; j < l; j ++) {
            if (data[j].data[i]) {
                current_row.push(data[j].data[i][1]);
            } else {
                current_row.push(null);
            }
        }
        rows.push(current_row);
    }
    return rows;
}

function drawViz2(num) {
    var i = 0;
    if (! num) {
        if (run_data[currentI] == null) {
            $.getJSON("requests_per_interval_" + currentI + ".json", 
                    function(data) {
                if (data) {
                    run_data[currentI] = data;
                }
                currentI++;
                drawViz2();
            });
        }
        return;
    }
    $.getJSON("requests_per_interval_" + num + ".json", function(res) {
        var i, j, k;
        var data = [];
        for (i = 0; i < 2; i++) {
            data[i] = new google.visualization.DataTable();
            data[i].addColumn("string", "Interval");
        }
        var maxRows = [];
        maxRows[0] = 0;
        maxRows[1] = res.length;

        var dataSet;

        for (i = 1; i < num; i++) {
            var colTitle = (run_data[i] && run_data[i][0]) ? run_data[i][0][1] + " " : "";
           
            dataSet = (i <= 12) ? 0 : 1;

            data[dataSet].addColumn("number", colTitle + "Run " + i);
            maxRows[dataSet] = (run_data[i] && run_data[i].length > maxRows[dataSet]) 
                ? run_data[i].length : maxRows[dataSet];

        }
        data[1].addColumn("number", res[0][1] + " Run " + num);
        maxRows[1] = (res.length > maxRows[1]) ? res.length : maxRows[1];

        for (dataSet = 0; dataSet < 2; dataSet++) {
            for (j = 1; j < maxRows[dataSet]; j++) {
                var row = [];
                var rows = []
                // Assemble the list of rows
                var startK = (dataSet) ? 13 : 0;
                var endK = (dataSet) ? num : 12;
                for (k = startK; k < endK; k++) {
                    rows.push((run_data[k] && run_data[k][j]) ? run_data[k][j] : []);
                }
                if (dataSet) {
                    rows.push((res[j]) ? res[j] : []);
                }

                // Collate into one row for data table.
                for (k = 0; k < rows.length; k++) {
                    if (! row[0]) {
                        // Set row label if not set
                        row[0] = rows[k][0];
                    }
                    // Set col value
                    row[k + 1] = rows[k][1];
                }
                data[dataSet].addRow(row);
            }
        }

        for (dataSet = 0; dataSet < 2; dataSet++) {
            var target = document.getElementById("visualization" + dataSet);
            var chart = new google.visualization.LineChart(target);
            chart.draw(data[dataSet], {curveType: "function",
                title: "Requests per interval - following webapp rebuild.",
                legend: "in",
                lineWidth: 0.75,
                pointSize: 0,
                fontSize: 10,
                width: 100 + Math.max(1100, 2 * maxRows[dataSet]), height: 500,
                chartArea: {left: 100, top: 100},
                hAxis: {title: "interval"},
                vAxis: {baseline: 0, title: "requests", minValue: 0}}
            );
        }

     });
}
