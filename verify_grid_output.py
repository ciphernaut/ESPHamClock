def verify_wx_file():
    target_locations = {
        "India": {"lat": 28.0, "lng": 77.0, "expected_tz": 19800},
        "Adelaide": {"lat": -34.0, "lng": 138.0, "expected_tz": 34200}, # Use grid snap points
        "Sri Lanka": {"lat": 8.0, "lng": 80.0, "expected_tz": 19800},   # UTC+5:30
    }
    
    found = {}
    
    with open('data/processed_data/worldwx/wx.txt', 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            parts = line.split()
            if len(parts) < 9: continue
            
            try:
                lat = float(parts[0])
                lng = float(parts[1])
                tz = int(parts[8])
            except ValueError:
                continue
            
            # Simple approximate match for grid points
            for name, loc in target_locations.items():
                if abs(lat - loc['lat']) < 2.0 and abs(lng - loc['lng']) < 2.5:
                    found[name] = {"lat": lat, "lng": lng, "tz": tz}

    print("Verification Results:")
    for name, data in found.items():
        expected = target_locations[name]['expected_tz']
        print(f"{name}: Found TZ={data['tz']} (Expected {expected})")
        
verify_wx_file()
