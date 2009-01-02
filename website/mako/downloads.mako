<%
import math, os
from glob import glob

def byteformat(n, units=('B', 'KiB', 'MiB', 'GiB', 'TiB')):
    """Format a number of bytes"""
    i = n and int(math.log(n, 1024)) or 0
    if i >= len(units):
        i = len(units)-1
    n /= 1024.0**i
    return "%.2f %s" % (n, units[i])

%>

<%def name="list_files(pattern, description)">
<ul>
% for name in sorted(glob('htdocs/downloads/' + pattern)):
<% basename = os.path.basename(name) %>
    <li><a href="/downloads/${basename}">${basename} (${description})</a>
        ${byteformat(os.path.getsize(name))}
    </li>
% endfor
</ul>
</%def>

<h3>GNU/Linux <img src="../images/tux_commons.png" alt="Tux" height="32"></h3>
${list_files("*.tar.bz2", "Sourcecode")}

<h3>Microsoft Windows XP/Vista</h3>
${list_files("*.exe", "Windows Installer")}
${list_files("*.zip", "Windows Portable Zip")}
