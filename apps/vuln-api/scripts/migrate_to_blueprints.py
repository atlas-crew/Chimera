#!/usr/bin/env python3
"""
Script to migrate monolithic app.py to Flask Blueprints architecture.
"""

import re
import os
from pathlib import Path

# Blueprint mapping based on route patterns
BLUEPRINT_MAPPING = {
    'main': [r'^/$', r'^/healthz$'],
    'auth': [r'^/api/v1/auth/', r'^/api/auth/', r'^/api/oauth/', r'^/api/saml/', r'^/api/v1/device/'],
    'banking': [r'^/banking/', r'^/api/v1/accounts/', r'^/api/v1/transfers/'],
    'mobile': [r'^/api/mobile/'],
    'healthcare': [r'^/api/hipaa/', r'^/api/providers/', r'^/api/medical/'],
    'compliance': [r'^/api/compliance/', r'^/api/audit/', r'^/api/regulatory/', r'^/api/sanctions/',
                   r'^/api/kyc/', r'^/api/reporting/(sar|ctr)'],
    'ecommerce': [r'^/api/products/', r'^/api/cart/', r'^/api/vendors/', r'^/api/reviews/',
                  r'^/api/ratings/', r'^/api/inventory/'],
    'checkout': [r'^/api/checkout/', r'^/api/shipping/', r'^/api/taxes/', r'^/api/giftcards/',
                 r'^/api/refund/', r'^/api/promotions/', r'^/api/discounts/'],
    'payments': [r'^/api/payments/', r'^/api/cards/', r'^/api/merchant/', r'^/api/payment/',
                 r'^/api/currency/'],
    'loyalty': [r'^/api/loyalty/', r'^/api/cashback/', r'^/api/referrals/'],
    'insurance': [r'^/claims/', r'^/api/claims/', r'^/api/policies/', r'^/api/underwriting/',
                  r'^/api/premiums/', r'^/api/actuarial/', r'^/api/risk/'],
    'infrastructure': [r'^/api/gateway/', r'^/api/microservices/', r'^/api/service-discovery$',
                       r'^/api/containers/', r'^/api/rbac/', r'^/api/pods/', r'^/api/secrets/',
                       r'^/api/network/', r'^/api/monitoring/', r'^/api/configurations/'],
    'attack_sim': [r'^/api/recon/', r'^/api/intelligence/', r'^/api/employees/', r'^/api/technologies/',
                   r'^/api/social/', r'^/api/vulnerabilities/', r'^/api/lateral/', r'^/api/privilege/',
                   r'^/api/credentials/', r'^/api/persistence/', r'^/api/backdoors/', r'^/api/domain/',
                   r'^/api/certificates/', r'^/api/forensics/', r'^/api/timestamps/', r'^/api/evidence/',
                   r'^/api/incident/', r'^/api/coordination$', r'^/api/exfiltration/', r'^/api/data/',
                   r'^/api/communication/', r'^/api/commands/', r'^/api/targets/', r'^/api/operations/',
                   r'^/api/mission/'],
    'ics_ot': [r'^/api/ics/', r'^/api/plc/', r'^/api/ot/'],
    'security_ops': [r'^/api/incidents/', r'^/api/threats/', r'^/api/remediation/', r'^/api/security/',
                     r'^/api/patches/', r'^/api/defense/'],
    'integrations': [r'^/api/integrations/', r'^/api/webhooks/'],
    'admin': [r'^/api/admin/', r'^/api/customers/', r'^/api/transactions/', r'^/api/system/',
              r'^/api/logs/'],
}


def get_blueprint_for_route(route_path):
    """Determine which blueprint a route belongs to."""
    for blueprint_name, patterns in BLUEPRINT_MAPPING.items():
        for pattern in patterns:
            if re.match(pattern, route_path):
                return blueprint_name
    return None


def extract_route_blocks(app_file_content):
    """Extract individual route blocks from app.py."""
    # Find all @app.route decorators and their functions
    route_pattern = re.compile(
        r"(@app\.route\([^\)]+\)[^\n]*\n(?:@[^\n]+\n)*def [^(]+\([^)]*\):[^\n]*\n(?:.*?\n)*?(?=\n@app\.route|\nif __name__|$))",
        re.MULTILINE | re.DOTALL
    )

    routes = []
    for match in route_pattern.finditer(app_file_content):
        route_block = match.group(1)
        # Extract the route path
        route_path_match = re.search(r"@app\.route\('([^']+)'", route_block)
        if route_path_match:
            route_path = route_path_match.group(1)
            blueprint = get_blueprint_for_route(route_path)
            if blueprint:
                routes.append({
                    'path': route_path,
                    'blueprint': blueprint,
                    'code': route_block
                })

    return routes


def generate_blueprint_files(routes, app_dir):
    """Generate blueprint files from extracted routes."""
    blueprints_by_name = {}

    # Group routes by blueprint
    for route in routes:
        bp_name = route['blueprint']
        if bp_name not in blueprints_by_name:
            blueprints_by_name[bp_name] = []
        blueprints_by_name[bp_name].append(route)

    # Generate files for each blueprint
    for bp_name, bp_routes in blueprints_by_name.items():
        bp_dir = app_dir / 'blueprints' / bp_name
        bp_dir.mkdir(parents=True, exist_ok=True)

        # Generate __init__.py
        init_content = f'''"""
{bp_name.replace('_', ' ').title()} blueprint.
"""

from flask import Blueprint

{bp_name}_bp = Blueprint('{bp_name}', __name__)

from . import routes
'''
        (bp_dir / '__init__.py').write_text(init_content)

        # Generate routes.py
        routes_content = f'''"""
Routes for {bp_name.replace('_', ' ')} endpoints.
"""

from flask import request, jsonify, render_template_string, session
from datetime import datetime, timedelta
import uuid
import random
import json
import time

from . import {bp_name}_bp
from app.models import *

'''

        # Add all route handlers, replacing @app.route with @{bp_name}_bp.route
        for route in bp_routes:
            route_code = route['code'].replace('@app.route', f'@{bp_name}_bp.route')
            routes_content += route_code + '\n\n'

        (bp_dir / 'routes.py').write_text(routes_content)

        print(f"Generated blueprint: {bp_name} with {len(bp_routes)} routes")


def main():
    """Main migration function."""
    script_dir = Path(__file__).parent
    app_file = script_dir / 'app.py'
    app_dir = script_dir / 'app'

    print(f"Reading {app_file}...")
    with open(app_file, 'r') as f:
        content = f.read()

    print("Extracting routes...")
    routes = extract_route_blocks(content)
    print(f"Found {len(routes)} routes")

    print("\nRoute distribution:")
    blueprint_counts = {}
    for route in routes:
        bp = route['blueprint']
        blueprint_counts[bp] = blueprint_counts.get(bp, 0) + 1

    for bp, count in sorted(blueprint_counts.items()):
        print(f"  {bp}: {count} routes")

    print("\nGenerating blueprint files...")
    generate_blueprint_files(routes, app_dir)

    print("\nMigration complete!")
    print("\nNext steps:")
    print("1. Review generated blueprint files in app/blueprints/")
    print("2. Extract DEMO_PAGE_TEMPLATE and other constants to app/utils/")
    print("3. Create application factory in app/__init__.py")
    print("4. Update main app.py to use the factory pattern")


if __name__ == '__main__':
    main()
