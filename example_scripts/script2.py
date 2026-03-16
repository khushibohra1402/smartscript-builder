# Author: Kaishik Gundu
# Date: 10-06-21

"""
Sprint No: 100

Test Case ID: NGTVTEST-11205

Test Case Description: Change volume of VOD content

Expected result: VOD is playing, volume change possible

Notes: None

OCR Engine - Tesseract
"""

from src.stb_lib.stb import *

# Variable to hold the counter (to handle --count case)
pytest.test_NGTVTEST_11205_counter = 0


def executeTestCase():
    """
    This function validates all the required check conditions
    :return : return True if all the check conditions are validated successfully.
    Note: Mention the reason in case of a failure (return False, "error message")
    """

    # Navigate to home
    if not action.home():
        return False, "Home screen not validated"

    # Navigating to series section
    if not action.submenu("film"):
        return False, "Film screen not validated"

    # Navigating to a film content
    print("Navigating to a film content")
    cmdList = ["pdown"] * 2
    stb_rcu.sendmulti(cmdList, 2)
    time.sleep(5)

    # Opening a film content
    cmdList = ["pok"] * 1
    stb_rcu.sendmulti(cmdList, 7)
    time.sleep(10)

    # Validate the details page
    if not screen.isDetailsPage():
        return False, "Details page not validated"

    # Play the content
    action.playVODContent()
    time.sleep(10)

    # Unlock if locked
    if screen.isPCONPinPopupScreen():
        print("PCON Pin appeared. Unlocking it now")
        stb_rcu.send("pdown")
        time.sleep(3)
        action.enterPin()
    time.sleep(20)
    
    # Set volume
    assert stb_rcu.send("pvolplus")
    
    # Validate if the content is playing properly
    if not screen.isContentPlaying():
        return False, "VOD content(Series) is not playing"
    
    # Decreasing the volume
    print("Decreasing the volume")
    assert stb_rcu.send("pvolminus")
    time.sleep(2)
    print("Volume decreased")
    
    # Increasing the volume
    print("Increasing the volume")
    assert stb_rcu.send("pvolplus")
    time.sleep(2)
    print("Volume increased")
    
    # Navigate to home
    if not action.home():
        return False, "Home screen not validated"

    return True, "All the steps executed and validated properly"


def test_NGTVTEST_11205(extra):
    pytest.test_NGTVTEST_11205_counter += 1
    testoutputname = __name__ + "_" + str(pytest.test_NGTVTEST_11205_counter)
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
    test_NGTVTEST_11205('')
