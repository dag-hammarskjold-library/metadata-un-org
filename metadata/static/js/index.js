$( document ).ready(function(){

    // enable tooltips
    $(function () {
        $('[data-toggle="tooltip"]').tooltip()
    });

    /* if lang is not set in uri,
     get the browser language
     and set lang parmeter
     default to en 
    */
    var lang = getParameterByName('lang');
    if ( ! lang ){
        var pref_lang = get_browser_language();
        switch(pref_lang){
            case 'ar':
                setDefaultLang('ar');
                break;
            case 'zh':
                setDefaultLang('zh');
                break;
            case 'en':
                setDefaultLang('en');
                break;
            case 'fr':
                setDefaultLang('fr');
                break;
            case 'ru':
                setDefaultLang('ru');
                break;
            case 'es':
                setDefaultLang('es');
                break;
            default:
                setDefaultLang('en');
                break;
            }
        }

    /* autocomplete functionality
     want to grab characters typed into search form
     and pass them via ajax to the search method
     if search method returns results, add
     to select area under form
    */
    var xhr;
    var lang = getParameterByName('lang');
    xhr = $('#autocomplete').autocomplete({
        minLength:2,   
        delay:500,
        source: function( request, response ){
            xhr = $.ajax({
                url: "autocomplete?lang=" + lang + "&q=" + request.term,
                dataType: "json",
                cache: false,
                success: function(data) {
                    console.log(data);
                    response($.map(data, function(item) {
                        return {
                            label: item.pref_label,
                            uri: item.uri
                        };
                    }));
                }
            });
        }, select: function(event, ui) {
            lang = getParameterByName('lang');
            console.log(ui.item);
            window.location = ui.item.uri + "?lang=" + lang;
        }
    });

    /* when click on a language
        translate whole page
    */
    $(".lang").on("click", function(e){
        e.preventDefault();
        var currentURL = window.location.href;
        var lang = getParameterByName('lang');
        var prefLang = this.id;
        var disabled = $(this).hasClass('disabled');
        //console.log(disabled);
        var searchParams = new URLSearchParams(window.location.search);
        searchParams.set("lang", prefLang);
        if (disabled == false) {
            window.location.search = searchParams.toString();
        }
        
    });

    // show API dialog
    $("#getNode").on("click", function(e){
        $("#show-dl-options").modal("show");
    });
});

function getParameterByName(name) {
    var url = window.location.href;
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}

function get_browser_language(){
    var lang_locale = navigator.language;
    var parts = lang_locale.split('-');
    return parts[0];
}

function setDefaultLang(lang){
    // var href = document.getElementById(lang);
    // console.log(href);
    // href.style.fontWeight = 'bold';
    var searchParams = new URLSearchParams(window.location.search);
    searchParams.set("lang", lang);
    window.location.search = searchParams.toString();
}
