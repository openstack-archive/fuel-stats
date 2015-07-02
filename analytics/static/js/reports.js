$(function() {
    var defaultDate = new Date(),
        reportUrl = '/api/v1/csv/';

    $( '#from' ).datepicker({
        defaultDate: '-1m',
        changeMonth: true,
        numberOfMonths: 3,
        dateFormat: "yy-mm-dd",
        onClose: function( selectedDate ) {
            $( '#to' ).datepicker( 'option', 'minDate', selectedDate );
        }
    });
    $( '#to' ).datepicker({
        changeMonth: true,
        numberOfMonths: 3,
        dateFormat: "yy-mm-dd",
        onClose: function( selectedDate ) {
            $( '#from' ).datepicker( 'option', 'maxDate', selectedDate );
        }
    });
    $('#to').datepicker('setDate',  defaultDate);
    defaultDate.setMonth(defaultDate.getMonth() - 1);
    $('#from').datepicker('setDate', defaultDate);

    $('.link').click(function(e) {
        e.preventDefault();
        url = reportUrl + $(this).attr('id') + '?from_date=' + $('#from').val() + '&to_date=' + $('#to').val();
        window.open(url);
    });
});
