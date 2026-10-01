import urllib.request
import json

base_api = 'http://127.0.0.1:8005'
base_fe = 'http://localhost:3005'

# 1. Health
with urllib.request.urlopen(f'{base_api}/health') as res:
    health = json.loads(res.read())
    assert health['status'] == 'healthy'
    assert health['offline_enforced'] is True
    print('PASS: /health is healthy and offline_enforced=True')

# 2. Trend real data
with urllib.request.urlopen(f'{base_api}/trend?region_id=BGD&parameter_id=air_temperature_2m&start_year=1980&end_year=2024') as res:
    trend = json.loads(res.read())
    assert trend['region']['id'] == 'BGD'
    assert len(trend['identity']['result_id']) == 64
    assert trend['provenance']['data_sha256'] is not None
    res_id = trend['identity']['result_id'][:16]
    data_sha = trend['provenance']['data_sha256'][:16]
    print(f'PASS: /trend BGD air_temp returned 200 with result_id={res_id}... and data_sha256={data_sha}...')

# 3. Unacquired dataset produces 404 with truthful message
try:
    urllib.request.urlopen(f'{base_api}/trend?region_id=USA&parameter_id=precipitation_total&start_year=2000&end_year=2024')
    raise AssertionError('Expected 404 for unacquired dataset')
except urllib.error.HTTPError as e:
    assert e.code == 404
    body = json.loads(e.read())
    assert 'Offline cache miss' in body['detail']
    print('PASS: /trend unacquired dataset produced truthful 404 error (No synthetic generation)')

# 4. Comparisons
req = urllib.request.Request(
    f'{base_api}/comparisons',
    data=json.dumps({
        'region_id_a': 'MOZ',
        'region_id_b': 'ZMB',
        'parameter_id': 'air_temperature_2m',
        'binding_id': 'NASA_MERRA2_M2TMNXSLV'
    }).encode(),
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req) as res:
    comp = json.loads(res.read())
    direction = comp['contrast_difference_series']['direction']
    assert direction in ['a_higher_rate', 'b_higher_rate', 'equal_rate']
    print(f'PASS: /comparisons returned parameter-neutral direction: {direction}')

# 5. Layers TileJSON, GeoJSON, and honest 501 Tile endpoint
with urllib.request.urlopen(f'{base_api}/layers/merra2_trend_slope/tilejson') as res:
    tilejson = json.loads(res.read())
    assert 'tiles' in tilejson
    print('PASS: /layers TileJSON valid')

with urllib.request.urlopen(f'{base_api}/layers/merra2_trend_slope/geojson') as res:
    geojson_data = json.loads(res.read())
    assert geojson_data['type'] == 'FeatureCollection'
    assert 'fdr_family_size' in geojson_data
    print('PASS: /layers GeoJSON regional summary returned with FDR statistics')

try:
    urllib.request.urlopen(f'{base_api}/tiles/merra2_trend_slope/0/0/0')
    raise AssertionError('Expected 501 for unrendered raster tiles')
except urllib.error.HTTPError as e:
    assert e.code == 501
    print('PASS: /tiles returned honest 501 Not Implemented (Raster tiles unavailable; vector GeoJSON supported)')


# 6. Frontend
with urllib.request.urlopen(f'{base_fe}/') as res:
    html = res.read().decode('utf-8', errors='ignore')
    assert res.status == 200
    assert 'fonts.googleapis.com' not in html
    assert 'Earth System Trend Detective' in html
    print('PASS: Frontend loaded 200 OK without any Google Fonts CDN references')

print('\nALL END-TO-END CRITERIA VERIFIED!')
