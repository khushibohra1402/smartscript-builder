# Author: Karan Sehgal
# Date: 02/02/2021

"""
Sprint No: 5.1

Test Case ID: NGTVTEST-20592

Test Case Description: 1h: Timeshift

Expected result: The test case is to give a brief feeling of the latest sw
                    and to find blocker problems in a first state.

OCR Engine - Tesseract
"""
from src.stb_lib.stb import *
# Importing the necessary driver files


def executeTestCase():
    """
    This function validates all the required check conditions
    :return : return True if all the check conditions are validated successfully.
    """
    pauseTime = 100

    # Step-1 Navigate to Home Screen
    if not action.home():
        return False

    # Step-2 Navigate to Settings Screen
    if not action.submenu("settings"):
        return False

    # Step-3 Navigate to Kinder&Jugendschutz and Enter PCon Pin
    if not action.kinder():
        return False
    time.sleep(3)

    # Step-4 Activate komfort feature
    action.activateKomfort()

    # Step-5 Navigate to LiveTV
    print("Navigating to Live TV")
    action.liveTV()

    # Step-6 Navigating to Above12 channel with timeshift enabled on it.
    print("Tuning to channel number 1")
    action.tuneChannel("1")

    assert stb_rcu.sendmulti(["pok"] * 2, 1)
    time.sleep(1)

    # Step-7 Check if time shift is present or not
    if not screen.isTimeShiftAvailable():
        return False
    print("Content paused. Waiting for a few mins")
    time.sleep(pauseTime)

    # Step-8 Validate timeshift
    assert stb_rcu.sendmulti(["pok"] * 2, 1)
    time.sleep(7)

    # Step-9 Checking whether rewind is working or not (1 rewind press takes us 10 secs backwards).
    if not action.trickPlay("LiveTV", "rewind", 6):
        print("Failed to perform Rewind operation.")
        return False
    print("Rewind working fine")

    # Step-10 Check fast forward functionality
    if not action.trickPlay("LiveTV", "fastForward", 3):
        print("Failed to perform fast forward operation.")
        return False

    return True


def test_NGTVTEST20592(extra):
    testoutputname = __name__
    try:
        #Choosing OCR Engine (True - GV, False - Tesseract)
        action.useVision(False)

        if connection_type == "telnet":
            assert stb.connect()
        assert tv.connect()
        tv.show()
        tv.saveVideo(testoutputname)
        assert executeTestCase()
        print('Test Case Passed.')
    except:
        print("Test Case Failed")
        tv.saveframe(testoutputname)
        extra.append(extras.video("file:Videos\\" + testoutputname + ".mp4"))
        extra.append(extras.image("file:Images\\" + testoutputname + ".png"))
        assert False
    finally:
        tv.closescreen()
        tv.shutdown()
        time.sleep(10)


if __name__ == '__main__':
    test_NGTVTEST20592('')