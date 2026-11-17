import os

from dotenv import load_dotenv

from aqi.ingestion.clients.openaq import OpenAQClient

# Read variables from the .env file.
load_dotenv()

# Get the API key without displaying it.
api_key = os.getenv("OPENAQ_API_KEY")

if not api_key:
    raise RuntimeError("OPENAQ_API_KEY was not found in the .env file.")


# Connect to OpenAQ and retrieve the example New Delhi location.
with OpenAQClient(api_key) as client:
    location = client.get_location(8118)

    print("OpenAQ connection successful")
    print("Location:", location.get("name"))
    print("Timezone:", location.get("timezone"))

    print("\nSensors:")

    for sensor in location.get("sensors", []):
        parameter = sensor.get("parameter", {})

        print(
            "Sensor ID:",
            sensor.get("id"),
            "| Parameter:",
            parameter.get("name"),
            "| Unit:",
            parameter.get("units"),
        )
