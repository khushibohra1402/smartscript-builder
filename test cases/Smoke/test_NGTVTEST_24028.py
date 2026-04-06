# Author : Gundu V Sai Shankar Kaishik
# Date : 18/12/2020

"""
Sprint No: 1
Test Case ID: NGTVTEST-24028

Test Case Description: Verify the parameters BLS2 Version, Browser Version, UI Version, Software Version match with the data in the release Notes

Expected Result: The parameters should be same

Notes: Start this testcase with LiveTV streaming

OCR Engine - Google Vision
"""

# Importing the necessary driver files
from src.stb_lib.stb import *


def executeTestCase():
    """
    This function validates all the required check conditions
    :return : return True if all the check conditions are validated successfully.
    """

    # STB Command to send PMENU command
    if not action.home():
        return False

    # Navigate to  settings screen
    # Based on current UI, its 11 right keys
    if not action.submenu("settings"):
        return False

    # Navigate to System Menu
    print("Settings Screen Validated, navigating to system Menu")
    if not action.mediaReceiver('sysinf'):
        return False

    cmdList = ["pright", "pok"]
    assert (stb_rcu.sendmulti(cmdList, 1.5))
    # Exhausted...Give couple of seconds for UI to appear!!
    time.sleep(3)

    # (Validation of parameters)
    print("Validating the Parameters \n")
    ret, frame = tv.getFrame()
    assert ret
    screenText = screen.image_to_text(frame).lower()
    print(screenText)
    tempList = []
    defaultList = ["bls2-version: " + config.bls2Version.lower(), "sw-version: " + config.swVersion.lower(),
                   "ui-version: " + config.uiVersion.lower(), "browser- " + config.browserVersion.lower()]
    for word in screenText.split("\n"):
        if defaultList == tempList:
            pass
        else:
            for data in defaultList:
                if data in word:
                    if data not in tempList:
                        tempList.append(data)
                        print("{} is matched".format(data.upper()))
    nonMatchedList = [x for x in defaultList if x not in set(tempList)]
    if len(nonMatchedList) != 0:
        print("--------------------------\n")
        for x in nonMatchedList:
            print("This value did not match {}".format(x.upper()))
        return False

    return True


def test_NGTVTEST24028(extra):
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
    test_NGTVTEST24028('')