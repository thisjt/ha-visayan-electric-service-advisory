# Visayan Electric Service Advisory Board for Home Assistant

## Overview

Get the latest service advisory from Visayan Electric Company and use it to
automate various home assistant automations such as conserving power, setting up
alternative power sources and many more depending on the scheduled outages and
maintenance. Uses the official
[VECO Service Advisory](https://www.visayanelectric.com/customer-services/service-advisory)
page to get the latest service advisories.

## Features

- **Real-time Data**: Fetches the latest bulletin directly everyday from VECO.
- **Manual Control**: Includes a button to force a data refresh.
- **Service Advisory List**: A list of service advisories that are currently active.
- **Service Advisory Details**: A list of service advisories that are currently active.


## Installation

### Method 1: HACS (Recommended)
We have yet to submit this module to the HACS repository. In the meantime, you can install it manually or use the custom repositories feature of HACS.

1. Ensure [HACS](https://hacs.xyz/) is installed.
2. Go to **HACS > Integrations**.
3. Click the menu (three dots) > **Custom repositories**.
4. Add the URL of this repository and select **Integration** as the category.
5. Click **Add**.
6. Search for "Visayan Electric Service Advisory Board" and click **Download**.
7. Restart Home Assistant.

### Method 2: Manual Installation
1. Download the `visayan_electric_service_advisory` folder from this repository.
2. Copy it to your Home Assistant's `config/custom_components/` directory.
3. Restart Home Assistant.

## Configuration

## Entities

## Dependencies

## License
MIT License