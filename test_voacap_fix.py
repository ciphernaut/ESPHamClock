from backend.ingestion import voacap_service, band_service
import time

test_query = {'TXLAT': ['45'], 'TXLNG': ['-75'], 'RXLAT': ['51'], 'RXLNG': ['0']}
print("Generated Band Conditions:")
print(band_service.get_band_conditions(test_query))

print("\nDirect VOACAP Point test:")
muf, rel = voacap_service.calculate_point_propagation(45, -75, 51, 0, 14.0, 3.0, 2026, 2, 12, 131)
print(f"MUF: {muf:.2f}, REL: {rel:.2f}")
