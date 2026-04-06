# Author: Kaishik Gundu
# Date: 16/09/2021

"""
Sprint No: 99

Test Case ID: NGTVTEST-2764

Test Case Description: Play VOD on STB Client for free content

Expected result: VOD is playing fine

Notes: None

OCR Engine - Tesseract
"""

from src.stb_lib.stb import *

# Variable to hold the counter (to handle --count case)
pytest.test_NGTVTEST_2764_counter = 0


def playVOD():
    """
    The function is used to play the VOD in Film and Meine Film and Series Section
    @return:
    """
    # Opening the VOD content
    print("Opening the VOD content")
    stb_rcu.send("pok")
    time.sleep(10)

    # Validate the details page
    if not screen.isDetailsPage("VOD"):
        return False, "Details page not validated"
    print("VOD Detail Page Validated, Navigating to play the content")

    # Play the VOD content
    cmdList = ["pok"]
    stb_rcu.sendmulti(cmdList, 5)
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
    if not screen.isContentPlaying():
        return False, "VOD content(Film) is not playing"
    print("VOD content is playing fine")

    return True, "VOD content(Film) is playing"


def executeTestCase():
    """
    This function validates all the required check conditions
    :return : return True if all the check conditions are validated successfully.
    Note: Mention the reason in case of a failure (return False, "error message")
    """

    # Navigate to Home Screen
    if not action.home():
        return False, "Home screen is not validated"

    # Navigating to Recordings Menu
    if not action.submenu("recordings"):
        return False, "Film screen not validated"

    # Delete all the recordings
    iteration = 5
    while not screen.isAllRecordingsDeleted():
        if not action.deleteAllRecordings():
            return False, "Unable to delete all recordings"
        iteration -= 1
        if iteration == 0:
            break
    print("All recording deleted")

    # Navigate to film and series
    print("Navigating to film section")
    cmdList = ["pdown"] * 3
    stb_rcu.sendmulti(cmdList, 5)
    time.sleep(5)

    # Validate the Meine filme logo
    if not screen.isMeineFilmAndSeries():
        return False, "The Meine Filme and Series logo is not verified"

    # Opening film and series section
    print("Opening film and series section")
    stb_rcu.send("pok")

    # Wait for the film section to load (timeout=40secs)
    startTime = time.time()
    loaded = False
    while time.time() - startTime < 40:
        if screen.isLogoInDetailsPage("VOD"):
            loaded = True
            break
    if not loaded:
        print("Film and series section not loaded")
        return False, "Film and series section not loaded"
    print("Film and series page loaded")
    
    # Play the VOD content
    ret, message = playVOD()
    if not ret:
        print(message)
        return False, message

    # Navigate to home
    if not action.home():
        return False, "Home screen not validated"

    return True, "All the steps executed and validated properly"


def test_NGTVTEST_2764(extra):
    pytest.test_NGTVTEST_2764_counter += 1
    testoutputname = __name__ + "_" + str(pytest.test_NGTVTEST_2764_counter)
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
    test_NGTVTEST_2764('')