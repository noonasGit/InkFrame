from garbage import get_garbage_status
from datetime import date, datetime, timedelta
# importing the modules
from urllib.request import urlopen

url = "http://olympus.realpython.org/profiles/aphrodite"
page = urlopen(url)
html_bytes = page.read()
html = html_bytes.decode("utf-8")
print(html)
title_index = html.find("<title>")
start_index = title_index + len("<title>")
end_index = html.find("</title>")
title = html[start_index:end_index]
print(title)




deg = "this is "+"8\N{DEGREE SIGN}"

print(deg)

g_data = get_garbage_status()

Tomorrow_Days = datetime.now() + timedelta(days=1)
print(Tomorrow_Days)



print("Dumpster: ",g_data.dumpster)
print("Prepare for dumpster: ",g_data.dumpster_prepapre)

print("landfill: ",g_data.landfill)
print("Prepare for landfill: ",g_data.landfill_prepapre)

print("recycle: ",g_data.recycle)
print("Prepapre for recycle: ",g_data.recycle_prepare)

print("x-mas: ",g_data.xmas_tree)

is_garbage = (g_data.landfill, g_data.landfill_prepapre, g_data.recycle, g_data.recycle_prepare, g_data.xmas_tree)

if 1 in is_garbage :
 print("there is garbage")

currenttime = datetime.now() 
print("It is ",currenttime.strftime("%H:%M")," now")
comparetime = currenttime.replace(hour=18, minute=0)

print("Compared to",comparetime.strftime("%H:%M")," now")

if currenttime > comparetime :
 print("Time to take bins in!")
