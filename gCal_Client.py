from gCal import get_gCal_events
from datetime import date, datetime

print(datetime.now())

#today_events = []
today_events = get_gCal_events()
#print(today_events)

print(str(len(today_events))+" Events returned")
if len(today_events) > 0:
    event_total = len(today_events)
    n = 0
    while n < event_total:
        next_event = today_events[n]
        #print(today_events[0])
        next_start = next_event.cal_start
        print(next_event.cal_start.strftime("%A, %b %-d"))
        #print(next_event.cal_stop)
        print(next_event.cal_time+" "+next_event.cal_summary)
        #print(next_event.cal_summary)
        
        n+=1

    #print(gevent)