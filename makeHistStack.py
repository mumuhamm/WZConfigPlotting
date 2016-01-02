#!/usr/bin/env python
import Utilities.plot_functions as plotter
import Utilities.helper_functions as helper
import argparse
import ROOT
import Utilities.config_object as config_object
import Utilities.UserInput as UserInput
import datetime
import os
import errno
from Utilities.ConfigHistFactory import ConfigHistFactory 

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
    for plot_set in filelist:
        hist = helper.getConfigHist(config_factory, plot_set, selection, branch_name, 
                states, luminosity, cut_string)
        hist_stack.Add(hist)
    return hist_stack
def makePlot(config_factory, filelist, branch_name, cut_string, args):
    canvas = ROOT.TCanvas("canvas", "canvas", 800, 600) 
    hist_stack = getStacked(config_factory, args.selection, filelist, branch_name, 1340, cut_string)
    hists = hist_stack.GetHists()
    hist_stack.Draw("nostack hist" if args.nostack else "hist")
    if not args.no_decorations:
        ROOT.CMSlumi(canvas, 0, 11, "%0.2f fb^{-1} (13 TeV)" % luminosity/1000.)
    if not args.no_data:
        data_hist = helper.getConfigHist(config_factory, "data", args.selection, branch_name, states)
        data_hist.Draw("e1 same")
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
                if not args.no_data else 1.1*hist.GetMaximum()
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
def savePlot(canvas, branch_name, plot_path, args):
    if args.output_file != "":
        canvas.Print(args.output_file)
        return
    makeDirectory(plot_path)
    canvas.Print("/".join([plot_path, branch_name + ".pdf"]))
    canvas.Print("/".join([plot_path, branch_name + ".root"]))
    if not args.no_html:
        plot_path = plot_path.replace("/nfs_scratch/kdlong", 
            "/afs/hep.wisc.edu/home/kdlong/public_html")
        makeDirectory(plot_path)
        canvas.Print("/".join([plot_path, branch_name + ".pdf"]))
def main():
    args = getComLineArgs()
    base_dir = "/nfs_scratch/kdlong/WZAnalysisData/PlottingResults"
    plot_path = "/".join([base_dir, args.selection, 
        '{:%Y-%m-%d}'.format(datetime.datetime.today()),
        '{:%Hh%M}'.format(datetime.datetime.today())])
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
    branches = UserInput.readJson(object_file).keys() if args.branches == "all" \
            else [x.strip() for x in args.branches.split(",")]
    cut_string = args.make_cut
    for branch in branches:
        print "Branch name is %s" % branch
        canvas = makePlot(config_factory, filelist, branch, cut_string, args)
        print canvas
        savePlot(canvas, branch, plot_path, args)
    global log_info
    with open("test.txt", "w") as log_file:
        log_file.write(log_info)
if __name__ == "__main__":
    main()
