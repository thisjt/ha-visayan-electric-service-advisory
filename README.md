# Visayan Electric Service Advisory for Home Assistant

## Overview

Automatically track and alert on service interruptions from Visayan Electric Company (VECO). This integration scrapes the official [VECO Service Advisory](https://www.visayanelectric.com/customer-services/service-advisory) page, follows the latest advisory post, and parses all scheduled maintenance and outages into Home Assistant entities.

## Features

- **Automated Scraping**: Fetches the latest bulletin daily (every 6 hours by default).
- **Full Detail Extraction**: Unlike simple excerpt scrapers, this follows the post link to extract full details for every advisory in the post (Time, Purpose, Areas Affected, and Map images).
- **Location Alerts**: Configure your specific locations (e.g., "Canduman", "Jagobiao") to get a binary "Problem" alert if your area is affected.
- **Manual Control**: Includes a button to force an immediate data refresh.

## Installation

### Method 1: HACS (Recommended)
1. Ensure [HACS](https://hacs.xyz/) is installed.
2. Go to **HACS > Integrations**.
3. Click the menu (three dots) > **Custom repositories**.
4. Add the URL of this repository and select **Integration** as the category.
5. Click **Add**.
6. Search for "Visayan Electric Service Advisory" and click **Download**.
7. Restart Home Assistant.

### Method 2: Manual Installation
1. Download the `visayan_electric_service_advisory` folder.
2. Copy it to your Home Assistant's `config/custom_components/` directory.
3. Restart Home Assistant.

## Configuration

When adding the integration, you can provide a list of locations (one per line or comma-separated) that you want to monitor. The integration will search for these keywords in the "Areas Affected" field of every advisory.

## Entities

- **`sensor.visayan_electric_service_advisories`**: Reports the total number of advisories in the latest post. Attributes contain the full list of parsed advisories.
- **`binary_sensor.visayan_electric_area_affected`**: Turns `on` (Problem) if any of your configured locations are mentioned in an active (non-cancelled) advisory.
- **`button.visayan_electric_manual_scrape`**: Press to manually trigger a fetch of the latest data.

## Automation Examples

### Alert when your area is affected
This automation sends a notification to your mobile device if a new advisory is found that affects your configured locations.

```yaml
alias: "Alert: Power Interruption Advisory"
description: "Notify when a scheduled power interruption affects our area"
trigger:
  - platform: state
    entity_id: binary_sensor.visayan_electric_area_affected
    from: "off"
    to: "on"
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "⚠️ VECO Service Advisory"
      message: >
        {% set adv = state_attr('binary_sensor.visayan_electric_area_affected', 'matching_advisories')[0] %}
        A scheduled interruption is planned for {{ adv.date }} from {{ adv.time }}.
        Purpose: {{ adv.purpose }}
        Areas: {{ adv.areas_affected }}
      data:
        image: "{{ state_attr('binary_sensor.visayan_electric_area_affected', 'matching_advisories')[0].map }}"
        clickAction: "{{ state_attr('binary_sensor.visayan_electric_area_affected', 'matching_advisories')[0].post_url }}"
```

### Displaying advisories in a dashboard
You can use the `flex-table-card` or a simple `Markdown` card to display the list of upcoming interruptions:

```yaml
type: markdown
content: >
  ### Upcoming VECO Advisories
  {% for adv in state_attr('sensor.visayan_electric_service_advisories', 'advisories') %}
  **Date**: {{ adv.date }} | **Time**: {{ adv.time }}
  **Purpose**: {{ adv.purpose }}
  **Areas**: {{ adv.areas_affected }}
  {% if adv.map %}![Map]({{ adv.map }}){% endif %}
  ---
  {% endfor %}
```

## License
MIT License