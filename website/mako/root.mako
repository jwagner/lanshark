<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml"> 
	<head>
		<title>Lanshark - Lan filesharing tool</title>
        <link rel="stylesheet" type="text/css" href="/css/design.css" />
        <!-- Hack for stupid browsers -->
        <!--[if lte IE 6]>
            <link rel="stylesheet" type="text/css" href="/css/ie.css" />
        <![endif]-->
        <script type="text/javascript" src="/js/lanshark.js"></script>
	</head>
	<body>
        <div id="header">
            <strong>lanshark lan filesharing file sharing tool</strong>
            <ul id="navigation">
            % for name in self.navigation():
                <li class="${ name + ".html" == page and "active page" or "page"}">
                    <a href="/${dirpath}/${name}.html">${name}</a>
                </li>
            % endfor
            % for language in ('en', 'de'):
                <li class="language"><a href="/${language}/" title="${language}">
                    <img src="/images/${language}.png" alt="${language}" />
                </a></li>
            % endfor
            </ul>
        </div>
        <div id="content">
            ${self.body()}
        </div>
        <script type="text/javascript">
            var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
            document.write(unescape("%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E"));
        </script>
        <script type="text/javascript">
            var pageTracker = _gat._getTracker("UA-5205069-1");
            pageTracker._trackPageview();
        </script>
	</body>
</html>
