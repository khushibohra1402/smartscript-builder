# Author: Pradeep Umesh

"""
Sprint No: 120

Test Case ID: NGTVTEST-38509

Test Case Description: EPG Live Event to next EPG event time calculation without recordings

Expected result: This script will help us in the performance testing. It will calculate the total time taken from Current
EPG event to next EPG event of same channel.

Pre-requisite:  Before starting the script, the parental rating should be unlocked.
                Tune to Home Screen and start the testcase.
"""

from src.stb_lib.stb import *
import cv2

def executeTestCase():

    # Going to Live TV
    stb_rcu.send("pexit")
    time.sleep(5)
    print("In Live TV")
    if screen.isContentPlaying():
        print("Live TV Content is playing")
    else:
        print("Some issue with Live TV playback")
        return False

    # Going to EPG menu
    stb_rcu.send("pguide")
    currentEvent = False
    template1 = cv2.imread(screen.dataSetFilePath + "NOCH_data.png")
    result["waitTime"] = time.time()
    while not currentEvent:
        ret, frame = screen.tv.getFrame()
        frame = frame[143:156, 226:251]
        if "heute" in screen.image_to_text(screen.tv.getFrame()[1][213:230, 74:138]).lower() and screen.frameComparision(frame, template1) == 1:
            result["startTime"] = time.time()
            print("startTime  =", result["startTime"])
            currentEvent = True
        else:
            time.sleep(0.5)
            result["waitTime"] = result["waitTime"] + 0.5
            if time.time() - result["waitTime"] > 20:       # Timeout value can be increased on need basis
                print("Failed in either frame or text comparison within the timeout")
                return currentEvent

    #Navigate to next Event in the current Channel or Service.
    stb_rcu.send("pright")
    template2 = cv2.imread(screen.dataSetFilePath + "Heute_data.png")
    nextEvent = False
    result["eventTime"] = time.time()
    while not nextEvent:
        ret, frame1 = screen.tv.getFrame()
        frame1 = frame1[146:154, 228:252]
        if screen.frameComparision(frame1, template2) == 1:
            # Ending the timer
            result["endTime"] = time.time()
            print("\nEnd Time: ", result["endTime"])
            result["TotalTime"] = (result["endTime"] - result["startTime"])
            print(f'Total time of the change Event in EPG {result["TotalTime"]} secs')
            nextEvent = True
        else:
            time.sleep(0.5)
            result["eventTime"] = result["eventTime"] + 0.5
            if time.time() - result["eventTime"] > 20:       # Timeout value can be increased on need basis
                print("Failed in either frame or text comparison within the timeout in next event")
                return nextEvent
    return nextEvent

def test_EPG_Event_Navigation(extra):
    testoutputname = __name__
    global result

    result = {"startTime": 'NA',
              "endTime": 'NA',
              "TotalTime":'NA',
              "waitTime": 'NA',
              "eventTime": 'NA'}
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
        add_row_to_excel(['Start', 'End', 'Change time from EPG current event to next event'],
                         [result["startTime"], result["endTime"], result["TotalTime"]],
                         'report/' + sessionid() + '/EPG_Next_Event.xlsx', 'ChangeTime')

        result.clear()
        tv.closescreen()
        tv.shutdown()

if __name__ == '__main__':
    test_EPG_Event_Navigation('')