# Author: Pranita Rathore

"""
Sprint No: 120

Test Case ID: NGTVTEST-38448

Test Case Description: Live to Startsite navigation time calculation.

Expected result: This script will help us in the performance testing. It will calculate the total time taken from Live TV to Startsite / Menu screen navigation.

Pre-requisite:  Before starting the script, the parental rating should be unlocked.
                Tune to channel 1 or Home Screen and start the testcase.
                Frames for DEV STB for the banner will be same but in PROD banner keeps changing.
                Ensure the banner remains same in the complete test execution. If test failed with frame comparison
                in any iteration check the banner first.
                PROD STB ONLY: Frame which is considered as test data, should be edited in the test case before execution by the tester manually.
"""

from src.stb_lib.stb import *
import cv2

def executeTestCase():

    # Going to Live TV
    stb_rcu.send("pexit")
    print("In Live TV")
    if screen.isContentPlaying():
        # Starting the timer
        print("Content is playing, starting the timer...")
        result["startTime"] = time.time()
        print("startTime  =", result["startTime"])
    else:
        print("Some issue with Live TV")
        return False

    # Going to Home menu
    stb_rcu.send("pmenu")
    if action.screen.isHomeScreen(50):
        print("In Home menu screen")
        # If screen loading takes more time, increase the sleep time here.
        time.sleep(20)
        template1 = cv2.imread(screen.dataSetFilePath + "startsite_data.png")
        ret, frame = screen.tv.getFrame()
        frame = frame[168:207, 506:558]
        if screen.frameComparision(frame, template1) == 1 and "jetzt läuft im tv" in screen.image_to_text(screen.tv.getFrame()[1][305:329, 20:142]).lower():
            # Ending the timer
            result["endTime"] = time.time()
            print("\nEnd Time: ", result["endTime"])
            result["TotalTime"] = (result["endTime"] - result["startTime"])
            # The time which is being decreased here should be same as time.sleep() in line 32
            result["TotalTime"] = result["TotalTime"] - 20
            print(f'Total time of the change from Live TV to Home menu {result["TotalTime"]} secs')
        else:
            print("Failed in either frame or text comparison")
            return False
    else:
        print("Some issue in loading Home screen")
        return False

    return True

def test_LiveTV_to_Home(extra):
    testoutputname = __name__
    global result

    result = {"startTime": 'NA',
              "endTime": 'NA',
              "TotalTime":'NA'}
    try:
        assert tv.connect()
        tv.show()
        if connection_type == "telnet":
            assert stb.connect()
        tv.saveVideo(testoutputname)
        assert executeTestCase()
        print('Test execution completed')
    except:
        print("Test Case Failed")
        tv.saveframe(testoutputname)
        extra.append(extras.video("file:Videos\\" + testoutputname + ".mp4"))
        extra.append(extras.image("file:Images\\" + testoutputname + ".png"))
        assert False
    finally:
        # Create a folder in report with the name sessionid if not created previously
        if not os.path.isdir("report/" + sessionid()):
            os.mkdir("report/" + sessionid())

        # Add data to the excel sheet
        add_row_to_excel(['Start', 'End', 'Change time from Live TV to Home menu'],
                         [result["startTime"], result["endTime"], result["TotalTime"]],
                         'report/' + sessionid() + '/LiveTV_to_Home_menu.xlsx', 'ChangeTime')

        result.clear()
        tv.closescreen()
        tv.shutdown()


if __name__ == '__main__':
    test_LiveTV_to_Home('')