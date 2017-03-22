import ROOT
from Utilities.ConfigHistFactory import ConfigHistFactory 
import Utilities.helper_functions as helper
from collections import OrderedDict
import array

class CutFlowEntry(object):
    def __init__(self, name, dataset_manager, analysis):
        self.name = name
        self.analysis = analysis 
        self.config_factory = ConfigHistFactory(
            dataset_manager,
            self.analysis,
        )
        self.states = "eee,eem,emm,mmm"
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
    def getValue(self, plot_group, unc, hist_file, scale_facs=False):
        if hist_file == "":
            hist = helper.getConfigHist(self.config_factory, 
                    plot_group, 
                    self.analysis,
                    "l1Pt", 
                    self.states, 
                    luminosity=self.luminosity, 
                    cut_string=self.additional_cut,
                    no_scalefacs=not scale_facs,
                    uncertainties=unc,
            )
        else:
            hist = helper.getConfigHistFromFile(hist_file,
                    self.config_factory, 
                    plot_group, 
                    self.analysis,
                    "ZMass", 
                    self.states, 
                    luminosity=self.luminosity, 
                    uncertainties=unc,
            )
        error = array.array('d', [0])
        events = hist.IntegralAndError(0, hist.GetNbinsX(), error)
        hist.Delete()
        return (events, error[0])
class ManualCutFlowEntry(object):
    def setEntryValues(self, entry_name, entry_value):
        self.entries[entry_name] = entry_value
    def getValue(self, entry_name, unc):
        if entry_name not in self.entries.keys():
            return 0
        else:
            return entries[entry_name]
class CutFlowHistMaker(object):
    def __init__(self, name, dataset_manager, analysis):
        self.name = name
        self.entries = []
        self.states = []
        self.luminosity = 0
        self.config_factory = ConfigHistFactory(dataset_manager,
            analysis,
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
    def getHist(self, plot_group, unc, hist_file, scale_facs=False):
        nbins = len(self.entries)
        hist = ROOT.TH1D(plot_group, plot_group, nbins, 0, nbins)
        for i, entry in enumerate(self.entries):
            value, error = entry.getValue(plot_group, unc, hist_file, scale_facs)
            hist.SetBinContent(i+1, value)
            hist.SetBinError(i+1, error)
            hist.GetXaxis().SetBinLabel(i+1, entry.getName())
        self.config_factory.setHistAttributes(hist, self.name, plot_group)
        return hist
