#coding: utf-8

import csv
import os
import myUtil

class LogFileReader(object):

    def __init__(self, csvFilePath):
        self.csvFilePath = csvFilePath
        self.csvFileName = os.path.basename(self.csvFilePath).rpartition('.')[0]
        self.csvDataSet = self.__getCSVDataSet(self.csvFilePath)
        self.timeSeries = self.__getTimeSeries()
        self.headerLine = self.__getHeaderLine()

    def __getCSVDataSet(self,csvFilePath):

        with open(self.csvFilePath,'rb') as f:
            f_csv = csv.DictReader(f)
            csvDataSet = [dictRow for dictRow in f_csv]
        return csvDataSet

    def __getColumnData(self,columnName):

        listTemp = []
        for row in self.csvDataSet:
            listTemp.append(row[columnName])
        return listTemp

    def __getHeaderLine(self):

        with open(self.csvFilePath,'rb') as f:
            f_csv = csv.reader(f)
            headerLine = next(f_csv)
            headerLine[0] = headerLine[0].replace('\xef\xbb\xbf','')
            return headerLine

    def __getTimeSeries(self):

        listTemp = self.__getColumnData('\xef\xbb\xbf'+'Time')
        timeSeries = [int(elem) for elem in listTemp]
        return timeSeries

    def getValueSeries(self,columnName):

        valueSeries = self.__getColumnData(columnName)
        valueSeries = [float(eachValue) for eachValue in valueSeries]
        return valueSeries

    def getLinePlotData(self,columnName):

        valueSeries = self.getValueSeries(columnName)
        linePlotData = [zip(self.timeSeries,valueSeries),]
        return linePlotData

    def getValueMax(self,columnName):

        valueMax = max(self.getValueSeries(columnName))
        return round(valueMax,3)
    
    def getValueMin(self,columnName):

        valueMin = min(self.getValueSeries(columnName))
        return round(valueMin,3)

    def getValueAvg(self,columnName):

        sumOfValueSeries = sum(self.getValueSeries(columnName))
        valueAvg = float(sumOfValueSeries)/len(self.getValueSeries(columnName))
        return round(valueAvg,3)

    def getValueDelta(self,columnName):

        valueSeries = self.getValueSeries(columnName)
        return round((valueSeries[-1] - valueSeries[0]),3)
