"""
Example STB Test Scripts for RAG Context

These scripts demonstrate correct usage of the STBDriver API.
The RAG engine indexes these as few-shot examples for LLM prompting.
"""

# ============================================================================
# Example 1: Basic Navigation Test
# ============================================================================

EXAMPLE_NAVIGATION_TEST = '''
"""Test: Navigate to Settings menu and verify screen"""
import time
from stb_driver import STBDriver

driver = STBDriver(redrat_ip="{redrat_ip}", hdmi_index={hdmi_index})

try:
    driver.connect()
    
    # Go to home screen
    driver.press("HOME")
    time.sleep(2)
    
    # Navigate to Settings
    driver.press("MENU")
    time.sleep(1)
    driver.navigate("DOWN", steps=3)
    driver.press("OK")
    time.sleep(2)
    
    # Verify settings screen loaded
    driver.verify_text("Settings")
    
    print("TEST PASSED: Settings navigation successful")
    
finally:
    driver.disconnect()
'''

# ============================================================================
# Example 2: Channel Change Test
# ============================================================================

EXAMPLE_CHANNEL_TEST = '''
"""Test: Change to channel 101 and verify playback"""
import time
from stb_driver import STBDriver

driver = STBDriver(redrat_ip="{redrat_ip}", hdmi_index={hdmi_index})

try:
    driver.connect()
    
    # Enter channel number
    driver.enter_channel("101")
    time.sleep(3)
    
    # Verify channel info is displayed
    driver.press("INFO")
    time.sleep(1)
    text = driver.read_text()
    assert "101" in text, f"Channel 101 not shown, got: {text}"
    
    # Capture screenshot as evidence
    driver.capture_screenshot("channel_101.png")
    
    print("TEST PASSED: Channel change verified")
    
finally:
    driver.disconnect()
'''

# ============================================================================
# Example 3: Playback Control Test
# ============================================================================

EXAMPLE_PLAYBACK_TEST = '''
"""Test: Play content and verify playback controls"""
import time
from stb_driver import STBDriver

driver = STBDriver(redrat_ip="{redrat_ip}", hdmi_index={hdmi_index})

try:
    driver.connect()
    
    # Navigate to content
    driver.press("HOME")
    time.sleep(2)
    driver.navigate("RIGHT", steps=2)
    driver.press("OK")
    time.sleep(3)
    
    # Start playback
    driver.play_content()
    time.sleep(5)
    
    # Pause and verify
    driver.pause_content()
    time.sleep(1)
    
    # Fast forward
    driver.press("FF")
    time.sleep(3)
    
    # Resume
    driver.play_content()
    time.sleep(2)
    
    # Capture evidence
    driver.capture_screenshot("playback_test.png")
    
    print("TEST PASSED: Playback controls working")
    
finally:
    driver.disconnect()
'''

# ============================================================================
# Example 4: App Launch Test  
# ============================================================================

EXAMPLE_APP_LAUNCH_TEST = '''
"""Test: Launch an application and verify it loads"""
import time
from stb_driver import STBDriver

driver = STBDriver(redrat_ip="{redrat_ip}", hdmi_index={hdmi_index})

try:
    driver.connect()
    
    # Go home first
    driver.press("HOME")
    time.sleep(2)
    
    # Navigate to app store/launcher
    driver.navigate("RIGHT", steps=1)
    driver.press("OK")
    time.sleep(3)
    
    # Wait for app screen to load
    text = driver.read_text()
    print(f"Screen text: {text}")
    
    # Verify app loaded
    driver.capture_screenshot("app_launch.png")
    
    print("TEST PASSED: App launched successfully")
    
finally:
    driver.disconnect()
'''
