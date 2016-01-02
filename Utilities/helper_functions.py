import ROOT
import plot_functions as plotter
import Utilities.WeightInfo as WeightInfo
import Utilities.WeightedHistProducer as WeightedHistProducer
from Utilities.ConfigHistFactory import ConfigHistFactory 
from collections import OrderedDict
import os
import glob
import logging

def buildChain(filelist, treename):
    chain = ROOT.TChain(treename)
    for filename in glob.glob(filelist):
        filename = filename.strip()
        if ".root" not in filename or not os.path.isfile(filename):
            raise IOError("%s is not a valid root file!" % filename)
        chain.Add(filename)
    return chain
def getHistFactory(config_factory, selection, filelist, luminosity=1, cut_string=""):
    mc_info = config_factory.getMonteCarloInfo()
    all_files = config_factory.getFileInfo()
    hist_factory = OrderedDict() 
    for name in filelist:
        if name not in all_files.keys():
            logging.warning("%s is not a valid file name (must match a definition in FileInfo/%s.json)" % \
                (name, selection))
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
            histProducer.setCutString(cut_string)
        else:
            histProducer = WeightedHistProducer.WeightedHistProducer(
                    WeightInfo.WeightInfo(1, 1,), "")  
        hist_factory[name].update({"histProducer" : histProducer})
    return hist_factory
def getConfigHist(config_factory, plot_group, selection, branch_name, 
    states, luminosity=1, cut_string=""):
    try:
        filelist = config_factory.getPlotGroupMembers(plot_group)
    except ValueError as e:
        logging.warning(e.message)
        logging.warning("Treating %s as file name" % plot_group)
        filelist = [plot_group]
    hist_info = getHistFactory(config_factory, selection, filelist, luminosity, cut_string)
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
            logging.debug("Draw expression was %s" % draw_expr)
            proof_name = "-".join([name, "WZAnalysis-%s#/%s/final/Ntuple" % (selection, state)])
            try:
                state_hist = producer.produce(draw_expr, proof_name)
                log_info += "\nNumber of events: %f" % state_hist.Integral()
                hist.Add(state_hist)
            except ValueError as error:
                logging.warning(error)
                log_info += "\nNumber of events: 0.0" 
        log_info += "total number of events: %f" % hist.Integral()
        config_factory.setHistAttributes(hist, branch_name, plot_group)
    logging.debug("Hist has %i entries" % hist.GetEntries())
    with open("testy.txt", "w") as log_file:
        log_file.write(log_info)
    return hist
