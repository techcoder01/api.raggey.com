#!/usr/bin/env python3
"""
Script to check and display all fabric isHidden status
"""
import os
import sys
import django

# Setup Django
sys.path.append('/home/techcoder01/Documents/GitHub/api.raggey.com')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'raggyBackend.settings')
django.setup()

from Design.models import FabricType

print("="*70)
print("FABRIC VISIBILITY STATUS CHECK")
print("="*70)

fabrics = FabricType.objects.all().order_by('id')
total_count = fabrics.count()
hidden_count = fabrics.filter(isHidden=True).count()
visible_count = fabrics.filter(isHidden=False).count()

print(f"\nTotal Fabrics: {total_count}")
print(f"Visible Fabrics (isHidden=False): {visible_count}")
print(f"Hidden Fabrics (isHidden=True): {hidden_count}")
print("\n" + "="*70)
print("DETAILED FABRIC LIST")
print("="*70)

for fabric in fabrics:
    status = "✅ VISIBLE (API will return)" if not fabric.isHidden else "❌ HIDDEN (API filters out)"
    print(f"\nID: {fabric.id}")
    print(f"Name: {fabric.fabric_name_eng}")
    print(f"isHidden: {fabric.isHidden}")
    print(f"Status: {status}")
    print("-"*70)

print("\n" + "="*70)
print("API FILTERING EXPLANATION")
print("="*70)
print("\nBackend API query: FabricType.objects.filter(isHidden=False)")
print(f"This query will return {visible_count} fabrics to the Flutter app\n")

# Show which fabrics are being filtered out
hidden_fabrics = fabrics.filter(isHidden=True)
if hidden_fabrics.exists():
    print("\n⚠️  FABRICS FILTERED OUT BY API (isHidden=True):")
    for fabric in hidden_fabrics:
        print(f"  - ID {fabric.id}: {fabric.fabric_name_eng}")
    print("\nTo show these fabrics in the app, set isHidden=False in Django admin")
else:
    print("\n✅ All fabrics are visible (no fabrics have isHidden=True)")

print("\n" + "="*70)
