import plot_functions as plotter
import Utilities.WeightInfo as WeightInfo
import Utilities.WeightedHistProducer as WeightedHistProducer
import Utilities.selection as selection
import ROOT
import json
import Utilities.UserInput as UserInput
import os
import glob

def append_cut(cut_string, cut):
    return ''.join([cut_string, "" if cut_string is "" else " && ", cut])
def getCutString(default, channel, user_cut):
    cut_string = ""
    if default == "WZ":
        cut_string = append_cut(cut_string, selection.getFiducialCutString("WZ", True))
    elif default == "zMass":
        cut_string = append_cut(cut_string, selection.getZMassCutString("WZ", True))
    if channel != "":
        cut_string = append_cut(cut_string, 
                getattr(selection, "getChannel%sCutString" % channel.upper())())
    if user_cut != "":
        cut_string = append_cut(cut_string, user_cut)
    return cut_string
def getHist(root_file_name, config, hist_name, name_in_config):
    root_file = ROOT.TFile(root_file_name)                          
    hist = plotter.getHistFromFile(root_file, 
            "".join([hist_name, "_", name_in_config]), 
            name_in_config, "")                                                                  
    hist.Draw("hist")
    config.setAttributes(hist, name_in_config)
    return hist
def getHistFromFile(root_file_name, config, hist_name, name_in_config):
    root_file = ROOT.TFile(root_file_name)                          
    hist = plotter.getHistFromFile(root_file, 
            "".join([hist_name, "_", name_in_config]), 
            name_in_config, "")                                                                  
    hist.Draw("hist")
    config.setAttributes(hist, name_in_config)
    return hist
def getFileInfo(info_file):
    with open(info_file) as json_file:    
        file_info = json.load(json_file)
    return file_info
def buildChain(filelist, treename):
    chain = ROOT.TChain(treename)
    for filename in glob.glob(filelist):
        filename = filename.strip()
        if ".root" not in filename or not os.path.isfile(filename):
            raise IOError("%s is not a valid root file!" % filename)
        chain.Add(filename)
    return chain
def setAliases(tree, state, aliases_json):
    aliases = UserInput.readJson(aliases_json)
    for name, value in aliases["State"][state].iteritems():
        tree.SetAlias(name, value)
def getHistFactory(info_file, state, selection, filelist):
    all_files = getFileInfo(info_file)
    file_info = {}
    for name in filelist:
        print "Name is %s at initialization" % name
        if name not in all_files.keys():
            print "%s is not a valid file name (must match a definition in %s)" % (name, info_file)
            continue
        file_info[name] = dict(all_files[name])
        print file_info
        weight_info = WeightInfo.WeightInfo(file_info[name]['cross_section'], 1)
        ntuple = buildChain(file_info[name]["file_paths"][selection],
                "%s/final/Ntuple" % state)
        setAliases(ntuple, state, "Aliases/aliases.json")
        histProducer = WeightedHistProducer.WeightedHistProducer(ntuple, weight_info, "GenWeight/abs(GenWeight)")  
        file_info[name]["histProducer"] = histProducer
    return file_info
