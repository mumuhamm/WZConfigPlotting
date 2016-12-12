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
    parser.add_argument("--ratio_text", default="",type=str, 
                        help="Ratio text")
    parser.add_argument("-t", "--extra_text", type=str, default="",
                        help="Extra text to be added below (above) the legend")
    parser.add_argument("--extra_text_above", action='store_true',
                        help="Position extra text above the legend")
    parser.add_argument("--folder_name", type=str, default="",
                        help="Folder name to save plots in (default is current time)")
    parser.add_argument("--simulation", action='store_true',
                        help="Write 'Simulation' in CMS style text")
    parser.add_argument("--no_overflow", action='store_true',
                        help="No overflow bin")
    parser.add_argument("--no_scalefactors", action='store_true',
                        help="No scale factors")
    parser.add_argument("--scaleymax", type=float, default=1.0,
                        help="Scale default ymax by this amount")
    parser.add_argument("--scaleymin", type=float, default=1.0,
                        help="Scale default ymin by this amount")
    parser.add_argument("--scalelegy", type=float, default=1.0,
                        help="Scale default legend entry size by this amount")
    parser.add_argument("--ratio_range", nargs=2, default=[0.5,1.5],
                        help="Ratio min ratio max (default 0.5 1.5)")
    parser.add_argument("--scalexmax", type=float, default=1.0,
                        help="Scale default xmax by this amount")
    return parser.parse_args()

log_info = ""

def writeMCLogInfo(hist_info, selection, branch_name, luminosity, cut_string):
    meta_info = '-'*80 + '\n' + \
        'Script called at %s\n' % datetime.datetime.now() + \
        'The command was: %s\n' % ' '.join(sys.argv) + \
        '-'*80 + '\n'
    mc_info = PrettyTable(["Plot Group", "Weighted Events", "Error", "Stat Error", "Raw Events"])
    weighted_events = 0
    total_background = 0
    background_err = 0
    total_err2 = 0
    sigbkgd = 0
    sigbkgd_err = 0
    signal = 0
    signal_err = 0
    likelihood = 0
    likelihood_err = 0
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
    likelihood = signal/math.sqrt(weighted_events)
    likelihood_err = likelihood*math.sqrt((signal_err/signal)**2 + \
        (0.5*total_err/weighted_events)**2)
    sigbkgd = signal/weighted_events
    sigbkgd_err = sigbkgd*math.sqrt(
        (signal_err/signal)**2 + (total_err/weighted_events)**2)
    with open("temp.txt", "w") as mc_file:
        mc_file.write(meta_info)
        mc_file.write("Selection: %s" % selection)
        mc_file.write("\nAdditional cut: %s" % ("None" if cut_string == "" else cut_string))
        mc_file.write("\nLuminosity: %0.2f fb^{-1}" % (luminosity))
        mc_file.write("\nPlotting branch: %s\n" % branch_name)
        mc_file.write(mc_info.get_string())
        mc_file.write("\nTotal sum of Monte Carlo: %0.2f +/- %0.2f" % (round(weighted_events, 2), 
            round(math.sqrt(sum([x["error"]*x["error"] for x in hist_info.values()])), 2)))
        mc_file.write("\nTotal sum of background Monte Carlo: %0.2f +/- %0.2f" % (round(total_background, 2), 
            round(math.sqrt(background_err), 2)))
        mc_file.write("\nRatio S/(S+B): %0.2f +/- %0.2f" % (round(sigbkgd, 2), 
            round(sigbkgd_err, 2)))
        mc_file.write("\nRatio S/sqrt(S+B): %0.2f +/- %0.2f" % (round(likelihood, 2), 
            round(likelihood_err, 2)))
def getStacked(config_factory, selection, filelist, branch_name, channels, addOverflow,
               cut_string="", luminosity=1, no_scalefacs=False):
    hist_stack = ROOT.THStack("stack", "")
    hist_info = {}
    for plot_set in filelist:
        print "plot set is %s " % plot_set 
        hist = helper.getConfigHist(config_factory, plot_set, selection,  
                branch_name, channels, addOverflow, cut_string, luminosity,
                no_scalefacs)
        raw_events = hist.GetEntries() - 1
        hist_stack.Add(hist)
        error = array.array('d', [0])
        weighted_events = hist.IntegralAndError(0, hist.GetNbinsX(), error)
        if not hist.GetSumw2(): hist.Sumw2()
        hist_info[plot_set] = {'raw_events' : raw_events, 
                               'weighted_events' : weighted_events,
                               'error' : 0 if int(raw_events) <= 0 else error[0],
                                'stat error' : weighted_events/math.sqrt(raw_events)}
    writeMCLogInfo(hist_info, selection, branch_name, luminosity, cut_string)
    scale_uncertainty = False
    if not scale_uncertainty:
        return hist_stack
    for plot_set in filelist:
        expression = "MaxIf$(LHEweights," \
            "Iteration$ < 6 || Iteration$ == 7 || Iteration$ == 9)" \
            "/LHEweights[0]"
        scale_hist_up = helper.getConfigHist(config_factory, plot_set, selection,  
                branch_name + "_scaleup", luminosity, expression + 
                ("*" + cut_string if cut_string != "" else ""))
        expression = "MinIf$(LHEweights," \
            "Iteration$ < 6 || Iteration$ == 7 || Iteration$ == 9)" \
            "/LHEweights[0]"
        scale_hist_down = helper.getConfigHist(config_factory, plot_set, selection,  
                branch_name + "_scaledown", luminosity, "(%s)" % expression + 
                ("*" + cut_string if cut_string != "" else ""))
        scale_hist_up.SetLineStyle(0)
        scale_hist_down.SetLineStyle(0)
        scale_hist_up.SetLineWidth(1)
        scale_hist_down.SetLineWidth(1)
        hist_stack.Add(scale_hist_up)
        hist_stack.Add(scale_hist_down)
    return hist_stack
def getListOfFiles(file_set, selection):
    if "WZxsec2016" in selection:
        filelist = ["vvv", "top"]
        filelist.append("vv" if "pow" not in file_set else "vv-powheg")
        if "preselection" not in selection:
            filelist.append("zg")
        drellyan = "dyjets"
        if "dynlo" in file_set:
            drellyan = "dy"
        elif "dylo" in file_set:
            drellyan = "dy-lo"
        filelist.append(drellyan)
        filelist.append("wz-powheg" if "pow" in file_set else "wz")
        if "vbs" in selection: 
            filelist.append("wlljj-ewk")
        return filelist
    return [x.strip() for x in file_set.split(",")]

def main():
    args = getComLineArgs()
    ROOT.gROOT.SetBatch(True)
    ROOT.TProof.Open('workers=12')
    filelist = getListOfFiles(args.files_to_plot, args.selection)
    path = "/cms/kdlong" if "hep.wisc.edu" in os.environ['HOSTNAME'] else \
        "/afs/cern.ch/user/k/kelong/work"
    print "MANAGER PATH IS ", path
    config_factory = ConfigHistFactory(
        "%s/AnalysisDatasetManager" % path,
        args.selection,
        args.object_restrict
    )
    branches = config_factory.getListOfPlotObjects() if args.branches == "all" \
            else [x.strip() for x in args.branches.split(",")]
    cut_string = args.make_cut
    (plot_path, html_path) = helper.getPlotPaths(args.selection, args.folder_name, True)
    for branch_name in branches:
        hist_stack = getStacked(config_factory, args.selection, filelist, 
                branch_name, args.channels, not args.no_overflow, cut_string,
                args.luminosity, args.no_scalefactors)
        if not args.no_data:
            data_hist = helper.getConfigHist(config_factory, "data", args.selection, 
                    branch_name, args.channels, not args.no_overflow, cut_string)
            with open("temp.txt", "a") as events_log_file:
                events_log_file.write("\nNumber of events in data: %i" % data_hist.Integral())
        else:
            data_hist = 0
        canvas = helper.makePlot(hist_stack, data_hist, branch_name, args)
        helper.savePlot(canvas, plot_path, html_path, branch_name, True, args)
        makeSimpleHtml.writeHTML(html_path, args.selection)
if __name__ == "__main__":
    main()
