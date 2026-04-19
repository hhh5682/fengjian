#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import io
from dotenv import load_dotenv
from services.provider_clients import AMapClient

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

def test_route_planning():
    amap = AMapClient()
    
    print("=" * 60)
    print("[TEST] AMap Route Planning")
    print("=" * 60)
    print("[INFO] API Key: {}...".format(amap.api_key[:20] if amap.api_key else "NOT SET"))
    print("[INFO] Security Code: {}...".format(amap.security_code[:20] if amap.security_code else "NOT SET"))
    print("[INFO] API Ready: {}".format(amap.is_ready()))
    print()
    
    if not amap.is_ready():
        print("[ERROR] AMap API not ready")
        return False
    
    print("[STEP 1] Search for Xiangbishan coordinates")
    print("-" * 60)
    pois_start = amap.search_poi("象鼻山", city="桂林", page_size=1)
    if pois_start:
        start_poi = pois_start[0]
        start_coords = "{},{}".format(start_poi['lng'], start_poi['lat'])
        print("[OK] Found: {}".format(start_poi['name']))
        print("[OK] Coords: {}".format(start_coords))
        print("[OK] Address: {}".format(start_poi['address']))
    else:
        print("[WARN] POI search failed, trying geocode...")
        geo = amap.geocode("象鼻山", city="桂林")
        if geo.get("lat") and geo.get("lng"):
            start_coords = "{},{}".format(geo['lng'], geo['lat'])
            print("[OK] Geocode success: {}".format(start_coords))
        else:
            print("[ERROR] Geocode failed")
            return False
    print()
    
    print("[STEP 2] Search for Chunji Shaoye coordinates")
    print("-" * 60)
    pois_end = amap.search_poi("椿记烧鹅", city="桂林", page_size=3)
    if pois_end:
        end_poi = None
        for poi in pois_end:
            if "滨江" in poi['address'] or "滨江" in poi['name']:
                end_poi = poi
                break
        if not end_poi:
            end_poi = pois_end[0]
        
        end_coords = "{},{}".format(end_poi['lng'], end_poi['lat'])
        print("[OK] Found: {}".format(end_poi['name']))
        print("[OK] Coords: {}".format(end_coords))
        print("[OK] Address: {}".format(end_poi['address']))
    else:
        print("[WARN] POI search failed, trying geocode...")
        geo = amap.geocode("椿记烧鹅", city="桂林")
        if geo.get("lat") and geo.get("lng"):
            end_coords = "{},{}".format(geo['lng'], geo['lat'])
            print("[OK] Geocode success: {}".format(end_coords))
        else:
            print("[ERROR] Geocode failed")
            return False
    print()
    
    print("[STEP 3] Plan routes")
    print("-" * 60)
    
    modes = ["driving", "transit", "walking"]
    results = {}
    
    for mode in modes:
        print("\n[MODE] {}".format(mode.upper()))
        route = amap.route_plan(start_coords, end_coords, mode=mode, city="桂林")
        results[mode] = route
        
        if route.get("distance_m"):
            print("[OK] Distance: {:.0f}m".format(route['distance_m']))
            print("[OK] Duration: {:.0f}s ({:.1f}min)".format(route['duration_s'], route['duration_s']/60))
            if route.get("taxi_cost"):
                print("[OK] Estimated cost: CNY {:.0f}".format(route['taxi_cost']))
            print("[OK] Steps: {}".format(len(route.get('steps', []))))
            if route.get('steps'):
                print("[OK] First step: {}".format(route['steps'][0].get('instruction', 'N/A')))
        else:
            print("[FAIL] Route planning failed")
            print("[DEBUG] Response: {}".format(route))
    
    print()
    print("=" * 60)
    print("[SUMMARY]")
    print("=" * 60)
    
    success_count = sum(1 for r in results.values() if r.get("distance_m"))
    print("[RESULT] Success: {}/3 modes".format(success_count))
    
    if success_count == 3:
        print("[OK] AMap API works correctly!")
        return True
    elif success_count > 0:
        print("[WARN] AMap API partially works")
        return True
    else:
        print("[ERROR] AMap API cannot plan routes")
        return False

if __name__ == "__main__":
    success = test_route_planning()
    sys.exit(0 if success else 1)