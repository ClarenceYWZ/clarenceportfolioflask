
    $(document).ready(function(){
      $(".form-control").on("keyup", function(event) {
        if (event.keyCode === 13) {
            event.preventDefault();
            $(".form-check-input").click();
        }

        });
    });


     $(document).ready(() => {
        $('#Mcst_no').change(() =>  {
            var mcst = $("#Mcst_no").val()
            var index = $("#Mcst_no").find(':selected')[0].id.substring(20,5) ;
            $("#Project_name").val($("#Mcst_no").val());

            $('.bank_option').remove();
            var bankaccountrequest = new XMLHttpRequest();
            bankaccountrequest.open('GET', '/get_mcst_bank/' + mcst);
            bankaccountrequest.onload = ()=> {
            if (bankaccountrequest.status >=200 && bankaccountrequest.status < 400)
                {
                var bankdata=  JSON.parse(bankaccountrequest.responseText);
                console.log(bankdata);
                renderbankoption(bankdata.bank_account);

                }
            }

            bankaccountrequest.send();
            let renderbankoption  = data => {
            var htmlstring="";
            for (i = 0; i < data.length; i++){

                $('#bank_select').append($('<option>',
                    {
                        value: data[i].bank_accounts_details.short_name,
                        text : data[i].bank_accounts_details.short_name,
                        class: 'bank_option'
                    }
                ))
            }
        }

    });
    $('.btn').on("click", ()=>{

        $('.loading_bar').append(
            '<div class="spinner-border text-success" role="status">',
            '<span class="ml-2"> File Generating, please wait... </span>','</div>',
            '</div>'

        )

         $('.loading_bar').addClass('alert alert-info');

        }
    );


        $('#Project_name').change(() =>  {
            var index = $("#Project_name").find(':selected')[0].id.substring(20,9) ;
            $("#Mcst_no").val($("#mcst_"+index ).val());
        });


    });

