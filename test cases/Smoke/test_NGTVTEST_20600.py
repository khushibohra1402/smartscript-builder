# Author: Vedant
# Date: 26/01/2021

"""
Sprint No: 5.1

Test Case Number: NGTVTEST-20600

Test Description: EPG data - all data collected

Expected result: The purpose of this test case is to verify that all EPG data is collected for the available channels.

Notes: Start this testcase with LiveTV streaming first channel.

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
    time.sleep(3)

    # Step 4
    # Activaiton of Komfort Feature.
    action.activateKomfort()

    action.liveTV()

    # Step 5
    # Navigating to Channel 2 and then go to EPG Screen.
    action.tuneChannel("1")
    time.sleep(5)

    print("Entering into EPG Screen")
    assert stb_rcu.send("pguide")
    if not screen.isEPGScreenValid(5):
        print("Not in EPG screen")
        assert (stb_rcu.send("pguide"))
    print("EPG Validated")
    time.sleep(15)

    # Step 6
    # Validation of past 7 days content.
    # Navigate to past 7 day.
    cmdList = ["pup", "pleft"]
    assert stb_rcu.sendmulti(cmdList, 1.5)
    time.sleep(1)

    # Step 7
    # Navigate to 7 days prior to the current date.
    print("Navigating to past 7th day....")
    cmdList = ["pok"] * 8
    assert stb_rcu.sendmulti(cmdList, 2)
    time.sleep(30)

    assert stb_rcu.send("pdown")
    time.sleep(3)
    print("On 7th day content.")
    if not screen.getChannelName():
        return False
    print("Validated Channel")
    time.sleep(3)

    # Step 8
    # Move additional left to check for the content of the ongoing content of previous day
    print("Going left....")
    for left in range(3):
        assert stb_rcu.send("pleft")
        print("Validating the channel.......")
        time.sleep(3)
        if not screen.getChannelName():
            return False
        time.sleep(1)
        print(f"Validated Channel and moved {left + 1} times left")
        time.sleep(2)

    # Step 9
    # Validation of the contents
    print("Going right...")
    for right in range(5):
        assert stb_rcu.send("pright")
        print("Validating the channel.......")
        time.sleep(3)
        if not screen.getChannelName():
            return False
        time.sleep(1)
        print(f"Validated Channel and moved {right + 1} times right")
        time.sleep(2)

    # Step 10
    # Navigating to the next channel:
    print("Navigating to the next channel contents....")
    assert stb_rcu.send("pdown")
    time.sleep(2)
    if not screen.getChannelName():
        return False
    print("Validated Channel")
    time.sleep(3)

    # Step 11
    # Moving to the initial position:
    print("Going left...")
    for left in range(6):
        assert stb_rcu.send("pleft")
        print("Validating the channel.......")
        time.sleep(3)
        if not screen.getChannelName():
            return False
        time.sleep(1)
        print(f"Validated Channel and moved {left + 1} times left")
        time.sleep(2)

    print("Validated past 7 days of content without any issues")
    time.sleep(2)

    # Step 12
    # Navigating to 14 days post the current date.
    print("Navigating to the 14th day content post the current date.")
    cmdList = ["pup"] * 2 + ["pok"] * 21
    assert stb_rcu.sendmulti(cmdList, 2)
    print("Reached the future EPG content.")
    time.sleep(30)

    assert stb_rcu.send("pdown")
    time.sleep(3)
    if not screen.getChannelName():
        return False
    print("Validated channel")
    time.sleep(2)

    # Step 13
    # Validation of the content.
    print("Going right...")
    for right in range(5):
        assert stb_rcu.send("pright")
        print("Validating the channel.......")
        time.sleep(3)
        if not screen.getChannelName():
            return False
        time.sleep(1)
        print(f"Validated Channel and moved {right + 1} times right")
        time.sleep(2)
    # Navigating to the next channel:
    print("Navigating to the next channel contents....")
    assert stb_rcu.send("pdown")
    time.sleep(2)
    if not screen.getChannelName():
        return False
    print("Validated Channel")
    time.sleep(3)

    # Move additional right to check for the content of the ongoing content.
    print("Going right....")
    for right in range(2):
        assert stb_rcu.send("pright")
        print("Validating the channel.......")
        time.sleep(3)
        if not screen.getChannelName():
            return False
        time.sleep(1)
        print(f"Validated Channel and moved {right + 1} times left")
        time.sleep(2)

    # Step 14
    # Moving to the initial position:
    print("Going left...")
    for left in range(5):
        assert stb_rcu.send("pleft")
        print("Validating the channel.......")
        time.sleep(3)
        if not screen.getChannelName():
            return False
        time.sleep(1)
        print(f"Validated Channel and moved {left + 1} times left")
        time.sleep(2)
    print("Validated next 14 days of content without any issues ")

    # Step 15
    # Go to home menu.
    if not action.home():
        return False
    return True


def test_NGTVTEST20600(extra):
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
    test_NGTVTEST20600('')