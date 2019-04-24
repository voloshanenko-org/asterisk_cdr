$(window).on('load', function(){
    if (window.location.pathname != "/login") {
        setControls();
        setToday();
    }
});

function setControls(){

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

    $.getJSON($SCRIPT_ROOT + '/_raw_data', {
        date_start: date_start,
        date_end: date_end
    }, function(data) {
        GenerateTableData(data)
    });
};

function GenerateTableData(data){

    if("result" in data){
        $('#sqlalertbox').modal('hide');

        var all_records = data["result"]
        hide_outgoing_missed = $('#hide_outgoing_missed_check')[0].checked

        if (hide_outgoing_missed){
            var important_records = data["result"].filter(function(item) {
                return !(item["disposition"] == "ANSWERED" && item['direction'] == "in") && !(item["direction"] == "out");
            });
        }else{
            var important_records = data["result"].filter(function(item) {
                return !(item["disposition"] == "ANSWERED");
            });
        }
        updateTable(important_records, all_records)
    }else if ("error" in data){
        $("#sqlalertbox .modal-title").text("DB Operational Error");
        $("#sqlalertbox .modal-body").text(data["error"]);
        $('#sqlalertbox').modal();
    }
}

function updateTable(important_records, all_records){

    var columns = [
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
            "sortable": true
        },
        {
            "field": "dst",
            "title": "To",
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
            "title": "Waiting, sec",
            "halign": "center",
            "align": "center",
            "sortable": true
        },
        {
            "field": "talking_duration",
            "title": "Talking, sec",
            "halign": "center",
            "align": "center",
            "sortable": true
        }
    ]

    $('#all-records-table').bootstrapTable({
        columns: columns,
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
        columns: columns,
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
    } else if (row.disposition == "NO ANSWER"){
        if ("callback" in row){
            css_class = "alert-primary"
        }else{
            css_class = "alert-danger"
        }
    } else {
        css_class = "alert-secondary"
    }

    return {
        classes: css_class,
        css: {"font-size": "13px", "padding": ".2rem"}
    };
}

function rowAttributes(row, index) {
    var result = ""

    if ("callback" in row && row.direction == "in" && row.disposition == "NO ANSWER") {
        result = {
            'data-toggle': 'popover',
            'data-placement': 'bottom',
            'data-trigger': 'hover',
            'data-content': [
                'Callback at: ' + row.callback.calldate,
                'By: ' + row.callback.src,
                'Before callback elapsed: ' + row.callback.before_call + ' seconds',
            ].join(', ')
        }
    } else if ("missed" in row && row.direction == "out"){
        result = {
            'data-toggle': 'popover',
            'data-placement': 'bottom',
            'data-trigger': 'hover',
            'data-content': [
                'Missed at: ' + row.missed.calldate,
                'By: ' + row.missed.src,
                'After call missed elapsed: ' + row.missed.before_call + ' seconds',
            ].join(', ')
        }
    }

    return result
}

function CallDirectionFormatter(value, row) {
    var icon
    if (row.direction == "in"){
        icon = "fa fa-sign-in"
        direction = "Incoming"
    } else if (row.direction == "out"){
        icon = "fa fa-sign-out"
        direction = "Outgoing"
    }
    return '<i class="' + icon + '" aria-hidden="true" style="font-size:20px"></i> ' + direction
}

function CallDispositionFormatter(value, row) {
    var icon
    if (row.disposition == "NO ANSWER"){
        icon = "fa fa-reply-all"
    }else if (row.disposition != "ANSWERED"){
        icon = "fa fa-exclamation-triangle"
    }else {
        icon = ''
    }

    return '<i class="' + icon + '" aria-hidden="true" style="font-size:20px"></i> ' + value
}