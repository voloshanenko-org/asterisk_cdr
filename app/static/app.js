$(window).on('load', function(){
    if (window.location.pathname != "/login") {
        setControls();
        setToday();
        // Execute first SIP status check, which also will act as auth check
        checkSipStatus()
        checkAllOperatorsSipStatus()
    }
});

function checkAllOperatorsSipStatus() {
    $.getJSON($SCRIPT_ROOT + '/_all_sip_status', {
    }).done(function(data) {
        // Schedule next sip_status check in 20 seconds
        setTimeout(checkAllOperatorsSipStatus, 20*1000);

        if (!("error" in data)){
            var external_sip_lines_status = data.filter(function(item) {
                return /8[0-9][0-9]/.test(item["id"]) || /Telegroup/.test(item["id"]);
            }).sort(function(a, b) {
                return a.id - b.id;
            });
            var internal_sip_agents_status = data.filter(function(item) {
                return item["device_state"] != "Unavailable" && /9[0-9][0-9]/.test(item["id"]);
            }).sort(function(a, b) {
                return a.id - b.id;
            });

            updateSipstatusTable(external_sip_lines_status, internal_sip_agents_status);
        }

    }).fail(function(data){
        if (data.status != 500){
            window.location.replace("/login");
        }
    });
}

function checkSipStatus() {
    $.getJSON($SCRIPT_ROOT + '/_sip_status', {
    }).done(function(data) {
        // Schedule next sip_status check in 15 seconds
        setTimeout(checkSipStatus, 15*1000);

        if ("error" in data){
            status_title = "Offline"
            status_details = data["error"]
            status_dot_class = "dot dot-lg dot-danger"
        } else if ("status" in data){
            status_title = "Online"
            status_details = data["status"]
            if (status_details == "In use"){
                status_dot_class = "dot dot-lg dot-warning"
            }else if (status_details == "Not in use"){
                status_dot_class = "dot dot-lg dot-success"
            }
        }

        $("#sip_status_label").text(status_title);
        $("#sip_status_label").attr("title", status_details);
        $("#sip_status_dot").attr("class", status_dot_class);
        $("#sip_status_dot").attr("title", status_details);

    }).fail(function(data){
        if (data.status != 500){
            window.location.replace("/login");
        }
    });
}

function setControls(){
    $("#oneday_picker").datetimepicker({
        format: 'L',
        MaxDate: moment()
    });

    $("#date_start_picker").datetimepicker({
        format: 'L',
        MaxDate: moment()
    });

    $("#date_end_picker").datetimepicker({
        format: 'L',
        MaxDate: moment()
    });

    $("#time_start_picker").datetimepicker({
        format: 'HH:mm',
        stepping: 15
    });
    $("#time_end_picker").datetimepicker({
        format: 'HH:mm',
        stepping: 1,
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
        $('#time_end_picker').datetimepicker('minDate', moment(e.date).add(15, 'm').toDate());
    });
    $("#time_end_picker").on("change.datetimepicker", function (e) {
        $('#time_start_picker').datetimepicker('maxDate', moment(e.date).add(-15, 'm').toDate());
    });

    $("#customNumberCallTo").on("keyup", function (e){
        if (e.keyCode === 13) {
            e.preventDefault();
            initCall($("#customNumberCallTo").val());
        }
    });
};

function setLastHour(){
    $("#oneday_picker").datetimepicker('date', moment());
    $("#date_start_picker").datetimepicker('date', moment());
    $("#date_end_picker").datetimepicker('date', moment());

    var timeStart = moment().toDate();
    var timeEnd = moment().add(1, 'h').toDate();
    timeStart.setMinutes(0,0,0)
    timeEnd.setMinutes(0,0,0)
    $("#time_start_picker").datetimepicker('date', timeStart);
    $("#time_end_picker").datetimepicker('date', timeEnd);

    $('#oneday_radio').click()
    $('#hide_outgoing_missed_check').prop('checked', true);
    LoadCallsData()
}

function setToday(){
    $("#oneday_picker").datetimepicker('date', moment());
    $("#date_start_picker").datetimepicker('date', moment());
    $("#date_end_picker").datetimepicker('date', moment());

    var timeStart = moment().toDate();
    var timeEnd = moment().toDate();
    timeStart.setHours(0, 0,0,0)
    timeEnd.setHours(23, 59,59,0)
    $("#time_start_picker").datetimepicker('date', timeStart);
    $("#time_end_picker").datetimepicker('date', timeEnd);

    $('#oneday_radio').click()
    $('#hide_outgoing_missed_check').prop('checked', true);
    LoadCallsData()
}

function setYesterday(){
    $("#oneday_picker").datetimepicker('date', moment().subtract(1, 'days'));
    $("#date_start_picker").datetimepicker('date', moment());
    $("#date_end_picker").datetimepicker('date', moment());

    var timeStart = moment().subtract(1, 'days').toDate();
    var timeEnd = moment().subtract(1, 'days').toDate();
    timeStart.setHours(0, 0,0,0)
    timeEnd.setHours(23, 59,59,0)
    $("#time_start_picker").datetimepicker('date', timeStart);
    $("#time_end_picker").datetimepicker('date', timeEnd);

    $('#oneday_radio').click()
    $('#hide_outgoing_missed_check').prop('checked', true);
    LoadCallsData()
}

function setCurrentWeek(){
    // Order of date range important
    $("#date_end_picker").datetimepicker('date', moment());
    $("#date_start_picker").datetimepicker('date', moment().startOf('isoWeek'));

    $('#range_radio').click()
    $('#hide_outgoing_missed_check').prop('checked', true);
    LoadCallsData()
}

function setLastWeek(){
    $("#date_start_picker").datetimepicker('date', moment().subtract(1, 'weeks').startOf('isoWeek'));
    $("#date_end_picker").datetimepicker('date', moment().subtract(1, 'weeks').endOf('isoWeek'));

    $('#range_radio').click()
    $('#hide_outgoing_missed_check').prop('checked', true);
    LoadCallsData()
}

function LoadCallsData() {
    // Update data each 5 minutes
    //setTimeout(LoadCallsData, 5*1000);

    oneday_checked = $('#oneday_radio')[0].checked
    range_checked = $('#range_radio')[0].checked

    endpoint = "/_raw_data"

    if (oneday_checked) {
        var time_start = $("#time_start_picker").datetimepicker('date').format('HH:mm:00')
        var time_end = $("#time_end_picker").datetimepicker('date').format('HH:mm:00')
        var oneday =  $("#oneday_picker").datetimepicker('date').format('YYYY-MM-DD')

        // Handle the case for TempusDominos stupid selector
        if (time_end == "00:00:00"){
            time_end = "23:59:59"
        }
        var date_start = oneday + ' ' + time_start
        var date_end = oneday + ' ' + time_end
    }else if(range_checked){
        var date_start = $("#date_start_picker").datetimepicker('date').format('YYYY-MM-DD 00:00:00')
        var date_end = $("#date_end_picker").datetimepicker('date').format('YYYY-MM-DD 23:59:59')
    }

    $('#all-records-table').bootstrapTable('removeAll')
    $('#important-records-table').bootstrapTable('removeAll')

    //Show loading spinner
    $('#loadingspinner').modal('show');

    $.getJSON($SCRIPT_ROOT + endpoint, {
        date_start: date_start,
        date_end: date_end
    }).done(function(data) {
        GenerateTableData(data)
    }).fail(function(data){
        if (data.status != 200){
            error_message = "Error " + data.status + ". " + data.statusText
            setTimeout(hideSpinnerLoading, 600)
            setTimeout(showToastr("error", error_message), 700)
        }else{
            window.location.replace("/login");
        }
    });
};

function GenerateTableData(data){
    if("result" in data){
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

        var my_number = $("#username").attr("value")
        var my_records = data["result"].filter(function(item) {
            return (item["dst"] == my_number && item["direction"] == "Incoming") || (item["src"] == my_number && item["direction"] == "Outgoing");
        });

        updateTable(important_records, all_records, my_records)
    }else if ("error" in data){
        error_message = "Operational error. " + data["error"]
        setTimeout(hideSpinnerLoading, 600)
        setTimeout(showToastr("error", error_message), 700)
    }
}

function updateSipstatusTable(external_sip_lines_status, internal_sip_agents_status){

    var columns_sip_status = [
        {
            "field": "id",
            "title": "#",
            "formatter": "DeviceNumberFormatter",
            "halign": "center",
            "align": "center"
        },
        {
            "field": "device_state",
            "title": "Status",
            "formatter": "DeviceStateFormatter",
            "halign": "center",
            "align": "center"
        }
    ]

    $('#sip-status-external-records-table').bootstrapTable({
        columns: columns_sip_status,
        rowStyle: SipStatusrowStyle
    });
    $('#sip-status-external-records-table').bootstrapTable('load', external_sip_lines_status);

    $('#sip-status-internal-records-table').bootstrapTable({
        columns: columns_sip_status,
        rowStyle: SipStatusrowStyle
    });
    $('#sip-status-internal-records-table').bootstrapTable('load', internal_sip_agents_status);
};

function DeviceNumberFormatter(value, row){
    var status_dot_class
    if (/^9[0-9][0-9]$/.test(row.id)){
        device_id = row.id
        device_type = "sip"
    } else if (/^999[0-9][0-9]$/.test(row.id)) {
        device_id = row.id.substr(2)
        device_type = "webrtc"
    } else {
        device_id = row.id
        device_type = "other"
    }

    if (device_type == "webrtc") {
        type_icon = " <i class=\"fa fa-globe\" aria-hidden=\"true\" style=\"font-size:18px\"></i>"
    } else {
        type_icon = ""
    }
    return '<div id="sip_id_label">' + device_id + ' ' + type_icon +'</div>\n'
}

function DeviceStateFormatter(value, row){
    var status_dot_class
    if (row.device_state == "In use"){
        status_title = "In-Use"
        status_dot_class = "dot dot-lg dot-warning"
    } else if (row.device_state == "Not in use"){
        status_title = "Online"
        status_dot_class = "dot dot-lg dot-success"
    } else if (row.device_state == "Unavailable"){
        status_title = "Offline"
        status_dot_class = "dot dot-lg dot-danger"
    }
        return '<div id="sip_status_label">' + status_title + '</div>\n' +
           '<div id="sip_status_dot" class=\'' + status_dot_class +  '\'</div>'
}

function updateTable(important_records, all_records, my_records){

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
            "formatter": "CallSrcFormatter",
            "halign": "center",
            "align": "center",
            "sortable": true
        },
        {
            "field": "dst",
            "title": "To",
            "formatter": "CallDstFormatter",
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
            "field": "call_action",
            "title": "Call",
            "formatter": "CallActionFormatter",
            "halign": "center",
            "align": "center",
            "sortable": false
        }
    ]

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
            "formatter": "CallSrcFormatter",
            "halign": "center",
            "align": "center",
            "sortable": true
        },
        {
            "field": "dst",
            "title": "To",
            "formatter": "CallDstFormatter",
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
        // {
        //     "field": "record_file",
        //     "title": "Call record",
        //     "formatter": "CallRecordFileFormatter",
        //     "halign": "center",
        //     "align": "center",
        //     "sortable": true
        // },
        {
            "field": "call_action",
            "title": "Call",
            "formatter": "CallActionFormatter",
            "halign": "center",
            "align": "center",
            "sortable": false
        }
    ]

    $('#important-records-table').bootstrapTable({
        columns: columns_important,
        rowStyle: rowStyle,
        pageSize: 100,
        pageList: [100, 200, 500],
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

    $('#all-records-table').bootstrapTable({
        columns: columns_all,
        rowStyle: rowStyle,
        pageSize: 100,
        pageList: [100, 200, 500],
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

    $('#all-records-table').on('post-body.bs.table', function (e) {
        $('[data-toggle="popover"]').popover()
    })

    $('#all-records-table').bootstrapTable('load', all_records);


    $('#my-records-table').bootstrapTable({
        columns: columns_all,
        rowStyle: rowStyle,
        pageSize: 100,
        pageList: [100, 200, 500],
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

    $('#my-records-table').on('post-body.bs.table', function (e) {
        $('[data-toggle="popover"]').popover()
    })

    $('#my-records-table').bootstrapTable('load', my_records);

    //Hide loading spinner
    setTimeout(hideSpinnerLoading, 600)
    setTimeout(showToastr("success", "Report updated"), 700)
};

function validateCallNumber(call_num) {
    if (call_num == null || call_num == ""){
        error = "Phone number can't be empty!"
        return '{ "error": "' + error +'"}'
    }
    if (call_num.match(/^[0-9]+$/) == null){
        error = "Phone number can include ONLY digits!"
        return '{ "error": "' + error +'"}'
    }

    allowed_num_lentgh = ["3", "4", "6", "7", "10"]

    if (!allowed_num_lentgh.includes(call_num.length).toString()){
        error = "Phone number should include ONLY " + allowed_num_lentgh + " DIGITS"
        return '{ "error": "' + error +'"}'
    }

    return '{ "result": "validated"}'
}

function initCall(call_num){

    my_number = $("#username").attr("value")
    endpoint = "/_init_call"
    number_validated = JSON.parse(validateCallNumber(call_num))

    if ("result" in number_validated) {
        $.getJSON($SCRIPT_ROOT + endpoint, {
            dstnum: call_num
        }).done(function(data) {
            if ("error" in data){
                if (data["error"] == "OPERATOR_OFFLINE"){
                    toastr_type = "error"
                    toastr_message = "Operator " + my_number + " OFFLINE</br>Can't originate the call!"
                }else if(data["error"] == "OPERATOR_BUSY"){
                    toastr_type = "warning"
                    toastr_message = "Operator " + my_number + " BUSY</br>Finish previous call and try again!"
                }else{
                    toastr_type = "error"
                    toastr_message = "ERROR: " + data["error"] + "</br>Can't originate the call!"
                }
            } else if("result" in data) {
                toastr_type = "call_success"
                toastr_message = "Call to " + call_num + " ORIGINATED.<br> Please answer the call"
            }
            showToastr(toastr_type, toastr_message)
        }).fail(function(data){
            if (data.status != 200){
                error_message = "Error " + data.status + ". " + data.statusText
                showToastr("error", error_message)
            }else{
                window.location.replace("/login");
            }
        });
    } else if ("error" in number_validated){
        error_message = number_validated["error"]
        showToastr("warning", error_message)
    }
}

function showToastr(toastr_type, toastr_message){
    if (toastr_type=="call_success"){
        toastr.options = {
            "debug": false,
            "newestOnTop": true,
            "progressBar": true,
            "positionClass": "toast-top-right",
            "preventDuplicates": false,
            "onclick": null,
            "showDuration": "300",
            "hideDuration": "1000",
            "timeOut": "10000",
            "extendedTimeOut": "1000",
            "showEasing": "swing",
            "hideEasing": "linear",
            "showMethod": "fadeIn",
            "hideMethod": "fadeOut"
        }
    } else if (toastr_type=="success"){
        toastr.options = {
            "debug": false,
            "newestOnTop": true,
            "progressBar": true,
            "positionClass": "toast-top-right",
            "preventDuplicates": false,
            "onclick": null,
            "showDuration": "300",
            "hideDuration": "1000",
            "timeOut": "1000",
            "extendedTimeOut": "1000",
            "showEasing": "swing",
            "hideEasing": "linear",
            "showMethod": "fadeIn",
            "hideMethod": "fadeOut"
        }
    }else if(toastr_type=="error"){
        toastr.options = {
            "closeButton": true,
            "debug": false,
            "newestOnTop": true,
            "positionClass": "toast-top-right",
            "preventDuplicates": true,
            "onclick": null,
            "showDuration": "300",
            "hideDuration": "1000",
            "timeOut": "0",
            "extendedTimeOut": "0",
            "showEasing": "swing",
            "hideEasing": "linear",
            "showMethod": "fadeIn",
            "hideMethod": "fadeOut"
        }
    }else if (toastr_type=="warning") {
        toastr.options = {
            "debug": false,
            "newestOnTop": true,
            "progressBar": true,
            "positionClass": "toast-top-right",
            "preventDuplicates": true,
            "onclick": null,
            "showDuration": "300",
            "hideDuration": "1000",
            "timeOut": "5000",
            "extendedTimeOut": "1000",
            "showEasing": "swing",
            "hideEasing": "linear",
            "showMethod": "fadeIn",
            "hideMethod": "fadeOut"
        }
    }
    if (toastr_type == "call_success"){
        toastr_type = "success"
    }
    toastr[toastr_type](toastr_message)
};

function hideSpinnerLoading() {
    if ($('#loadingspinner').hasClass('show')){
        $('#loadingspinner').modal('hide');
    }else{
        $('#loadingspinner').on('shown.bs.modal', function (e) {
            $('#loadingspinner').modal('hide');
        })
    }
}

function doOnMsoNumberFormat(cell, row, col){
    var result = "";
    if (row > 0 && col == 2){
        result = "\\@";
    }
    return result;
}

function SipStatusrowStyle(row, index) {
    if (row.device_state == "In use"){
        css_class = "alert-warning"
    } else if (row.device_state == "Not in use") {
        css_class = "alert-success"
    } else if (row.device_state == "Unavailable"){
        css_class = "alert-danger"
    }

    return {
        classes: css_class,
        css: {"font-size": "11px", "padding": ".2rem", "overflow-x": "visible !important", "overflow-y": "visible !important"}
    };
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
        css_class = "alert-warning"
    } else {
        css_class = "alert-secondary"
    }

    return {
        classes: css_class,
        css: {"font-size": "13px", "padding": ".2rem", "overflow-x": "visible !important", "overflow-y": "visible !important"}
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
                'Before callback elapsed: ' + secondsToHms(row.callback.before_call)
            ].join('<br>')
    } else if ("missed" in row && (row.direction == "Outgoing" || row.direction == "Internal")){
        missed_calls = []
        for (call_index in row.missed){
            missed_call = [
                'Missed at: ' + row.missed[call_index].calldate,
                'By: ' + row.missed[call_index].src,
                'After call missed elapsed: ' + secondsToHms(row.missed[call_index].before_call)
            ].join('<br>')
            missed_calls.push(missed_call)
        }
        result["data-content"] = missed_calls.join('<hr>')
    }

    return result
}

function CallSrcFormatter(value, row){
    if (typeof(row.src) != "undefined"){
        if (/^9[0-9][0-9]$/.test(row.src)){
            device_id = row.src
            device_type = "sip"
        } else if (/^999[0-9][0-9]$/.test(row.src)) {
            device_id = row.src.substr(2)
            device_type = "webrtc"
        } else {
            device_id = row.src
            device_type = "other"
        }

        if (device_type == "webrtc") {
            type_icon = " <i class=\"fa fa-globe\" aria-hidden=\"true\" style=\"font-size:18px\"></i>"
        } else {
            type_icon = ""
        }
        return '<div id="sip_id_label">' + device_id + ' ' + type_icon +'</div>\n'
    }
}

function CallDstFormatter(value, row){
    if (typeof(row.dst) != "undefined") {
        if (/^9[0-9][0-9]$/.test(row.dst)){
            device_id = row.dst
            device_type = "sip"
        } else if (/^999[0-9][0-9]$/.test(row.dst)) {
            device_id = row.dst.substr(2)
            device_type = "webrtc"
        } else {
            device_id = row.dst
            device_type = "other"
        }

        if (device_type == "webrtc") {
            type_icon = " <i class=\"fa fa-globe\" aria-hidden=\"true\" style=\"font-size:18px\"></i>"
        } else {
            type_icon = ""
        }
        return '<div id="sip_id_label">' + device_id + ' ' + type_icon +'</div>\n'
    }
}

function CallDirectionFormatter(value, row) {
    var icon
    if (row.direction == "Incoming"){
        icon = "fa fa-sign-in"
    } else if (row.direction == "Outgoing"){
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

function CallActionFormatter(value, row){

    my_number = $("#username").attr("value")

    if (row.direction == "Incoming"){
        call_to_num = row.src
    }else if (row.direction == "Outgoing"){
        call_to_num = row.dst
    }

    if (call_to_num != null && call_to_num!=my_number){
        call_action_html =
            '<div class="dropdown">' +
            '  <button class="btn btn-success btn-sm dropdown-toggle" type="button" id="dropdownMenu" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">' +
            '  <i class="fa fa-phone" aria-hidden="true"></i>' +
            '  </button>' +
            '  <div class="dropdown-menu" aria-labelledby="dropdownMenu">' +
            '    <button class="dropdown-item btn-sm" type="button" onclick="initCall(\'' + call_to_num.trim() + '\')">Call to ' + call_to_num.trim() + '</button>' +
            '  </div>' +
            '</div>'
        return call_action_html
    }
}

function CallRecordFileFormatter(value, row) {
    if (row.record_file) {
        return "<div class='mw-100'><audio class='mw-100' src='" + row.record_file + "' controls></audio></div>"
    }
}

function secondsToHms(d) {
    d = Number(d);
    var h = Math.floor(d / 3600);
    var m = Math.floor(d % 3600 / 60);
    var s = Math.floor(d % 3600 % 60);

    var hDisplay = h > 0 ? h + "h:" : "";
    var mDisplay = m > 0 ? m + "m:" : "";
    var sDisplay = s + "s";
    return hDisplay + mDisplay + sDisplay;
}