# Author: Anup
# Date: 01/09/2021

"""
Sprint No: 98

Test Case ID: NGTVTEST-3422

Test Case Description: Instant record from detailed page (SD channel)

Expected result: Recording should be possible

Notes: Update the sd channel in the configuration file (EGTF-VPN 1049: Channel Number - 85)

OCR Engine - Google Vision
"""

from src.stb_lib.stb import *

# Variable to hold the counter (to handle --count case)
pytest.test_NGTVTEST_3422_counter = 0


def executeTestCase():
    """
    This function validates all the required check conditions
    :return : return True if all the check conditions are validated successfully.
    Note: Mention the reason in case of a failure (return False, "error message")
    """

    # Navigate to home
    if not action.home():
        return False, "Home screen not validated"

    # Navigate to settings
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

    if pytest.test_NGTVTEST_3422_counter == 1:
        # Navigate to home
        if not action.home():
            return False, "Home screen not validated"

        # Navigate to settings
        if not action.submenu("settings"):
            return False, "Setting screen not validated"

        # Navigate to recording setting
        if not action.recordingSetting():
            return False, "Unable to navigate to recording settings"
        time.sleep(5)

        # Disable direct recording
        action.enableDirectRecording(False)

    # Navigate to live TV
    print("Navigating to live TV")
    action.liveTV()

    # Tune to a sd channel
    print(f"Tuning to an sd channel: {config.sdChannel}")
    action.tuneChannel(config.sdChannel)

    # Unlock if the content is locked
    if screen.isLiveTVLocked():
        action.unlockContent(komfort=True)

    # Navigate to EPG screen
    print("Navigating to EPG")
    stb_rcu.send("pguide")

    # Validate EPG screen
    if not screen.isEPGScreenValid(20):
        msg = "EPG screen not validated"
        print(msg)
        return False, msg
    print("EPG screen validated")

    # Open details page
    print("Opening the details page")
    stb_rcu.send("pinfo")
    time.sleep(10)

    # Validate the details page
    if not screen.isDetailsPage("TV"):
        return False, "Details page not validated"

    # Validate if start recording is present or not
    if not action.checkDetailsRecordingOption("start"):
        return False, "Start Recording option is not available in details page"

    # Record the content
    stb_rcu.send("pok")
    time.sleep(5)

    # Validate the recording popup
    if not screen.isAufnahmePlanen():
        msg = "Aufnameh planen popup did not appear"
        print(msg)
        return False, msg
    print("Popup appeared, recording the content now")
    stb_rcu.send("pok")

    # Validate popup if the content is getting recorded or not
    if not screen.isRecordingPopup("start"):
        return False, "Recording started popup did not appear"

    time.sleep(20)

    # Check if the screen is refreshed and play recording is available or not
    if not screen.isDetailsRecordingOption("play"):
        return False, "Play button is not available"
    print("Screen is refreshed and recording play button is present")

    # Check if the stop recording option is present in the screen or not
    if not action.checkDetailsRecordingOption("stop"):
        return False, "Stop Recording option in Details page is not present"

    # Stop the recording
    stb_rcu.send("pok")

    # Validate popup if the content recording is stopped or not
    if not screen.isRecordingPopup("stop"):
        return False, "Recording stopped popup did not appear"

    time.sleep(10)

    # Check if the screen is refreshed and play recording is available or not
    if not screen.isDetailsRecordingOption("play"):
        return False, "Play button is not available"
    print("Screen is refreshed and recording play button is present")

    # Check if the stop recording option is present in the screen or not
    if action.checkDetailsRecordingOption("stop"):
        return False, "Stop Recording option in Details page is present (Should not be present)"

    # Navigate to extreme left to check for delete recording option
    cmdList = ["pleft"]*5
    stb_rcu.sendmulti(cmdList, 2)
    time.sleep(3)

    # Check if the delete recording option is present in the screen or not
    if not action.checkDetailsRecordingOption("delete"):
        return False, "Delete Recording option in Details page is not present"

    # Delete the recording
    print("Deleting the recording")
    cmdList = ["pok"]*2
    stb_rcu.sendmulti(cmdList, 5)

    # Validate popup if the recorded content is deleted
    if not screen.isRecordingPopup("delete"):
        return False, "Recording stopped popup did not appear"
    print("Recording deleted")

    if not action.home():
        return False, "Home screen not validated"

    return True, "All the steps executed and validated properly"


def test_NGTVTEST_3422(extra):
    pytest.test_NGTVTEST_3422_counter += 1
    testoutputname = __name__ + "_" + str(pytest.test_NGTVTEST_3422_counter)
    try:
        #Choosing OCR Engine (True - GV, False - Tesseract)
        action.useVision(True)

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
    test_NGTVTEST_3422('')