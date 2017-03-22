#!/usr/bin/env python
import Utilities.plot_functions as plotter
import Utilities.helper_functions as helper
import argparse
import ROOT
import Utilities.config_object as config_object
import Utilities.UserInput as UserInput
import os
from Utilities.ConfigHistFactory import ConfigHistFactory 
from Utilities.prettytable import PrettyTable
import math
import sys
import array
import datetime
from Utilities.scripts import makeSimpleHtml
from IPython import embed

def getComLineArgs():
    parser = UserInput.getDefaultParser()
    parser.add_argument("-s", "--selection", type=str, required=True,
                        help="Specificy selection level to run over")
    parser.add_argument("-r", "--object_restrict", type=str, default="",
                        help="Use modified object file")
    parser.add_argument("-b", "--branches", type=str, default="all",
                        help="List (separate by commas) of names of branches "
                        "in root and config file to plot") 
    parser.add_argument("-m", "--make_cut", type=str, default="",
                        help="Enter a valid root cut string to apply")
    parser.add_argument("--blinding", type=list, default=["Mass < 400",
        "Pt < 200", "mjj < 500", "dEtajj < 2.5", "MTWZ < 400"],
        help="Blinding cuts to apply (only to that distribution)")
    return parser.parse_args()

log_info = ""

def writeMCLogInfo(hist_info, selection, branch_name, luminosity, cut_string):
    mc_info = PrettyTable(["Plot Group", "Weighted Events", "Error", "Stat Error", "Raw Events"])
    weighted_events = 0
    total_background = 0
    background_err = 0
    total_err2 = 0
    signal = 0
    signal_err = 0
    for plot_set, entry in hist_info.iteritems():
        mc_info.add_row([plot_set, round(entry["weighted_events"], 2), 
            round(entry["error"],2),
            round(entry["stat error"],2),
            entry["raw_events"]])
        weighted_events += entry["weighted_events"]
        total_err2 += entry["error"]**2
        if "wz" not in plot_set:
            total_background += entry["weighted_events"]
            background_err += entry["error"]*entry["error"]
        else:
            signal += entry["weighted_events"]
            signal_err += entry["error"]
    total_err = math.sqrt(total_err2)
    likelihood = 0 if weighted_events <= 0 else \
        signal/math.sqrt(weighted_events)
    likelihood_err = 0 if signal <= 0 or weighted_events <= 0 else \
        likelihood*math.sqrt((signal_err/signal)**2 + \
            (0.5*total_err/weighted_events)**2)
    sigbkgd = 0 if weighted_events <= 0 else signal/weighted_events
    sigbkgd_err = 0 if signal <= 0 or weighted_events <= 0 else \
        sigbkgd*math.sqrt((signal_err/signal)**2 + (total_err/weighted_events)**2)
    with open("temp.txt", "a") as mc_file:
        mc_file.write(mc_info.get_string())
        mc_file.write("\nTotal sum of Monte Carlo: %0.2f +/- %0.2f" % (round(weighted_events, 2), 
            round(math.sqrt(sum([x["error"]*x["error"] for x in hist_info.values()])), 2)))
        mc_file.write("\nTotal sum of background Monte Carlo: %0.2f +/- %0.2f" % (round(total_background, 2), 
            round(math.sqrt(background_err), 2)))
        mc_file.write("\nRatio S/(S+B): %0.2f +/- %0.2f" % (round(sigbkgd, 2), 
            round(sigbkgd_err, 2)))
        mc_file.write("\nRatio S/sqrt(S+B): %0.2f +/- %0.2f" % (round(likelihood, 2), 
            round(likelihood_err, 2)))
def getStacked(name, config_factory, selection, filelist, branch_name, channels, blinding, addOverflow,
               cut_string="", luminosity=1, no_scalefacs=False, uncertainties="none", hist_file=""):
    hist_stack = ROOT.THStack(name, "")
    ROOT.SetOwnership(hist_stack, False)
    hist_info = {}
    for plot_set in filelist:
        if hist_file == "":
            hist = helper.getConfigHist(config_factory, plot_set, selection,  
                    branch_name, channels, blinding, addOverflow, cut_string, luminosity,
                    no_scalefacs, uncertainties)
        else:
            hist = helper.getConfigHistFromFile(hist_file, config_factory, plot_set, 
                        selection, branch_name, channels, luminosity)
        raw_events = hist.GetEntries() - 1
        hist_stack.Add(hist)
        error = array.array('d', [0])
        weighted_events = hist.IntegralAndError(0, hist.GetNbinsX(), error)
        if not hist.GetSumw2(): hist.Sumw2()
        hist_info[plot_set] = {'raw_events' : raw_events, 
                               'weighted_events' : weighted_events,
                               'error' : 0 if int(raw_events) <= 0 else error[0],
                                'stat error' : 0 if raw_events <= 0 else \
                                    weighted_events/math.sqrt(raw_events) 
        }
    writeMCLogInfo(hist_info, selection, branch_name, luminosity, cut_string)
    return hist_stack
def main():
    args = getComLineArgs()
    ROOT.gROOT.SetBatch(True)
    if args.hist_file == "":
        ROOT.TProof.Open('workers=12')
    filelist = UserInput.getListOfFiles(args.files_to_plot, args.selection)
    path = "/cms/kdlong" if "hep.wisc.edu" in os.environ['HOSTNAME'] else \
        "/afs/cern.ch/user/k/kelong/work"
    config_factory = ConfigHistFactory(
        "%s/AnalysisDatasetManager" % path,
        args.selection,
        args.object_restrict
    )
    branches = config_factory.getListOfPlotObjects() if args.branches == "all" \
            else [x.strip() for x in args.branches.split(",")]
    cut_string = args.make_cut
    (plot_path, html_path) = helper.getPlotPaths(args.selection, args.folder_name, True)
    meta_info = '-'*80 + '\n' + \
        'Script called at %s\n' % datetime.datetime.now() + \
        'The command was: %s\n' % ' '.join(sys.argv) + \
        '-'*80 + '\n'
    for branch_name in branches:
        with open("temp.txt", "w") as mc_file:
            mc_file.write(meta_info)
            mc_file.write("Selection: %s" % args.selection)
            mc_file.write("\nAdditional cut: %s" % ("None" if cut_string == "" else cut_string))
            mc_file.write("\nLuminosity: %0.2f fb^{-1}" % (args.luminosity))
            mc_file.write("\nPlotting branch: %s\n" % branch_name)
        hist_stack = getStacked("stack", config_factory, args.selection, filelist, 
                branch_name, args.channels, args.blinding, not args.no_overflow, cut_string,
                args.luminosity, args.no_scalefactors, args.uncertainties, args.hist_file)
        if not args.no_data:
            if args.hist_file == "":
                data_hist = helper.getConfigHist(config_factory, "data_2016", args.selection, 
                        branch_name, args.channels, args.blinding, not args.no_overflow, cut_string)
            else:
                data_hist = helper.getConfigHistFromFile(args.hist_file, config_factory, "data_2016", 
                        args.selection, branch_name, args.channels)
            with open("temp.txt", "a") as events_log_file:
                events_log_file.write("\nNumber of events in data: %i\n" % data_hist.Integral())
        else:
            data_hist = 0
        signal_stack = 0
        if len(args.signal_files) > 0:
            signal_filelist = UserInput.getListOfFiles(args.signal_files, args.selection)
            signal_stack = getStacked("signal_stack", config_factory, args.selection, signal_filelist, 
                    branch_name, args.channels, args.blinding, not args.no_overflow, cut_string,
                    args.luminosity, args.no_scalefactors, args.uncertainties, args.hist_file)
        canvas = helper.makePlot(hist_stack, data_hist, branch_name, args, signal_stack)
        helper.savePlot(canvas, plot_path, html_path, branch_name, True, args)
        print "Done saving plot"
        makeSimpleHtml.writeHTML(html_path, args.selection)
        print "Done with main program"
if __name__ == "__main__":
    main()
