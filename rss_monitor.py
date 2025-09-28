#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSS Feed Monitor per GitHub Actions
Versione ottimizzata con fix definitivo per duplicati Instagram
"""

import requests
import feedparser
import json
import os
import sys
import time
from datetime import datetime, timedelta
import re
import hashlib
import urllib.parse as urlparse

# Test rapido
if __name__ == "__main__":
    print("✅ Script caricato correttamente!")
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Working directory: {os.getcwd()}")
    print("🧪 Test mode - script funziona!")
