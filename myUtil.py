#coding: UTF-8

import time
import subprocess

def timeIsUp(timeoutEvent):
    timeoutEvent.set()

def seconds2Str(seconds):
    structedTimeList = time.localtime(seconds)
    timeString = time.strftime("%H:%M:%S",structedTimeList)
    return timeString

def checkDevice():

    try:
        Output = subprocess.check_output('adb shell /data/local/tmp/busybox', shell=True)
    except subprocess.CalledProcessError:
        raise RuntimeError("Falha ao utilizar o ADB")

def dumpDeviceLog(logFileName):
    subprocess.call("adb logcat -v threadtime -d > {0}_LogCat.log".format(logFileName), shell=True)
    subprocess.call("adb logcat -c", shell=True)


class ProcessNotFoundException(Exception):
    pass

class FoundNewProcessException(Exception):
    pass

class ProcessChangedException(Exception):
    pass
