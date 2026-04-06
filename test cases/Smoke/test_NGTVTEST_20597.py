# Author: Vedant
# Date: 25/01/2021

"""
Sprint No: 4

Test Case Number: NGTVTEST-20597

Test Description: 3PP functionality

Expected result: The purpose of this test case is to verify the basic trickplay on the 3rd Party Apps video.

Notes: Start this testcase with pre-login to the 3rd Party Apps.

OCR Engine - Google Vision
"""

# Importing the necessary driver files
from src.stb_lib.stb import *


def performKeyOperation():
    """
    This function is used to check the effect of numeric keys and power button on the 3pp apps
    """
    # Check if any change channel button is affecting the current state
    if not action.noChange3pp("p1"):
        return False

    if not action.noChange3pp("p2"):
        return False

    if not action.noChange3pp("p3"):
        return False

    # Check if functionality of power button
    assert stb_rcu.send("pstdby")
    time.sleep(7)

    if not screen.isActiveStandby():
        print("Power button did not work")
        return False

    if not action.wakeBoxFromActiveStandby("pstdby"):
        return False

    return True


def executeTestCase():
    """
    This function validates all the required check conditions
    :return : return True if all the check conditions are validated successfully.
    """

    # Navigate to HOME page
    if not action.home():
        return False

    # Navigate to Apps Screen
    if not action.submenu("apps"):
        return False

    # Validating the availability of 3rd party apps.
    cmdlist = ["pdown"] * navigate["netflix"][0]
    assert stb_rcu.sendmulti(cmdlist, 1)

    appsName = config.beliebteApps[:10]
    for appName in appsName:
        if not screen.imageToTextValidation(appsName, tv.getFrame()[1][301:315, 23:135]):
            print("test" + appName)
            return False
        print(f'{appName} validated')

    cmdlist = ["pright"] * 5
    assert stb_rcu.sendmulti(cmdlist, 1)
    time.sleep(3)

    appsName = config.beliebteApps[5:]
    for appName in appsName:
        if not screen.imageToTextValidation(appsName, tv.getFrame()[1][301:315, 23:135]):
            return False
        print(f'{appName} validated')

    # Playing content of 3rd party app
    print("Navigating to Netflix")
    assert stb_rcu.send("pback")
    time.sleep(7)
    if not action.app("netflix"):
        return False

    # Play any content
    cmdList = ["pok"] * 2
    if screen.imageToTextValidation(["Resume", "Play Episode"]):
        cmdList = ["pok"]
    assert stb_rcu.sendmulti(cmdList, 3)
    time.sleep(10)

    cmdList = ["pright"]*15 + ["pok"]
    assert stb_rcu.sendmulti(cmdList, 1)
    time.sleep(7)
    # Performing basic trickplay functionalities.
    if not action.basicTrickPlay("Netflix", 5):
        return False

    # Exit from content
    assert stb_rcu.send("pback")
    time.sleep(7)

    # Check the effect of numeric keys and power button on Netflix
    if not performKeyOperation():
        return False

    # Navigate to youtube
    if not action.app("youtube"):
        return False

    # Navigate to search Screen
    cmdList = ["pleft", "pup", "pok"]
    assert stb_rcu.sendmulti(cmdList, 1)
    time.sleep(2)
    if not screen.isSearchScreen():
        print("Not inside search screen")
        return False

    # Search for content (HOPP)
    ret, beforeSearch = tv.getFrame()
    cmdList = ["pright"] + ["pdown", "pok"] * 2 + ["pright"] + ["pok"] * 2
    assert stb_rcu.sendmulti(cmdList, 1)
    time.sleep(3)
    ret, afterSearch = tv.getFrame()

    # Compare whether search is happening properly
    if screen.frameComparision(beforeSearch, afterSearch) == 1:
        print("Search did not happen")
        return False

    # Compare the search results contain the required content
    if not screen.searchResults("hoppe", "Youtube"):
        print("The searched word is absent")
        return False

    # If Youtube App Screen is validated, click "ok" to play the first video.
    cmdList = ["pdown"] * 3 + ["pok"]
    assert (stb_rcu.sendmulti(cmdList, 1.2))
    time.sleep(10)
    if screen.isAdd():
        time.sleep(5)
        assert stb_rcu.send("pok")
        print("First Add skipped")
        time.sleep(8)
    if screen.isAdd():
        time.sleep(5)
        assert stb_rcu.send("pok")
        print("Second Add skipped")
        time.sleep(8)
    time.sleep(4)

    # Check if youtube optimization screen
    if screen.isYoutubeOptimizationScreen():
        assert stb_rcu.send("pback")
        time.sleep(2)
    time.sleep(5)

    # Perform basic trickplay operations
    if not action.basicTrickPlay("Youtube", 5):
        print("Some issues with basic trickplay on Youtube")
        return False

    # Exit from the content
    assert stb_rcu.send("pback")
    time.sleep(7)

    # Check the effect of numeric keys and power button on Youtube
    if not performKeyOperation():
        return False

    # Navigate to Apps Screen
    if not action.submenu("apps"):
        return False

    # Navigate to Disney+ App and Open the App.
    if not action.app("disney"):
        return False

    # Navigating to a content
    cmdList = ["pdown"] + ["pright"] * 2 + ["pok"]
    assert stb_rcu.sendmulti(cmdList, 2)
    time.sleep(7)

    cmdList = ["pdown"] * 2 + ["pright"] * 3 + ["pok"]
    assert stb_rcu.sendmulti(cmdList, 2)
    time.sleep(7)

    # Checking if the content will play from the start
    newContent = screen.isNewContent()

    assert stb_rcu.send("pok")
    time.sleep(20)

    # Fast forwarding a content to skip initial introduction for a new content
    if newContent:
        cmdList = ["pok", "pright", "pright", "pok"]
        assert stb_rcu.sendmulti(cmdList, 1)
        time.sleep(10)

        cmdList = ["pleft"] * 2 + ["pok"]
        assert stb_rcu.sendmulti(cmdList, 1)
        time.sleep(5)

    # Validating if the content is playing or not
    if not screen.isContentPlaying():
        print("Content is not playing")
        return False
    print("Content playing successfully")

    # Basic trick play check
    if not action.basicTrickPlay("Disney", 4):
        print("error in trickplay functionality")
        return False

    # Exit from the content
    assert stb_rcu.send("pback")
    time.sleep(10)

    # Check the effect of numeric keys and power button on Disney
    if not performKeyOperation():
        return False

    # Navigate to apps
    if not action.submenu("apps"):
        return False

    # Navigate to Prime App and Open the App.
    if not action.app("prime"):
        return False

    # Navigating to search
    print("Navigating to search menu")
    assert stb_rcu.sendmulti(["pleft", "pok"], 2)
    time.sleep(7)

    # Search for "Hero"
    print("Searching for heroes")
    cmdList = ["pdown"]*2 + ["pright", "pok", "pup"] + ["pright"]*3 + ["pok"] + ["pdown"]*2 + ["pright", "pok"] + \
              ["pleft"]*3 + ["pok"] + ["pup"]*2 + ["pright"]*2 + ["pok"] + ["pdown"]*3 + ["pleft"]*4 + ["pok"]
    assert stb_rcu.sendmulti(cmdList, 1.5)
    time.sleep(7)

    # Navigate to the searched content
    print("Opening the searched content")
    cmdList = ["pright"]*7 + ["pdown"]
    assert stb_rcu.sendmulti(cmdList, 1.5)
    time.sleep(5)

    # Open the searched content
    assert stb_rcu.sendmulti(["pright", "pok"], 1.5)
    time.sleep(7)

    assert stb_rcu.send("pok")
    time.sleep(20)

    if not action.basicTrickPlay("Prime", 4):
        return False

    assert stb_rcu.send("pback")
    time.sleep(5)

    # Check the effect of numeric keys and power button on Disney
    if not performKeyOperation():
        return False

    return True


def test_NGTVTEST20597(extra):
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
    test_NGTVTEST20597('')