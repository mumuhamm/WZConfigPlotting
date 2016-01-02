import plot_functions as plotter
import Utilities.WeightInfo as WeightInfo
import Utilities.WeightedHistProducer as WeightedHistProducer
import Utilities.selection as selection
from Utilities.ConfigHistFactory import ConfigHistFactory 
import ROOT
import json
import Utilities.UserInput as UserInput
from collections import OrderedDict
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
def getHistFactory(config_factory, selection, filelist, luminosity):
    mc_info = config_factory.getMonteCarloInfo()
    all_files = config_factory.getFileInfo()
    hist_factory = OrderedDict() 
    for name in filelist:
        if name not in all_files.keys():
            print "%s is not a valid file name (must match a definition in FileInfo/%s.json)" % \
                (name, selection)
            continue
        hist_factory[name] = dict(all_files[name])
        if "data" not in name:
            metaTree = buildChain(hist_factory[name]["file_path"],
                    "eee/metaInfo")
            kfac = 1. if 'kfactor' not in mc_info[name].keys() else mc_info[name]['kfactor']
            weight_info = WeightInfo.WeightInfoProducer(metaTree, 
                    mc_info[name]['cross_section']*kfac,
                    "summedWeights").produce()
            histProducer = WeightedHistProducer.WeightedHistProducer(weight_info, "GenWeight")  
            histProducer.setLumi(luminosity)
        else:
            histProducer = WeightedHistProducer.WeightedHistProducer(
                    WeightInfo.WeightInfo(1, 1,), "")  
        hist_factory[name].update({"histProducer" : histProducer})
    return hist_factory
def getConfigHist(config_factory, plot_group, selection, branch_name, states, luminosity=1, cut_string=""):
    try:
        print "Plot Group is %s" % plot_group
        filelist = config_factory.getPlotGroupMembers(plot_group)
    except ValueError as e:
        print e.message
        filelist = [plot_group]
    hist_info = getHistFactory(config_factory, selection, filelist, luminosity)
    bin_info = config_factory.getHistBinInfo(branch_name)
    hist = ROOT.TH1F(plot_group, plot_group, bin_info['nbins'], bin_info['xmin'], bin_info['xmax'])
    log_info = ""
    for name, entry in hist_info.iteritems():
        producer = entry["histProducer"]
        log_info += "\n" + "-"*70 +"\nName is %s entry is %s" % (name, entry)
        for state in states:
            log_info += "\nFor state %s" % state
            config_factory.setProofAliases(state)
            draw_expr = config_factory.getHistDrawExpr(branch_name, name, state)
            print draw_expr
            proof_name = "-".join([name, "WZAnalysis-%s#/%s/final/Ntuple" % (selection, state)])
            try:
                state_hist = producer.produce(draw_expr, cut_string, proof_name)
                log_info += "\nNumber of events: %f" % state_hist.Integral()
                hist.Add(state_hist)
            except ValueError as error:
                print error
                log_info += "\nNumber of events: 0.0" 
        log_info += "total number of events: %f" % hist.Integral()
        config_factory.setHistAttributes(hist, branch_name, plot_group)
    print "\n\nHist has %i entries!!!\n" % hist.GetEntries()
    print log_info
    with open("testy.txt", "a+") as log_file:
        log_file.write(log_info)
    return hist
