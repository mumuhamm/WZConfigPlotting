import ROOT
import WeightInfo
import abc
import array
import logging

class HistProducer(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, weight_info):
        self.weight_info = weight_info 
        self.lumi = 1
    
    def getHistScaleFactor(self):
        if self.weight_info.getCrossSection() == 1:
            return 1
        if self.weight_info.getSumOfWeights() <= 0:
            logging.warning("Found non-positive sum of weights! Hist will be scaled only by lumi")
            return self.lumi
        return self.weight_info.getCrossSection()*self.lumi/self.weight_info.getSumOfWeights()
                        
    def getCrossSection(self):
        return self.weight_info.getCrossSection()
    
    def getSumOfWeights(self):
        return self.weight_info.getSumOfWeights()

    def setLumi(self, lumi, units='pb-1'):
        print "Lumi is", lumi
        if units == 'pb-1':
            lumi *= 1000
        elif units != 'fb-1':
            raise ValueError("Invalid luminosity units! Options are 'pb-1' and 'fb-1'")
        self.lumi = lumi if lumi > 0 else 1

    def rebin(self, hist, binning):
        if not binning:
            return hist
        if type(binning) == int:
            hist.Rebin(binning)
        elif len(binning) == 1:
            hist.Rebin(int(binning[0]))
        else:
            bins = array.array('d', binning)
            hist = hist.Rebin(len(bins)-1, "", bins)
        return hist

    @abc.abstractmethod
    def produce(self, input): 
        return
