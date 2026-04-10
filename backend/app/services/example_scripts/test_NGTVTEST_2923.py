# Author: Anup
# Date: 15-07-21

"""
Sprint No: 96

Test Case ID: NGTVTEST-2923

Test Case Description: Setting and checking unrated content lock on STB

Expected result: To test the function of the unrated content lock/unlock as per the age rating set

Notes:

OCR Engine - Tesseract
"""

from src.stb_lib.stb import *

# Variable to hold the counter (to handle --count case)
pytest.test_NGTVTEST_2923_counter = 0


def executeTestCase():
    """
    This function validates all the required check conditions
    :return : return True if all the check conditions are validated successfully.
    Note: Mention the reason in case of a failure (return False, "error message")
    """

    if pytest.test_NGTVTEST_2923_counter == 1:
        # Navigate to home screen
        if not action.home():
            return False, "Home screen not validated"

        # Navigate to settings screen
        if not action.submenu("settings"):
            return False, "Settings screen not validated"

        # Navigate to Kinder menu
        if not action.kinder():
            return False, "Could not navigate to kinder menu"

        # Lock 16
        if not action.setLock("Lock16"):
            return False, "Unable to set lock (Ab16)"

        # Lock KA content
        action.lockKAContent()

        # Disable Komfort feature
        action.activateKomfort(False)

    # Navigate to live TV
    action.liveTV()

    # Tune to channel 1 (unrated channel)
    action.tuneChannel("1")

    # Verify if the content is locked
    if not screen.isLiveTVLocked():
        return False, "Live TV unrated content is not locked"

    # Unlock the content
    action.unlockContent()

    # Increase the volume just in case volume is 0
    stb_rcu.sendmulti(["pvolplus"]*2, 1)
    time.sleep(3)

    # Check if the content is playing or not
    if not screen.isContentPlaying():
        return False, "Content is not playing"

    return True, "All the steps executed and validated properly"


def test_NGTVTEST_2923(extra):
    pytest.test_NGTVTEST_2923_counter += 1
    testoutputname = __name__ + "_" + str(pytest.test_NGTVTEST_2923_counter)
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
    test_NGTVTEST_2923('')