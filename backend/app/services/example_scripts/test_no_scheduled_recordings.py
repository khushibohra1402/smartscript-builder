"""
Test Case: No Scheduled Recordings Display
Description:
Validate that no scheduled recordings are displayed in the recordings menu when no recordings have been scheduled.
Steps:
- Navigate to the recordings menu
- Open the scheduled recordings section
- Verify that no scheduled recordings are listed
Expected:
The scheduled recordings list should be empty when no recordings are scheduled.
Preconditions:
- No recordings should be scheduled on the device
- Device should be powered on and accessible
OCR:
Tesseract
"""

from src.stb_lib.stb import *

# Variable to hold the counter (to handle --count case)
pytest.test_NGTVTEST_1518_counter = 0


def executeTestCase():
    """
    This function validates all the required check conditions
    :return : return True if all the check conditions are validated successfully.
    Note: Mention the reason in case of a failure (return False, "error message")
    """

    # Navigating to Home
    if not action.home():
        return False, "Home screen not validated"

    # Navigating to Film Section
    if not action.submenu("recordings"):
        return False, "Recordings screen not validated"

    # Delete all the recordings and validate No recordings available
    iteration = 5
    while not screen.isAllRecordingsDeleted():
        if not action.deleteAllRecordings():
            return False, "Unable to delete all recordings"
        iteration -= 1
        if iteration == 0:
            break
    print("No scheduled recordings are available in the Meine Aufnahme screen. 'Geplante Aufnahmen' is not displayed")

    return True, "All the steps executed and validated properly"


def test_NGTVTEST_1518(extra):
    pytest.test_NGTVTEST_1518_counter += 1
    testoutputname = __name__ + "_" + str(pytest.test_NGTVTEST_1518_counter)
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
    test_NGTVTEST_1518('')