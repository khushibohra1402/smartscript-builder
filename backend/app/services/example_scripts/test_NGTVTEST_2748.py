# Author: Kaishik Gundu
# Date: 19/08/21

"""
Sprint No: 98

Test Case ID: NGTVTEST-2748

Test Case Description: Play Trailer on STB Device for bought or rented content

Expected result: Trailer of VOD content must be available and playing as expected

Notes:

OCR Engine - Google Vision
"""
import time

from src.stb_lib.stb import *

# Variable to hold the counter (to handle --count case)
pytest.test_NGTVTEST_2748_counter = 0


def executeTestCase():
    """
    This function validates all the required check conditions
    :return : return True if all the check conditions are validated successfully.
    Note: Mention the reason in case of a failure (return False, "error message")
    """

    # Navigating to Home
    if not action.home():
        return False, "Home screen not validated"

    if not action.submenu("apps"):
        return False

    # Navigating to Film Section
    if not action.submenu("film"):
        return False, "Film screen not validated"

    # Navigating to a VOD content
    print("Navigating to a VOD content")
    cmdList = ["pdown"]*2
    stb_rcu.sendmulti(cmdList, 2)
    time.sleep(5)

    # Opening the VOD content
    print("Opening the VOD content")
    stb_rcu.send("pok")
    time.sleep(5)

    # Validate the details page
    if not screen.isDetailsPage("VOD"):
        return False, "Details page not validated"

    # Validate if trailer is present
    textCaptured = screen.image_to_text(tv.getFrame()[1][300:327, 27:143]).lower()
    if "trailer" not in textCaptured:
        msg = "Trailer option is not present"
        print(msg)
        print("Checking in the next VOD content")
        stb_rcu.send("pback")
        time.sleep(3)
        stb_rcu.send("pright")
        time.sleep(3)
        stb_rcu.send("pok")
        time.sleep(3)
        textCaptured1 = screen.image_to_text(tv.getFrame()[1][300:327, 27:143]).lower()
        if "trailer" not in textCaptured1:
            return False, msg
    print("Trailer is present in the VOD content")

    # Navigate to trailer
    print("Navigating to trailer")
    stb_rcu.send("pdown")
    time.sleep(5)

    # Play the trailer
    print("Playing the trailer")
    stb_rcu.send("pok")
    time.sleep(7)

    # If PCON pin popup, enter the pin
    if screen.isPCONPinPopupScreen():
        print("PCON Pin appeared. Unlocking it now")
        stb_rcu.send("pdown")
        time.sleep(3)
        action.enterPin()
    time.sleep(20)

    # Validate if the content is playing properly
    stb_rcu.send("pvolplus")
    time.sleep(3)
    if not screen.isContentPlaying():
        return False, "VOD content(Film) is not playing"

    # Navigate to home
    if not action.home():
        return False, "Home screen not validated"

    return True, "All the steps executed and validated properly"


def test_NGTVTEST_2748(extra):
    pytest.test_NGTVTEST_2748_counter += 1
    testoutputname = __name__ + "_" + str(pytest.test_NGTVTEST_2748_counter)
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
    test_NGTVTEST_2748('')