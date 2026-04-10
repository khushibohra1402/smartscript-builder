# Author: Pradeep Umesh

"""
Sprint No: 120

Test Case ID: NGTVTEST-38510

Test Case Description: Home(Startsite) to Live time calculation

Expected result: This script will help us in the performance testing. It will calculate the total time taken from Home screen (startsite) to Live TV.

Pre-requisite:  Before starting the script, the parental rating should be unlocked.
                Tune to channel 1 and start the testcase.
                This script will use background blank image and compare the coloured banner and if loaded then validation is successful.
"""

from src.stb_lib.stb import *
import cv2

def executeTestCase():

    stb_rcu.send("pexit")
    time.sleep(5)
    stb_rcu.send("pmenu")
    print("In Home menu screen")
    screenValid = False
    template1 = cv2.imread(screen.dataSetFilePath + "reference.png")
    result["waitTime"] = time.time()
    while not screenValid:
        ret, frame = screen.tv.getFrame()
        # Change the dimensions of frame according to the image cropped.
        frame = frame[100:230, 385:600]
        if screen.frameComparision(frame, template1) != 1 and "jetzt läuft im tv" in screen.image_to_text(screen.tv.getFrame()[1][305:329, 20:142]).lower():
            result["startTime"] = time.time()
            print("startTime  =", result["startTime"])
            screenValid = True
        else:
            time.sleep(0.2)
            result["waitTime"] = result["waitTime"] + 0.2
            if time.time() - result["waitTime"] > 20:       # Timeout value can be increased on need basis
                print("Failed in either frame or text comparison within the timeout in Home screen")
                return screenValid

    #Going back to Live TV
    stb_rcu.send("pexit")
    print("In Live TV")
    if screen.isContentPlaying():
        print("Live Tv Playing END the timer...")
        result["endTime"] = time.time()
        print("\nEnd Time: ", result["endTime"])
        result["TotalTime"] = (result["endTime"] - result["startTime"])
        print(f'Total time of the change from Live TV to Home menu {result["TotalTime"]} secs')
    else:
        print("Some issue with playback of Live TV")
        return False

    return True


def test_Home_to_LiveTV(extra):
    testoutputname = __name__
    global result

    result = {"startTime": 'NA',
              "endTime": 'NA',
              "TotalTime":'NA',
              "waitTime": 'NA'}
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
        add_row_to_excel(['Start', 'End', 'Change time from Home to Live TV'],
                         [result["startTime"], result["endTime"], result["TotalTime"]],
                         'report/' + sessionid() + '/Home_to_LiveTV.xlsx', 'ChangeTime')
        result.clear()
        tv.closescreen()
        tv.shutdown()

if __name__ == '__main__':
    test_Home_to_LiveTV('')