#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
from datetime import datetime, date, timedelta
picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'icons')
weatherdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'icons/weather')
fontdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fonts')
libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
from waveshare_epd import epd7in5b_V2
import time
from PIL import Image,ImageDraw,ImageFont
import traceback
from openweather import current_weather, tomorrow_weather
from generic_transit import next_transit
from transit import gettransitdepartures
from getquote import quoteoftheday, addquotetofile
from getquote_file import quotefromfile
from garbage_schedule import get_garbage_status, get_garbage_config_data
from pi_info import getRAMinfo, getDiskSpace, getCPUtemperature, getCPUuse

import configparser

from dataclasses import dataclass

@dataclass
class screen:
    width : int
    height : int
    middle_w : int
    middle_h : int
    quote_max : int
    reminder_max : int
    use_red : int
    refresh_rate_min : int
    clean_screen : int
    sleep_hour :int
    wake_hour : int

@dataclass
class dashboard:
    show_weather: int
    show_weather_details : int
    show_transit : int
    show_quote : int
    quote : str

@dataclass
class hourglass:
    day : int
    hour : int
    curenttime : int
    currentday : int
    live_cutin_hour : int
    live_cutout_hour : int
    last_refresh : str


@dataclass
class transit:
    use_live : str
    api_key : str
    transit1_icon :str
    transit1_name :str
    transit1_id : str
    transit1_stop : str
    transit2_icon :str
    transit2_name :str
    transit2_id : str
    transit2_stop : str

@dataclass
class performance:
    usedram : int
    freeram : int
    ramincrease : int
    previousram : int



def createDash():
    dash_config = dict()
    dash_config = get_dashboard_config_data("dashboard.ini")
    
    transit.use_live = dash_config['transit-use-live-id'] 
    transit.api_key = dash_config['transit-api-key-id']
    transit.transit1_name = dash_config['transit_name_1-id']
    transit.transit1_id = dash_config['transit_id_1-id']
    transit.transit1_stop = dash_config['transit_stop_1-id']
    transit.transit1_icon = dash_config['transit_icon_1-id']

    transit.transit2_name = dash_config['transit_name_2-id']
    transit.transit2_id = dash_config['transit_id_2-id']
    transit.transit2_stop = dash_config['transit_stop_2-id']
    transit.transit2_icon = dash_config['transit_icon_2-id']

    hourglass.live_cutin_hour = int(dash_config['transit_live_cutin_hour-id'])
    hourglass.live_cutout_hour = int(dash_config['transit_live_cutout_hour-id'])

    screen.refresh_rate_min = int(dash_config['refresh-rate-min-id'])
    screen.sleep_hour = int(dash_config['screen_sleep_hour-id'])
    screen.wake_hour = int(dash_config['screen_wake_hour-id'])

    if dash_config['use_red-id'] == "TRUE":
        screen.use_red = 1
    else:
        screen.use_red = 0

    if dash_config['show_weather-id'] == "TRUE":
        dashboard.show_weather = 1
    else : 
        dashboard.show_weather = 0
    if dash_config['show_weather_details-id'] == "TRUE":
        dashboard.show_weather_details = 1
    else : 
        dashboard.show_weather_details = 0
    if dash_config['show_transit-id'] == "TRUE":
        dashboard.show_transit = 1
    else : 
        dashboard.show_transit = 0
    if dash_config['show_quote-id'] == "TRUE":
        dashboard.show_quote = 1
    else : 
        dashboard.show_quote = 0




    try:

        epd = epd7in5b_V2.EPD()
        epd.init()
        #epd.Clear()
        screen.height = epd.height
        screen.width = epd.width
        screen.middle_w = screen.width/2
        screen.middle_h = screen.height/2
    except IOError as e:
        print(e)

    except KeyboardInterrupt:    
        print("ctrl + c:")
        epd7in5b_V2.epdconfig.module_exit()
        exit()

    # Check if we should clear the E-ink (daily)
    if screen.clean_screen < int(datetime.now().strftime("%d")):
        print("Time to clean the screen (once daily)")
        epd.Clear()
        screen.clean_screen = int(datetime.now().strftime("%d"))

    ####################
    ###################
    #######
    #######
    ############
    ############
    #######
    #######
    #######


    #DayTitle=ImageFont.truetype("fonts/Mont-Heavy-Bold.otf", 62)
    DayTitle = ImageFont.truetype("fonts/SF-Compact-Rounded-Bold.ttf", 62)
    SFMonth = ImageFont.truetype("fonts/SF-Compact-Rounded-Bold.ttf", 14)
    SFDate = ImageFont.truetype("fonts/SF-Compact-Rounded-Bold.ttf", 42)

    SFToday_temp = ImageFont.truetype("fonts/SF-Compact-Rounded-Bold.ttf",64)
    SFToday_cond = ImageFont.truetype("fonts/SF-Compact-Rounded-Semibold.otf",32)
    SFToday_hl = ImageFont.truetype("fonts/SF-Compact-Rounded-Medium.otf",26)
    SFWdetails = ImageFont.truetype("fonts/SF-Compact-Rounded-Medium.otf",22)
    SFWdetails_bold = ImageFont.truetype("fonts/SF-Compact-Rounded-Bold.ttf",22)
    SFWdetails_semibold = ImageFont.truetype("fonts/SF-Compact-Rounded-Semibold.otf",22)
    SFWdetails_sub = ImageFont.truetype("fonts/SF-Compact-Rounded-Semibold.otf",16)
    
    SFQuote = ImageFont.truetype("fonts/SF-Compact-Rounded-Semibold.otf",26)
    SFQuoteAuthor = ImageFont.truetype("fonts/SF-Compact-Rounded-Medium.otf",20)
    SFReminder = ImageFont.truetype("fonts/SF-Compact-Rounded-Semibold.otf",24)
    SFReminder_sub = ImageFont.truetype("fonts/SF-Compact-Rounded-Semibold.otf",20)
    SFTransitID = ImageFont.truetype("fonts/SF-Compact-Rounded-Semibold.otf",24)
    SF_TransitName = ImageFont.truetype("fonts/SF-Compact-Rounded-Semibold.otf",18)
    SFTransitTime = ImageFont.truetype("fonts/RobotoMono-Bold.ttf",24)


    black = 'rgb(0,0,0)'
    white = 'rgb(255,255,255)'
    grey = 'rgb(206,206,206)'

    w_x = 10
    w_y = 80
    w_icon_offset = 170
    w_icon_row_height = 40


    #white = 255
    #black = 0
    #grey = 132

    imageB = Image.new('L', (epd.width, epd.height), 255)  # 255: clear the frame
    imageR = Image.new('L', (epd.width, epd.height), 255)  # 255: clear the frame

    draw_black = ImageDraw.Draw(imageB)
    draw_red = ImageDraw.Draw(imageR)

    # Find out how many characters per line of screen for Quotes
    test_t = "H"
    test_w_max = int(screen.width - 220)
    text_c = 0
    test_t_w = 0
    while test_t_w < test_w_max :
        test_t = test_t + "H"
        test_g, test_g, test_t_w, test_t_h = draw_black.textbbox((0,0),test_t, font=SFQuote)
        #print("Quote Feature : Max text width is "+str(test_t_w)+" number of chars "+str(len(test_t)))
    screen.quote_max = test_t_w

    # Find out how many characters per line of screen for Reminder text
    test_t = "H"
    test_w_max = int(screen.width - 220)
    text_c = 0
    test_t_w = 0
    while test_t_w < test_w_max :
        test_t = test_t + "H"
        test_g, test_g, test_t_w, test_t_h = draw_black.textbbox((0,0),test_t, font=SFReminder)
        #print("Quote Feature : Max text width is "+str(test_t_w)+" number of chars "+str(len(test_t)))
    screen.reminder_max = test_t_w

    header_Day = datetime.now().strftime("%A")
    header_Month_Date = datetime.now().strftime("%b %-d")
    header_Month = datetime.now().strftime("%b")
    header_Date = datetime.now().strftime("%-d")

    header_Day_t_size = draw_black.textbbox((0, 0), header_Day, font=DayTitle)
    header_Date_t_size = draw_black.textbbox((0, 0), header_Date, font=SFDate)
    header_Month_t_size = draw_black.textbbox((0, 0), header_Month, font=SFMonth)
    header_Day_w = header_Day_t_size[2] + header_Day_t_size[0]
    header_Day_h = header_Day_t_size[3]
    header_Month_w = header_Month_t_size[2]
    header_Month_h = header_Month_t_size[3]
    header_date_w = header_Date_t_size[2]
    header_date_h = header_Date_t_size[3]

    print("drawing todays day")

    x = 10
    y = 2

    draw_black.text((x,y), header_Day, font = DayTitle, fill = black)

    cal_icon = Image.open(os.path.join(picdir, 'calendar_header.png'))
    cal_icon_R = Image.open(os.path.join(picdir, 'calendar_header_R.png'))
    cal_icon_B = Image.open(os.path.join(picdir, 'calendar_header_B.png'))
    
    xcal = int(screen.middle_w - (cal_icon.size[0] * 2))
    ycal = y + 6

    #xcal = 535 - int(cal_icon.size[0])
    #ycal = y + 8

    
    if screen.use_red == 1:
        #imageR.paste(cal_icon, (xcal,ycal), cal_icon) 
        imageR.paste(cal_icon_R, (xcal,ycal), cal_icon_R)
        imageB.paste(cal_icon_B, (xcal,ycal), cal_icon_B)
    else :
        imageB.paste(cal_icon, (xcal,ycal), cal_icon) 



    y = ycal + (int(cal_icon.size[1]/2) - int(header_date_h/2)) + 1
    x = xcal + (int(cal_icon.size[0]/2) - int(header_date_w/2))

    draw_black.text((x, y), header_Date, font = SFDate, fill = black)


    y = ycal + 2
    x = xcal + (int(cal_icon.size[0]/2) - int(header_Month_w/2))
    if screen.use_red == 1:
        draw_red.text((x, y), header_Month, font = SFMonth, fill=white)
    else:
        draw_black.text((x, y), header_Month, font = SFMonth, fill=white)

    
    today_weather = current_weather()
    weather_error = today_weather.error
    
    forecast_weather = tomorrow_weather()
    if weather_error != 404:
        today_forecast = forecast_weather[0]
        tomorrow_forecast = forecast_weather[1]
    
    #  #  # ######   ##   ##### #    # ###### #####  
    #  #  # #       #  #    #   #    # #      #    # 
    #  #  # #####  #    #   #   ###### #####  #    # 
    #  #  # #      ######   #   #    # #      #####  
    #  #  # #      #    #   #   #    # #      #   #  
     ## ##  ###### #    #   #   #    # ###### #    # 
 
    if dashboard.show_weather == 1:
        #x = xcal + int(cal_icon.size[0] + 10)
        weather_cond_icon = Image.open(os.path.join(weatherdir, today_weather.icon+'.png'))

        x = int(screen.middle_w - int(weather_cond_icon.size[1]/2))
        y = 10

        imageB.paste(weather_cond_icon, (x,y),weather_cond_icon) 

        temp_string = str(round(today_weather.temperature,1))+"\N{DEGREE SIGN}"
        header_Temp_t_size = draw_black.textbbox((0, 0), temp_string, font=SFToday_temp)

        y = 55
        x = screen.middle_w - int(header_Temp_t_size[2]/2)
        draw_black.text((x,y),temp_string , font = SFToday_temp, fill = black)

        w_cond = today_weather.condition
        header_Cond_t_size = draw_black.textbbox((0, 0), w_cond, font=SFToday_cond)

        y = y + header_Temp_t_size[3]
        x = screen.middle_w - int(header_Cond_t_size[2]/2)
        draw_black.text((x,y),w_cond , font = SFToday_cond, fill = black)

        y = y + header_Cond_t_size[3]
        temp_high_low = "H:"+str(round(today_weather.temp_high,1))+"\N{DEGREE SIGN} L:"+str(round(today_weather.temp_low,1))+"\N{DEGREE SIGN}"
        header_high_low_t_size = draw_black.textbbox((0, 0), temp_high_low, font=SFToday_hl)
        x = screen.middle_w - int(header_high_low_t_size[2]/2)
        draw_black.text((x,y),temp_high_low , font = SFToday_hl, fill = black)

    if dashboard.show_weather_details == 1 :
    ###############################
    # Weather details section #####
    ###############################

        x = w_x
        y = w_y

        #Load the right feels like icon


        fl_icon = Image.open(os.path.join(weatherdir, "t.png"))
        fl_icon_red = 0
        if today_weather.feelslike <= -10 :
            fl_icon = Image.open(os.path.join(weatherdir, "temp_low.png"))
        if today_weather.feelslike >-10 and today_weather.feelslike <= 20 :
            fl_icon = Image.open(os.path.join(weatherdir, "t.png"))
        if today_weather.feelslike > 20  :
            fl_icon_b = Image.open(os.path.join(weatherdir, "temp_high_b.png"))
            fl_icon_r =  Image.open(os.path.join(weatherdir, "temp_high_r.png"))
            fl_icon_red = 1

        if fl_icon_red == 1 and screen.use_red == 1:
            imageB.paste(fl_icon_b, (x,y),fl_icon_b)
            imageR.paste(fl_icon_r, (x,y),fl_icon_r)
        else :
            imageB.paste(fl_icon, (x,y),fl_icon)
        Tx = int(x + fl_icon.size[0]) + 4
        Ty = y
        if fl_icon_red == 1 and screen.use_red == 1:
            draw_red.text((Tx,Ty),str(round(today_weather.feelslike,1))+"\N{DEGREE SIGN}" , font = SFWdetails_semibold, fill = black)
        else:
            draw_black.text((Tx,Ty),str(round(today_weather.feelslike,1))+"\N{DEGREE SIGN}" , font = SFWdetails_semibold, fill = black)


        #Move in for the next icon using the w_icon_offset constant
        x = x + w_icon_offset


        #Load the right humidity icon
        h_icon = Image.open(os.path.join(weatherdir, "h.png"))
        if today_weather.humidity <= 20 :
            h_icon = Image.open(os.path.join(weatherdir, "h_low.png"))
        if today_weather.humidity >20 and today_weather.humidity <= 70 :
            h_icon = Image.open(os.path.join(weatherdir, "h.png"))
        if today_weather.humidity > 70  :
            h_icon = Image.open(os.path.join(weatherdir, "h_high.png"))

        imageB.paste(h_icon, (x,y),h_icon)
        Tx = int(x + h_icon.size[0]) + 4
        Ty = y
        draw_black.text((Tx,Ty),str(today_weather.humidity)+"%" , font = SFWdetails_semibold, fill = black)

        #Move down one row using w_icon_row_height

        x = 10
        y = y + w_icon_row_height

        windkmh = (today_weather.wind*3600)/1000

        w_icon = Image.open(os.path.join(weatherdir, "w.png"))
        if windkmh <= 10 :
            w_icon = Image.open(os.path.join(weatherdir, "w_low.png"))
        if windkmh >10 and windkmh <= 25 :
            w_icon = Image.open(os.path.join(weatherdir, "w.png"))
        if windkmh > 25  :
            w_icon = Image.open(os.path.join(weatherdir, "w_high.png"))

        imageB.paste(w_icon, (x,y),w_icon)
        Tx = int(x + w_icon.size[0]) + 4
        Ty = y
        draw_black.text((Tx,Ty),str(int(windkmh))+"km/h" , font = SFWdetails_semibold, fill = black)

        #Move in for the next icon using the w_icon_offset constant
        x = x + w_icon_offset

        #Load the umbrella icon
        if weather_error == 404:
            popp = 0
        else:
            popp = int(today_forecast.pop * 100)

        if popp == 0:
            rain_icon = Image.open(os.path.join(weatherdir, "rain_off.png"))
        else:
            rain_icon = Image.open(os.path.join(weatherdir, "rain.png"))

        imageB.paste(rain_icon, (x,y),rain_icon)

        Tx = int(x + rain_icon.size[0]) + 4
        Ty = y

        if popp == 0:
            draw_black.text((Tx,Ty),"No rain" , font = SFWdetails_semibold, fill = black)
        if popp > 0:
            draw_black.text((Tx,(Ty-6)),str(popp)+"%" , font = SFWdetails_semibold, fill = black)
            draw_black.text((Tx,(Ty+16)),str(round(today_forecast.rain['3h'],1))+"mm" , font = SFWdetails_sub, fill = black)


        #Move down one row using w_icon_row_height

        x = 10
        y = y + w_icon_row_height

        p_icon = Image.open(os.path.join(weatherdir, "p.png"))
        p_text = "Normal"
        if today_weather.pressure <= 990 :
            p_icon = Image.open(os.path.join(weatherdir, "p_low.png"))
            p_text = "Low"
        if today_weather.pressure >990 and today_weather.pressure <= 1025 :
            p_icon = Image.open(os.path.join(weatherdir, "p.png"))
            p_text = "Normal"
        if today_weather.pressure > 1025  :
            p_icon = Image.open(os.path.join(weatherdir, "p_high.png"))
            p_text = "High"

        imageB.paste(p_icon, (x,y),p_icon)
        Tx = int(x + p_icon.size[0]) + 4
        Ty = y
        draw_black.text((Tx,Ty),p_text , font = SFWdetails_semibold, fill = black)

        sunrise=datetime.fromtimestamp(today_weather.sun_rise).strftime('%H:%M')
        sunset=datetime.fromtimestamp(today_weather.sun_set).strftime('%H:%M')

        #Move in one row using w_icon_row_height

        x = x + w_icon_offset

        sr_icon = Image.open(os.path.join(weatherdir, "SunRise.png"))
        ss_icon = Image.open(os.path.join(weatherdir, "SunSet.png"))
        ssr_icon = Image.open(os.path.join(weatherdir, "SunSetRise.png"))
        s_icon = ssr_icon
        s_time = "--:--"
        red_sun = 0

        if hourglass.hour >= int(datetime.fromtimestamp(today_weather.sun_rise).strftime('%H')):
            s_icon = ss_icon
            s_time = sunset
        if hourglass.hour >= int(datetime.fromtimestamp(today_weather.sun_set).strftime('%H')):
            s_icon = sr_icon
            s_time = sunrise
            red_sun = 1

        if screen.use_red == 1 and red_sun ==1 :
            imageR.paste(s_icon, (x,y),s_icon)
        else:
            imageB.paste(s_icon, (x,y),s_icon)
        Tx = int(x + s_icon.size[0]) + 4
        Ty = y
        draw_black.text((Tx,Ty),s_time , font = SFWdetails_semibold, fill = black)



    if dashboard.show_transit == 1:

        ########################
        #Transit section########
        ########################

         ###########
        #############
        ##         ##
        ##   BUS   ##
        ###       ###
        #############
        ###       ###

        #adding a slit for Transit
        draw_black.line([(540,10),(540,185)], black)
        draw_black.line([(541,10),(541,185)], black)


        ti1X = 565
        ti1Y = 20
        live_ind = Image.open(os.path.join(picdir, "transit_live.png"))
        live_ind_B = Image.open(os.path.join(picdir, "transit_live_B.png"))
        live_ind_R = Image.open(os.path.join(picdir, "transit_live_R.png"))
        #live_ind = Image.open(os.path.join(picdir, "transit_live2.png"))
        not_live_ind  = Image.open(os.path.join(picdir, "transit_not_live.png"))
        not_live_ind_B  = Image.open(os.path.join(picdir, "transit_not_live_B.png"))
        not_live_ind_R  = Image.open(os.path.join(picdir, "transit_not_live_R.png"))
        #Set the type of data indicator
        transit_ind = live_ind
        transit_ind_B = live_ind_B
        transit_ind_R = live_ind_R

        #Draw the 1st Transit icon segment
        t_icon1 = Image.open(os.path.join(picdir, transit.transit1_icon))
        ti1M = ti1X + int(t_icon1.size[0]/2)
        imageB.paste(t_icon1, (ti1X,ti1Y),t_icon1)
        t_name1 = transit.transit1_name
        t_nameSize = draw_black.textbbox((0, 0), t_name1, font=SF_TransitName)
        i1x = ti1M - int(t_nameSize[2]/2)
        i1y = ti1Y + int(t_icon1.size[1])
        draw_black.text((i1x,i1y),t_name1 , font = SF_TransitName, fill = black)
        t_id1 = transit.transit1_id
        t_idSize = draw_black.textbbox((0, 0), t_id1, font=SFTransitID)
        i1x = ti1M - int(t_idSize[2]/2)
        i1y = ti1Y + 10
        draw_black.text((i1x,i1y),t_id1 , font = SFTransitID, fill = black)

        #Get Live departures for 1st stop
        live_transit_state = 0   

        #Check if it is time to get live data
        print("Current hour is: "+str(hourglass.curenttime))
        print("Live cut in is: "+str(hourglass.live_cutin_hour))
        print("Live cut out is: "+str(hourglass.live_cutout_hour))
        if transit.use_live == 'TRUE':
            print("Live Transit is ON")
            if hourglass.curenttime >= hourglass.live_cutin_hour and hourglass.curenttime <= hourglass.live_cutout_hour:
                print("Live Transit Feature: within cut in times")
                live_transit_state = 1
                print("Attemting to get Live data for transit stop 1")
                get_transit_times1 = gettransitdepartures(datetime.now(),transit.api_key,transit.transit1_stop)
                print("Got "+str(len(get_transit_times1))+" live departures")
                if len(get_transit_times1) == 0:
                    print("No live data for stop 1 - fallback to static")
                    get_transit_times1 = next_transit(1)
                    live_transit_state = 0
                    transit_ind = not_live_ind
                    transit_ind_B = not_live_ind_B
                    transit_ind_R = not_live_ind_R
                print("Attemting to get Live data for transit stop 2")
                get_transit_times2 = gettransitdepartures(datetime.now(),transit.api_key,transit.transit2_stop)
                print("Got "+str(len(get_transit_times1))+" live departures")
                if len(get_transit_times2) == 0:
                    print("No live data for stop 1 - fallback to static")
                    get_transit_times1 = next_transit(2)
                    live_transit_state = 0
                    transit_ind = not_live_ind
                    transit_ind_B = not_live_ind_B
                    transit_ind_R = not_live_ind_R
            else :
                print("Getting static times")
                get_transit_times1 = next_transit(1)
                print("Got "+str(len(get_transit_times1))+" static departures for stop 1")
                get_transit_times2 = next_transit(2)
                print("Got "+str(len(get_transit_times2))+" static departures for stop 2")
                transit_ind = not_live_ind
                transit_ind_B = not_live_ind_B
                transit_ind_R = not_live_ind_R

        if transit.use_live == 'FALSE':
            live_transit_state = 0   
            print("Getting static times")
            get_transit_times1 = next_transit(1)
            print("Got "+str(len(get_transit_times1))+" static departures for stop 1")
            get_transit_times2 = next_transit(2)
            print("Got "+str(len(get_transit_times2))+" static departures for stop 2")
            transit_ind = not_live_ind
            transit_ind_B = not_live_ind_B
            transit_ind_R = not_live_ind_R

    
    
        dep_cnt = len(get_transit_times1)
        dept_text = draw_black.textbbox((0, 0), "00:00", font=SFTransitTime)
    
        bc = 0
        bx = ti1M - int(dept_text[2]/2)
        by = i1y + 70
        blx = bx + int(dept_text[2]) + 2
        bly = by + 8

        if dep_cnt >= 3 :

            while bc < 3 :
                draw_black.text((bx, by), get_transit_times1[bc], font=SFTransitTime, fill=black)
                if live_transit_state == 0  and screen.use_red == 1:
                    imageR.paste(transit_ind_R,(blx,bly),transit_ind_R)
                    imageB.paste(transit_ind_B,(blx,bly),transit_ind_B)
                else:
                    imageB.paste(transit_ind,(blx,bly),transit_ind)
                bc = bc +1
                by = by + (dept_text[3])
                bly = bly + (dept_text[3])
    
        if dep_cnt == 0 :
            draw_black.text((x, y), "--:--", font=SFTransitTime, fill=black)


        #Draw the second transit icon segment

        ti2X = ti1X + 120
        ti2Y = 20

        t_icon2 = Image.open(os.path.join(picdir, transit.transit2_icon))
        ti2M = ti2X + int(t_icon1.size[0]/2)
        imageB.paste(t_icon2, (ti2X,ti2Y),t_icon2)
        t_name2 = transit.transit2_name
        t_nameSize2 = draw_black.textbbox((0, 0), t_name2, font=SF_TransitName)
        i2x = ti2M - int(t_nameSize2[2]/2)
        i2y = ti2Y + int(t_icon2.size[1])
        draw_black.text((i2x,i2y),t_name2 , font = SF_TransitName, fill = black)
        t_id2 = transit.transit2_id
        t_idSize = draw_black.textbbox((0, 0), t_id2, font=SFTransitID)
        i2x = ti2M - int(t_idSize[2]/2)
        i2y = ti2Y + 10
        draw_black.text((i2x,i2y),t_id2 , font = SFTransitID, fill = black)

        #Get departures for transit stop 2


        dep_cnt = len(get_transit_times2)
        dept_text = draw_black.textbbox((0, 0), "00:00", font=SFTransitTime)
    
        bc = 0
        bx = ti2M - int(dept_text[2]/2)
        by = i2y + 70
        blx = bx + int(dept_text[2]) + 2
        bly = by + 8

        if dep_cnt >= 3 :
            
            while bc < 3 :
                draw_black.text((bx, by), get_transit_times1[bc], font=SFTransitTime, fill=black)
                if live_transit_state == 0 and screen.use_red == 1:
                    imageR.paste(transit_ind_R,(blx,bly),transit_ind_R)
                    imageB.paste(transit_ind_B,(blx,bly),transit_ind_B)
                else:
                    imageB.paste(transit_ind,(blx,bly),transit_ind)
                bc = bc +1
                by = by + (dept_text[3])
                bly = bly + (dept_text[3])
    
        if dep_cnt == 0 :
            draw_black.text((x, y), "--:--", font=SFTransitTime, fill=black)



    
        #Drawing a line below weather and transit
        x = 10
        y = 190

        draw_black.line([(x, y), (int(screen.width - (x*2)), y)], black)

        if dashboard.show_weather == 1 and weather_error != 404:
            y = y + 1
            draw_black.text((x,y),"Tomorrow: ", font = SFWdetails_semibold, fill = black)
            t_G, t_G, test_t_w, test_t_h = draw_black.textbbox((0,0),"Tomorrow :", font=SFWdetails_semibold)
            x = x + test_t_w

            # Tomorrows Weahter Icon:      
            tomorrow_cond_icon = Image.open(os.path.join(weatherdir, tomorrow_forecast.icon+'.png'))
            tomorrow_cond_icon = tomorrow_cond_icon.resize((int(tomorrow_cond_icon.size[0] /2.5), int(tomorrow_cond_icon.size[1] / 2.5)))
            tomorrow_pop_icon = Image.open(os.path.join(weatherdir, 'rain.png'))
            tomorrow_pop_icon = tomorrow_pop_icon.resize((int(tomorrow_pop_icon.size[0] /1.5), int(tomorrow_pop_icon.size[1] / 1.5)))
            tomorrow_sunrise_icon = Image.open(os.path.join(weatherdir, 'SunRise.png'))
            tomorrow_sunrise_icon = tomorrow_sunrise_icon.resize((int(tomorrow_sunrise_icon.size[0] /1.5), int(tomorrow_sunrise_icon.size[1] / 1.5)))
            imageB.paste(tomorrow_cond_icon, (x,(y+1)),tomorrow_cond_icon)
            x = x + int(tomorrow_cond_icon.size[0]+ 4)

        
            # Tomorrow's Weather string:
            fc_string = tomorrow_forecast.condition.capitalize()
            tomorrow_string = fc_string+"   | H:"+str(round(tomorrow_forecast.temp_high,1))+"\N{DEGREE SIGN}"+" L:"+str(round(tomorrow_forecast.temp_low,1))+"\N{DEGREE SIGN}"
            popp = int(tomorrow_forecast.pop * 100)
            #DEBUG RAIN
            #popp = 2
            #DEBUG RAIN
            draw_black.text((x,y),tomorrow_string , font = SFWdetails_semibold, fill = black)
            t_G, t_G, test_t_w, test_t_h = draw_black.textbbox((0,0),tomorrow_string, font=SFWdetails_semibold)
            x = x + test_t_w + 2
            if popp > 0:
                imageB.paste(tomorrow_pop_icon, (x,(y+3)),tomorrow_pop_icon)
                x = x + int(tomorrow_pop_icon.size[0]) + 2
                draw_black.text((x,y),str(popp)+"%" , font = SFWdetails_semibold, fill = black)
                t_G, t_G, test_t_w, test_t_h = draw_black.textbbox((0,0),str(popp)+"%", font=SFWdetails_semibold)
                x = x + int(test_t_w) + 2
            imageB.paste(tomorrow_sunrise_icon, (x,(y+2)),tomorrow_sunrise_icon)
            x = x + int(tomorrow_sunrise_icon.size[0]) +2
            draw_black.text((x,y),datetime.fromtimestamp(today_weather.sun_rise).strftime('%H:%M') , font = SFWdetails_semibold, fill = black)
            y = y + int(test_t_h) + 2
            y = y + 5
        else:
            y = y +1
        x = 10
        draw_black.line([(x, y), (int(screen.width - (x*2)), y)], black)
    
    if dashboard.show_quote == 1:

    # Quote Section

           #######
        ####     ####
        ####     #### 
        ####     ####
        ####     #### 
            #######  ###

        quote_icon = Image.open(os.path.join(picdir, "quote_icon.png"))
        quote_iconB = Image.open(os.path.join(picdir, "quote_b.png"))
        quote_iconR = Image.open(os.path.join(picdir, "quote_r.png"))

        qx = w_x
        qy = y + 8
    

        qml = 85
        qll = qml+1
        qmaxtries = 0
        print("Hourglass day : "+str(hourglass.day))
        print("Hourglass currentday: "+str(hourglass.currentday))
        if hourglass.currentday > hourglass.day:
            print("Time to get a new quote...")
            hourglass.day = int(datetime.now().strftime("%d"))

            print("Quote Feature : Getting a quote under "+str(qml)+" lenght")
            while qll >= qml :
                dashboard.quote = quoteoftheday()
                qll = len(dashboard.quote.quote_text)
                qmaxtries +=1
                if qmaxtries > 10:
                    break
                if qll >  qml:
                    print("Quote Feature : Attempt: "+str(qmaxtries))
                else:
                    print("Quote Feature : Quote lenght is "+str(qll))
            if qll == 0 :
            # Last effort to fill quote of the day if online fails
                quote_icon = Image.open(os.path.join(picdir, "quote_icon_disabled.png"))
                quote_iconB = Image.open(os.path.join(picdir, "quote_b_disabled.png"))
                quote_iconR = Image.open(os.path.join(picdir, "quote_r_disabled.png"))
                dashboard.quote = quotefromfile("quotes.txt")
                qll = len(dashboard.quote.quote_text)
    
            if qll > qml:
                print("Quote Feature : Max attempts to get a short enough quote exhausted.")
                #Just in case we could not find a short enough quote in 10 attempts.
                dashboard.quote.quote_text = "Sorry, No short Quote found, please adjust the quote-of-the-day-max-lenght value"
                dashboard.quote.quote_author = "Dashboard Ai"
            else :
                addquotetofile("quotes.txt","quotes.txt",dashboard.quote.quote_text, dashboard.quote.quote_author)
                print("Quote Feature : "+dashboard.quote.quote_text+" - "+dashboard.quote.quote_author)
        else:
            next_quote_hour = datetime.now() + timedelta(days=1)
            print("Only one quote per day : Keeping quote, next one at "+next_quote_hour.strftime("%d")+" daycount at "+str(hourglass.day))
        #print("Now trying to slice the text in chunks")
        text_g, text_g, test_t_w, test_t_h = draw_black.textbbox((0,0),dashboard.quote.quote_text, font=SFQuote)
        text_max = test_t_w
        text_line_max = screen.quote_max
        text_line = []
        textbuffer = ""

        #Show the quote icon status
        if screen.use_red == 1:
            imageB.paste(quote_iconB,(qx,qy),quote_iconB)
            imageR.paste(quote_iconR,(qx,qy),quote_iconR)
        else:
            imageB.paste(quote_icon,(qx,qy),quote_icon)


        #Split the quote into words in an array

        quote_words = dashboard.quote.quote_text.split()
        wl = len(dashboard.quote.quote_text)

        #See if the total is larger than the text_line_max value set.
        print("Quote Feature : Max pixels per line is "+str(text_line_max))

        if text_max > text_line_max:
            l = 0
            ql = len(quote_words)
            while l < ql:
                textbuffer = textbuffer + quote_words[l] + " "
                l += 1
                t_g, t_g, test_t_w, test_t_h = draw_black.textbbox((0,0),textbuffer, font=SFQuote)
                #print(textbuffer)
                if test_t_w > text_line_max:
                    text_line.append(textbuffer)
                    textbuffer = ""
                    #print(l)
            if (len(textbuffer)):
                text_line.append(textbuffer)
        else :
            text_line.append(dashboard.quote.quote_text)

        # Get number of arrays generated
        qs = len(text_line)
        qc = 0
        #qx = 20
    
        g_w = 0
        q_h = 0
        q_w = 0
    
        #Getting the widest line of text
        tq_g, tq_g, tq_w, tq_h = draw_black.textbbox((0,0),text_line[qc], font=SFQuote)
        while qc < qs :
            tq_g, tq_g, tq_w, tq_h = draw_black.textbbox((0,0),text_line[qc], font=SFQuote)
            q_h = tq_h
            if tq_w > q_w :
                q_w = tq_w
            qc +=1

        #Writing the quote line by line.
        qc = 0

        gTy = qy
        gTx = x + int(quote_icon.size[0]+2)


        while qc < qs:
            draw_black.text((gTx, gTy), text_line[qc], font=SFQuote, fill=black)
            #print(text_line[qc])
            qc += 1
            gTy = gTy + int(q_h)
            if qc == 1:
                gTx = gTx + 20
        
        qG, qG, q_w, q_h = draw_black.textbbox((0,0),"- "+dashboard.quote.quote_author, font=SFQuote)
        gTx = int(screen.middle_w) - int(q_w/2)
        #gTy = gTy + 4
        if screen.use_red == 1:
            draw_red.text((gTx, gTy), "- "+dashboard.quote.quote_author, font=SFQuoteAuthor, fill=black)
        else :
            draw_black.text((gTx, gTy), "- "+dashboard.quote.quote_author, font=SFQuoteAuthor, fill=black)
        gTy = gTy + int(q_h) + 4

        ###########################
        # End of Quote of the day
        ###########################

            ############
    ############################
    # Generic Garbage Schedule #
    ##  ##  ##  ##  ##  ##  ## #
    ##  ##  ##  ##  ##  ##  ## #
    ##  ##  ##  ##  ##  ##  ## #
    ##  ##  ##  ##  ##  ##  ## #
    ##  ##  ##  ##  ##  ##  ## #
    ##  ##  ##  ##  ##  ##  ## #
    ##  ##  ##  ##  ##  ##  ## #
    ##  ##  ##  ##  ##  ##  ## #
     ## ##  ##  ##  ##  ##  ### 
        ####################

    # Setting up Garabage Variables          
    garbage_vars = dict()
    garbage_vars = get_garbage_config_data("garbage_schedules.ini")
    g_data = get_garbage_status()

    is_garbage_tomorrow = (g_data.landfill_prepapre, g_data.recycle_prepare, g_data.compost_prepare, g_data.dumpster_prepapre)
    is_garbage_today = (g_data.landfill, g_data.recycle, g_data.compost, g_data.xmas_tree, g_data.dumpster)

    garbage_collection_hour = int(garbage_vars['all-collection-time-over-id'])
    comparetime = hourglass.curenttime
    
    gTx = 10
    gYincr = 6
    gx = 50
    gy = screen.width - 280

    # Load the Calendar Icon
    cal_todo_icon = Image.open(os.path.join(picdir, 'today_icon.png'))
    cal_todo_icon_R = Image.open(os.path.join(picdir, 'today_icon_R.png'))
    
    if 1 in is_garbage_today :
        if dashboard.show_quote == 1:
            lx = 247
            ly = gTy
            draw_black.line([(lx, ly), ((lx+300), ly)], black)
            gTy = gTy + 10

        print("Garbage schedule : there is garbage today")
        if screen.use_red == 1:
            imageB.paste(cal_todo_icon,(gTx, gTy),cal_todo_icon)
            imageR.paste(cal_todo_icon_R,(gTx, gTy),cal_todo_icon_R)
        else:
            imageB.paste(cal_todo_icon,(gTx, gTy),cal_todo_icon)
        gTx = gTx + int( cal_todo_icon.size[0] + 8 )
        gTy = gTy - 8
        if hourglass.curenttime <= comparetime:
            print("get ready for the truck!")
            g_image_end_icon = Image.open(os.path.join(picdir, 'Garbage_Truck.png'))
            g_string = garbage_vars['all-garbage-time-message-today-id']
            g_sub_sting = garbage_vars['all-garbage-collect-message-id']
            if g_data.landfill == 1:
                g_string = g_string + " "+garbage_vars['landfill_title-id']
            if g_data.recycle == 1:
                g_string = g_string + " & "+garbage_vars['recycle_title-id']
            if g_data.compost == 1:
                g_string = g_string + " & "+garbage_vars['compost_title-id']
            if g_data.dumpster == 1:
                g_string = g_string + " & "+garbage_vars['dumpster_title-id']
            if g_data.xmas_tree == 1:
                g_string = g_string + " & "+garbage_vars['holiday-tree-schedule_title-id']
                g_string = g_string + " " + garbage_vars['all-garbage-time-message-end-id']
        else:
            print("Time to take the bins back in")
            g_image_end_icon = Image.open(os.path.join(picdir, 'Garbage_Garage.png'))
            g_string = garbage_vars['all-collection-time-over-message-line1-id']
            g_sub_sting = garbage_vars['all-collection-time-over-message-line2-id']
        #print("Now trying to slice the text in chunks")
        t_g, t_g, test_t_w, test_t_h = draw_black.textbbox((0,0),g_string, font=SFReminder)
        text_max = test_t_w
        text_line_max = screen.reminder_max
        text_line = []
        textbuffer = ""
        #Split the quote into words in an array
        schedule_words = g_string.split()
        wl = len(g_string)
        #See if the total is larger than the text_line_max value set.
        if text_max > text_line_max:
            l = 0
            ql = len(schedule_words)
            while l < ql:
                textbuffer = textbuffer + schedule_words[l] + " "
                l += 1
                t_g, t_g, test_t_w, test_t_h = draw_black.textbbox((0,0),textbuffer, font=SFReminder)
                if test_t_w > text_line_max:
                    text_line.append(textbuffer)
                    textbuffer = ""
            if (len(textbuffer)):
                text_line.append(textbuffer)
        else :
            text_line.append(g_string)
        # Get number of arrays generated
        qs = len(text_line)  
        qc = 0
        t_g, t_g, tg_w, tg_h = draw_black.textbbox((0,0),text_line[0], font=SFReminder)
        while qc < qs:
            draw_black.text((gTx, gTy), text_line[qc], font=SFReminder, fill=black)
            qc += 1
            gTy = gTy + int(tg_h)
        draw_black.text((gTx, gTy), g_sub_sting, font=SFReminder_sub, fill=black)
        sy_g, st_g, st_w, st_h = draw_black.textbbox((0,0),g_sub_sting, font=SFReminder_sub)
        #gTy = gTy + int(st_h)
        gTy = gTy + 5
        
        # Now add the icons in sequence below the Schedule text
        # Show the truck icon at the very right.
        gTx = int(screen.width - int(g_image_end_icon.size[0])) - 10
        imageB.paste(g_image_end_icon, (gTx, gTy), g_image_end_icon)
        # Add the arrows icon poiting to the street
        g_image_icon = Image.open(os.path.join(picdir, 'Garbage_Arrow.png'))
        gTx = gTx - (int(g_image_icon.size[0])+10)
        if screen.use_red == 1:
            imageR.paste(g_image_icon, (gTx, gTy), g_image_icon)
        else:
            imageB.paste(g_image_icon, (gTx, gTy), g_image_icon)
        gTx = gTx - (int(g_image_icon.size[0])+10)
        if g_data.xmas_tree == 1:
            g_image_icon = Image.open(os.path.join(picdir, 'Garbage_Holiday.png'))
            imageB.paste(g_image_icon, (gTx, gTy), g_image_icon)
            gTx = gTx - int(g_image_icon.size[1]+4)
        if g_data.dumpster == 1:
            g_image_icon = Image.open(os.path.join(picdir, 'Garbage_Dumpster.png'))
            imageB.paste(g_image_icon, (gTx, gTy), g_image_icon)
            gTx = gTx - int(g_image_icon.size[1]+4)
        if g_data.compost == 1:
            g_image_icon = Image.open(os.path.join(picdir, 'Garbage_Compost.png'))
            imageB.paste(g_image_icon, (gTx, gTy), g_image_icon)
            gTx = gTx - int(g_image_icon.size[1]+4)
        if g_data.recycle == 1:
            g_image_icon = Image.open(os.path.join(picdir, 'Garbage_Recycle.png'))
            imageB.paste(g_image_icon, (gTx, gTy), g_image_icon)
            gTx = gTx - int(g_image_icon.size[1]+4)
        if g_data.landfill == 1:
            g_image_icon = Image.open(os.path.join(picdir, 'Garbage_Trash.png'))
            imageB.paste(g_image_icon, (gTx, gTy), g_image_icon)
            gTx = gTx - int(g_image_icon.size[1]+4)
        gYincr = int(g_image_icon.size[1]+10)
        gTy = gTy + gYincr
        if dashboard.show_quote == 1:
            lx = 247
            ly = gTy
            draw_black.line([(lx, ly), ((lx+300), ly)], black)
            gTy = gTy + 10

    if 1 in is_garbage_tomorrow :
        if dashboard.show_quote == 1:
            lx = 247
            ly = gTy
            draw_black.line([(lx, ly), ((lx+300), ly)], black)
            gTy = gTy + 10


        cal_todo_icon = Image.open(os.path.join(picdir, 'tomorrow_icon.png'))
        cal_todo_iconB = Image.open(os.path.join(picdir, 'tomorrow_icon_B.png'))
        cal_todo_iconR = Image.open(os.path.join(picdir, 'tomorrow_icon_R.png'))
        gTx = 10 
        print("Garbage schedule : there is garbage tomorrow")
        
        if screen.use_red == 1:
            imageR.paste(cal_todo_iconR,(gTx, gTy),cal_todo_iconR)
            imageB.paste(cal_todo_iconB,(gTx, gTy),cal_todo_iconB)
        else:
            imageB.paste(cal_todo_icon,(gTx, gTy),cal_todo_icon)
        gTx = gTx + int( cal_todo_icon.size[0] + 8 )
        gTy = gTy - 8
        #Build the garbage schedule reminder string
        g_string = garbage_vars['all-garbage-time-message-tomorrow-id']
        if g_data.landfill_prepapre == 1:
            g_string = g_string + " "+garbage_vars['landfill_title-id']
        if g_data.recycle_prepare == 1:
            g_string = g_string + " & "+garbage_vars['recycle_title-id']
        if g_data.compost_prepare == 1:
            g_string = g_string + " & "+garbage_vars['compost_title-id']
        if g_data.dumpster_prepapre == 1:
            g_string = g_string + " & "+garbage_vars['dumpster_title-id']
        g_string = g_string + " " + garbage_vars['all-garbage-time-message-end-id']

        #print("Now trying to slice the text in chunks")
        t_G, t_G, test_t_w, test_t_h = draw_black.textbbox((0,0),g_string, font=SFReminder)
        text_max = test_t_w
        text_line_max = screen.reminder_max
        text_line = []
        textbuffer = ""
        #Split the quote into words in an array
        schedule_words = g_string.split()
        wl = len(g_string)
        #See if the total is larger than the text_line_max value set.
        if text_max > text_line_max:
            l = 0
            ql = len(schedule_words)
            while l < ql:
                textbuffer = textbuffer + schedule_words[l] + " "
                l += 1
                t_G, t_G, test_t_w, test_t_h = draw_black.textbbox((0,0),textbuffer, font=SFReminder)
                if test_t_w > text_line_max:
                    text_line.append(textbuffer)
                    textbuffer = ""
            if (len(textbuffer)):
                text_line.append(textbuffer)
        else :
            text_line.append(g_string)
        # Get number of arrays generated
        qs = len(text_line)  
        qc = 0
        t_G, t_G, tg_w, tg_h = draw_black.textbbox((0,0),text_line[0], font=SFReminder)

        while qc < qs:
            draw_black.text((gTx, gTy), text_line[qc], font=SFReminder, fill=black)
            qc += 1
            gTy = gTy + int(tg_h)
        draw_black.text((gTx, gTy), garbage_vars['all-garbage-prepare-message-id'], font=SFReminder_sub, fill=black)

        # Now add the icons in sequence below the Schedule text
        sy_g, st_g, st_w, st_h = draw_black.textbbox((0,0),garbage_vars['all-garbage-prepare-message-id'], font=SFReminder_sub)
        #gTy = gTy + int(st_h)

        # Show the street icon at the very right.
        g_image_end_icon = Image.open(os.path.join(picdir, 'Garbage_Tree.png'))
        gTx = int(screen.width - int(g_image_end_icon.size[0])) - 10
        imageB.paste(g_image_end_icon, (gTx, gTy), g_image_end_icon)
        # Add the arrows icon poiting to the street
        g_image_icon = Image.open(os.path.join(picdir, 'Garbage_Arrow.png'))
        gTx = gTx - (int(g_image_icon.size[0])+10)
        if screen.use_red == 1:
           imageR.paste(g_image_icon, (gTx, gTy), g_image_icon)
        else:
           imageB.paste(g_image_icon, (gTx, gTy), g_image_icon)

        gTx = gTx - (int(g_image_icon.size[0])+10)
        

        if g_data.dumpster_prepapre == 1:
            g_image_icon = Image.open(os.path.join(picdir, 'Garbage_Dumpster.png'))
            imageB.paste(g_image_icon, (gTx, gTy), g_image_icon)
            gTx = gTx - int(g_image_icon.size[1]+4)

        if g_data.compost_prepare == 1:
            g_image_icon = Image.open(os.path.join(picdir, 'Garbage_Compost.png'))
            imageB.paste(g_image_icon, (gTx, gTy), g_image_icon)
            gTx = gTx - int(g_image_icon.size[1]+4)

        if g_data.recycle_prepare == 1:
            g_image_icon = Image.open(os.path.join(picdir, 'Garbage_Recycle.png'))
            imageB.paste(g_image_icon, (gTx, gTy), g_image_icon)
            gTx = gTx - int(g_image_icon.size[1]+4)

        if g_data.landfill_prepapre == 1:
            g_image_icon = Image.open(os.path.join(picdir, 'Garbage_Trash.png'))
            imageB.paste(g_image_icon, (gTx, gTy), g_image_icon)
            gTx = gTx - int(g_image_icon.size[1]+4)



    t_G, t_G, test_t_w, test_t_h = draw_black.textbbox((0,0),hourglass.last_refresh, font=SFMonth)
    gTx = int(screen.middle_w) - int(test_t_w/2)
    gTy = screen.height - int(test_t_h + 4)
    draw_black.text((gTx, gTy), hourglass.last_refresh, font=SFMonth, fill=black)


    #Save screenshot
    #s_b = imageB.convert('RGBA')
    #s_r = imageR.convert('RGBA')
    #s_b.save("InkFrame_B.png", format='png')
    #s_r.save("InkFrame_R.png", format='png')
    epd.display(epd.getbuffer(imageB),epd.getbuffer(imageR))
    #epd.display(epd.getbuffer(imageR),epd.getbuffer(imageB))
    epd.sleep()


def get_dashboard_config_data(file_path:str):
    parser = configparser.ConfigParser()
    parser.read(file_path)
    data = dict()
    
    data['transit-use-live-id'] = parser.get("transit-config", "transit-use-live")
    
    data['transit-api-key-id'] = parser.get("transit-config", "api-key")
    data['transit_name_1-id'] = parser.get("transit-config", "transit_name_1")
    data['transit_id_1-id'] = parser.get("transit-config", "transit_id_1")
    data['transit_stop_1-id'] = parser.get("transit-config", "transit_stop_1")
    data['transit_icon_1-id'] = parser.get("transit-config", "transit_icon_1")

    data['transit_name_2-id'] = parser.get("transit-config", "transit_name_2")
    data['transit_id_2-id'] = parser.get("transit-config", "transit_id_2")
    data['transit_stop_2-id'] = parser.get("transit-config", "transit_stop_2")
    data['transit_icon_2-id'] = parser.get("transit-config", "transit_icon_2")

    data['transit_live_cutin_hour-id'] = parser.get("transit-config", "transit_live_cutin_hour")
    data['transit_live_cutout_hour-id'] = parser.get("transit-config", "transit_live_cutout_hour")

    data['screen_type-id'] = parser.get("screen-config", "screen_type")
    data['use_red-id'] = parser.get("screen-config", "use_red")
    data['refresh-rate-min-id'] = parser.get("screen-config", "refresh-rate-min")
    data['screen_sleep_hour-id'] = parser.get("screen-config", "screen_sleep_hour")
    data['screen_wake_hour-id'] = parser.get("screen-config", "screen_wake_hour")


    data['show_weather-id'] = parser.get("feature-config", "show_weather")
    data['show_weather_details-id'] = parser.get("feature-config", "show_weather_details")
    data['show_transit-id'] = parser.get("feature-config", "show_transit")
    data['show_quote-id'] = parser.get("feature-config", "show_quote")
    return data

def get_garbage_config_data(file_path:str):
    parser = configparser.ConfigParser()
    parser.read(file_path)
    data = dict()
    data['landfill_title-id'] = parser.get("landfill-schedule", "title")
    data['landfill_prepare-date-month-id'] = parser.get("landfill-schedule", "prepare-date-month")
    data['landfill_collect-date-month-id'] = parser.get("landfill-schedule", "collect-date-month")

    data['recycle_title-id'] = parser.get("recycle-schedule", "title")
    data['recycle_prepare-date-month-id'] = parser.get("recycle-schedule", "prepare-date-month")
    data['recycle_collect-date-month-id'] = parser.get("recycle-schedule", "collect-date-month")

    data['compost_title-id'] = parser.get("compost-schedule", "title")
    data['compost_prepare-date-month-id'] = parser.get("compost-schedule", "prepare-date-month")
    data['compost_collect-date-month-id'] = parser.get("compost-schedule", "collect-date-month")

    data['dumpster_title-id'] = parser.get("dumpster-schedule", "title")
    data['dumpster_prepare-date-month-id'] = parser.get("dumpster-schedule", "prepare-date-month")
    data['dumpster_collect-date-month-id'] = parser.get("dumpster-schedule", "collect-date-month")

    data['holiday-tree-schedule_title-id'] = parser.get("holiday-tree-schedule", "title")
    data['holiday-tree-schedule_collect-date-month-id'] = parser.get("holiday-tree-schedule", "collect-date-month")

    data['all-garbage-prepare-message-id'] = parser.get("all-garbage", "prepare-message")
    data['all-garbage-collect-message-id'] = parser.get("all-garbage", "collect-message")
    data['all-collection-time-over-id'] = parser.get("all-garbage", "collection-time-over")
    data['all-garbage-time-message-today-id'] = parser.get("all-garbage", "garbage-time-message-today")
    data['all-garbage-time-message-tomorrow-id'] = parser.get("all-garbage", "garbage-time-message-tomorrow")
    data['all-garbage-time-message-end-id'] = parser.get("all-garbage", "garbage-time-message-end")
    data['all-collection-time-over-message-line1-id'] = parser.get("all-garbage", "collection-time-over-message-line1")
    data['all-collection-time-over-message-line2-id'] = parser.get("all-garbage", "collection-time-over-message-line2")
    return data

def sleep_screen(wake_date:date):
    print("Sleeping screen initiated")
    SleepFont = ImageFont.truetype("fonts/SF-Compact-Rounded-Semibold.otf",32)
    try:

        epd = epd7in5b_V2.EPD()
        epd.init()
        epd.Clear()
        screen.height = epd.height
        screen.width = epd.width
        screen.middle_w = screen.width/2
        screen.middle_h = screen.height/2
    except IOError as e:
        print(e)

    except KeyboardInterrupt:    
        print("ctrl + c:")
        epd7in5b_V2.epdconfig.module_exit()
        exit()
    imageB = Image.new('L', (epd.width, epd.height), 255)  # 255: clear the frame
    imageR = Image.new('L', (epd.width, epd.height), 255)  # 255: clear the frame
    draw_black = ImageDraw.Draw(imageB)

    sleep_icon = Image.open(os.path.join(picdir, 'sleep_icon.png'))
    sX = int(screen.middle_w) - int(sleep_icon.size[0]/2)
    sY = int(screen.middle_h) - int(sleep_icon.size[1]/2)
    imageB.paste(sleep_icon, (sX,sY), sleep_icon)

    sleep_string = "Good Night, see you tomorrow at "+str(screen.wake_hour)
    t_g, t_g, test_t_w, test_t_h = draw_black.textbbox((0,0),sleep_string, font=SleepFont)
    sX = int(screen.middle_w) - int(test_t_w/2)
    sY = int(sY + sleep_icon.size[1]) + 4
    draw_black.text((sX, sY), sleep_string, font = SleepFont, fill = 'rgb(0,0,0)')

    epd.display(epd.getbuffer(imageB),epd.getbuffer(imageR))
    epd.sleep()
    wakeup_day = wake_date.strftime("%d")
    print("Set to wake up on the "+wakeup_day)
    while True:
        print("Entring coma...")
        if datetime.now().strftime("%d") == wakeup_day:
            if int(datetime.now().strftime("%H")) >= screen.wake_hour:
                break
        print("Sleeping for one hour")
        time.sleep(3600)
        


def main():
    hourglass.day = 0
    screen.clean_screen = 0
    trend = 0
    ram = getRAMinfo()
    performance.usedram = int(ram[2])
    performance.previousram = performance.usedram
    dash_config = dict()
    dash_config = get_dashboard_config_data("dashboard.ini")
    screen.refresh_rate_min = int(dash_config['refresh-rate-min-id'])
    screen.sleep_hour = int(dash_config['screen_sleep_hour-id'])
    screen.wake_hour = int(dash_config['screen_wake_hour-id'])
    #screen.sleep_hour = 16

    print("Initial used RAM is: "+str(performance.usedram))
    while True :
        print("Screen sleep at: "+str(screen.sleep_hour))
        print("Wake up at: "+str(screen.wake_hour))
        min = 0
        hourglass.currentday = int(datetime.now().strftime("%d"))
        hourglass.last_refresh = datetime.now().strftime("Last Refresh @ %H:%M")
        hourglass.curenttime = int(datetime.now().strftime("%H"))
        hourglass.hour = int(datetime.now().strftime("%H"))
        print("it is now "+datetime.now().strftime("%H"))
        if int(datetime.now().strftime("%H")) < screen.sleep_hour:
            print("Time to draw the dashboard...")
            createDash()
        else:
            print("Time to go to sleep...")
            sleep_screen(datetime.now() + timedelta(days=1))

        ram = getRAMinfo()
        performance.usedram = int(ram[2])
        if performance.previousram > performance.usedram :
            trend = -1
            performance.ramincrease = performance.previousram - performance.usedram
        if performance.previousram < performance.usedram :
            trend = 1
            performance.ramincrease = performance.usedram - performance.previousram

        if performance.previousram == performance.usedram :
            trend = 0
            performance.ramincrease = performance.usedram - performance.previousram
            
        performance.freeram = int(ram[1])
        
        cpuT = getCPUtemperature()
        cpuU = getCPUuse()
        print("********************************")
        print("RAM: "+str(performance.usedram)+" used, and "+str(performance.freeram)+" free")
        print("RAM Previous was: "+str(performance.previousram))
        if trend == 1:
            print("Used RAM Increase by: "+str(performance.ramincrease))
        if trend == -1 :
            print("Used RAM Decresed by: "+str(performance.ramincrease))
        if trend == 0 :
            print("Used RAM unchanged ")

        print("CPU Temp: "+cpuT)
        print("CPU Usage: "+cpuU)
        print("********************************")
        performance.previousram = performance.usedram

        print("Refresh in "+str(screen.refresh_rate_min)+" minutes")
        time.sleep((screen.refresh_rate_min*60))
        

if __name__ == "__main__":
    main()
