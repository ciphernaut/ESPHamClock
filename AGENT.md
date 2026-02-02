# ESPHamClock - Agent Development Guide
This guide provides essential information for AI agents working on the ESPHamClock project, a comprehensive amateur radio weather and propagation display system.
The prime objective of this project is to develop the backend to workl with the existing client.

## Project Architecture
ESPHamClock consists of three main components:
- **Backend**: Python HTTP server (`backend/server.py`) providing weather, propagation, and geolocation services
- **Proxy**: Shadow proxy (`proxy/proxy.py`) for external service integration and development
- **Client**: Compiled C++ application (`client/`) with multiple build targets (X11, web, framebuffer)

## Build Commands
### C++ Client (Primary)
```bash
cd client
make hamclock-web-1600x960    # Web server version (default target)
make hamclock-1600x960         # X11 GUI version
make hamclock-800x480          # Smaller version
make clean                     # Clean build artifacts
make install                   # Install system-wide (requires sudo)
```
**Available targets:**
- X11 GUI: `hamclock-800x480`, `hamclock-1600x960`, `hamclock-2400x1440`, `hamclock-3200x1920`
- Web server: `hamclock-web-800x480`, `hamclock-web-1600x960`, `hamclock-web-2400x1440`
- Framebuffer: `hamclock-fb0-800x480`, `hamclock-fb0-1600x960` (Raspberry Pi)
**Build options:**
```bash
make FB_DEPTH=16 hamclock-1600x960      # 16-bit framebuffer
make WIFI_NEVER=1 hamclock-1600x960     # Disable WiFi configuration
```

### Python Backend
```bash
# Individual services
python3 backend/server.py                           # Main HTTP server (port 9086)
python3 backend/ingestion/scheduler.py              # Data scheduler
# Stack management (recommended)
./run_stack.sh start backend    # Start backend only
./run_stack.sh start all        # Start full stack
./run_stack.sh status           # Check service status
```
## Testing Commands
### Backend Services
```bash
# Run individual tests
python3 backend/scripts/verify_stability.py         # Full endpoint testing
python3 backend/scripts/test_weather.py             # Weather service tests
python3 backend/scripts/test_voacap_diversity.py    # VOACAP map testing
python3 backend/scripts/test_sdo_local.py           # SDO image processing
# Quick health check (manual endpoint testing)
curl http://localhost:9086/fetchIPGeoloc.pl
curl http://localhost:9086/geomag/kindex.txt
```
### Integration Testing
```bash
# Start full stack first
./run_stack.sh start all
# Test client access
curl http://localhost:8081/                           # Web client interface
curl http://localhost:9085/                           # Proxy interface
```
## Code Style Guidelines
### Python (Backend Services)
**Imports:**
```python
# Standard library imports first
import os
import json
import logging
import time
# Third-party imports second
import requests
# Local imports third (use absolute paths)
import geoloc_service
import weather_service
```
**Logging:**
```python
import logging
logger = logging.getLogger(__name__)
def my_function():
    logger.info("Information message")
    logger.warning("Warning condition")
    logger.error(f"Error occurred: {error_details}")
```
**Error Handling:**
```python
try:
    # Operation that might fail
    result = risky_operation()
except Exception as e:
    logger.error(f"Error in operation: {e}")
    return None  # or raise with context
```
**Path Handling:**
```python
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "processed_data")
cache_file = os.path.join(DATA_DIR, "cache.json")
```
**Constants:**
```python
UPPER_CASE_CONSTANT = "value"
API_TIMEOUT = 30
CACHE_TTL = 3600
```
### C++ (Client Application)
**File Headers:**
```cpp
/* HamClock Module Name
 * Brief description of module purpose
 */
```
**Includes:**
```cpp
// System headers
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
// Project headers
#include "HamClock.h"
#include "ArduinoLib.h"
```
**Naming Conventions:**
- Functions: `snake_case_function_name()`
- Variables: `snake_case_variable_name` (local), `camelCaseVariable` (some globals)
- Constants: `UPPER_CASE_MACROS`
- Types: `PascalCaseStruct`
- Files: `snake_case_module.cpp`
**Global Variables:**
```cpp
// Screen boxes and coordinates
SBox clock_b = { 0, 65, 230, 49};
static SBox askdx_b;                    // dx lat/lng dialog
// Time zone state
TZInfo de_tz = {{75, 158, 50, 17}, DE_COLOR, de_ll, true, 0};
```
**Function Structure:**
```cpp
void function_name(type param1, type param2)
{
    // Local variables
    int local_var;
    bool success = false;
    
    // Implementation
    if (condition) {
        success = true;
    }
    
    return;
}
```
## Development Workflow
### 1. Backend Changes
1. Modify services in `backend/ingestion/` or main `backend/server.py`
2. Test with `python3 backend/scripts/verify_stability.py`
3. Restart services: `./run_stack.sh restart backend`
### 2. Client Changes  
1. Modify C++ files in `client/`
2. Rebuild: `cd client && make hamclock-web-1600x960`
3. Restart client: `./run_stack.sh restart client`
### 3. Full Stack Testing
```bash
./run_stack.sh stop all
./run_stack.sh start all
sleep 5
./run_stack.sh status
python3 backend/scripts/verify_stability.py
```
## Key Directories
- `client/` - C++ application source code and build system
- `backend/ingestion/` - Data fetching services (weather, propagation, etc.)
- `backend/scripts/` - Testing and utility scripts  
- `backend/data/processed_data/` - Cached data files
- `proxy/` - Shadow proxy for development
- `logs/` - Runtime logs and stack output
## Debugging Tips
**Backend Logs:**
```bash
tail -f logs/server.log        # Main server logs
tail -f logs/scheduler.log     # Data scheduler logs
```
**Common Issues:**
- Port conflicts: Check `./run_stack.sh status` before starting
- Missing data: Services gracefully degrade with cached data
- Build failures: Ensure all subdirectories are present and clean build if needed
## Service Ports
- Backend API: 9086
- Shadow Proxy: 9085  
- Web Client: 8081
## Testing Individual Services
**Weather Service:**
```python
# In backend/ingestion/weather_service.py
from weather_service import fetch_weather, get_prevailing_stats
data = fetch_weather(40.7, -74.0)  # NYC coordinates
stats = get_prevailing_stats()
```
**VOACAP Service:**
```python
# In backend/ingestion/voacap_service.py  
from voacap_service import get_muf_toa_map
map_data = get_muf_toa_map(40.7, -74.0, time.time())
```
Remember: The project uses file-based caching extensively for performance and resilience. Always check for existing cached data before implementing new data fetching logic.
