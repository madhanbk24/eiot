import requests
import time
from datetime import datetime, timedelta

# Function to get user's location using IP address
def get_user_location():
    try:
        response = requests.get("https://ipinfo.io")
        data = response.json()
        location = data.get("loc")
        return location.split(',')
    except Exception as e:
        print(f"Error getting location: {e}")
        return None

# Function to get weather information for a given location
def get_weather_info(api_key, lat, lon):
    try:
        base_url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": api_key,
            "units": "metric"  # Use Celsius for temperature
        }
        response = requests.get(base_url, params=params)
        weather_data = response.json()
        return weather_data
    except Exception as e:
        print(f"Error getting weather data: {e}")
        return None

# Function to get ThingSpeak data for field 1
def get_thingspeak_data():
    try:
        thingspeak_url = "https://api.thingspeak.com/channels/1800115/feeds.json?results=1"
        response = requests.get(thingspeak_url)
        data = response.json()
        field1 = data['feeds'][0]['field1']
        field2 = data['feeds'][0]['field2']
        return [int(field1),int(field2)]
    except Exception as e:
        print(f"Error getting ThingSpeak data: {e}")
        return None

# Function to update ThingSpeak fields with motor status and next on times
def update_thingspeak(api_key, field1, field2, field3, field4,field5,field6,field7,field8):
    try:
        thingspeak_url = f"https://api.thingspeak.com/update?api_key={api_key}&field1={field1}&field2={field2}&field3={field3}&field4={field4}&field5={field5}&field6={field6}&field7={field7}&field8={field8}"
        response = requests.get(thingspeak_url)
        return response.status_code == 200
    except Exception as e:
        print(f"Error updating ThingSpeak: {e}")
        return False

# Function to control the motor
def control_motor(motor, turn_on):
    if turn_on:
        print(f"Motor {motor} is ON")
    else:
        print(f"Motor {motor} is OFF")

if __name__ == "__main__":
    # Replace 'YOUR_API_KEY' with the provided OpenWeatherMap API key
    api_key = "ce5d16dd2ea5b63d67b8fbcd88af0389"
    
    # Replace 'YOUR_THINGSPEAK_API_KEY' with your ThingSpeak API key
    thingspeak_api_key = "I4PLB69HDZ2CMFHV"

    # Get user's location
    user_location = get_user_location()
    if user_location:
        lat, lon = user_location
        print(f"Latitude: {lat}, Longitude: {lon}")

        # Get weather information
        weather_data = get_weather_info(api_key, lat, lon)
        if weather_data:
            temperature = weather_data["main"]["temp"]
            description = weather_data["weather"][0]["description"]
            humidity = weather_data["main"]["humidity"]
            
            # Check for rain information
            if "rain" in weather_data:
                rain_info = weather_data["rain"]
                precipitation = rain_info.get("3h", 0)  # Precipitation in the last 3  hour
                is_raining_now = precipitation > 0
            else:
                precipitation = 0
                is_raining_now = False

            print(f"Weather: {description}")
            print(f"Temperature: {temperature}°C")
            print(f"Humidity: {humidity}%")
            print(f"Precipitation (last 3 hour): {precipitation} mm")
            print(f"Is Raining Now: {is_raining_now}")

            # Get ThingSpeak data for field 1
            field1 = get_thingspeak_data()[0]
            field2 = get_thingspeak_data()[1]
            
                

            if field2 and field1 is not None:
                print(f"ThingSpeak Field 1 Value: {field1} and Field 2 value: {field2}")   # Calculate the next scheduled time to turn on the motors
                current_time = datetime.now()
                next_time_motor1_on = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
                next_time_motor1_off = current_time.replace(hour=9, minute=30, second=0, microsecond=0)
                next_time_motor2_on = current_time.replace(hour=8, minute=30, second=0, microsecond=0)
                next_time_motor2_off = current_time.replace(hour=9, minute=30, second=0, microsecond=0)
                motor1_on = False
                motor2_on = False

                while True:
                    # Get ThingSpeak data for field 1
                    field1 = get_thingspeak_data()[0]
                    field2 = get_thingspeak_data()[1]
                    #Calculate the next scheduled time to turn on the motors
                    current_time = datetime.now()
                    if not is_raining_now:  # Check if it's not raining
                        if current_time >= next_time_motor1_off:
                            # Schedule Motor 1 for the next day at 9:00 AM
                            next_time_motor1_on = current_time + timedelta(days=field1)
                            next_time_motor1_on = next_time_motor1_on.replace(hour=9, minute=0, second=0, microsecond=0)
                            next_time_motor1_off = current_time + timedelta(days=field1)
                            next_time_motor1_off = next_time_motor1_off.replace(hour=9, minute=30, second=0, microsecond=0)
                        
                        if current_time >= next_time_motor2_off:
                            # Schedule Motor 2 for the next day at 8:30 AM
                            next_time_motor2_on = current_time + timedelta(days=field2)
                            next_time_motor2_on = next_time_motor2_on.replace(hour=8, minute=30, second=0, microsecond=0)
                            next_time_motor2_off = current_time + timedelta(days=field2)
                            next_time_motor2_off = next_time_motor2_off.replace(hour=9, minute=30, second=0, microsecond=0)
                        
                        if next_time_motor1_on <= current_time < next_time_motor1_off:
                            # It's between 9:00 AM and 9:30 AM for Motor 1, turn it on
                            if not motor1_on:
                                control_motor("1", True)
                                motor1_on = True
                        else:
                            if motor1_on:
                                control_motor("1", False)
                                motor1_on = False
                        
                        if next_time_motor2_on <= current_time < next_time_motor2_off:
                            # It's between 8:30 AM and 9:30 AM for Motor 2, turn it on
                            if not motor2_on:
                                control_motor("2", True)
                                motor2_on = True
                        else:
                            if motor2_on:
                                control_motor("2", False)
                                motor2_on = False
                    else:
                        # If it's raining, skip the current day and move to the next day
                        next_time_motor1_on = current_time + timedelta(days=field1)
                        next_time_motor1_on = next_time_motor1_on.replace(hour=9, minute=0, second=0, microsecond=0)
                        next_time_motor1_off = current_time + timedelta(days=field1)
                        next_time_motor1_off = next_time_motor1_off.replace(hour=9, minute=30, second=0, microsecond=0)
                        next_time_motor2_on = current_time + timedelta(days=field2)
                        next_time_motor2_on = next_time_motor2_on.replace(hour=8, minute=30, second=0, microsecond=0)
                        next_time_motor2_off = current_time + timedelta(days=field2)
                        next_time_motor2_off = next_time_motor2_off.replace(hour=9, minute=30, second=0, microsecond=0)
                        motor1_on = False
                        motor2_on = False
                    
                    # Update ThingSpeak fields
                    motor1_status = int(motor1_on)  # 1 if motor1_on is True, else 0
                    motor2_status = int(motor2_on)  # 1 if motor2_on is True, else 0
                    motor1_next_on = next_time_motor1_on.strftime("%Y-%m-%d %H:%M:%S")
                    motor2_next_on = next_time_motor2_on.strftime("%Y-%m-%d %H:%M:%S")
                    
                    update_thingspeak(thingspeak_api_key, motor1_status, motor2_status, motor1_next_on, motor2_next_on,current_time,temperature,humidity,is_raining_now)

                    print(f"Current Time: {current_time}")
                    print(f"Next Motor 1 On Time: {next_time_motor1_on}")
                    print(f"Next Motor 1 Off Time: {next_time_motor1_off}")
                    print(f"Next Motor 2 On Time: {next_time_motor2_on}")
                    print(f"Next Motor 2 Off Time: {next_time_motor2_off}")
                    print("----------------------------------------------------")
                    time.sleep(10)  # Check every minute
                    
            else:
                print("Unable to get ThingSpeak data.")
        else:
            print("Unable to get weather information.")
    else:
        print("Unable to get location information.")
