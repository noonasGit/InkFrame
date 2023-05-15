from dataclasses import dataclass
import requests
from requests.exceptions import RequestException
import json
import time
from typing import List
import configparser
from datetime import datetime, timedelta



@dataclass
class weather_forecast:
    date: int
    temp_low: float
    temp_high: float
    feels_like : float
    condition: str
    pop : int
    rain : dict
    snow : dict
    # icon's path
    icon: str

@dataclass
class weather_current:
    city: str
    temperature: float
    temp_high: float
    temp_low: float
    feelslike: float
    pressure: float
    humidity: float
    wind: float
    condition: str
    desciption: str
    icon: str
    sun_rise: int
    sun_set : int
    error : int

def get_weather_config_data(file_path:str):
    parser = configparser.ConfigParser()
    parser.read(file_path)
    data = dict()
    data['api-key-id'] = parser.get("weather-config", "api-key")
    data['lat-id'] = parser.get("weather-config", "lat")
    data['lon-id'] = parser.get("weather-config", "lon")
    data['units-id'] = parser.get("weather-config", "units")
    data['lang-id'] = parser.get("weather-config", "lang")
    parser.clear
    return data

def current_weather():
    connection_error = 0
    weather_config = dict()
    weather_config = get_weather_config_data("openweather.ini")


    base_url = "http://api.openweathermap.org/data/2.5/weather"
    apikey = "APPID="+weather_config['api-key-id']
    lat = "lat="+weather_config['lat-id']
    lon = "lon="+weather_config['lon-id']
    lang = "lang="+weather_config['lang-id']
    units = "units="+weather_config['units-id']
    


    #Construct the entire request URL
    url = base_url+"?"+apikey+"&"+lat+"&"+lon+"&"+units+"&"+lang
    #print("URL Constructed...")
    #print(url)
    api_error = ""
    print("Connecting to Weather API, current weather...")
    
    for attempt in range(2):
        try:
            rawresponse = requests.get(url)
            break  # If the requests succeeds break out of the loop
        except RequestException as e:
            api_error = format(e)
            print("API call failed {}".format(e))
            time.sleep(2 ** attempt)
            continue  # if not try again. Basically useless since it is the last command but we keep it for clarity
    #print(rawresponse.ok)   

    #print(rawresponse.text)

    if rawresponse.ok == True:
        return_data = []
        json_data = rawresponse.json()
        for i in json_data['weather']:
            weather_current.condition = i['main']
            weather_current.desciption = i['description']
            weather_current.icon = i['icon']


        
            weather_current.temperature = json_data['main']['temp']
            weather_current.feelslike = json_data['main']['feels_like']
            weather_current.temp_low = json_data['main']['temp_min']
            weather_current.temp_high = json_data['main']['temp_max']
            weather_current.pressure = json_data['main']['pressure']
            weather_current.humidity = json_data['main']['humidity']
            weather_current.wind = json_data['wind']['speed']
            #weather_current.wind_gust = json_data['wind']['gust']
            weather_current.city = json_data['name']
            weather_current.sun_rise = json_data['sys']['sunrise']
            weather_current.sun_set = json_data['sys']['sunset']

            return_data = weather_current(city=weather_current.city,
                                   temperature=weather_current.temperature,
                                   temp_high=weather_current.temp_high,
                                   temp_low=weather_current.temp_low,
                                   feelslike=weather_current.feelslike,
                                   pressure=weather_current.pressure,
                                   humidity=weather_current.humidity,
                                   wind=weather_current.wind,
                                   condition=weather_current.condition,
                                   desciption=weather_current.desciption,
                                   sun_rise=weather_current.sun_rise,
                                   sun_set=weather_current.sun_set,
                                   error=connection_error,
                                   icon=weather_current.icon)


        return return_data
    else:
        print("Error gettin data from Transi API, "+rawresponse.reason)
        if rawresponse.reason == "Unauthorized" :
            print("API KEY ISSUE!!")
            print("Please ensure you have entered a correct API key for transit in the openweather.ini file")
            print("####################################################################################")
            print(api_error)
            connection_error = 404
            return_data = weather_current(city="Error",
                          temperature=0,
                          temp_high=0,
                          temp_low=0,
                          feelslike=0,
                          pressure=0,
                          humidity=0,
                          wind=0,
                          condition="Error",
                          desciption="Error",
                          sun_rise=0,
                          sun_set=0,
                          error=connection_error,
                          icon="EE")
        return return_data


def get_forecast(numbdays:int):

    weather_config = dict()
    weather_config = get_weather_config_data("openweather.ini")


    base_url = "https://api.openweathermap.org/data/2.5/forecast"
    apikey = "APPID="+weather_config['api-key-id']
    lat = "lat="+weather_config['lat-id']
    lon = "lon="+weather_config['lon-id']
    lang = "lang="+weather_config['lang-id']
    units = "units="+weather_config['units-id']
    days = "cnt="+str(numbdays)
    


    #Construct the entire request URL
    url = base_url+"?"+apikey+"&"+lat+"&"+lon+"&"+units+"&"+lang+"&"+days
    #print("URL Constructed...")
    #print(url)
    api_error = ""
    print("Connecting to Weather API, forecast...")
    
    for attempt in range(2):
        try:
            rawresponse = requests.get(url)
            break  # If the requests succeeds break out of the loop
        except RequestException as e:
            api_error = format(e)
            print("API call failed {}".format(e))
            time.sleep(2 ** attempt)
            continue  # if not try again. Basically useless since it is the last command but we keep it for clarity
    #print(rawresponse.ok)   

    #print(rawresponse.text)

    if rawresponse.ok == True:
        return_data = []
        json_data = rawresponse.json()
        for i in json_data['list']:
            weather_forecast.date = datetime.utcfromtimestamp(i['dt'])
            
            weather_forecast.temp_high = i['main']['temp_max']
            weather_forecast.temp_low = i['main']['temp_min']
            weather_forecast.feels_like = i['main']['feels_like']
            weather_forecast.condition = i['weather'][0]['description']
            weather_forecast.pop = i['pop']
            weather_forecast.icon = i['weather'][0]['icon']
            try :
                weather_forecast.rain = i['rain']
                #print(i['rain'])
                #print(weather_forecast.rain['3h'])
            except:
                weather_forecast.rain = {'3h': 0}
            try :
                weather_forecast.snow =i['snow']
                #print(i['snow'])
            except:
                weather_forecast.snow = {'3h': 0}

            #print(i)
            dayofweather = weather_forecast.date
            print("Date: "+dayofweather.strftime("%b, %d"))
            print(i['dt_txt'])
            print(weather_forecast.date)
            print(weather_forecast.temp_high)
            print(weather_forecast.temp_low)
            print(weather_forecast.feels_like)
            print(weather_forecast.condition)
            print(weather_forecast.pop)
            print(weather_forecast.rain)
            print(weather_forecast.snow)
            print(weather_forecast.icon)

            

            return_data.append(weather_forecast(temp_high=weather_forecast.temp_high,
                                temp_low=weather_forecast.temp_low,
                                feels_like=weather_forecast.feels_like,
                                condition=weather_forecast.condition,
                                pop=weather_forecast.pop,
                                rain=weather_forecast.rain,
                                snow=weather_forecast.snow,
                                icon=weather_forecast.icon,
                                date=weather_forecast.date))


        return return_data
    else:
        print("Error gettin data from Transi API, "+rawresponse.reason)
        if rawresponse.reason == "Unauthorized" :
            print("API KEY ISSUE!!")
            print("Please ensure you have entered a correct API key for transit in the openweather.ini file")
            print("####################################################################################")
            print(api_error)
            return_data.append(weather_forecast(temp_high=0,
                        temp_low=0,
                        feels_like=0,
                        condition="Error",
                        pop=0,
                        rain=0,
                        snow=0,
                        icon="EE",
                        date=datetime.now()))

        return return_data

def tomorrow_weather():
    day_offset = 0
    tomorrow_day = datetime.now() + timedelta(days=day_offset)
    tomorrow_ref = int(tomorrow_day.strftime("%d"))
    weather_config = dict()
    weather_config = get_weather_config_data("openweather.ini")


    base_url = "https://api.openweathermap.org/data/2.5/forecast"
    apikey = "APPID="+weather_config['api-key-id']
    lat = "lat="+weather_config['lat-id']
    lon = "lon="+weather_config['lon-id']
    lang = "lang="+weather_config['lang-id']
    units = "units="+weather_config['units-id']
    
    return_data = []
    return_data: List[weather_forecast]

    #Construct the entire request URL
    url = base_url+"?"+apikey+"&"+lat+"&"+lon+"&"+units+"&"+lang
    #print("URL Constructed...")
    #print(url)
    api_error = ""
    print("Connecting to Weather API, forecast...")
    
    for attempt in range(2):
        try:
            rawresponse = requests.get(url)
            break  # If the requests succeeds break out of the loop
        except RequestException as e:
            api_error = format(e)
            print("API call failed {}".format(e))
            time.sleep(2 ** attempt)
            continue  # if not try again. Basically useless since it is the last command but we keep it for clarity
    #print(rawresponse.ok)   

    #print(rawresponse.text)

    if rawresponse.ok == True:
        json_data = rawresponse.json()
        for i in json_data['list']:
            tomorrow_check = int(datetime.utcfromtimestamp(i['dt']).strftime("%d"))
            #print("tomorrow check "+str(tomorrow_check))
            #print("tomorrow ref "+str(tomorrow_ref))
            #print(i['dt'])
            if tomorrow_check >= tomorrow_ref :
                #print("Next day")
                day_offset +=1

                tomorrow_day = datetime.now() + timedelta(days=day_offset)
                tomorrow_ref = int(tomorrow_day.strftime("%d"))


                weather_forecast.date = datetime.utcfromtimestamp(i['dt'])
            
                weather_forecast.temp_high = i['main']['temp_max']
                weather_forecast.temp_low = i['main']['temp_min']
                weather_forecast.feels_like = i['main']['feels_like']
                weather_forecast.condition = i['weather'][0]['description']
                weather_forecast.icon = i['weather'][0]['icon']
                weather_forecast.pop = i['pop']
                
                
                try :
                    weather_forecast.rain = i['rain']
                    #print(i['rain'])
                    #print(weather_forecast.rain['3h'])
                except:
                    weather_forecast.rain = {'3h': 0}
                try :
                    weather_forecast.snow =i['snow']
                    #print(i['snow'])
                except:
                    weather_forecast.snow = {'3h': 0}

                #print(i)
                #dayofweather = weather_forecast.date
                #print("Date: "+dayofweather.strftime("%b, %d"))
                #print(i['dt_txt'])
                #print(weather_forecast.date)
                #print(weather_forecast.temp_high)
                #print(weather_forecast.temp_low)
                #print(weather_forecast.feels_like)
                #print(weather_forecast.condition)
                #print(weather_forecast.icon)



            

                return_data.append(weather_forecast(date=weather_forecast.date,
                                        temp_high=weather_forecast.temp_high,
                                        temp_low=weather_forecast.temp_low,
                                        feels_like=weather_forecast.feels_like,
                                        condition=weather_forecast.condition,
                                        pop=weather_forecast.pop,
                                        rain=weather_forecast.rain,
                                        snow=weather_forecast.snow,
                                        icon=weather_forecast.icon))
            


        return return_data
    else:
        print("Error gettin data from Transi API, "+rawresponse.reason)
        if rawresponse.reason == "Unauthorized" :
            print("API KEY ISSUE!!")
            print("Please ensure you have entered a correct API key for transit in the openweather.ini file")
            print("####################################################################################")
            print(api_error)
            return_data.append(weather_forecast(temp_high=0,
                    temp_low=0,
                    feels_like=0,
                    condition="Error",
                    pop=0,
                    rain=0,
                    snow=0,
                    icon="EE",
                    date=datetime.now()))

        return return_data
