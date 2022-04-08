 pad = (num, size)  => {
    var s = num+"";
    while (s.length < size) s = "0" + s;
    return s;
}


$(document).ready(function() {
      $('#Smart_listing_table_body > tr').each(function() {
        var YEdate = new Date($(this).find('.YE').attr('value'));
        var shortMonth = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        console.log(YEdate)
        if (isNaN (YEdate) ) {
            $(this).find('.YE').text("N.A.");
        }
        else{
            $(this).find('.YE').text(pad(YEdate.getMonth()+1 , 2) +   " - " +   shortMonth[YEdate.getMonth()]);
            }
        })




  $("#search_text").on("keyup", function() {
    var value = $(this).val().toLowerCase();
    var header_value = $("#header_selector").val();
    $("#Smart_listing_table_body tr").filter(function() {
        if($("#header_selector").val() ==  "Search All field" ){
             $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);

        }
        else {
                var i ,tr , header_index
                header_index = $( "#" + $("#header_selector").val()).index()
                tr = $("tr")
                for (i = 0; i < tr.length; i++) {
                td = tr[i].getElementsByTagName("td")[header_index];
                if (td) {
                  txtValue = td.textContent || td.innerText;
                  if (txtValue.toLowerCase().indexOf(value) > -1) {
                    tr[i].style.display = "";
                  } else {
                    tr[i].style.display = "none";
                  }
                }
               }
           }
        });
  });
});
