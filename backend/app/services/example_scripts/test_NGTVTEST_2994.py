# Author: Kaishik Gundu
# Date: 14/09/2021

"""
Sprint No: 99

Test Case ID: NGTVTEST-2994

Test Case Description: Filter Local Channels by using the Option Panel in the EPG Grid

Expected result: Filtering is possible

Notes: None

OCR Engine - Tesseract
"""

from src.stb_lib.stb import *

# Variable to hold the counter (to handle --count case)
pytest.test_NGTVTEST_2994_counter = 0


def executeTestCase():
    """
    This function validates all the required check conditions
    :return : return True if all the check conditions are validated successfully.
    Note: Mention the reason in case of a failure (return False, "error message")
    """

    # Navigating to Live TV
    action.liveTV()

    # Navigate to epg
    stb_rcu.send("pguide")

    # Navigate to EPG
    action.tuneChannelInEPG("1")

    # Filter the local channels
    print("Navigating to options menu")
    cmdList = ["pup"] * 2
    stb_rcu.sendmulti(cmdList, 2)

    print("Navigating to filter menu")
    cmdList = ["pok", "pdown", "pok"]
    stb_rcu.sendmulti(cmdList, 2)

    print("Filtering the local channels")
    cmdList = ["pup", "pok"]
    stb_rcu.sendmulti(cmdList, 2)
    print("Validating the filtered local channels")
    time.sleep(10)

    # Validate the local channel filtering
    # TODO: add cropped ocr instead of image comparison
    if not screen.isLocalStationsOnEPG():
        print("Local sender channels are not filtered")
        return False, "Local sender channels are not filtered"
    print("Local channels are now filtered")

    # Exit from the EPG
    stb_rcu.send("pback")
    time.sleep(5)

    if screen.isEPGScreenValid(5):
        return False, "Still in EPG screen after pressing back on RCU"
    print("Not in EPG Screen. Working as expected")

    # Validate EPG again
    print("Navigating to EPG Screen")
    stb_rcu.send("pguide")
    time.sleep(5)

    if not screen.isEPGScreenValid(25):
        return False, "Not in EPG screen"
    print("EPG Screen validated")

    # Validate if Local sender is absent
    if screen.isLocalStationsOnEPG():
        return False, "Local sender channels filter is not removed"
    print("All channels visible. Local channels are now not filtered")

    # Navigate to home
    if not action.home():
        return False, "Home screen not validated"

    return True, "All the steps executed and validated properly"


def test_NGTVTEST_2994(extra):
    pytest.test_NGTVTEST_2994_counter += 1
    testoutputname = __name__ + "_" + str(pytest.test_NGTVTEST_2994_counter)
    try:
        #Choosing OCR Engine (True - GV, False - Tesseract)
        action.useVision(False)

        # Connection to STB and TV
        if connection_type == "telnet":
            assert stb.connect()
        assert tv.connect()

        # Open Virtual TV and show frames
        tv.show()

        # Save the video in report folder
        tv.saveVideo(testoutputname)

        # Start test case step execution
        ret, msg = executeTestCase()
        assert ret
        print('Test Case Passed.')
    except:
        print("Test Case Failed")

        # Save the last frame where the test case failed
        tv.saveframe(testoutputname)

        # Append image and video in test report file
        extra.append(extras.video("file:Videos\\" + testoutputname + ".mp4"))
        extra.append(extras.image("file:Images\\" + testoutputname + ".png"))
        assert False, msg
    finally:
        # Pass the value from screen,action to conftest,
        set_vision_count(screen.visionCount + action.screen.visionCount)
        set_tesseract_count(screen.tesseractCount + action.screen.tesseractCount)

        # Initialise screen and action to 0
        action.clearOCRHitCounts()
        screen.clearOCRHitCounts()

        tv.closescreen()
        tv.shutdown()
        time.sleep(10)


if __name__ == '__main__':
    test_NGTVTEST_2994('')