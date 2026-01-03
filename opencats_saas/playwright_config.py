"""Playwright configuration for e2e tests"""
import os

# Base URL for the application
BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')

# Browser settings
HEADLESS = os.getenv('HEADLESS', 'true').lower() == 'true'
SLOW_MO = int(os.getenv('SLOW_MO', '0'))

# Timeout settings
TIMEOUT = 30000  # 30 seconds
NAVIGATION_TIMEOUT = 30000  # 30 seconds

# Screenshot settings
SCREENSHOT_ON_FAILURE = True
SCREENSHOT_DIR = 'test-results/screenshots'

# Video settings
VIDEO_ON_FAILURE = False

# Browser options
BROWSER_OPTIONS = {
    'headless': HEADLESS,
    'slow_mo': SLOW_MO,
    'args': [
        '--disable-blink-features=AutomationControlled',
        '--disable-dev-shm-usage',
        '--no-sandbox',
    ]
}

# Viewport size
VIEWPORT = {'width': 1280, 'height': 720}
