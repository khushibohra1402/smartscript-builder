# Author: Kaishik Gundu
# Date: 25/1/2021

"""
Sprint No: 4

Test Case ID: NGTVTEST-20751

Test Case Description: Instant Restart - program length

Expected result: Instant restart has additional 5 minutes added to them when restarted

Notes: Comfort feature should be activated

OCR Engine - Google Vision
"""

# Importing the necessary driver files
from src.stb_lib.stb import *


def executeTestCase():
    """
    This function validates all the required check conditions
    :return : return True if all the check conditions are validated successfully.
    """

    # Step 1
    # Navigate to home page
    if not action.home():
        return False

    # Navigate to settings screen
    if not action.submenu("settings"):
        return False

    # Step 2
    # Navigate to kinder settings
    if not action.kinder():
        print("Error going to kinder")
        return False
    time.sleep(3)

    # Step 3
    # If not locked all, lock all
    if not action.setLock("Lock0"):
        print("Error setting the lock")
        return False
    print("Locked all.")

    # Step 4
    # Lock the KA content
    action.lockKAContent()
    print("KA is locked.")

    # Step 5
    # Activate Comfort feature if deactivated
    cmdList = ["pdown"] * 3
    assert stb_rcu.sendmulti(cmdList, 1)
    time.sleep(3)
    action.activateKomfort()
    print("Komfort feature is activated. Navigating to Live TV now...")

    # Step 6
    # Navigate to live TV
    action.liveTV()

    # Step 7
    # Tune in to a channel that has instant restart
    action.tuneChannelInEPG("11")
    ret, originalEndTime = action.performInstantRestart("originalEndTime")
    if not ret:
        return False
    time.sleep(4)
    print("Instant restart successful, now checking the new end Time")

    # Step 8
    # Check the changed time
    assert stb_rcu.send("pok")
    time.sleep(5)
    ret, newEndTime = screen.fetchTime("LiveTVend")
    if not ret:
        return False

    # Check whether instant restart happened properly
    if newEndTime - originalEndTime < 300:
        return False

    # Step 9
    # Move Forward
    if not action.trickPlay("LiveTVstart", "fastForward", 4):
        return False
    print("Fast forward working fine")

    # Step 10
    # Check if rewind is working fine
    if not action.trickPlay("LiveTVstart", "rewind", 4):
        return False
    print("Content is rewinded")

    assert stb_rcu.send("pok")
    time.sleep(7)
    assert stb_rcu.send("pok")
    time.sleep(7)

    # Step 11
    # Go to Live TV
    if not action.cancelInstantRestart():
        return False

    return True

def test_NGTVTEST20751(extra):
    testoutputname = __name__
    try:
        #Choosing OCR Engine (True - GV, False - Tesseract)
        action.useVision(True)

        if connection_type == "telnet":
            assert stb.connect()
        assert tv.connect()
        tv.show()
        tv.saveVideo(testoutputname)
        assert executeTestCase()
        print("Test case passed")
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
    test_NGTVTEST20751('')