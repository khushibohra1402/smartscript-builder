# Author: Kaishik Gundu
# Date: 17/09/2021

"""
Sprint No: 99

Test Case ID: NGTVTEST-3102

Test Case Description: PCON PIN check when playing an Instant Recording of an unrated content

Expected result: PCON PIN is asked everytime

Notes: Unrated content is locked

OCR Engine - Tesseract
"""
import time

from src.stb_lib.stb import *

# Variable to hold the counter (to handle --count case)
pytest.test_NGTVTEST_3102_counter = 0


def executeTestCase():
    """
    This function validates all the required check conditions
    :return : return True if all the check conditions are validated successfully.
    Note: Mention the reason in case of a failure (return False, "error message")
    """

    # Navigate to live TV
    print("Navigating to live TV")
    action.liveTV()

    # Navigating to home screen
    if not action.home():
        return False, "Home screen not validated"

    # Navigating to Recordings Menu
    if not action.submenu("recordings"):
        return False, "Recording screen not validated"

    # Delete all the recordings
    iteration = 5
    while not screen.isAllRecordingsDeleted():
        if not action.deleteAllRecordings():
            return False, "Unable to delete all recordings"
        iteration -= 1
        if iteration == 0:
            break
    print("All recording deleted")

    if pytest.test_NGTVTEST_3102_counter == 1:

        # Navigating to home screen
        if not action.home():
            return False, "Home screen not validated"

        # Navigating to setting screen
        if not action.submenu("settings"):
            return False, "Setting screen not validated"

        # Navigating to kinder
        if not action.kinder():
            return False, "Error navigating to kinder"

        # lock KA content
        action.lockKAContent()

        # Deativate komfort
        action.activateKomfort(False)

        # Navigate to direct recording menu
        cmdList = ["pback", "pok"]
        stb_rcu.sendmulti(cmdList, 5)
        time.sleep(10)
        cmdList = ["pleft"]*3 + ["pok"]
        stb_rcu.sendmulti(cmdList, 2)

        # Enable direct recording
        action.enableDirectRecording()

    # Navigate to live TV
    print("Navigating to live TV")
    action.liveTV()

    # Navigate to Unrated channel
    print("Tuning to an unrated channel")
    action.tuneChannel("1")
    time.sleep(5)

    # Validate if the live tv is locked
    if not screen.isLiveTVLocked():
        return False, "Live TV is not locked. Live TV should be locked"
    print("Live TV is locked, Unlocking content now")

    # Unlock the content
    action.unlockContent()

    # Check if the content is playing
    stb_rcu.send("pvolplus")
    if not screen.isContentPlaying():
        return False, "Content is not playing"
    print("Content is playing fine, Recording the content")

    # Record the content
    stb_rcu.send("precord")
    time.sleep(60)

    # Stop the recording
    stb_rcu.send("precord")
    time.sleep(7)

    # Navigating to Recordings Menu
    if not action.submenu("recordings"):
        return False, "Recording screen not validated"

    # Play the recording
    cmdList = ["pdown", "pdown", "pok"]
    stb_rcu.sendmulti(cmdList, 3)
    time.sleep(7)

    # Validate the details page
    if not screen.isDetailsPage("REC"):
        return False, "Details page not validated"
    print("Recording Detail Page Validated, Navigating to play the content")

    # Play the content
    stb_rcu.send("pok")
    time.sleep(7)

    # Validate if the recording is locked
    if not screen.isLiveTVLocked():
        return False, "Live TV is not locked. Live TV should be locked"
    print("Live TV is locked, Unlocking content now")

    # Unlock the content
    action.unlockContent()

    # Check if the content is playing
    if not screen.isContentPlaying():
        return False, "Content is not playing"
    print("Content is playing fine, Recording the content")

    # Navigate to home
    if not action.home():
        return False, "Home screen not validated"

    return True, "All the steps executed and validated properly"


def test_NGTVTEST_3102(extra):
    pytest.test_NGTVTEST_3102_counter += 1
    testoutputname = __name__ + "_" + str(pytest.test_NGTVTEST_3102_counter)
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
    test_NGTVTEST_3102('')