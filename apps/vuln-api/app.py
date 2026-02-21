#!/usr/bin/env python3
"""
Chimera - Multi-domain Exploitation Framework
Refactored with Flask Blueprints for better organization.
"""
import os
from app import create_app

# Create the application instance using the factory pattern
app = create_app()

if __name__ == '__main__':
    # Use port 80 in container, 8880 for local development
    port = int(os.environ.get('PORT', 80))
    app.run(host='0.0.0.0', port=port, debug=True)
