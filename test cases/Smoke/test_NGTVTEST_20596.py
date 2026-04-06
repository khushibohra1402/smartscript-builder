# Author: Vedant
# Date: 25/01/2021

"""
Sprint No: 4

Test Case Number: NGTVTEST-20596

Test Description: VOD

Expected result: The purpose of this test case is to test the performance of basic trickplay in VOD Movie Content and
                 TV Series VOD Content

Notes: Start this testcase with LiveTV streaming.

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
    # Navigate to HOME page
    if not action.home():
        return False

    # Navigate to setting screen
    if not action.submenu("settings"):
        return False

    # Navigate to kinder menu
    if not action.kinder():
        return False
    time.sleep(3)

    # Activate Komfort feature
    action.activateKomfort()

    # Navigate to HOME page
    if not action.home():
        return False

    # Step 2
    # Navigate to Film
    if not action.submenu("film"):
        return False

    # Play a content
    cmdList = ["pdown"] * 2
    assert stb_rcu.sendmulti(cmdList, 1)

    # Navigate to VoD Content and play the content.
    assert stb_rcu.send("pok")
    time.sleep(10)

    assert stb_rcu.send("pvolplus")
    time.sleep(3)

    # Play the content.
    action.playVODContent()
    time.sleep(20)

    # Functionality of basic trick play:
    if not action.basicTrickPlay("VOD"):
        return False

    # Navigate to HOME page
    if not action.home():
        return False

    # Navigate to Series section
    if not action.submenu("series"):
        return False

    # Navigate to VoD Series Content and play the content.
    time.sleep(5)
    cmdList = ["pdown"]*2 + ["pok"]
    assert stb_rcu.sendmulti(cmdList, 3)
    time.sleep(7)
    assert stb_rcu.send("pok")
    time.sleep(10)

    # Play the content.
    action.playVODContent()
    time.sleep(20)

    # Functionality of basic trick play:
    if not action.basicTrickPlay("VOD"):
        return False

    if not action.home():
        return False
    return True


def test_NGTVTEST20596(extra):
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
        print('Test Case Passed.')
    except:
        print("Test Case Failed")
        tv.saveframe(testoutputname)
        extra.append(extras.video("file:Videos\\" + testoutputname + ".mp4"))
        extra.append(extras.image("file:Images\\" + testoutputname + ".png"))
        assert False
    finally:
        tv.closescreen()
        tv.shutdown()
        time.sleep(10)

if __name__ == '__main__':
    test_NGTVTEST20596('')