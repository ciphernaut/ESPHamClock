import zlib
import os

files = os.listdir('/tmp/sdo_cache')
with open('sdo_debug.txt', 'w') as out:
    for f in files:
        if f.endswith('.z'):
            path = os.path.join('/tmp/sdo_cache', f)
            try:
                with open(path, 'rb') as zf:
                    comp_data = zf.read()
                    comp_header = comp_data[:10].hex()
                    data = zlib.decompress(comp_data)
                    header = data[:20].hex()
                    is_bm = data[:2] == b'BM'
                    out.write(f"{f}: size={len(data)}, is_bm={is_bm}, c_hdr={comp_header}, header={header}\n")
            except Exception as e:
                out.write(f"{f}: error={e}\n")
