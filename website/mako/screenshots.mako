## vim: syntax=mako
<%
import os
from PIL import Image
# this is because it will be included at language level!
screenshots_dir = "htdocs/images/screenshots"
thumbs_dir = "htdocs/images/thumbs"
screenshots = sorted(os.listdir("htdocs/images/screenshots/"))
for screenshot in screenshots:
    path = os.path.join(screenshots_dir, screenshot)
    thumb = os.path.join(thumbs_dir, screenshot)
    if not os.path.exists(thumb)\
            or os.stat(thumb).st_mtime < os.stat(path).st_mtime:
        print "* Generating " + thumb
        im = Image.open(path)
        im.thumbnail((256, 230), Image.ANTIALIAS)
        im.save(thumb)
%>
% for screenshot in screenshots:
    <div class="screenshot">
    <a class="thickbox" rel="screenshots" href="/images/screenshots/${screenshot}" >
        <img class="reflect rheight25" src="/images/thumbs/${screenshot}" alt="Screebshot" />
    </a>
    </div>
% endfor
<div class="clear"></div>
