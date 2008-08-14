<%
import math, os
def byteformat(n, units=('B', 'KiB', 'MiB', 'GiB', 'TiB')):
    """Format a number of bytes"""
    i = n and int(math.log(n, 1024)) or 0
    if i >= len(units):
        i = len(units)-1
    n /= 1024.0**i
    return "%.2f %s" % (n, units[i])
%>
<ul>
% for file_ in sorted(os.listdir('htdocs/downloads/')):
<%
    name = file_
    for ending, description in (
            ('.tar.bz2', ' (Source)'),
            ('.deb', ' (Debian/Ubuntu)'),
            ('.rpm', ' (Redhat/Fedora/SuSe)'),
            ('.zip', ' (Windows Portable)'),
            ('.exe', ' (Windows Installer)')):
        if name.endswith(ending):
            name += description
%>
    <li><a href="/downloads/${file_}">${name}</a>
        ${byteformat(os.path.getsize('htdocs/downloads/' + file_))}
    </li>
% endfor
</ul>
