import re
import os

with open('../frontend/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

match = re.search(r'<script type="text/babel">(.*?)</script>', content, re.DOTALL)
if match:
    script_content = match.group(1)
    
    # We want translations, Calendar, SettingsDrawer, Main
    # Split before LandingPage since LandingPage is right after translations in index.html!
    # Wait, in index.html: translations -> LandingPage -> Calendar -> SettingsDrawer -> Main -> AppRoot -> render
    
    # Let's extract everything, then remove LandingPage, AppRoot, root.render
    
    script_content = script_content.replace("const root = ReactDOM.createRoot(document.getElementById('root'));", "")
    script_content = script_content.replace("root.render(<AppRoot />);", "")
    
    # Add imports
    header = '''"use client";
import React, { useState, useEffect, useRef } from "react";
const API_BASE = "http://localhost:8000";

'''
    
    # Replace React.useState with just useState if needed, but the original code just uses useState directly
    # We should add export default Main;
    final_content = header + script_content + '''\nexport default Main;\n'''
    
    os.makedirs('src/components', exist_ok=True)
    with open('src/components/Dashboard.tsx', 'w', encoding='utf-8') as out:
        out.write(final_content)
    print("Extracted successfully.")
else:
    print("Could not find script block")
