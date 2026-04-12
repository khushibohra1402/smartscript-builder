# Author: Shreya Mehortra
# Date: 12/1/2021

"""
Sprint No: 3

Test Case ID: NGTVTEST-45092

Test Case Description: Aufnahme Plannen popup should appear

Expected result: Aufnahme Plannen popup should appear while scheduling the recording if "Direktaufnahme" option is ticked under setting

Notes: Start this testcase with LiveTV streaming and lock all the contents (Ab0 and KA locked).

OCR Engine - Tesseract
"""

# Importing the necessary driver files
from src.stb_lib.stb import *


def executeTestCase():
    """
    This function validates all the required check conditions
    :return : return True if all the check conditions are validated successfully.
    """

    # Navigate to home menu
    if not action.home():
        return False

    # Navigate to Settings screen
    if not action.submenu("settings"):
        return False

    # Navigating to recording Settings
    if not action.enableDirectRecording():
        return False

    action.liveTV()

    # Tune to channel number 1 in EPG
    action.tuneChannelInEPG("1")

    # Schedule a future content recording
    print("Scheduling future recording...")
    cmdList = ["pright", "pright", "pok", "pok"]
    stb_rcu.sendmulti(cmdList, 2)
    time.sleep(7)

    # Check if recording details will be visible form event details
    if screen.isAufnahmePlanen():
        print("Test passed")
        return True

    return False


def test_NGTVNEW45092(extra):
    testoutputname = __name__
    try:
        #Choosing OCR Engine (True - GV, False - Tesseract)
        action.useVision(False)

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
    test_NGTVNEW45092('')