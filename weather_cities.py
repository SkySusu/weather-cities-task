from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from collections import defaultdict
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


DEFAULT_CITIES_FILE = "cities.txt"


@dataclass(frozen=True)
class WeatherData:
    city: str
    temperature_celsius: int
    country: str


def load_cities(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as file:
        cities = [line.strip() for line in file if line.strip()]

    unique_cities: list[str] = []
    seen = set()
    for city in cities:
        key = city.casefold()
        if key not in seen:
            unique_cities.append(city)
            seen.add(key)

    return unique_cities


def fetch_weather(city: str) -> WeatherData:
    url = f"https://wttr.in/{quote(city)}?format=j1"
    request = Request(url, headers={"User-Agent": "weather-cities-task/1.0"})

    with urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))

    nearest_area = payload["nearest_area"][0]
    current_condition = payload["current_condition"][0]

    country = nearest_area["country"][0]["value"]
    temperature = int(current_condition["temp_C"])

    return WeatherData(
        city=city,
        temperature_celsius=temperature,
        country=country,
    )


def print_city_weather(items: list[WeatherData]) -> None:
    print("Weather by city:")
    for item in items:
        print(f"{item.city}, {item.country} {format_temperature(item.temperature_celsius)}")


def print_country_summary(items: list[WeatherData]) -> None:
    grouped: dict[str, list[WeatherData]] = defaultdict(list)
    for item in items:
        grouped[item.country].append(item)

    print()
    print("Summary by country:")
    for country in sorted(grouped):
        temperatures = [item.temperature_celsius for item in grouped[country]]
        average = round(sum(temperatures) / len(temperatures))
        minimum = min(temperatures)
        maximum = max(temperatures)
        count = len(temperatures)
        city_word = "city" if count == 1 else "cities"

        print(
            f"{country} — {count} {city_word}, "
            f"avg: {format_temperature(average)}, "
            f"min: {format_temperature(minimum)}, "
            f"max: {format_temperature(maximum)}"
        )


def format_temperature(value: int) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{value} °C"


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CITIES_FILE

    try:
        cities = load_cities(path)
        weather = [fetch_weather(city) for city in cities]
    except FileNotFoundError:
        print(f"Cities file not found: {path}", file=sys.stderr)
        return 1
    except (HTTPError, URLError, TimeoutError) as error:
        print(f"Failed to load weather data: {error}", file=sys.stderr)
        return 1
    except (KeyError, IndexError, ValueError, json.JSONDecodeError) as error:
        print(f"Unexpected weather API response: {error}", file=sys.stderr)
        return 1

    print_city_weather(weather)
    print_country_summary(weather)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
