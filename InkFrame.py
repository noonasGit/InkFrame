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
from aqidata import current_aqi, get_aqi_status_data, aqi_trend, write_aqi_stats
from todoist import gettodolist, getodolistbyduedate
from generic_transit import next_transit
from transit import gettransitdepartures
from getquote import quoteoftheday, addquotetofile, quotefromfile
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
    show_quote_live : int
    quote : str
    show_todo : int
    todo_rows : int
    todo_filter :str
    show_garbage : int

@dataclass
class hourglass:
    day : int
    hour : int
    curenttime : int
    currentday : int
    live_cutin_hour : int
    live_cutout_hour : int
    last_refresh : str
    evening_hour : str


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
    cli : str



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
        applog("System settings" ,"Red pigment is enabled")

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
    
    if dash_config['show_quote_live-id'] == "TRUE":
        dashboard.show_quote_live = 1
    else : 
        dashboard.show_quote_live = 0

    if dash_config['show-todo-id'] == "TRUE":
        dashboard.show_todo = 1
    else : 
        dashboard.show_todo = 0

    if dash_config['show-garbage-id'] == "TRUE":
        dashboard.show_garbage = 1
    else : 
        dashboard.show_garbage = 0
        
    
    dashboard.todo_rows = int(dash_config['todo-rows-id'])
    dashboard.todo_filter = dash_config['todo-filter-id']



    try:

        epd = epd7in5b_V2.EPD()
        epd.init()
        #epd.Clear()
        screen.height = epd.height
        screen.width = epd.width
        screen.middle_w = screen.width/2
        screen.middle_h = screen.height/2
    except IOError as e:
        applog("Screen init" ,e)

    except KeyboardInterrupt:
        applog("System runtime" ,"ctrl + c:")
        epd7in5b_V2.epdconfig.module_exit()
        exit()

    # Check if we should clear the E-ink (daily)
    if screen.clean_screen < int(datetime.now().strftime("%d")):
        if performance.cli == "noclean":
            applog("System runtime" ,"Screen cleaning skipped")
            performance.cli = ""
        else:
            applog("System runtime" ,"Time to clean the screen - once daily")
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
    SFWdetails_sub_bold = ImageFont.truetype("fonts/SF-Compact-Rounded-Bold.ttf",16)
    SFWAQI_bold = ImageFont.truetype("fonts/SF-Compact-Rounded-Bold.ttf",22)
    SFWAQI_bold_small = ImageFont.truetype("fonts/SF-Compact-Rounded-Bold.ttf",14)

    SFToDo = ImageFont.truetype("fonts/SF-Compact-Rounded-Medium.otf",24)
    SFToDo_sub = ImageFont.truetype("fonts/SF-Compact-Rounded-Medium.otf",16)

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
    w_y = 75
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
    screen.quote_max = screen.width - 40

    # Find out how many characters per line of screen for Reminder text
    screen.reminder_max = screen.width - 40

    screen.offset = 95

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

    applog("Dashboard" ,"drawing todays day")

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

    
    
    #  #  # ######   ##   ##### #    # ###### #####  
    #  #  # #       #  #    #   #    # #      #    # 
    #  #  # #####  #    #   #   ###### #####  #    # 
    #  #  # #      ######   #   #    # #      #####  
    #  #  # #      #    #   #   #    # #      #   #  
     ## ##  ###### #    #   #   #    # ###### #    # 
 
    if dashboard.show_weather == 1:
        today_weather = current_weather()
        today_aqi = current_aqi()
        weather_error = today_weather.error

        yesterday = datetime.now()+ timedelta(days=-1)
        y_aqi_stats_file = "aqi_stats/aqi_"+yesterday.strftime("%d_%m")
        aqi_stats_file = "aqi_stats/aqi_"+datetime.now().strftime("%d_%m")

        write_aqi_stats(aqi_stats_file, today_aqi.aqi_value)
        aqi_trend_ind = aqi_trend(aqi_stats_file, y_aqi_stats_file, today_aqi.aqi_value)

    
        forecast_weather = tomorrow_weather()
        today_forecast = forecast_weather[0]
        tomorrow_forecast = forecast_weather[1]

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
        feels_line_text = str(round(today_weather.feelslike,1))+"\N{DEGREE SIGN}"
        if today_weather.icon == "EE":
            feels_line_text = "?"
        if fl_icon_red == 1 and screen.use_red == 1:
            imageB.paste(fl_icon_b, (x,y),fl_icon_b)
            imageR.paste(fl_icon_r, (x,y),fl_icon_r)
        else :
            imageB.paste(fl_icon, (x,y),fl_icon)
        Tx = int(x + fl_icon.size[0]) + 4
        Ty = y
        if fl_icon_red == 1 and screen.use_red == 1:
            draw_red.text((Tx,Ty),feels_line_text , font = SFWdetails_semibold, fill = black)
        else:
            draw_black.text((Tx,Ty),feels_line_text , font = SFWdetails_semibold, fill = black)


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
        if today_weather.icon == "EE":
            today_weather.humidity = "-"

        imageB.paste(h_icon, (x,y),h_icon)
        Tx = int(x + h_icon.size[0]) + 4
        Ty = y
        draw_black.text((Tx,Ty),str(today_weather.humidity)+"%" , font = SFWdetails_semibold, fill = black)

        #Move down one row using w_icon_row_height

        x = 10
        y = y + w_icon_row_height

        windkmh = (today_weather.wind*3600)/1000
        wind_text = str(round(windkmh,1))+" km/h"

        w_icon = Image.open(os.path.join(weatherdir, "w.png"))
        if windkmh <= 10 :
            w_icon = Image.open(os.path.join(weatherdir, "w_low.png"))
            wind_sev = 0
        if windkmh >10 and windkmh <= 25 :
            w_icon = Image.open(os.path.join(weatherdir, "w.png"))
            wind_sev = 1
        if windkmh > 25  :
            w_icon = Image.open(os.path.join(weatherdir, "w_high.png"))
            wind_sev = 3
        w_text = today_weather.wind_conditions

        imageB.paste(w_icon, (x,y),w_icon)
        Tx = int(x + w_icon.size[0]) + 4
        Ty = y
        draw_black.text((Tx,(Ty-6)),w_text , font = SFWdetails_semibold, fill = black)
        if screen.use_red == 1:
            if wind_sev == 0:
                draw_black.text((Tx,(Ty+16)),wind_text, font = SFWdetails_sub, fill = black)
            if wind_sev == 1:
                draw_red.text((Tx,(Ty+16)),wind_text, font = SFWdetails_sub_bold, fill = black)
            if wind_sev == 2:
                draw_red.text((Tx,(Ty+16)),wind_text, font = SFWdetails_sub_bold, fill = black)
        if screen.use_red == 0:
            if wind_sev == 0:
                draw_black.text((Tx,(Ty+16)),wind_text, font = SFWdetails_sub, fill = black)
            if wind_sev == 1:
                draw_black.text((Tx,(Ty+16)),wind_text, font = SFWdetails_sub_bold, fill = black)
            if wind_sev == 2:
                draw_black.text((Tx,(Ty+16)),wind_text, font = SFWdetails_sub_bold, fill = black)

        #Move in for the next icon using the w_icon_offset constant
        x = x + w_icon_offset

        #Load the umbrella icon
        if weather_error == 404:
            popp = -1
        else:
            popp = int(today_forecast.pop * 100)

        if popp == 0:
            rain_icon = Image.open(os.path.join(weatherdir, "rain_off.png"))
        else:
            rain_icon = Image.open(os.path.join(weatherdir, "rain.png"))

        imageB.paste(rain_icon, (x,y),rain_icon)

        Tx = int(x + rain_icon.size[0]) + 4
        Ty = y

        if popp == -1:
            draw_black.text((Tx,Ty),"No data" , font = SFWdetails_semibold, fill = black)
        if popp == 0:
            draw_black.text((Tx,Ty),"No rain" , font = SFWdetails_semibold, fill = black)
        if popp > 0:
            draw_black.text((Tx,(Ty-6)),str(popp)+"%" , font = SFWdetails_semibold, fill = black)
            draw_black.text((Tx,(Ty+16)),str(round(today_forecast.rain,1))+"mm" , font = SFWdetails_sub, fill = black)


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
        if today_weather.icon == "EE":
            p_text = "No Data"


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


        # DEBUG AQI
        # today_aqi = 120

        aqi_number ="?"
        aqi_icon_name = "AQI_badge.png"
        aqi_sev = -1
        aqi_font = SFWAQI_bold_small


        if today_aqi.aqi_value == -1:
            aqi_sev = -1
            aqi_font = SFWAQI_bold
        if today_aqi.aqi_value >= 10:
            aqi_sev = 0
            aqi_font = SFWAQI_bold
            aqi_icon_name = "AQI_good.png"
        if today_aqi.aqi_value > 10 and today_aqi.aqi_value <=50:
            aqi_sev = 0
            aqi_font = SFWAQI_bold
            aqi_icon_name = "AQI_good.png"
        if today_aqi.aqi_value > 50 and today_aqi.aqi_value <=80:
            aqi_sev = 0
            aqi_font = SFWAQI_bold
            aqi_icon_name = "AQI_good.png"
        if today_aqi.aqi_value > 80 and today_aqi.aqi_value <=100:
            aqi_sev = 1
            aqi_icon_name = "AQI_badge.png"
            aqi_font = SFWAQI_bold_small
        if today_aqi.aqi_value > 100 and today_aqi.aqi_value <=150:
            aqi_sev = 2
            aqi_icon_name = "AQI_badge.png"
            aqi_font = SFWAQI_bold_small
        if today_aqi.aqi_value > 150 and today_aqi.aqi_value <=200:
            aqi_sev = 3
            aqi_icon_name = "AQI_badge.png"
            aqi_font = SFWAQI_bold_small
        if today_aqi.aqi_value > 200:
            aqi_sev = 4
            aqi_icon_name = "AQI_badge.png"
            aqi_font = SFWAQI_bold_small

        if today_aqi.aqi_value >0:
            aqi_number = str(today_aqi.aqi_value)
        a_g, a_g, aqi_w, aqi_h = draw_black.textbbox((0,0), aqi_number, font=aqi_font)

        aqi_icon = Image.open(os.path.join(weatherdir,aqi_icon_name)) 
        
        if screen.use_red == 1 and aqi_sev > 0:
            imageR.paste(aqi_icon, (x,y),aqi_icon)
        else:
            imageB.paste(aqi_icon, (x,y),aqi_icon)


        aqiw_m = x + int(aqi_icon.size[0]/2)
        aqih_m = y + int(aqi_icon.size[1]/2)
        ax = aqiw_m - int(aqi_w/2)
        #Adjust Y axis based on screen

        ay = y + int(aqi_h/4)
        if aqi_sev < 1:
            ay = ay - 4
        else:
            ay = ay + 3

        if aqi_sev > 0:
            # Print the AQI number inside the badge icon

            if screen.use_red == 1 and aqi_sev > 0:
                draw_red.text((ax,ay),aqi_number , font = aqi_font, fill = white)
                draw_black.text((ax,ay),aqi_number , font = aqi_font, fill = black)

        Tx = int(x + aqi_icon.size[0]) + 4
        Ty = y +2
        if aqi_sev > 0:
            if screen.use_red == 1 and aqi_sev > 0:
                draw_red.text((Tx,Ty),today_aqi.aqi_status , font = SFWdetails_semibold, fill = black)
            else:
                draw_black.text((Tx,Ty),today_aqi.aqi_status , font = SFWdetails_semibold, fill = black)
        else :
                #Print the AQI text and value below (like Rain), use the other icon. 
                draw_black.text((Tx,Ty-6),today_aqi.aqi_status , font = SFWdetails_semibold, fill = black)
                draw_black.text((Tx,Ty+16),"AQI ("+aqi_number+")" , font = SFWdetails_sub, fill = black)

        trend_icon = False
        if aqi_trend_ind == 0 :
            trend_icon = Image.open(os.path.join(weatherdir,"aqi_trend_same.png"))
            trendY = ay + (int(trend_icon.size[1]/2))

        if aqi_trend_ind == 1 :
            trend_icon = Image.open(os.path.join(weatherdir,"aqi_trend_up.png"))
            trendY = ay

        if aqi_trend_ind == -1 :
            trend_icon = Image.open(os.path.join(weatherdir,"aqi_trend_down.png"))
            trendY = ay + (int(trend_icon.size[1]))

        if trend_icon :
            trendX = int(ax - (trend_icon.size[0]+6))
            imageB.paste(trend_icon, (trendX,trendY),trend_icon)


        y = y + w_icon_row_height
        tomorrow_y = y


        '''
        if screen.use_red == 1 and red_sun == 1 :
            imageR.paste(s_icon, (x,y),s_icon)
            print("Sun in red")
        else: 
            imageB.paste(s_icon, (x,y),s_icon)
            print("Sun in black")
        Tx = int(x + s_icon.size[0]) + 4
        Ty = y
        draw_black.text((Tx,Ty),s_time , font = SFWdetails_semibold, fill = black)
        '''

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
        not_live_ind  = Image.open(os.path.join(picdir, "transit_not_live2.png"))
        not_live_ind_B  = Image.open(os.path.join(picdir, "transit_not_live_B.png"))
        not_live_ind_R  = Image.open(os.path.join(picdir, "transit_not_live_R.png"))

        live_ind_corner = Image.open(os.path.join(picdir, "transit_live_corner.png"))
        not_live_ind_corner = Image.open(os.path.join(picdir, "transit_notlive_corner.png"))

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
        applog("Transit feature" ,"Current hour is: "+str(hourglass.curenttime))
        applog("Transit feature" ,"Live cut in is: "+str(hourglass.live_cutin_hour))
        applog("Transit feature" ,"Live cut out is: "+str(hourglass.live_cutout_hour))
        if transit.use_live == 'TRUE':
            applog("Transit feature" ,"Live transit times is ON")
            if hourglass.curenttime >= hourglass.live_cutin_hour and hourglass.curenttime <= hourglass.live_cutout_hour:
                applog("Transit feature" ,"Live Transit Feature: within cut in times")
                live_transit_state = 1
                applog("Transit feature" ,"Attemting to get Live data for transit stop 1")
                get_transit_times1 = gettransitdepartures(datetime.now(),transit.api_key,transit.transit1_stop)
                applog("Transit feature" ,"Got "+str(len(get_transit_times1))+" live departures")
                if len(get_transit_times1) == 0:
                    applog("Transit feature" ,"No live data for stop 1 - fallback to static")
                    get_transit_times1 = next_transit(1)
                    live_transit_state = 0
                    transit_ind = not_live_ind
                    transit_ind_B = not_live_ind_B
                    transit_ind_R = not_live_ind_R
                applog("Transit feature" ,"Attemting to get Live data for transit stop 2")
                
                get_transit_times2 = gettransitdepartures(datetime.now(),transit.api_key,transit.transit2_stop)
                applog("Transit feature" ,"Got "+str(len(get_transit_times1))+" live departures")
                if len(get_transit_times2) == 0:
                    applog("Transit feature" ,"No live data for stop 2 - fallback to static")
                    get_transit_times1 = next_transit(2)
                    live_transit_state = 0
                    transit_ind = not_live_ind
                    transit_ind_B = not_live_ind_B
                    transit_ind_R = not_live_ind_R
            else :
                applog("Transit feature" ,"Getting static times")
                get_transit_times1 = next_transit(1)
                applog("Transit feature" ,"Got "+str(len(get_transit_times1))+" static departures for stop 1")
                get_transit_times2 = next_transit(2)
                applog("Transit feature" ,"Got "+str(len(get_transit_times2))+" static departures for stop 2")
                transit_ind = not_live_ind
                transit_ind_B = not_live_ind_B
                transit_ind_R = not_live_ind_R

        if transit.use_live == 'FALSE':
            live_transit_state = 0
            applog("Transit feature" ,"Getting static times")
            get_transit_times1 = next_transit(1)
            applog("Transit feature" ,"Got "+str(len(get_transit_times1))+" static departures for stop 1")
            get_transit_times2 = next_transit(2)
            applog("Transit feature" ,"Got "+str(len(get_transit_times2))+" static departures for stop 2")
            transit_ind = not_live_ind
            transit_ind_B = not_live_ind_B
            transit_ind_R = not_live_ind_R

        if live_transit_state == 1:
            imageB.paste(live_ind_corner, ( int(ti1X+t_icon1.size[0]-4) , int(ti1Y -(live_ind_corner.size[1]/2)) ),live_ind_corner)
        else :
            imageB.paste(not_live_ind_corner, ( int(ti1X+t_icon1.size[0]-4) , int(ti1Y - (not_live_ind_corner.size[1]/2)) ),not_live_ind_corner)

    
        dep_cnt = len(get_transit_times1)
        dept_text = draw_black.textbbox((0, 0), "00:00", font=SFTransitTime)
    
        bc = 0
        bx = ti1M - int(dept_text[2]/2)
        by = i1y + 70
        blx = bx + int(dept_text[2]) + 2
        bly = by + 8

        if dep_cnt >= 3 :

            for t in  get_transit_times1:
                draw_black.text((bx, by), t, font=SFTransitTime, fill=black)
                #if live_transit_state == 0  and screen.use_red == 1:
                    #imageR.paste(transit_ind_R,(blx,bly),transit_ind_R)
                    #imageB.paste(transit_ind_B,(blx,bly),transit_ind_B)
                #else:
                    #imageB.paste(transit_ind,(blx,bly),transit_ind)
                bc = bc +1
                by = by + (dept_text[3])
                bly = bly + (dept_text[3])
                if bc > 2:
                    break

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

        if live_transit_state == 1:
            imageB.paste(live_ind_corner, ( int(ti2X+t_icon2.size[0]-4) , int(ti2Y -(live_ind_corner.size[1]/2)) ),live_ind_corner)
        else :
            imageB.paste(not_live_ind_corner, ( int(ti2X+t_icon2.size[0]-4) , int(ti2Y - (not_live_ind_corner.size[1]/2)) ),not_live_ind_corner)


        dep_cnt = len(get_transit_times2)
        dept_text = draw_black.textbbox((0, 0), "00:00", font=SFTransitTime)
    
        bc = 0
        bx = ti2M - int(dept_text[2]/2)
        by = i2y + 70
        blx = bx + int(dept_text[2]) + 2
        bly = by + 8

        if dep_cnt >= 3 :
            
            for t in get_transit_times2 :
                draw_black.text((bx, by), t, font=SFTransitTime, fill=black)
                #if live_transit_state == 0 and screen.use_red == 1:
                    #imageR.paste(transit_ind_R,(blx,bly),transit_ind_R)
                    #imageB.paste(transit_ind_B,(blx,bly),transit_ind_B)
                #else:
                    #imageB.paste(transit_ind,(blx,bly),transit_ind)
                bc = bc +1
                by = by + (dept_text[3])
                bly = bly + (dept_text[3])
                if bc > 2:
                    break
    
        if dep_cnt == 0 :
            draw_black.text((x, y), "--:--", font=SFTransitTime, fill=black)



    
        #Drawing a line below weather and transit
        x = 10
        y = tomorrow_y

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
            tomorrow_string = fc_string+" | H:"+str(round(tomorrow_forecast.temp_high,1))+"\N{DEGREE SIGN}"+" L:"+str(round(tomorrow_forecast.temp_low,1))+"\N{DEGREE SIGN}"
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
            if screen.use_red == 1:
                imageR.paste(tomorrow_sunrise_icon, (x,(y+2)),tomorrow_sunrise_icon)
            else:
                imageB.paste(tomorrow_sunrise_icon, (x,(y+2)),tomorrow_sunrise_icon)
            x = x + int(tomorrow_sunrise_icon.size[0]) +2
            draw_black.text((x,y),datetime.fromtimestamp(today_weather.sun_rise).strftime('%H:%M') , font = SFWdetails_semibold, fill = black)
            y = y + int(test_t_h) + 2
            y = y + 5
        else:
            y = y +1
        x = 10
        screen_y = y

        draw_black.line([(x, y), (int(screen.width - (x*2)), y)], black)
    


    # MASK Section
    if dashboard.show_weather_details == 1 and aqi_sev>0:
        mask_icon = Image.open(os.path.join(picdir, "Mask.png"))
        x = w_x
        y = y + 4

        imageB.paste(mask_icon, (x,y), mask_icon)

        mtx = x + int(mask_icon.size[0]) + 8
        mty = y + 4
        mask_text = today_aqi.aqi_message
        mask_g, mask_g, mask_w, mask_h = draw_black.textbbox((0,0),mask_text, font = SFReminder)
        draw_black.text((mtx,mty),mask_text, font = SFReminder, fill=black)
        y = y + int(mask_h) + 15
        draw_black.line([(x, y), (int(screen.width - (x*2)), y)], black)
        y = y + 6
        screen_y = y




    # Quote Section

           #######
        ####     ####
        ####     #### 
        ####     ####
        ####     #### 
            #######  ###
    if dashboard.show_quote == 1:

        quote_icon = Image.open(os.path.join(picdir, "quote_icon.png"))
        quote_iconB = Image.open(os.path.join(picdir, "quote_b.png"))
        quote_iconR = Image.open(os.path.join(picdir, "quote_r.png"))

        qx = w_x
        qy = y + 8
    

        qml = 85
        qll = qml+1
        qmaxtries = 0
        applog("Quote of the day" ,"Hourglass day : "+str(hourglass.day))
        if hourglass.currentday > hourglass.day:
            applog("Quote of the day" ,"Time to get a new quote...")
            hourglass.day = int(datetime.now().strftime("%d"))

            applog("Quote of the day" ,"Getting a quote under "+str(qml)+" lenght")
            while qll >= qml :
                if dashboard.show_quote_live == 1:
                    applog("Quote of the day" ,"Getting random quote from the internet...")
                    dashboard.quote = quoteoftheday()
                else:
                    applog("Quote of the day" ,"Getting random quote from local database...")
                    dashboard.quote = quotefromfile("quotes.txt")
                qll = len(dashboard.quote.quote_text)
                qmaxtries +=1
                if qmaxtries > 10:
                    break
                if qll >  qml:
                    applog("Quote of the day" ,"Quote Feature : Attempt: "+str(qmaxtries))
                else:
                    applog("Quote of the day" ,"Quote lenght is "+str(qll))
            if qll == 0 :
            # Last effort to fill quote of the day if online fails
                quote_icon = Image.open(os.path.join(picdir, "quote_icon_disabled.png"))
                quote_iconB = Image.open(os.path.join(picdir, "quote_b_disabled.png"))
                quote_iconR = Image.open(os.path.join(picdir, "quote_r_disabled.png"))
                dashboard.quote = quotefromfile("quotes.txt")
                qll = len(dashboard.quote.quote_text)
    
            if qll > qml:
                applog("Quote of the day" ,"Max attempts to get a short enough quote exhausted.")
                #Just in case we could not find a short enough quote in 10 attempts.
                dashboard.quote.quote_text = "Sorry, No short Quote found, please adjust the \nquote-of-the-day-max-lenght value"
                dashboard.quote.quote_author = "Dashboard Ai"
            else :
                if dashboard.show_quote_live == 1:
                    addquotetofile("quotes.txt","quotes.txt",dashboard.quote.quote_text, dashboard.quote.quote_author)
                    applog("Quote of the day" ,dashboard.quote.quote_text)
                    applog("Quote of the day" ,dashboard.quote.quote_author)
                else:
                    quote_icon = Image.open(os.path.join(picdir, "quote_icon_disabled.png"))
        else:
            next_quote_hour = datetime.now() + timedelta(days=1)
            applog("Quote of the day" ,"Only one quote per day : Keeping quote, next one at "+next_quote_hour.strftime("%d")+" daycount at "+str(hourglass.day))
        #print("Now trying to slice the text in chunks")
        text_g, text_g, test_t_w, test_t_h = draw_black.textbbox((0,0),dashboard.quote.quote_text, font=SFQuote)
        text_max = test_t_w
        toff = x + int(quote_icon.size[0]+2)
        text_line_max = screen.quote_max - (toff + screen.offset)

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
        applog("Quote of the day" ,"Max pixels per line is "+str(text_line_max))

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
        gTy = gTy -2
        if screen.use_red == 1:
            draw_red.text((gTx, gTy), "- "+dashboard.quote.quote_author, font=SFQuoteAuthor, fill=black)
        else :
            draw_black.text((gTx, gTy), "- "+dashboard.quote.quote_author, font=SFQuoteAuthor, fill=black)
        gTy = gTy + int(q_h) + 2
        screen_y = gTy

        ###########################
        # End of Quote of the day
        ###########################
    if dashboard.show_todo == 1 :

        
        applog("Todoist feature" ,"geting todoist list...")

        todo_icon = Image.open(os.path.join(picdir, "tasks_icon.png"))
        todo_icon_B = Image.open(os.path.join(picdir, "tasks_iconB.png"))
        todo_icon_R = Image.open(os.path.join(picdir, "tasks_iconR.png"))
        todo_mini_icon  = Image.open(os.path.join(picdir, "todo_mini.png"))
        x = w_x
        y = screen_y
        
        draw_black.line([(x, y), (int(screen.width - (x*2)), y)], black)

        qx = w_x
        qy = screen_y + 4

        #Show the todo icon status
        if screen.use_red == 1:
            imageB.paste(todo_icon_B,(qx,qy),todo_icon_B)
            imageR.paste(todo_icon_R,(qx,qy),todo_icon_R)
        else:
            imageB.paste(todo_icon,(qx,qy),todo_icon)
        gTy = qy + 14
        gTx = x + int(todo_icon.size[0]+5)
        gTTop = gTy
        gTTy = int(qy + todo_icon.size[1] + 5)
        tg, tg, td_w, tdrow_h = draw_black.textbbox((0,0),"adjGgTsK", font=SFToDo)
        tg, tg, td_w_s, tdrow_h_s = draw_black.textbbox((0,0),",adjGgTsK", font=SFToDo_sub)
        daymonth = datetime.today().strftime("%d%m")


        if dashboard.todo_filter == "TODAY":
            applog("Todoist feature" ,"Getting only todo's due today...")
            show_dude_date = False
            today_todo_list = getodolistbyduedate(datetime.now())
        else:
            applog("Todoist feature" ,"Getting all todos due...")
            show_dude_date = True
            today_todo_list = gettodolist()
        numtodos = len(today_todo_list)
        applog("Todoist feature" ,"Got "+str(numtodos)+" tasks to show")
        tnum = 0
        tdrow = 0
        col_space = 0
        if numtodos > 0:
            today_todo_list.sort(key=lambda x: x.due_date, reverse=True) # Sort by Due date
            for tsk in today_todo_list:
                #tsk_title = "\u25E6"+tsk.content.replace('\n', '') # Shows a circle in front of text
                tsk_title = tsk.content.replace('\n', '')
                tg, tg, td_w, td_h = draw_black.textbbox((0,0),tsk_title, font=SFToDo)
                if int(td_w + (todo_mini_icon.size[0]*2)) > col_space:
                    col_space = int(td_w + (todo_mini_icon.size[0]*2))
                if int(gTx + col_space) >= int(screen.width - 5):
                    applog("Todoist feature" ,"No more space for tasks on screen...")
                    break
                imageB.paste(todo_mini_icon,(gTx, gTy),todo_mini_icon)
                draw_black.text((int(gTx+todo_mini_icon.size[0]+2), int(gTy - todo_mini_icon.size[1]/3)), tsk_title, font=SFToDo, fill=black)
                if show_dude_date and tsk.due_date:
                    due_daymonth = tsk.due_date.strftime("%d%m")
                    if due_daymonth == daymonth:
                        due_date_text = "Today"
                    else:
                        due_date_text = tsk.due_date.strftime("%A, %b %-d")
                    gTy = gTy + tdrow_h_s
                    
                    draw_black.text((int(gTx+todo_mini_icon.size[0]+8), int(gTy - todo_mini_icon.size[1]/3)), due_date_text, font=SFToDo_sub, fill=black)
                gTy = gTy + tdrow_h
                if gTy > gTTy:
                    gTTy = gTy
                tdrow +=1
                if tdrow == dashboard.todo_rows:
                    gTx = gTx + col_space
                    gTy = gTTop
                    col_space = 0
                    tdrow = 0
        else:
            todo_text = "All tasks are done!"
            tg, tg, t_w, t_h = draw_black.textbbox((0,0),todo_text, font=SFToDo)
            x = int(screen.middle_w - (t_w/2))
            y = gTy
            draw_black.text((x,y), todo_text, font=SFToDo, fill=black)
  

        if gTy > gTTy:
            screen_y = int(gTy)
        else:
            screen_y = gTTy
    else:
        applog("Todoist feature" ,"OFF")

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
    comparetime = hourglass.evening_hour
    gTy = screen_y
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
        applog("Garbage schedule" ,"there is garbage today")
        if screen.use_red == 1:
            imageB.paste(cal_todo_icon,(gTx, gTy),cal_todo_icon)
            imageR.paste(cal_todo_icon_R,(gTx, gTy),cal_todo_icon_R)
        else:
            imageB.paste(cal_todo_icon,(gTx, gTy),cal_todo_icon)
        gTx = gTx + int( cal_todo_icon.size[0] + 8 )
        gTy = gTy - 8
        if hourglass.curenttime <= comparetime:
            applog("Garbage schedule" ,"get ready for the truck!")
            g_image_end_icon = Image.open(os.path.join(picdir, 'Garbage_Truck.png'))
            g_string = garbage_vars['all-garbage-time-message-today-id']+ " "
            g_sub_sting = garbage_vars['all-garbage-collect-message-id']

            if g_data.landfill == 1:
                g_string = g_string + garbage_vars['landfill_title-id']
            if g_data.recycle == 1:
                if g_data.landfill == 1:
                    g_string = g_string + " & "
                g_string = g_string + garbage_vars['recycle_title-id']
            if g_data.compost == 1:
                if g_data.recycle == 1:
                    g_string = g_string + " & "
                g_string = g_string + garbage_vars['compost_title-id']
            if g_data.dumpster == 1:
                if g_data.compost == 1:
                    g_string = g_string + " & "
                g_string = g_string + garbage_vars['dumpster_title-id']
            if g_data.xmas_tree == 1:
                if g_data.dumpster == 1:
                    g_string = g_string + " & "
                g_string = g_string + garbage_vars['holiday-tree-schedule_title-id']
            g_string = g_string + " " + garbage_vars['all-garbage-time-message-end-id']

        else:
            applog("Garbage schedule" ,"Time to take the bins back in")
            g_image_end_icon = Image.open(os.path.join(picdir, 'Garbage_Garage.png'))
            g_string = garbage_vars['all-collection-time-over-message-line1-id']
            g_sub_sting = garbage_vars['all-collection-time-over-message-line2-id']
        #print("Now trying to slice the text in chunks")
        t_g, t_g, test_t_w, test_t_h = draw_black.textbbox((0,0),g_string, font=SFReminder)
        text_max = test_t_w
        text_line_max = screen.reminder_max  - gTx
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
        applog("Garbage schedule" ,"there is garbage tomorrow")
        if screen.use_red == 1:
            imageR.paste(cal_todo_iconR,(gTx, gTy),cal_todo_iconR)
            imageB.paste(cal_todo_iconB,(gTx, gTy),cal_todo_iconB)
        else:
            imageB.paste(cal_todo_icon,(gTx, gTy),cal_todo_icon)
        gTx = gTx + int( cal_todo_icon.size[0] + 8 )
        gTy = gTy - 8
        #Build the garbage schedule reminder string
        g_string = garbage_vars['all-garbage-time-message-tomorrow-id'] + " "
        if g_data.landfill_prepapre == 1:
            g_string = g_string + " "+garbage_vars['landfill_title-id']
        if g_data.recycle_prepare == 1:
            if g_data.landfill_prepapre == 1:
                g_string = g_string + " & "
            g_string = g_string + garbage_vars['recycle_title-id']
        if g_data.compost_prepare == 1:
            if g_data.recycle_prepare == 1:
                g_string = g_string + " & "
            g_string = g_string + garbage_vars['compost_title-id']
        if g_data.dumpster_prepapre == 1:
            if g_data.compost_prepare == 1:
                g_string = g_string + " & "
            g_string = g_string + garbage_vars['dumpster_title-id']
        g_string = g_string + " " + garbage_vars['all-garbage-time-message-end-id']

        #print("Now trying to slice the text in chunks")
        t_G, t_G, test_t_w, test_t_h = draw_black.textbbox((0,0),g_string, font=SFReminder)
        text_max = test_t_w
        text_line_max = screen.reminder_max - gTx
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
    data['evening_hour-id'] = parser.get("screen-config", "evening_hour")


    data['show_weather-id'] = parser.get("feature-config", "show_weather")
    data['show_weather_details-id'] = parser.get("feature-config", "show_weather_details")
    data['show_transit-id'] = parser.get("feature-config", "show_transit")
    data['show_quote-id'] = parser.get("feature-config", "show_quote")
    data['show_quote_live-id'] = parser.get("feature-config", "show_quote_live")
    data['show-todo-id'] = parser.get("feature-config", "show-todo")
    data['todo-rows-id'] = parser.get("feature-config", "todo-rows")
    data['todo-filter-id'] = parser.get("feature-config", "todo-filter")
    data['show-garbage-id'] = parser.get("feature-config", "show-garbage")

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
    applog("Inkframe" ,"Sleeping screen initiated")
    SleepFont = ImageFont.truetype("fonts/SF-Compact-Rounded-Semibold.otf",32)
    SleepFont_foot = ImageFont.truetype("fonts/SF-Compact-Rounded-Semibold.otf",24)
    SFWdetails_semibold = ImageFont.truetype("fonts/SF-Compact-Rounded-Semibold.otf",22)
    black = 'rgb(0,0,0)'
    white = 'rgb(255,255,255)'


    try:

        epd = epd7in5b_V2.EPD()
        epd.init()
        epd.Clear()
        screen.height = epd.height
        screen.width = epd.width
        screen.middle_w = screen.width/2
        screen.middle_h = screen.height/2
    except IOError as e:
        applog("Inkframe" ,"error"+str(e)) 

    except KeyboardInterrupt:
        applog("Inkframe" ,"ctrl + c received") 
        epd7in5b_V2.epdconfig.module_exit()
        exit()
    imageB = Image.new('L', (epd.width, epd.height), 255)  # 255: clear the frame
    imageR = Image.new('L', (epd.width, epd.height), 255)  # 255: clear the frame
    draw_black = ImageDraw.Draw(imageB)

    #  #  # ######   ##   ##### #    # ###### #####  
    #  #  # #       #  #    #   #    # #      #    # 
    #  #  # #####  #    #   #   ###### #####  #    # 
    #  #  # #      ######   #   #    # #      #####  
     ## ##  ###### #    #   #   #    # ###### #    # 
 
    if dashboard.show_weather == 1:
        forecast_weather = tomorrow_weather()
        tomorrow_forecast = forecast_weather[1]
        tmr_g, tmr_g, tmr_w, tmr_h = draw_black.textbbox((0,0),"Tomorrow: ", font=SFWdetails_semibold)
        x = 10
        y = int(tmr_h)
        draw_black.text((x,y),"Tomorrow: ", font = SFWdetails_semibold, fill = black)
        t_G, t_G, test_t_w, test_t_h = draw_black.textbbox((0,0),"Tomorrow :", font=SFWdetails_semibold)
        x = int(x + test_t_w)

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
        tomorrow_string = fc_string+" | H:"+str(round(tomorrow_forecast.temp_high,1))+"\N{DEGREE SIGN}"+" L:"+str(round(tomorrow_forecast.temp_low,1))+"\N{DEGREE SIGN}, feels like "+str(round(tomorrow_forecast.feels_like,1))+"\N{DEGREE SIGN}"
        popp = int(tomorrow_forecast.pop * 100)
        draw_black.text((x,y),tomorrow_string , font = SFWdetails_semibold, fill = black)
        t_G, t_G, test_t_w, test_t_h = draw_black.textbbox((0,0),tomorrow_string, font=SFWdetails_semibold)
        x = x + test_t_w + 2
        if popp > 0:
            imageB.paste(tomorrow_pop_icon, (x,(y+3)),tomorrow_pop_icon)
            x = x + int(tomorrow_pop_icon.size[0]) + 2
            draw_black.text((x,y),str(popp)+"%" , font = SFWdetails_semibold, fill = black)
            t_G, t_G, test_t_w, test_t_h = draw_black.textbbox((0,0),str(popp)+"%", font=SFWdetails_semibold)
            x = x + int(test_t_w) + 2

    sleep_icon = Image.open(os.path.join(picdir, 'sleep_icon.png'))

    sleep_string = "Good Night..."
    t_g, t_g, test_t_w, test_t_h = draw_black.textbbox((0,0),sleep_string, font=SleepFont)

    sX = int(screen.middle_w) - int(sleep_icon.size[0]/2)
    sY = int(screen.middle_h) - int(sleep_icon.size[1]/2)
    sY = sY - int(test_t_h)
    imageB.paste(sleep_icon, (sX,sY), sleep_icon)



    sX = int(screen.middle_w) - int(test_t_w/2)
    sY = int(sY + sleep_icon.size[1]) + 4
    draw_black.text((sX, sY), sleep_string, font = SleepFont, fill = 'rgb(0,0,0)')



    sleep_string = "Screen will wakeup tomorrow at "+str(screen.wake_hour)+", sleep well!"
    t_g, t_g, test_t_w, test_t_h = draw_black.textbbox((0,0),sleep_string, font=SleepFont_foot)
    sX = int(screen.width - (int(test_t_w) + 5))
    sY = int(screen.height - (int(test_t_h) + 5))
    draw_black.text((sX, sY), sleep_string, font = SleepFont_foot, fill = 'rgb(0,0,0)')

    epd.display(epd.getbuffer(imageB),epd.getbuffer(imageR))
    epd.sleep()
    wakeup_day = wake_date.strftime("%d")
    applog("Sleep screen" ,"Set to wake up on the "+wakeup_day)
    while True:
        applog("Sleep screen" ,"Entring coma...")
        if datetime.now().strftime("%d") == wakeup_day:
            if int(datetime.now().strftime("%H")) >= screen.wake_hour:
                break
        applog("Sleep screen" ,"Sleeping for one hour")
        time.sleep(3600)
        
def crashlog(file_path:str, crash_message: str):
    subdir = os.path.dirname(file_path)
    #print(subdir)
    if os.path.exists(subdir) == False:
        os.mkdir(subdir)
    aqi_array = []
    date_time_stamp = datetime.now().strftime("%m.%b.%Y, %H:%M:%S")
    my_file = open(file_path, 'a')
    applog("Inkscreen" ,"Logging crash message")
    my_file.write(date_time_stamp+" | "+crash_message+'\n')
    my_file.close

def applog(app_section: str ,app_message: str):
    date_time_stamp = datetime.now().strftime("%m.%b.%Y, %H:%M:%S")
    print(date_time_stamp+" | "+app_section+" | "+app_message)


def main():
    try:
        performance.cli = sys.argv[1]
    except:
        performance.cli = ""

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
    hourglass.evening_hour = int(dash_config['evening_hour-id'])
    applog("Inkscreen","Evening hour is set to: "+str(hourglass.evening_hour))
    applog("Inkscreen","Initial used RAM is: "+str(performance.usedram))
    while True :
        applog("Inkscreen","Screen sleep at: "+str(screen.sleep_hour))
        applog("Inkscreen","Wake up at: "+str(screen.wake_hour))
        min = 0
        hourglass.currentday = int(datetime.now().strftime("%d"))
        hourglass.last_refresh = datetime.now().strftime("Last Refresh @ %H:%M")
        hourglass.curenttime = int(datetime.now().strftime("%H"))
        hourglass.hour = int(datetime.now().strftime("%H"))
        applog("Inkscreen","it is now "+datetime.now().strftime("%H"))
        if int(datetime.now().strftime("%H")) < screen.sleep_hour:
            applog("Inkscreen","Time to draw the dashboard...")
            createDash()
        else:
            applog("Inkscreen","Time to go to sleep...")
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
        applog("System Performance","********************************")
        applog("System Performance","RAM: "+str(performance.usedram)+" used, and "+str(performance.freeram)+" free")
        applog("System Performance","RAM Previous was: "+str(performance.previousram))
        if trend == 1:
            applog("System Performance","Used RAM Increase by: "+str(performance.ramincrease))
        if trend == -1 :
            applog("System Performance","Used RAM Decresed by: "+str(performance.ramincrease))
        if trend == 0 :
            applog("System Performance","Used RAM unchanged")


        applog("System Performance","CPU Usage: "+cpuU)
        applog("System Performance","********************************")
        performance.previousram = performance.usedram

        applog("Inkscreen","Refresh in "+str(screen.refresh_rate_min)+" minutes")
        time.sleep((screen.refresh_rate_min*60))

if __name__ == "__main__":
    main()
