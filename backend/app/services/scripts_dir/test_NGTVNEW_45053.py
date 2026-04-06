# Author: Kaishik Gundu
# Date: 11/01/21

"""
Sprint No: 3

Defect ID: NGTVNEW_45053

Defect Description: STB shows 4-5secs of black screen at start of VOD content

Expected result: Black screen should not be present

Actual Result: Black screen is visible

Notes: Activate the comfort feature before executing the test case

OCR Engine - Google Vision
"""

# Importing the necessary driver files
from src.stb_lib.stb import *


def executeTestCase():
    """
    This function validates all the required check conditions
    :return : return True if all the check conditions are validated successfully.
    """

    # Exit to Live TV for initial test case execution
    action.liveTV()

    # Step 1
    # STB Command to send PMENU command
    if not action.home():
        return False

    # Step 2
    # Navigate to settings screen
    if not action.submenu("settings"):
        return False

    # Step 3
    # Navigate to kinder settings
    if not action.kinder():
        return False

    # Navigate to Komfort screen
    cmdList = ["pdown"] * 3
    assert stb_rcu.sendmulti(cmdList, 1)
    time.sleep(5)

    # Activate Komfort feature
    action.activateKomfort()
    print("Komfort feature is activated. Navigating to Live TV now...")

    # Step 4
    # Navigate to home screen
    if not action.home():
        return False

    # Navigating to Film Section
    if not action.submenu("recordings"):
        return False

    # Delete all the recordings
    iteration = 5
    while not screen.isAllRecordingsDeleted():
        if not action.deleteAllRecordings():
            return False
        iteration -= 1
        if iteration == 0:
            break
    print("All recording deleted")

    # Navigate to film and series
    print("Navigating to film section")
    cmdList = ["pdown"] * 3
    stb_rcu.sendmulti(cmdList, 5)
    time.sleep(5)

    # Validate the meine filme/series button
    if not screen.isMeineFilmAndSeries():
        return False
    print("Reached meine film and series section")

    # Opening film and series section
    print("Opening film and series section")
    stb_rcu.send("pok")

    # Wait for the film section to load (timeout=40secs)
    startTime = time.time()
    loaded = False
    while time.time() - startTime < 40:
        if screen.isLogoInDetailsPage("VOD"):
            loaded = True
            break
    if not loaded:
        print("Film and series section not loaded")
        return False
    print("Film and series page loaded")

    # Opening the VOD content
    print("Opening the VOD content")
    stb_rcu.send("pok")
    time.sleep(10)

    # Play the content
    print("Playing VOD content")
    stb_rcu.send("pok")
    time.sleep(20)

    # Step 7
    # Validate Black Screen
    if screen.isBlackScreen():
        print("Defect is present")
        action.liveTV()
        return False

    action.liveTV()
    return True


def test_NGTVNEW45053(extra):
    testoutputname = __name__
    try:
        #Choosing OCR Engine (True - GV, False - Tesseract)
        action.useVision(True)

        assert tv.connect()
        tv.show()
        if connection_type == "telnet":
            assert stb.connect()
        tv.saveVideo(testoutputname)
        assert executeTestCase()

        print("Defect is not present")
    except:
        print("Test case failed")
        tv.saveframe(testoutputname)
        extra.append(extras.video("file:Videos\\" + testoutputname + ".mp4"))
        extra.append(extras.image("file:Images\\" + testoutputname + ".png"))
        assert False
    finally:
        tv.closescreen()
        tv.shutdown()
        time.sleep(5)


if __name__ == '__main__':
    test_NGTVNEW45053('')