# Author: Kaishik Gundu
# Date: 16/08/2021

"""
Sprint No: 97

Test Case ID: NGTVTEST-1446

Test Case Description: Create a bookmark for local PVR program

Expected result: Local PVR bookmark is successfully added

Notes: None

OCR Engine - Google Vision
"""

from src.stb_lib.stb import *

# Variable to hold the counter (to handle --count case)
pytest.test_NGTVTEST_1446_counter = 0


def executeTestCase():
    """
    This function validates all the required check conditions
    :return : return True if all the check conditions are validated successfully.
    Note: Mention the reason in case of a failure (return False, "error message")
    """

    recordSeconds = 300
    playContentFor = 30

    if pytest.test_NGTVTEST_1446_counter == 1:
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

        # if pytest.test_NGTVTEST_1446_counter == 1:
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

        # Enable direct recording
        action.enableDirectRecording()

        # Exit to live TV
        print("Navigating to live TV")
        action.liveTV()

        action.tuneChannel("1")

        # If the content is locked, unlock it
        if screen.isLiveTVLocked():
            action.unlockContent(komfort=True)

        # Record a content for 5mins
        print("Recording the content for 5mins")
        action.recordLive(recordSeconds)

    # Navigate to home
    if not action.home():
        return False, "Home screen not validated"

    # Navigate to Recordings submenu
    if not action.submenu("recordings"):
        return False, "Recording screen not validated"

    # Open the recording
    print("Opening the recorded content")
    cmdList = ["pdown"]*2 + ["pok"]
    stb_rcu.sendmulti(cmdList, 2)
    time.sleep(7)

    # Validate details page
    if not screen.isDetailsPage("REC"):
        return False, "Recording details page not validated"

    # Play the recording
    print("Playing the recording")
    stb_rcu.send("pok")
    time.sleep(5)

    # If Locked, then unlock it
    if screen.isLiveTVLocked():
        action.unlockContent(komfort=True)

    # Check if the content is playing or not
    stb_rcu.send("pvolplus")
    time.sleep(3)

    # Perform instant restart
    cmdList = ["pok", "pdown", "pleft", "pok"]
    stb_rcu.sendmulti(cmdList, 0.7)
    print("Content starting from beginning")
    time.sleep(7)

    # After performing instant restart , check if the content is playing
    if not screen.isContentPlaying():
        return False, "Content is not playing"

    # Wait for 1min
    time.sleep(playContentFor)

    # Pause the content
    print("Pausing the content")
    cmdList = ["pok"]*2
    stb_rcu.sendmulti(cmdList, 2)

    # Fetch time - Bookmark 1
    ret, bookmarkTime = screen.fetchTime("VOD")
    if not ret:
        msg = "Could not fetch the time"
        print(msg)
        return False, msg

    # Exit recording
    print("Navigating to live TV")
    action.liveTV()

    # Navigate to home
    if not action.home():
        return False, "Home screen not validated"

    # Navigate to Recording submenu
    if not action.submenu("recordings"):
        return False, "Recording screen not validated"

    # Open the recording
    print("Opening the recorded content")
    cmdList = ["pdown"] * 2 + ["pok"]
    stb_rcu.sendmulti(cmdList, 2)
    time.sleep(7)

    # Validate details page
    if not screen.isDetailsPage("REC"):
        return False, "Recording details page not validated"

    # Play the recording
    print("Playing the content")
    stb_rcu.send("pok")
    time.sleep(5)

    # If Locked, then unlock it
    if screen.isLiveTVLocked():
        action.unlockContent()

    # Fetch new time
    stb_rcu.send("pok")
    time.sleep(3)
    ret, newTime = screen.fetchTime("VOD")
    if not ret:
        msg = "Could not fetch the time"
        print(msg)
        return False, msg

    # Fetch time >= BookmarkTime
    if newTime < bookmarkTime:
        msg = "New bookmark time is less than the older bookmark time"
        print(msg)
        return False, msg

    if newTime - bookmarkTime > 30:
        msg = "New bookmark time much greater than the old bookmark time"
        print(msg)
        return False, msg

    # Check if the content is playing
    if not screen.isContentPlaying():
        return False, "Content is not playing"

    # Exit the recording
    print("Navigating to live TV")
    action.liveTV()

    # Navigate to home
    if not action.home():
        return False, "Home screen not validated"

    return True, "All the steps executed and validated properly"


def test_NGTVTEST_1446(extra):
    pytest.test_NGTVTEST_1446_counter += 1
    testoutputname = __name__ + "_" + str(pytest.test_NGTVTEST_1446_counter)
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
    test_NGTVTEST_1446('')