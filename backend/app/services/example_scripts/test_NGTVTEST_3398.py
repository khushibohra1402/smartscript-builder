# Author: Anup Kumar B
# Date:

"""
Sprint No: 100

Test Case ID: NGTVTEST-3398

Test Case Description: Creating an instant one click single recording from master STB while watching live TV

Expected result: Instant record for unencrypted channel should work fine

Notes:

OCR Engine - Tesseract
"""

from src.stb_lib.stb import *

# Variable to hold the counter (to handle --count case)
pytest.test_NGTVTEST_3398_counter = 0


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

    # Navigating to home screen
    if not action.home():
        return False, "Home screen not validated"

    # Navigating to setting screen
    if not action.submenu("settings"):
        return False, "Setting screen not validated"

    # Enable direct recording
    action.enableDirectRecording()

    # Navigate to live TV
    print("Navigating to live TV")
    action.liveTV()

    # Navigate to unicast uencrypted channel
    print("Tuning to a unicast uencrypted channel")
    action.tuneChannel(config.unicastUnencrypted)

    # Validate if the live tv is locked
    if screen.isLiveTVLocked():
        print("Live TV is locked, Unlocking content now")
        action.unlockContent(komfort=True)

    # Check if the content is playing
    stb_rcu.send("pvolplus")
    if not screen.isContentPlaying():
        return False, "Content is not playing"
    print("Content is playing fine, Recording the content")

    # Record the content
    stb_rcu.send("precord")

    # Validate recording started popup
    if not screen.isRecordingPopup("start"):
        return False, "Popup did not appear after recording started"

    # Let content play for 5mins
    time.sleep(300)

    # Stop the recording
    print("Stopping the recording")
    stb_rcu.send("precord")

    # Validate recording stopped popup
    if not screen.isRecordingPopup("stop"):
        return False, "Popup did not appear after recording stopped"

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

    # Navigate to home
    if not action.home():
        return False, "Home screen not validated"

    return True, "All the steps executed and validated properly"


def test_NGTVTEST_3398(extra):
    pytest.test_NGTVTEST_3398_counter += 1
    testoutputname = __name__ + "_" + str(pytest.test_NGTVTEST_3398_counter)
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
    test_NGTVTEST_3398('')