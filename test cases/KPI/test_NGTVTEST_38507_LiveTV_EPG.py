# Author: Pradeep Umesh

"""
Sprint No: 120

Test Case ID: NGTVTEST-38507

Test Case Description: Live to EPG time calculation without recordings

Expected result: This script will help us in the performance testing. It will calculate the total time taken from Live TV to EPG.

Pre-requisite:  Fresh boot of STB is required to start the test.
                Before starting the script, the parental rating should be unlocked.
                Tune to channel 1 or Home Screen and start the testcase.
                NOCH_data file should be present in the data set folder
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

    # Going to EPG menu
    stb_rcu.send("pguide")
    print("In EPG screen")
    screenValid = False
    template = cv2.imread(screen.dataSetFilePath + "NOCH_data.png")
    result["waitTime"] = time.time()
    while not screenValid:
        ret, frame = screen.tv.getFrame()
        frame = frame[143:156, 226:251]
        if screen.frameComparision(frame, template) == 1 and "heute" in screen.image_to_text(screen.tv.getFrame()[1][213:230, 74:138]).lower():
            # Ending the timer
            print("\nEnd Time: ", result["waitTime"])
            # Total time calculation
            result["TotalTime"] = (result["waitTime"] - result["startTime"])
            print(f'Total time of the change from Live TV to EPG {result["TotalTime"]} secs')

        else:
            time.sleep(0.2)
            result["waitTime"] = result["waitTime"] + 0.2
            if time.time() - result["waitTime"] > 20:       # Timeout value can be increased on need basis
                print("Failed in either frame or text comparison within the timeout")
                break
    return screenValid

def test_LiveTV_to_EPG(extra):
    testoutputname = __name__
    global result

    result = {"startTime": 'NA',
              "waitTime": 'NA',
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
        add_row_to_excel(['Start', 'End', 'Change time from Live TV to EPG'],
                         [result["startTime"], result["waitTime"], result["TotalTime"]],
                         'report/' + sessionid() + '/LiveTV_to_epg.xlsx', 'ChangeTime')

        result.clear()
        tv.closescreen()
        tv.shutdown()

if __name__ == '__main__':
    test_LiveTV_to_EPG('')