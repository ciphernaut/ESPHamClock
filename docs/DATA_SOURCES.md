# Data Sources

This project uses several external data sources to power its features. This document outlines the sources, their usage, and any deviations from the original HamClock implementation.

## Weather Data

### Source: wttr.in / Open-Meteo
- **Primary Source**: [wttr.in](https://wttr.in) (which acts as a frontend for various weather data models).
- **Secondary/Fallback**: [Open-Meteo](https://open-meteo.com).
- **Original HamClock Source**: OpenWeatherMap (OWM).

### Reason for Divergence
The original HamClock uses OpenWeatherMap, which requires an API key. To simplify deployment and avoid requiring every user to obtain an API key for basic functionality, this project defaults to keyless services (`wttr.in` and `Open-Meteo`).

### Parity and Attribution
- The `get_dx.txt` endpoint mimics the original HamClock format.
- **Attribution**: The attribution field in `get_dx.txt` has been updated to `wttr.in` to correctly reflect the source, whereas the original server (and our previous implementation) stated `openweathermap.org`.
- **Data Variances**: Users may notice differences in specific weather values (temperature, wind speed/direction, condition text) between this project and the original HamClock due to the different underlying meteorological models used by OWM vs. Open-Meteo/wttr.in.

### Impact on Propagation
**None.** 
Extensive code analysis confirms that terrestrial weather data (temperature, pressure, humidity, wind) is **NOT** used in any propagation calculations (VOACAP, DRAP, etc.). Propagation logic relies exclusively on Space Weather data (SSN, Solar Flux, Kp Index, Bz, Solar Wind Speed), which are sourced separately from NOAA/SWPC.

## Space Weather Data
- **Source**: NOAA Space Weather Prediction Center (SWPC).
- **Usage**: Driver for VOACAP, DRAP, and Aurora model visualizations.
