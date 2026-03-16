# Author: Kaishik Gundu
# Date: 24/08/21

"""
Sprint No: 98

Test Case ID: NGTVTEST-14012

Test Case Description: Watch unicast encrypted HD and SD channels

Expected result: Unicast encrypted channels must play in HD/SD properly

Notes: Find the required channel and update in the json file. (VPN: VPNClient1059 -> channel: 260)

OCR Engine - Tesseract
"""

from src.stb_lib.stb import *

# Variable to hold the counter (to handle --count case)
pytest.test_NGTVTEST_14012_counter = 0


def executeTestCase():
    """
    This function validates all the required check conditions
    :return : return True if all the check conditions are validated successfully.
    Note: Mention the reason in case of a failure (return False, "error message")
    """

    # Navigate to live TV
    action.liveTV()

    # Tune to a unicast encrypted channel: 11(Auto motor sport channel)
    print("Tuning to a unicast encrypted channel: 260")
    action.tuneChannel(config.unicastEncrypted)

    # Unlock the content if it is locked
    if screen.isLiveTVLocked():
        action.unlockContent(komfort=True)

    # Set resolution to HD
    if not action.setResolution("HD"):
        return False, "Could not set resolution to HD"

    action.liveTV()

    # Validate if the content is playing properly
    stb_rcu.send("pvolplus")
    time.sleep(3)
    if not screen.isContentPlaying():
        return False, "Content is not playing in HD quality"
    print("Content is playing in HD quality successfully")

    # Set resolution to SD
    if not action.setResolution("SD"):
        return False, "Could not set resolution to HD"

    action.liveTV()

    # Validate if the content is playing properly
    if not screen.isContentPlaying():
        return False, "Content is not playing in SD quality"
    print("Content is playing in SD quality successfully")

    return True, "All the steps executed and validated properly"


def test_NGTVTEST_14012(extra):
    pytest.test_NGTVTEST_14012_counter += 1
    testoutputname = __name__ + "_" + str(pytest.test_NGTVTEST_14012_counter)
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
    test_NGTVTEST_14012('')
