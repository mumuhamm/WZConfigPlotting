#!/usr/bin/env python
import Utilities.plot_functions as plotter
import Utilities.helper_functions as helper
import argparse
import ROOT
import Utilities.config_object as config_object
import Utilities.UserInput as UserInput
import datetime
import shutil
import os
import errno
from Utilities.ConfigHistFactory import ConfigHistFactory 
from Utilities.prettytable import PrettyTable

states = ['eee', 'eem', 'emm', 'mmm']
log_info = ""
def getComLineArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output_file", type=str, default="",
                        help="Name of file to be created (type pdf/png etc.) " \
                        "Note: Leave unspecified for auto naming")
    parser.add_argument("-s", "--selection", type=str, required=True,
                        help="Specificy selection level to run over")
    parser.add_argument("-r", "--no_ratio", action="store_true",
                        help="Do not add ratio comparison")
    parser.add_argument("--legend_left", action="store_true",
                        help="Put legend left or right")
    parser.add_argument("--no_errors", action="store_true",
                        help="Include error bands")
    parser.add_argument("-b", "--branches", type=str, default="all",
                        help="List (separate by commas) of names of branches "
                        "in root and config file to plot") 
    parser.add_argument("-m", "--make_cut", type=str, default="",
                        help="Enter a valid root cut string to apply")
    parser.add_argument("-l", "--luminosity", type=float, default=1340,
                        help="Luminsoity in pb-1. Default 1340")
    parser.add_argument("--nostack", action='store_true',
                        help="Don't stack hists")
    parser.add_argument("--no_html", action='store_true',
                        help="Don't copy plot pdfs to website")
    parser.add_argument("--no_data", action='store_true',
                        help="Plot only Monte Carlo")
    parser.add_argument("--no_decorations", action='store_true',
                        help="Don't add CMS plot decorations")
    parser.add_argument("-c","--channel", type=str, default="",
                        choices=['eee', 'eem', 'emm', 'mmm'],
                        help="Select only one channel")
    parser.add_argument("-f", "--files_to_plot", type=str, required=False,
                        default="all", help="Files to make plots from, "
                        "separated by a comma (match name in file_info.json)")
    return parser.parse_args()
def getStacked(config_factory, selection, filelist, branch_name, luminosity, cut_string=""):
    hist_stack = ROOT.THStack("stack", "")
    hist_info = {}
    for plot_set in filelist:
        hist = helper.getConfigHist(config_factory, plot_set, selection, branch_name, 
                states, luminosity, cut_string)
        hist_stack.Add(hist)
        hist_info[plot_set] = {'raw_events' : hist.GetEntries(), 
                               'weighted_events' : hist.Integral()}
    writeMCLogInfo(hist_info, selection, branch_name, luminosity, cut_string)
    return hist_stack
def writeMCLogInfo(hist_info, selection, branch_name, luminosity, cut_string):
    mc_info = PrettyTable(["Plot Group", "Weighted Events", "Raw Events"])
    weighted_events = 0
    for plot_set, entry in hist_info.iteritems():
        mc_info.add_row([plot_set, round(entry["weighted_events"], 2), entry["raw_events"]])
        weighted_events += entry["weighted_events"]
    with open("temp.txt", "w") as mc_file:
        mc_file.write("Selection: %s" % selection)
        mc_file.write("\nAdditional cut: %s" % "None" if cut_string == "" else cut_string)
        mc_file.write("\nLuminosity: %0.2f fb^{-1}" % (luminosity/1000.))
        mc_file.write("\nPlotting branch: %s\n" % branch_name)
        mc_file.write(mc_info.get_string())
        mc_file.write("\nTotal sum of Monte Carlo: %0.2f" % round(weighted_events, 2))
def makePlot(config_factory, filelist, branch_name, cut_string, args):
    canvas = ROOT.TCanvas("canvas", "canvas", 800, 600) 
    hist_stack = getStacked(config_factory, args.selection, filelist, branch_name, args.luminosity, cut_string)
    hists = hist_stack.GetHists()
    hist_stack.Draw("nostack hist" if args.nostack else "hist")
    if not args.no_decorations:
        ROOT.CMSlumi(canvas, 0, 11, "%0.2f fb^{-1} (13 TeV)" % (args.luminosity/1000.))
    if not args.no_data:
        data_hist = helper.getConfigHist(config_factory, "data", args.selection, branch_name, states)
        data_hist.Draw("e1 same")
        with open("temp.txt", "a") as events_log_file:
            events_log_file.write("\nNumber of events in data: %i" % data_hist.Integral())
    else:
        data_hist = 0
    hist_stack.GetYaxis().SetTitleSize(hists[0].GetYaxis().GetTitleSize())    
    hist_stack.GetYaxis().SetTitleOffset(hists[0].GetYaxis().GetTitleOffset())    
    hist_stack.GetYaxis().SetTitle(
        hists[0].GetYaxis().GetTitle())
    hist_stack.GetHistogram().GetXaxis().SetTitle(
        hists[0].GetXaxis().GetTitle())
    hist_stack.GetHistogram().SetLabelSize(0.04)
    if hist_stack.GetMaximum() < hists[0].GetMaximum():
        hist_stack.SetMaximum(hists[0].GetMaximum())
        hist_stack.SetMinimum(hists[0].GetMinimum())
    else:
        new_max = 1.1*max(data_hist.GetMaximum(), hist_stack.GetMaximum()) \
                if not args.no_data else 1.1*hist_stack.GetMaximum()
        hist_stack.SetMaximum(new_max)
        hist_stack.SetMinimum(0.001)
    if not args.no_errors:
        histErrors = getHistErrors(hist_stack, args.nostack)
        for error_hist in histErrors:
            error_hist.Draw("E2 same")
    legend = getPrettyLegend(hist_stack, data_hist, args.legend_left)
    legend.Draw()
    
    output_file_name = args.output_file
    if not args.no_ratio:
        canvas = plotter.splitCanvas(canvas, "stack", ("#Sigma MC", "Data"))
    return canvas
def getHistErrors(hist_stack, separate):
    histErrors = []
    for hist in hist_stack.GetHists():
        error_hist = plotter.getHistErrors(hist)
        if separate:
            error_hist.SetFillColor(hist.GetFillColor())
            histErrors.append(error_hist)
        else:
            error_hist.SetFillColor(ROOT.kBlack)
            if len(histErrors) == 0:
                histErrors.append(error_hist)
            else:
                histErrors[0].Add(error_hist)
    return histErrors
def getPrettyLegend(hist_stack, data_hist, left):
    hists = hist_stack.GetHists()
    xcoords = [.15, .35] if left else [.75, .90]
    unique_entries = len(set([x.GetFillColor() for x in hists]))
    ycoords = [.9, .9 - 0.06*unique_entries]
    legend = ROOT.TLegend(xcoords[0], ycoords[0], xcoords[1], ycoords[1])
    legend.SetFillColor(0)
    if data_hist:
        legend.AddEntry(data_hist, data_hist.GetTitle(), "lp")
    hist_names = []
    for hist in reversed(hists):
        if hist.GetTitle() not in hist_names:
            legend.AddEntry(hist, hist.GetTitle(), "f")
        hist_names.append(hist.GetTitle())
    return legend
def makeDirectory(path):
    '''
    Make a directory, don't crash
    '''
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: 
            raise
def getPlotPaths(selection):
    if "hep.wisc.edu" in os.environ['HOSTNAME']:
        storage_area = "/nfs_scratch/kdlong"
        html_area = "/afs/hep.wisc.edu/home/kdlong/public_html"
    else:
        storage_area = "/data/kelong"
        html_area = "/afs/cern.ch/user/k/kelong/www"
    base_dir = "%s/WZAnalysisData/PlottingResults" % storage_area
    plot_path = "/".join([base_dir, selection, 
        '{:%Y-%m-%d}'.format(datetime.datetime.today()),
        '{:%Hh%M}'.format(datetime.datetime.today())])
    makeDirectory(plot_path)
    makeDirectory("/".join([plot_path, "logs"]))
    html_path = plot_path.replace(storage_area, html_area)
    return (plot_path, html_path)
def savePlot(canvas, plot_path, html_path, branch_name, args):
    if args.output_file != "":
        canvas.Print(args.output_file)
        return
    log_file = "/".join([plot_path, "logs", "%s_event_info.log" % branch_name])
    shutil.move("temp.txt", log_file) 
    canvas.Print("/".join([plot_path, branch_name + ".pdf"]))
    canvas.Print("/".join([plot_path, branch_name + ".root"]))
    if not args.no_html:
        makeDirectory(html_path)
        makeDirectory("/".join([html_path, "logs"]))
        canvas.Print("/".join([html_path, branch_name + ".pdf"]))
        shutil.copy(log_file, log_file.replace(plot_path, html_path))
def main():
    args = getComLineArgs()
    ROOT.gROOT.SetBatch(True)
    ROOT.dotrootImport('nsmith-/CMSPlotDecorations')
    ROOT.TProof.Open('workers=12')
    filelist = ["ttbar", "st", "ttv", "vvv", "ww", "zz", "zg", "dy",
            "wz"] if args.files_to_plot == "all" else \
            [x.strip() for x in args.files_to_plot.split(",")]
    path = "/cms/kdlong" if "hep.wisc.edu" in os.environ['HOSTNAME'] else \
        "/afs/cern.ch/user/k/kelong/work"
    config_factory = ConfigHistFactory(
        "%s/AnalysisDatasetManager" % path,
        "WZAnalysis", 
        args.selection
    )
    branches = config_factory.getListOfPlotObjects() if args.branches == "all" \
            else [x.strip() for x in args.branches.split(",")]
    cut_string = args.make_cut
    (plot_path, html_path) = getPlotPaths(args.selection)
    for branch in branches:
        canvas = makePlot(config_factory, filelist, branch, cut_string, args)
        savePlot(canvas, plot_path, html_path, branch, args)
        for primitive in ROOT.gPad.GetListOfPrimitives():
            primitive.Delete()
        for obj in ROOT.gDirectory.GetList():
            obj.Delete()
        del canvas
if __name__ == "__main__":
    main()
