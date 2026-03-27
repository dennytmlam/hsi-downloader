#!/usr/bin/env python3
"""Simple weather checker using wttr.in (no API key required)"""

import requests
import sys

def get_weather(location="Hong Kong"):
    """Get current weather for a location using wttr.in"""
    url = f"http://wttr.in/{location}?format=j1"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Current weather
        current = data['current_condition'][0]
        temp_c = current['temp_C']
        temp_f = current['temp_F']
        weather_desc = current['weatherDesc'][0]['value']
        humidity = current['humidity']
        wind_kmph = current['windspeedKmph']
        
        # 3-day forecast
        forecasts = data['weather'][0]['hourly'][:3]
        
        print(f"\n🌤️  Weather in {location}")
        print("=" * 40)
        print(f"Current: {weather_desc}")
        print(f"Temperature: {temp_c}°C ({temp_f}°F)")
        print(f"Humidity: {humidity}%")
        print(f"Wind: {wind_kmph} km/h")
        print("\nNext 3 hours:")
        print("-" * 40)
        
        for hour in forecasts[:3]:
            time = int(str(hour['time'])[-2:])
            temp = hour['tempC']
            desc = hour['weatherDesc'][0]['value']
            print(f"  {time:02d}:00 - {desc}, {temp}°C")
        
        print()
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching weather: {e}")
        sys.exit(1)
    except (KeyError, IndexError) as e:
        print(f"❌ Error parsing weather data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    location = sys.argv[1] if len(sys.argv) > 1 else "Hong Kong"
    get_weather(location)
