# Author: Anup Kumar B
# Date: 05/05/2021

"""
Test Case Number: NGTVTEST_CHannel_banner_load_time

Test Case Description: Measuring Zap time delay for channel change in secs

Expected Result: Excel sheet with delays for the required iterations.

Notes: Make sure that Ab18 and KA is unlocked. Identify the 3sat channel, update the channel number in the test case.

Steps:  1. set to live TV
        2. Change the channel and capture the time.
        3. Identify channel number (capture channel number for ocr/image comparison - non transparent)
        4. Capture time after channel change (timeout = 10secs)
        5. get delta
        6. store in excel file

OCR Engine - Google Vision
"""

# Importing the necessary driver files
from src.stb_lib.stb import *
from _datetime import datetime
import pytz

# Set german time
tz = pytz.timezone('Europe/Berlin')

tmpFile = "temp/kpiTimings.txt"

pytest.test_TC_NGTVTEST_31546_counter = 0


def executeTestCase():
    """
    This function validates all the required check conditions
    :return : return True if all the check conditions are validated successfully.
    """

    # Set irrcu time capture to True
    stb_rcu.stb.timeCapture = True

    # Exit to Live TV
    stb_rcu.send("pexit")
    time.sleep(4)

    # Tune to the previous channel wrt to 3sat.
    # Eg: In this case, 3sat is channel 12 and the previous channel number is 11
    # Tune to channel 11
    action.tuneChannel("11")
    stb_rcu.send("pexit")
    time.sleep(4)

    # Clear the contents from txt file
    truncate_file(tmpFile)

    # Change the channel and navigate to 3sat
    stb_rcu.send("pup")

    # Note down the command hit time as start time
    with open(tmpFile, 'r') as tmpContent:
        start_time = tmpContent.read().strip()
        print(f'\n\nStart time: {start_time}')
    start = datetime.strptime(start_time, '[%d-%m-%Y] %H:%M:%S.%f')

    # Keeping a timeout of 10secs
    timeout = 10
    startTime = time.time()

    # Wait for 10secs to check if channel is tuned to 3sat
    while not screen.isChannel12():
        if time.time() - startTime > timeout:
            print("Either the zap did not happen or there was some issue with the framework side...")
            return False, start_time, 'NA', 'NA', 'NA'

    # Capture the time after it is tuned to 3sat as end time
    now = datetime.now(tz)
    end_time = "[%02d-%02d-%04d] %02d:%02d:%02d.%03d" % (
        now.day, now.month, now.year, now.hour, now.minute, now.second, now.microsecond / 1000)
    end = datetime.strptime(end_time, '[%d-%m-%Y] %H:%M:%S.%f')

    print(f'End time: {end_time}')

    # Get the delta -> KPI zap time delay in secs [end_time - start_time]
    delay = end - start
    print(f'delay: {(str(delay.seconds + delay.microseconds / 1000000))}')
    return True, start_time, end_time, (delay.seconds + delay.microseconds / 1000000)


def test_NGTVTEST31546(extra):
    pytest.test_TC_NGTVTEST_31546_counter = pytest.test_TC_NGTVTEST_31546_counter + 1
    testoutputname = __name__ + "_" + str(pytest.test_TC_NGTVTEST_31546_counter)
    try:
        #Choosing OCR Engine (True - GV, False - Tesseract)
        action.useVision(True)

        assert tv.connect()
        tv.show()
        if connection_type == "telnet":
            assert stb.connect()
        if not os.path.exists("temp/"):
            os.mkdir("temp/")
        ret, start, end, delay = executeTestCase()
        assert ret
        print('Test execution completed')
    except:
        print("Test Case Failed")
        assert False
    finally:
        # Create a folder in report with the name sessionid if not created previously
        if not os.path.isdir("report/" + sessionid()):
            os.mkdir("report/" + sessionid())

        # Add data to the excel sheet
        add_row_to_excel(['Start time', 'End time', 'KPI(Zap Time Delay in secs)'], [start, end, delay],
                         'report/' + sessionid() + '/zaptime.xlsx', 'KPI')

        # Delete the temporary text file
        deleteFile(tmpFile)

        # Disable the time capture
        stb_rcu.stb.timeCapture = False

        tv.closescreen()
        tv.shutdown()


if __name__ == '__main__':
    test_NGTVTEST31546('')