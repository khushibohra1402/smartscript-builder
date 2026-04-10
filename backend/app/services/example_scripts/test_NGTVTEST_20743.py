# Author: Karan Sehgal
# Date: 4/01/2021

"""
Sprint No: 3

Test Case ID: NGTVTEST-20743

Test Case Description: Personal Channel list: Manage

Expected result: Channel list should be displayed as per the settings done within "Sender verwalten" Option.

Notes: Start this testcase with LiveTV streaming.

OCR Engine - Tesseract
"""
from src.stb_lib.stb import *


# Importing the necessary driver files


def executeTestCase():
    """
    This function validates all the required check conditions
    :return : return True if all the check conditions are validated successfully.
    """

    # Step-1
    # Navigate to EPG screen from Homescreen.
    if not action.home():
        return False

    # Goto EPG Screen
    assert stb_rcu.send("pguide")
    time.sleep(3)

    # Step-2
    # Navigate to channel Number 1
    action.tuneChannelInEPG("1")
    time.sleep(5)

    # Capture cropped frame to get the default channel icons list
    defaultChannelList = config.dataSetFilePath + "defaultChannelList.png"

    # Step-3
    # Goto Sender Verwalten
    action.manageChannels()

    # Step-4
    # Hide channel
    hiddenChannel = screen.getCroppedFrame(205, 236, 77, 128)
    cmdList = ["pdown"] + ["pright"] * 2 + ["pok"]
    assert (stb_rcu.sendmulti(cmdList, 0.9))
    time.sleep(2)

    # Step-5
    # Launch EPG screen
    print("Launching EPG Screen. ")
    cmdList = ["pright"] + ["pok"]
    assert (stb_rcu.sendmulti(cmdList, 0.9))
    if not screen.isEPGScreenValid(10):
        return False
    time.sleep(10)

    # Getting the cropped channel list to look into, whether the hidden channel is there or not.
    hiddenChannelList = screen.getCroppedFrame(238, 394, 50, 104)

    # Checking whether or not hidden channel is present on EPG Screen.
    isChannelHidden = screen.frameComparision(hiddenChannelList, hiddenChannel)

    if not isChannelHidden:
        print("The channel is hidden and can't be seen on EPG Screen.")
        # Capturing the 1st channel on EPG Screen, required for validation after resetting.
        epgChannelNum1 = screen.getCroppedFrame(238, 260, 54, 104)

        # Goto Sender Verwalten
        cmdList = ["pdown"] * 2
        assert (stb_rcu.sendmulti(cmdList, 0.9))
        time.sleep(2)
        action.manageChannels()

        # Getting the cropped channel list from sender verwalten Menu.
        managedChannelList = screen.getCroppedFrame(156, 377, 74, 132)

        # Checking whether the previously hidden channel is there or not.
        isListUpdated = screen.frameComparision(managedChannelList, hiddenChannel)

        if not isListUpdated:
            print("The previously hidden channel is not present in the list.")
            print("Renumbering the channel List.")
            # Capturing the first channel in List
            manageChannelNum1 = screen.getCroppedFrame(158, 194, 77, 128)
            cmdList = ["pok"] + ["pdown"] + ["pok"]
            assert (stb_rcu.sendmulti(cmdList, 0.9))
            time.sleep(2)
            # The co-ordinates provided are for the second channel number on Sender-Verwalten Settings Menu.
            if screen.frameComparision(manageChannelNum1, screen.getCroppedFrame(205, 236, 77, 128)):
                print("Channel Re-numbered within Sender verwalten Screen.")
                cmdList = ["pright"] * 3 + ["pok"]
                assert (stb_rcu.sendmulti(cmdList, 0.9))
                time.sleep(5)

                # The co-ordinates provided are for the second channel number on EPG Screen.
                if screen.frameComparision(epgChannelNum1, screen.getCroppedFrame(265, 287, 54, 104)):
                    print("Renumbering of channels at EPG Screen is validated.")

                    # Goto Sender Verwalten
                    cmdList = ["pdown"] * 2
                    assert (stb_rcu.sendmulti(cmdList, 0.9))
                    time.sleep(2)
                    action.manageChannels()

                    # Goto reset Channel List Options
                    cmdList = ["pup"] + ["pok"] + ["pdown"] * 3 + ["pok"] + ["pright"] + ["pok"]
                    assert (stb_rcu.sendmulti(cmdList, 0.9))
                    time.sleep(20)

                    # Verifying whether the channel list is reset or not.
                    if screen.frameComparision(tv.readImage(defaultChannelList),
                                               screen.getCroppedFrame(239, 394, 56, 99)):
                        print("The channel List matched after resetting.")
                        return True
                    else:
                        print("Channel List failed to reset.")
                else:
                    print("Channel re-numbering failed for validation in EPG Screen.")
                    return False
            else:
                print("Channel re-numbering failed for validation within Sender verwalten Menu Screen.")
            return False
        else:
            print("The channel is present in the Sender-Verwalten List, shouldn't be there.")
            return False
    print("The channel is still seen on the EPG Screen, shouldn't be there.")
    return False


def test_NGTVTEST20743(extra):
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
        print('Test Case Passed.')
    except:
        print("Test Case Failed")
        tv.saveframe(testoutputname)

        action.resetEPGSettings()

        extra.append(extras.video("file:Videos\\" + testoutputname + ".mp4"))
        extra.append(extras.image("file:Images\\" + testoutputname + ".png"))
        assert False
    finally:
        tv.closescreen()
        tv.shutdown()
        time.sleep(10)


if __name__ == '__main__':
    test_NGTVTEST20743('')