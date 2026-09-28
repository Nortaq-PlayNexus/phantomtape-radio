import pathlib, os
from playwright.sync_api import sync_playwright
EXE = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
url = os.environ["PT_URL"]
P = pathlib.Path("shots/_permtest.html")
P.write_text('<!doctype html><meta charset=utf-8><div id=log>boot</div>'
  '<iframe id=w width="100%" height=166 allow="autoplay" '
  'src="https://w.soundcloud.com/player/?url=' + url + '&visual=false"></iframe>'
  '<script src="https://w.soundcloud.com/player/api.js"></script><script>'
  'const log=(m)=>document.getElementById("log").textContent+="\\n"+m;'
  'const wd=SC.Widget(document.getElementById("w"));'
  'wd.bind(SC.Widget.Events.READY,()=>{log("READY");'
  ' wd.getDuration(d=>log("duration="+d+"ms ("+(d/1000).toFixed(1)+"s)"));'
  ' wd.getCurrentSound(s=>log("sound="+JSON.stringify(s).slice(0,120)));});'
  'wd.bind(SC.Widget.Events.ERROR,e=>log("ERR "+JSON.stringify(e)));'
  '</script>', encoding='utf-8')
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=EXE)
    pg=b.new_page(); pg.goto(P.resolve().as_uri()); pg.wait_for_timeout(9000)
    print("  permalink form test:")
    for l in pg.inner_text('#log').splitlines(): print('   ',l)
    b.close()
