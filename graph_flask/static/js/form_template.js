
     $(document).ready(() => {
        $('#survey_form').submit(() =>  {
            console.log('this');
            $("#submit").attr("disabled" , true);
            });

        $('#survey_form').change(()=> {

            $("#submit").removeAttr("disabled");

            });
        $('#attending').change(()=> {
            conso
            $("#submit").removeAttr("disabled");

            });

        });

