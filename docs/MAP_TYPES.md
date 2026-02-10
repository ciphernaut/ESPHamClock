# Map View types

The `set_mapview` REST API call controls the main map display on the HamClock client.

## API Endpoint

`GET /set_mapview?Style=S&Grid=G&Projection=P&RSS=on|off&Night=on|off`

### Parameters

| Parameter | Description | Valid Values |
| :--- | :--- | :--- |
| `Style` | The background map style. | See [Map Styles](#map-styles) |
| `Grid` | The coordinate grid overlay. | See [Grid Styles](#grid-styles) |
| `Projection` | The map projection. | See [Map Projections](#map-projections) |
| `RSS` | Toggle RSS feed banner. | `on`, `off` |
| `Night` | Toggle night cycle shading. | `on`, `off` |

---

## Map Styles

These values are passed to the `Style=` parameter. They correspond to the `CoreMaps` enum in `client/mapmanage.cpp`.

| Style Name | Description | Type | Source / Endpoint |
| :--- | :--- | :--- | :--- |
| `Countries` | Political map with country borders | File | `/maps/map-D-WxH-Countries.bmp` |
| `Terrain` | Physical terrain map | File | `/maps/map-D-WxH-Terrain.bmp` |
| `DRAP` | D-Region Absorption Prediction | File | `/maps/map-D-WxH-DRAP-S.bmp` |
| `MUF-VCAP` | VOACAP Max Usable Frequency | Query | `/fetchVOACAP-MUF.pl?...` |
| `MUF-RT` | Real-time MUF (JPL/GIM) | File | `/maps/map-D-WxH-MUF-RT.bmp` |
| `Aurora` | Ovation Prime Aurora forecast | File | `/maps/map-D-WxH-Aurora.bmp` |
| `Weather` | Global weather map | File | `/maps/map-D-WxH-Wx-{mB|in}.bmp` |
| `TOA` | VOACAP Take-Off Angle | Query | `/fetchVOACAP-TOA.pl?...` |
| `REL` | VOACAP Reliability | Query | `/fetchVOACAPArea.pl?...` |
| `Clouds` | Global cloud cover | File | `/maps/map-D-WxH-Clouds.bmp` |
| `User` | User-uploaded background | File | (User uploaded) |

### Query-Based Maps

The `MUF-VCAP`, `TOA`, and `REL` maps are generated dynamically using VOACAP. The client constructs a query string containing:
- `YEAR`, `MONTH`, `UTC`
- `TXLAT`, `TXLNG`
- `PATH` (Short/Long)
- `WATTS`
- `MHZ` (Frequency)
- `MODE` (SP, LP, etc.)

---

## Grid Styles

These values are passed to the `Grid=` parameter. Defined in `client/ESPHamClock.cpp`.

| Grid Name | Description |
| :--- | :--- |
| `None` | No grid |
| `Tropics` | Tropics of Cancer/Capricorn & Equator |
| `Lat/Long` | Standard Latitude/Longitude grid |
| `Maidenhead` | Maidenhead Locator grid |
| `Azimuthal` | Azimuthal equidistant grid centered on DE |
| `CQ Zones` | CQ Contest Zones |
| `ITU Zones` | ITU Administrative Zones |

---

## Map Projections

These values are passed to the `Projection=` parameter. Defined in `client/ESPHamClock.cpp`.

| Projection Name | Description |
| :--- | :--- |
| `Mercator` | Standard Mercator projection |
| `Azimuthal` | Azimuthal Equidistant (Global) |
| `Azim 1` | Azimuthal Equidistant (Hemisphere/Zoomed) |
| `Rob` | Robinson projection |
