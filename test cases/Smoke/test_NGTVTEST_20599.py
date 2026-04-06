# Author: Kaishik Gundu
# Date: 20/1/2021

"""
Sprint No: 4

Test Case ID: NGTVTEST-20599

Test Case Description: Instant Restart

Expected result: Instant restart forward backward functionality should be fine

Notes: Comfort feature should be activated

OCR Engine - Tesseract
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
    # Tune in to a channel and perform instant restart
    action.tuneChannelInEPG("11")
    ret, originalStartTime = action.performInstantRestart("originalStartTime")
    assert ret
    print("Instant restart successful, Going to almost live TV")

    # Step 8
    # Move forward till the Live TV
    ret, beforeRewindTime = action.moveRightToLiveTvfromInstantRestart(originalStartTime, "Yes")
    assert ret
    if not screen.isContentPlaying():
        return False
    assert stb_rcu.send("pok")
    time.sleep(1)

    # Step 9
    # Check if rewind is working fine
    if not action.trickPlay("LiveTV", "rewind", 9):
        print("Rewind has some issues")
        return False
    print("Rewind is working fine")

    assert stb_rcu.send("pok")
    time.sleep(5)

    # Step 10
    # Go to Live TV
    time.sleep(3)
    if not action.cancelInstantRestart():
        return False

    return True

def test_NGTVTEST20599(extra):
    testoutputname = __name__
    try:
        #Choosing OCR Engine (True - GV, False - Tesseract)
        action.useVision(False)

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
    test_NGTVTEST20599('')