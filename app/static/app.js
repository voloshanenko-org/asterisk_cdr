$(window).on('load', function(){
    if (window.location.pathname != "/login") {
        setControls();
        setToday();
        // Schedule first auth check in 1 minute after load
        setTimeout(checkAuth, 60*1000);
    }
});

function checkAuth() {
    $.getJSON($SCRIPT_ROOT + '/_is_authorized', {
    }).done(function(data) {
        // Schedule next auth check in 1 minute
        setTimeout(checkAuth, 60*1000);
    }).fail(function(data){
        window.location.replace("/login");
    });
}

function setControls(){

    // $('#method2_radio').click()
    //
    // $('#method1_radio').on("click", function() {
    //     LoadCallsData()
    // });
    //
    // $('#method2_radio').on("click", function() {
    //     LoadCallsData()
    // });

    $("#oneday_picker").datetimepicker({
        format: 'L',
        MaxDate: '0'
    });

    $("#date_start_picker").datetimepicker({
        format: 'L',
        MaxDate: '0'
    });

    $("#date_end_picker").datetimepicker({
        format: 'L',
        MaxDate: '0'
    });

    $("#time_start_picker").datetimepicker({
        format: 'HH:mm',
        stepping: 30
    });
    $("#time_end_picker").datetimepicker({
        format: 'HH:mm',
        stepping: 30
    });

    $('#oneday_radio').on("click", function() {
        $(".period_controls").hide()
        $(".oneday_controls").show()
    });

    $('#range_radio').on("click", function() {
        $(".oneday_controls").hide()
        $(".period_controls").show()
    });

    $("#date_start_picker").on("change.datetimepicker", function (e) {
        $('#date_end_picker').datetimepicker('minDate', e.date);
    });
    $("#date_end_picker").on("change.datetimepicker", function (e) {
        $('#date_start_picker').datetimepicker('maxDate', e.date);
    });

    $("#time_start_picker").on("change.datetimepicker", function (e) {
        $('#time_end_picker').datetimepicker('minDate', moment(e.date).add(30, 'm').toDate());
    });
    $("#time_end_picker").on("change.datetimepicker", function (e) {
        $('#time_start_picker').datetimepicker('maxDate', moment(e.date).add(-30, 'm').toDate());
    });

};

function setToday(){
    $("#oneday_picker").datetimepicker('date', moment());
    $("#date_start_picker").datetimepicker('date', moment());
    $("#date_end_picker").datetimepicker('date', moment());

    $("#time_start_picker").datetimepicker('date', "07:00");
    $("#time_end_picker").datetimepicker('date', "20:00");

    $('#oneday_radio').click()
    $('#hide_outgoing_missed_check').prop('checked', true);
    LoadCallsData()
}

function setYesterday(){
    $("#oneday_picker").datetimepicker('date', moment().subtract(1, 'days'));
    $("#date_start_picker").datetimepicker('date', moment());
    $("#date_end_picker").datetimepicker('date', moment());

    $("#time_start_picker").datetimepicker('date', "07:00");
    $("#time_end_picker").datetimepicker('date', "20:00");

    $('#oneday_radio').click()
    $('#hide_outgoing_missed_check').prop('checked', true);
    LoadCallsData()
}

function setCurrentWeek(){
    $("#oneday_picker").datetimepicker('date', moment());
    $("#date_start_picker").datetimepicker('date', moment().startOf('isoWeek'));
    $("#date_end_picker").datetimepicker('date', moment());

    $("#time_start_picker").datetimepicker('date', "07:00");
    $("#time_end_picker").datetimepicker('date', "20:00");

    $('#range_radio').click()
    $('#hide_outgoing_missed_check').prop('checked', true);
    LoadCallsData()
}

function setLastWeek(){
    $("#oneday_picker").datetimepicker('date', moment());
    $("#date_start_picker").datetimepicker('date', moment().subtract(1, 'weeks').startOf('isoWeek'));
    $("#date_end_picker").datetimepicker('date', moment().subtract(1, 'weeks').endOf('isoWeek'));

    $("#time_start_picker").datetimepicker('date', "07:00");
    $("#time_end_picker").datetimepicker('date', "20:00");

    $('#range_radio').click()
    $('#hide_outgoing_missed_check').prop('checked', true);
    LoadCallsData()
}

function LoadCallsData() {
    oneday_checked = $('#oneday_radio')[0].checked
    range_checked = $('#range_radio')[0].checked

    endpoint = "/_raw_data"

    if (oneday_checked) {
        var time_start = $("#time_start_picker").datetimepicker('date').format('HH:mm:00')
        var time_end = $("#time_end_picker").datetimepicker('date').format('HH:mm:00')
        var oneday =  $("#oneday_picker").datetimepicker('date').format('YYYY-MM-DD')

        var date_start = oneday + ' ' + time_start
        var date_end = oneday + ' ' + time_end
    }else if(range_checked){
        var date_start = $("#date_start_picker").datetimepicker('date').format('YYYY-MM-DD 00:00:00')
        var date_end = $("#date_end_picker").datetimepicker('date').format('YYYY-MM-DD 23:59:59')
    }

    $('#all-records-table').bootstrapTable('removeAll')
    $('#important-records-table').bootstrapTable('removeAll')

    $.getJSON($SCRIPT_ROOT + endpoint, {
        date_start: date_start,
        date_end: date_end
    }).done(function(data) {
        GenerateTableData(data)
    }).fail(function(data){
        if (data.status != 200){
            $("#alertbox .modal-title").text(data.statusText);
            $("#alertbox .modal-body").text(data.status + ': Please contact support to fix it!');
            $('#alertbox').modal();
        }else{
            window.location.replace("/login");
        }
    });
};

function GenerateTableData(data){

    if("result" in data){
        $('#alertbox').modal('hide');

        var all_records = data["result"]
        hide_outgoing_missed = $('#hide_outgoing_missed_check')[0].checked

        if (hide_outgoing_missed){
            var important_records = data["result"].filter(function(item) {
                return !(item["disposition"] == "ANSWERED" && item['direction'] == "Incoming")
                    && !(item["direction"] == "Outgoing" || item["direction"] == "Internal");
            });
        }else{
            var important_records = data["result"].filter(function(item) {
                return !(item["disposition"] == "ANSWERED");
            });
        }
        updateTable(important_records, all_records)
    }else if ("error" in data){
        $("#alertbox .modal-title").text("DB Operational Error");
        $("#alertbox .modal-body").text(data["error"]);
        $('#alertbox').modal();
    }
}

function updateTable(important_records, all_records){

    var columns_all = [
        {
            "field": "calldate",
            "title": "Date",
            "halign": "center",
            "align": "center",
            "sortable": true
        },
        {
            "field": "direction",
            "title": "Direction",
            "formatter": "CallDirectionFormatter",
            "halign": "center",
            "align": "center",
            "sortable": true
        },
        {
            "field": "src",
            "title": "From",
            "halign": "center",
            "align": "center",
            "sortable": true
        },
        {
            "field": "dst",
            "title": "To",
            "halign": "center",
            "align": "center",
            "sortable": true
        },
        {
            "field": "disposition",
            "title": "Status",
            "formatter": "CallDispositionFormatter",
            "halign": "center",
            "align": "center",
            "sortable": true
        },
        {
            "field": "waiting_duration",
            "title": "Wait, sec",
            "halign": "center",
            "align": "center",
            "sortable": true
        },
        {
            "field": "talking_duration",
            "title": "Talk, sec",
            "halign": "center",
            "align": "center",
            "sortable": true
        },
        {
            "field": "record_file",
            "title": "Call record",
            "formatter": "CallRecordFileFormatter",
            "halign": "center",
            "align": "center",
            "sortable": true
        }
    ]
    var columns_important = [
        {
            "field": "calldate",
            "title": "Date",
            "halign": "center",
            "align": "center",
            "sortable": true
        },
        {
            "field": "direction",
            "title": "Direction",
            "formatter": "CallDirectionFormatter",
            "halign": "center",
            "align": "center",
            "sortable": true
        },
        {
            "field": "src",
            "title": "From",
            "halign": "center",
            "align": "center",
            "sortable": true
        },
        {
            "field": "dst",
            "title": "To",
            "halign": "center",
            "align": "center",
            "sortable": true
        },
        {
            "field": "disposition",
            "title": "Status",
            "formatter": "CallDispositionFormatter",
            "halign": "center",
            "align": "center",
            "sortable": true
        },
        {
            "field": "waiting_duration",
            "title": "Wait, sec",
            "halign": "center",
            "align": "center",
            "sortable": true
        }
    ]

    $('#all-records-table').bootstrapTable({
        columns: columns_all,
        rowStyle: rowStyle,
        pageSize: 25,
        rowAttributes: rowAttributes,
        exportDataType: "all",
        exportTypes: ['excel', 'pdf'],
        exportOptions:{
            fileName: 'call_report',
            worksheetName: 'Call Report',
            tableName: 'call_report',
            mso: {
                fileFormat: 'xlshtml',
                onMsoNumberFormat: doOnMsoNumberFormat
            }
        }
     });

    $('#all-records-table').on('all.bs.table', function (e) {
        $('[data-toggle="popover"]').popover()
    })

    $('#all-records-table').bootstrapTable('load', all_records);


    $('#important-records-table').bootstrapTable({
        columns: columns_important,
        rowStyle: rowStyle,
        pageSize: 25,
        rowAttributes: rowAttributes,
        exportDataType: "all",
        exportTypes: ['excel', 'pdf'],
        exportOptions:{
            fileName: 'call_report',
            worksheetName: 'Call Report',
            tableName: 'call_report',
            mso: {
                fileFormat: 'xlshtml',
                onMsoNumberFormat: doOnMsoNumberFormat
            }
        }
    });

    $('#important-records-table').on('all.bs.table', function (e) {
        $('[data-toggle="popover"]').popover()
    })

    $('#important-records-table').bootstrapTable('load', important_records);

    $("#loadingspinner").modal('hide');
};

function doOnMsoNumberFormat(cell, row, col){
    var result = "";
    if (row > 0 && col == 2){
        result = "\\@";
    }
    return result;
}

function rowStyle(row, index) {
    if (row.disposition == "ANSWERED"){
        if ("missed" in row){
            css_class = "alert-primary"
        }else{
            css_class = "alert-success"
        }
    } else if (row.disposition == "MISSED") {
        if ("callback" in row) {
            css_class = "alert-primary"
        } else {
            css_class = "alert-danger"
        }
    } else if (row.disposition == "NO ANSWER") {
        css_class = "alert alert-warning"
    } else {
        css_class = "alert-secondary"
    }

    return {
        classes: css_class,
        css: {"font-size": "13px", "padding": ".2rem"}
    };
}

function rowAttributes(row, index) {
    var result = {
        'data-toggle': 'popover',
        'data-placement': 'bottom',
        'data-trigger': 'hover',
        'data-html': true
    }

    if ("callback" in row && row.direction == "Incoming" && row.disposition == "MISSED") {
        result["data-content"] = [
                'Callback at: ' + row.callback.calldate,
                'By: ' + row.callback.src,
                'Before callback elapsed: ' + row.callback.before_call + ' seconds'
            ].join('<br>')
    } else if ("missed" in row && (row.direction == "Outgoing" || row.direction == "Internal")){
        result["data-content"] = [
                'Missed at: ' + row.missed.calldate,
                'By: ' + row.missed.src,
                'After call missed elapsed: ' + row.missed.before_call + ' seconds'
            ].join('<br>')
    }

    result["data-content"]

    return result
}

function CallDirectionFormatter(value, row) {
    var icon
    if (row.direction == "Incoming"){
        icon = "fa fa-sign-in"
    } else if (row.direction == "out"){
        icon = "fa fa-sign-out"
    }
    return '<i class="' + icon + '" aria-hidden="true" style="font-size:20px"></i> ' + row.direction
}

function CallDispositionFormatter(value, row) {
    var icon
    if (row.disposition == "NO ANSWER" || row.disposition == "MISSED"){
        icon = "fa fa-reply-all"
    }else if (row.disposition != "ANSWERED"){
        icon = "fa fa-exclamation-triangle"
    }else {
        icon = ''
    }
    return '<i class="' + icon + '" aria-hidden="true" style="font-size:20px"></i> ' + value
}


function CallRecordFileFormatter(value, row) {
    if (row.record_file) {
        return "<div class='mw-100'><audio class='mw-100' src='" + row.record_file + "' controls></audio></div>"
    }
}