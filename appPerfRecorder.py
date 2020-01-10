#!/bin/env python
#encoding: UTF-8

from time import sleep
from adbpy.adb import Adb
from collections import defaultdict
import threading
import csv
import argparse
import myUtil

ADB_TIMEOUT = 5
BUSYBOX_PATH = '/data/local/tmp/busybox'

class AppUnderTest(object):
    def __init__(self,strPackageName):
        self.DEFAULT_ADDRESS = ("localhost",5037)
        self.adb = Adb(self.DEFAULT_ADDRESS)
        self.strPackageName = strPackageName
        self.strUID = self.__get_UID()
        self.listProcessInfo = self.__init_processInfo()

    def __sizeof__(self):
        return super(AppUnderTest, self).__sizeof__()
    
    def __get_UID(self):
        strTemp = self.adb.shell('dumpsys package "{0}"|grep userId'.format(self.strPackageName),timeout=ADB_TIMEOUT)
        strUID = strTemp[11:16].strip()
        return strUID

    def __init_processInfo(self):
        strTemp = self.adb.shell("{0} top -bn 1|grep '{1}'".format(BUSYBOX_PATH, self.strPackageName),timeout=ADB_TIMEOUT)
        listTemp = [elem.split() for elem in strTemp.splitlines() if elem.find('grep') == -1]
        if len(listTemp)!=0:
            listProcessInfo = [[elem[0],elem[-1]] for elem in listTemp]
            listProcessInfo.sort(key=lambda x:x[1])
        else:
            raise SystemExit("Processo não encontrado")
        
        print '[Debug]:ProcessInfo\n', listProcessInfo
        return listProcessInfo

    def __update_processInfo(self,listOutputOfTop):
        if len(listOutputOfTop)!=0:
            listProcessInfo = [[elem[0],elem[-1]] for elem in listOutputOfTop]
            listProcessInfo.sort(key=lambda x:x[1])
        else:
            raise SystemExit("Processo não encontrado")
        if cmp(listProcessInfo,self.listProcessInfo) != 0:
            if len(listProcessInfo) > len(self.listProcessInfo):
                tempList = [elem for elem in listProcessInfo if elem not in self.listProcessInfo]
                self.listProcessInfo.extend(tempList)
                raise myUtil.FoundNewProcessException
            elif len(listProcessInfo) == len(self.listProcessInfo):
                tempList = [elem for elem in listProcessInfo if elem not in self.listProcessInfo]
                for elem in tempList:
                    flag = 'Not_Found'
                    for i,process in enumerate(self.listProcessInfo):
                        if elem[1] in process:
                            process[0] = elem[0]
                            self.listProcessInfo[i] = process
                            flag = 'Found'
                    if flag == 'Not_Found':
                        self.listProcessInfo.append(elem)
                raise myUtil.ProcessChangedException
            else:
                pass


    def get_networkTraffic(self):

        flag_net = self.adb.shell('cat /proc/net/xt_qtaguid/stats',timeout=ADB_TIMEOUT)

        if "No such file or directory" not in flag_net:
            list_rx = []
            list_tx = []
            str_uid_net_stats = self.adb.shell('cat /proc/net/xt_qtaguid/stats|grep {0}'.format(self.strUID),timeout=ADB_TIMEOUT)

            try:
                for item in str_uid_net_stats.splitlines():
                    rx_bytes = item.split()[5]
                    tx_bytes = item.split()[7]
                    list_rx.append(int(rx_bytes))
                    list_tx.append(int(tx_bytes))
                # print list_rx, sum(list_rx)
                floatTotalNetTraffic = (sum(list_rx) + sum(list_tx))/1024.0/1024.0
                floatTotalNetTraffic = round(floatTotalNetTraffic,4)
                return floatTotalNetTraffic
            except:
                print "[ERROR]: Falha ao ler uso da rede, return 0.0"
                return 0.0

        else:
            strTotalTxBytes = self.adb.shell('cat /proc/uid_stat/{0}/tcp_snd'.format(self.strUID),timeout=ADB_TIMEOUT)
            strTotalRxBytes = self.adb.shell('cat /proc/uid_stat/{0}/tcp_rcv'.format(self.strUID),timeout=ADB_TIMEOUT)
            try:
                floatTotalTraffic = (int(strTotalTxBytes) + int(strTotalRxBytes))/1024.0/1024.0
                floatTotalTraffic = round(floatTotalTraffic,4)
                return floatTotalTraffic
            except:
                return 0.0

    def get_procCPULoad(self):
        listProcCPULoad = []
        strTemp = self.adb.shell("{0} top -bn 1|grep {1}".format(BUSYBOX_PATH, self.strPackageName),timeout=ADB_TIMEOUT)
        listTemp = [elem.split() for elem in strTemp.splitlines() if elem.find('grep') == -1]
        self.__update_processInfo(listTemp)
        for elemOfProcessInfo in self.listProcessInfo:
            flag_Found = False
            for elem in listTemp:
                if (elem != []) and (elem[0] == elemOfProcessInfo[0]):
                    if elem[4] == '<':
                        strSubProcCPULoad = elem[7+1]
                        listProcCPULoad.append(float(strSubProcCPULoad))
                    else:
                        value = elem[7]
                        strSubProcCPULoad = value.replace('%', '')
                        listProcCPULoad.append(float(strSubProcCPULoad))
                    flag_Found = True 
                    break
            if flag_Found == False:
                listProcCPULoad.append(0.0) 
        return listProcCPULoad

    def get_procMemUsage(self):
        listProcMemUsage = []
        for elem in self.listProcessInfo:
            strTemp = self.adb.shell("dumpsys meminfo {0}|grep 'TOTAL'".format(elem[0]),timeout=ADB_TIMEOUT)
            try:
                strSubProcMemUsage = strTemp.split()[1].encode('UTF-8')
            except IndexError:
                currentOutput = self.adb.shell("dumpsys meminfo {0}".format(elem[0]),timeout=ADB_TIMEOUT)
                if currentOutput.find('No process found')!=-1:
                    strSubProcMemUsage = 0.0
                else:
                    raise
            listProcMemUsage.append(round(int(strSubProcMemUsage)/1024.0,4))
        return listProcMemUsage

    def collect_allPerfInfo(self):
        strCurrentTime = myUtil.seconds2Str(int(self.adb.shell(r"date +%s",timeout=ADB_TIMEOUT).replace("\r\n","").encode('UTF-8')))
        strCurrentTraffic = str(self.get_networkTraffic()).replace('.', ',')
        listEachProcCPULoad = self.get_procCPULoad()
        listEachProcMemUsage = self.get_procMemUsage()
        floatTotalCPULoad = str(round(sum(listEachProcCPULoad),4)).replace('.', ',')
        floatTotalMemUsage = str(round(sum(listEachProcMemUsage),4)).replace('.', ',')
        listAllPerfInfo = [strCurrentTime,strCurrentTraffic,floatTotalCPULoad,floatTotalMemUsage]
        for x in xrange(len(listEachProcCPULoad)):
            listAllPerfInfo.append(str(listEachProcCPULoad[x]).replace('.', ','))
            listAllPerfInfo.append(str(listEachProcMemUsage[x]).replace('.', ','))
        listForPrinting = [elem for elem in listAllPerfInfo]
        listForPrinting[0] = listAllPerfInfo[0]
        print listForPrinting
        return listAllPerfInfo

class CSVRecorder(object):
    def __init__(self,listProcessInfo,logFileName):
        listProcName = self.__getProcessName(listProcessInfo)
        print listProcName
        self.logFileName = logFileName
        listColumnHeader = ['Tempo','TragefoRede(MB)','CPU(%)','Memoria(MB)']
        for elem in listProcName:
            listColumnHeader.append('CPU(%)_' + elem)
            listColumnHeader.append('Memoria(MB)_' + elem)

        with open(logFileName,'wb') as csvFile:
            csvFile.write('\xEF\xBB\xBF')
            writer = csv.writer(csvFile)
            writer.writerow(listColumnHeader)


    def __getProcessName(self,listProcessInfo):
        listProcName = []
        for elem in listProcessInfo:
            listProcName.append(elem[1])

        lastList=listProcName[-1]
        for i in range(len(listProcName)-2,-1,-1):
            if listProcName[i]==lastList:
                listProcName[i]=str(listProcName[i]) + "_1"
            else:
                lastList=listProcName[i]
        return listProcName

    def saveCurrentData(self,listAllPerfInfo,testStep = None):
        with open(self.logFileName,'ab') as csvFile:
            writer = csv.writer(csvFile)
            if testStep == None:
                writer.writerow(listAllPerfInfo)
            else:
                listAllPerfInfo[0] = ''.join([listAllPerfInfo[0],testStep])
                writer.writerow(listAllPerfInfo)            

def main():
    toolHelpDescription = ("Grava indicadores de performance e exporta para CSV:\n"
        "\tTotalNetworkTraffic: Tx+Rx trafego do app.(KB)\n"
        "\tCPULoad: Carga do CPU(%).\n"
        "\tMemUsage: Uso de memória(KB).")
    parser = argparse.ArgumentParser(description = toolHelpDescription, formatter_class = argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-p', metavar = 'appPackageName', required = True, dest = 'strPackageName', action = 'store', help = '')
    parser.add_argument('-f', metavar = 'LogCSVFileName', required = True, dest = 'strLogFileName', action = 'store', help = '')
    parser.add_argument('-t', metavar = 'Execution time', required = False, dest = 'intTime', action = 'store', default= 'NULL' ,help = '')
    args = parser.parse_args()

    try:
        myUtil.checkDevice()
    except Exception as e:
        print e
        return

    app = AppUnderTest(args.strPackageName)
    dataRecorder = CSVRecorder(app.listProcessInfo,args.strLogFileName)
    errorCounts = 0
    SamplingInterval = 0.5
    timeoutEvent = threading.Event()
    if args.intTime != 'NULL':
        t = threading.Timer(int(args.intTime),myUtil.timeIsUp,args=(timeoutEvent,))
        t.start()

    while True:
        if timeoutEvent.isSet() != True:
            try:
                currentPerfInfo = app.collect_allPerfInfo()
                dataRecorder.saveCurrentData(currentPerfInfo)

                sleep(SamplingInterval)    
            except KeyboardInterrupt:
                if args.intTime != 'NULL' and timeoutEvent.isSet() != True:
                    t.cancel()
                myUtil.dumpDeviceLog(args.strLogFileName.rpartition('.')[0])
                raise SystemExit('Log salvo em .\\{0}'.format(args.strLogFileName))
            except myUtil.FoundNewProcessException:
                print "Encontrado novo subprocesso"
            except Exception as e:
                errorCounts+=1
                if errorCounts <= 5:
                    print "Ocorreu um erro, tentando novamente."
                    sleep(1)            
                else:
                    if args.intTime != 'NULL' and timeoutEvent.isSet() != True:
                        t.cancel()
                    myUtil.dumpDeviceLog(args.strLogFileName.rpartition('.')[0])
                    raise SystemExit("\nErro na execução:\n{0}".format(e))
            else:
                errorCounts = 0
        else:
            myUtil.dumpDeviceLog(args.strLogFileName.rpartition('.')[0])
            return

if __name__ == '__main__':
    main()
