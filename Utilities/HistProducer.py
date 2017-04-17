import ROOT
import WeightInfo
import abc

class HistProducer(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, weight_info):
        self.weight_info = weight_info 
        self.lumi = 1
    
    def getHistScaleFactor(self):
        if self.weight_info.getCrossSection() == 1:
            return 1
        return self.weight_info.getCrossSection()*self.lumi/self.weight_info.getSumOfWeights() \
                        if self.weight_info.getSumOfWeights() > 0 else 0
    def getCrossSection(self):
        return self.weight_info.getCrossSection()
    
    def setLumi(self, lumi, units='pb-1'):
        if units == 'pb-1':
            lumi *= 1000
        elif units != 'fb-1':
            raise ValueError("Invalid luminosity units! Options are 'pb-1' and 'fb-1'")
        self.lumi = lumi if lumi > 0 else 1/self.getCrossSection()

    @abc.abstractmethod
    def produce(self, input): 
        return
