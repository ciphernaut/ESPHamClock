# Design Notes

## VOACAP Base Map Blending
- **Date**: 2026-02-06
- **Context**: Implemented service-side blending in `voacap_service.py` to simulate transparency.
- **Implementation**: Uses `blend_rgb565` to pre-compose propagation data over `Countries` or `Terrain` map.
- **Risk**: Using a "cooler" base map than the original server might make it harder to debug exact pixel parity if the original server uses a different baseline or simple solid colors.
- **Future Action**: If parity debugging becomes difficult, consider adding a query parameter to `voacap_service.py` to disable blending or switch to a "legacy" base map.

## Parity Verification Strategy
- **Goal**: Run multiple client instances with different backends to identify discrepancies.
- **Shadow Mode**: One client tracking the proxy in SHADOW mode (logging but not blocking).
- **Verify Mode**: Another client or proxy in VERIFY mode to capture authoritative discrepancies.
