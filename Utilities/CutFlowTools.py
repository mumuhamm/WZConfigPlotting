import ROOT
from Utilities.ConfigHistFactory import ConfigHistFactory 
import Utilities.helper_functions as helper
from collections import OrderedDict

class CutFlowEntry(object):
    def __init__(self, name, data_tier, dataset_manager, analysis):
        self.name = name
        self.data_tier = data_tier
        self.config_factory = ConfigHistFactory(
            dataset_manager,
            analysis, 
            data_tier
        )
        self.states = []
        self.luminosity = 1.
        self.additional_cut = ""
    def addAdditionalCut(self, cut_string):
        self.additional_cut = cut_string
    def setLuminosity(self, lumi):
        self.luminosity = lumi
    def setStates(self, states):
        self.states = states
    def getName(self):
        return self.name
    def getValue(self, plot_group):
        hist = helper.getConfigHist(self.config_factory, 
                plot_group, 
                self.data_tier, 
                "l1Pt", 
                self.states, 
                self.luminosity, 
                self.additional_cut
        )
        return hist.Integral()
class ManualCutFlowEntry(object):
    def setEntryValues(self, entry_name, entry_value):
        self.entries[entry_name] = entry_value
    def getValue(self, entry_name):
        if entry_name not in self.entries.keys():
            return 0
        else:
            return entries[entry_name]
class CutFlowHistMaker(object):
    def __init__(self, dataset_manager, analysis):
        self.entries = []
        self.states = []
        self.luminosity = 0
        self.config_factory = ConfigHistFactory(dataset_manager,
            analysis,
            "CutFlow"
        )
    def setLuminosity(self, lumi):
        self.luminosity = lumi
        for entry in self.entries:
            entry.setLuminosity(lumi)
    def setStates(self, states):
        self.states = states
        for entry in self.entries:
            entry.setStates(states)
    def addEntry(self, entry):
        if self.luminosity != 0:
            entry.setLuminosity(self.luminosity)
        if self.states != []:
            entry.setStates(self.states)
        self.entries.append(entry)
    def setLogFile(log_file):
        self.log_file = log_file
    def getHist(self, plot_group):
        nbins = len(self.entries)
        hist = ROOT.TH1F(plot_group, plot_group, nbins, 0, nbins)
        for i, entry in enumerate(self.entries):
            hist.SetBinContent(i+1, entry.getValue(plot_group))
            #hist.GetXaxis().SetBinLabel(i+1, entry.getName())
            #hist.GetXaxis().SetLabelSize(0.08)
        self.config_factory.setHistAttributes(hist, "CutFlow", plot_group)
        return hist
