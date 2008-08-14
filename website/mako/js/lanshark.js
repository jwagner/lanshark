<%include file="jquery.mako" />
<%include file="thickbox.mako" />
if(!$.browser.msie)
{
<%include file="reflection.mako" />
}
language = navigator.language ? navigator.language : navigator.browserLanguage;
if(window.location.pathname == '/' && language.indexOf("de") > -1)
{
    window.location.href = 'de/';
}
