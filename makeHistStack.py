#!/usr/bin/env python
import Utilities.plot_functions as plotter
import Utilities.helper_functions as helper
import argparse
import ROOT
import Utilities.config_object as config_object
#import Utilities.selection as selection
import Utilities.UserInput as UserInput
import datetime
import os
import errno
from Utilities.ConfigHistFactory import ConfigHistFactory 

states = ['eee', 'eem', 'emm', 'mmm']
#states = ["eee"]
def getComLineArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output_file", type=str, default="",
                        help="Name of file to be created (type pdf/png etc.) " \
                        "Note: Leave unspecified for auto naming")
    parser.add_argument("-t", "--selection", type=str, required=True,
                        help="Specificy selection level to run over")
    parser.add_argument("-r", "--make_ratio", action="store_true",
                        help="Add ratio comparison")
    parser.add_argument("--legend_left", action="store_true",
                        help="Put legend left or right")
    parser.add_argument("--errors", action="store_true",
                        help="Include error bands")
    parser.add_argument("-b", "--branches", type=str, default="all",
                        help="List (separate by commas) of names of branches "
                        "in root and config file to plot") 
    parser.add_argument("-m", "--make_cut", type=str, default="",
                        help="Enter a valid root cut string to apply")
    parser.add_argument("--nostack", action='store_true',
                        help="Don't stack hists")
    parser.add_argument("--copy_to_web", action='store_true',
                        help="Copy plot pdfs to website")
    parser.add_argument("-d","--default_cut", type=str, default="",
                        choices=['', 'WZ', 'zMass'],
                        help="Apply default cut string.")
    parser.add_argument("-c","--channel", type=str, default="",
                        choices=['eee', 'eem', 'emm', 'mmm',
                                 'eeee', 'eemm', 'mmmm'],
                        help="Select only one channel")
    parser.add_argument("-f", "--files_to_plot", type=str, required=False,
                        default="all", help="Files to make plots from, "
                        "separated by a comma (match name in file_info.json)")
    return parser.parse_args()
def getDataHist(selection, branch_name, cut_string):
    file_info = UserInput.readJson("/afs/cern.ch/user/k/kelong/work/AnalysisDatasetManager/FileInfo/data.json")
    filelist = file_info.keys()
    #filelist = ["data_DoubleEG_Run2015C_05Oct2015_25ns", "data_DoubleEG_Run2015D_05Oct2015_25ns"]
    hist_info = helper.getHistFactory(file_info, states, selection, filelist)
    hist_factory = ConfigHistFactory(
        "/afs/cern.ch/user/k/kelong/work/AnalysisDatasetManager",
        "WZAnalysis", 
        selection
    )
    print "Hist factor is %s " % hist_factory
    bin_info = hist_factory.getHistBinInfo(branch_name)
    hist = ROOT.TH1F("data", "Data", bin_info['nbins'], bin_info['xmin'], bin_info['xmax'])
    for name, entry in hist_info.iteritems():
        producer = entry["histProducer"]
        print "name is %s entry is %s at plot time" % (name, entry)
        for state in states:
            hist_factory.setProofAliases(state)
            draw_expr = hist_factory.getHistDrawExpr(branch_name, name, state)
            print draw_expr
            #producer.setLumi(-1) #In picobarns
            proof_name = "-".join([name, "WZAnalysis-%s#/%s/final/Ntuple" % (selection, state)])
            try:
                state_hist = producer.produce(draw_expr, cut_string, proof_name)
            except ValueError as error:
                print error
                continue
            hist.Add(state_hist)
    hist_factory.setHistAttributes(hist, branch_name, name)
    print "\n\nData hist has %i entries!!!\n" % hist.GetEntries()
    return hist

def getStacked(file_info, selection, branch_name, cut_string):
    hist_stack = ROOT.THStack("stack", "")
    hist_factory = ConfigHistFactory(
        "/afs/cern.ch/user/k/kelong/work/AnalysisDatasetManager",
        "WZAnalysis", 
        selection
    )
    for name, entry in file_info.iteritems():
        hist = 0
        producer = entry["histProducer"]
        print "name is %s entry is %s at plot time" % (name, entry)
        for state in states:
            hist_factory.setProofAliases(state)
            draw_expr = hist_factory.getHistDrawExpr(branch_name, name, state)
            print draw_expr
            producer.setLumi(1340) #In inverse picobarns
            proof_name = "-".join([name, "WZAnalysis-%s#/%s/final/Ntuple" % (selection, state)])
            try:
                state_hist = producer.produce(draw_expr, cut_string, proof_name)
            except ValueError as error:
                print error
                continue
            if not hist:
                hist = state_hist
            else:
                hist.Add(state_hist)
            hist_factory.setHistAttributes(hist, branch_name, name)
        hist_stack.Add(hist, "hist")
    return hist_stack
def makePlot(selection, hist_stack, branch_name, args):
    canvas = ROOT.TCanvas("canvas", "canvas", 800, 600) 
    hists = hist_stack.GetHists()
    hist_stack.Draw("nostack" if args.nostack else "")
    data_hist = getDataHist(selection, branch_name, "")#, cut_string)
    data_hist.Draw("e1 same") 
    if data_hist.GetMaximum() > hist_stack.GetMaximum():
        hist_stack.SetMaximum(data_hist.GetMaximum() + 5)
    else:
        hist_stack.SetMaximum(hist_stack.GetMaximum() + 5)
    hist_stack.GetYaxis().SetTitleSize(hists[0].GetYaxis().GetTitleSize())    
    hist_stack.GetYaxis().SetTitleOffset(hists[0].GetYaxis().GetTitleOffset())    
    hist_stack.GetYaxis().SetTitle( 
        hists[0].GetYaxis().GetTitle())
    hist_stack.GetXaxis().SetTitle(
        hists[0].GetXaxis().GetTitle())
    hist_stack.GetHistogram().SetLabelSize(0.04)
    hist_stack.SetMinimum(0.0001)
    print "Seg fault?"
    if args.errors:
        histErrors = getHistErrors(hist_stack, args.nostack)
        for error_hist in histErrors:
            error_hist.Draw("E2 same")
    legend = getPrettyLegend(hist_stack, data_hist, args.legend_left)
    legend.Draw()
    
    output_file_name = args.output_file
    ROOT.CMSlumi(canvas, 0, 11, "1.34 fb^{-1} (13 TeV)")
    if args.make_ratio:
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
    xcoords = [.15, .35] if left else [.70, .90]
    ycoords = [.9, .9 - 0.05*len(hists)]
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
    if args.copy_to_web:
        plot_path = plot_path.replace("/data/kelong", "/afs/cern.ch/user/k/kelong/www/")
        makeDirectory(plot_path)
        canvas.Print("/".join([plot_path, branch_name + ".pdf"]))
def main():
    args = getComLineArgs()
    base_dir = "/data/kelong/WZAnalysisData/PlottingResults"
    plot_path = "/".join([base_dir, args.selection, 
        '{:%Y-%m-%d}'.format(datetime.datetime.today()),
        '{:%Hh%M}'.format(datetime.datetime.today())])
    ROOT.gROOT.SetBatch(True)
    ROOT.dotrootImport('nsmith-/CMSPlotDecorations')
    ROOT.TProof.Open('workers=12')
    file_info = UserInput.readJson("/afs/cern.ch/user/k/kelong/work/AnalysisDatasetManager/FileInfo/montecarlo.json")
    filelist = ["tt", "ttz", "ttv", "zz4l", "zg-filt", "DYm50-filt", "wz3lnu-powheg"] if args.files_to_plot == "all" else \
            [x.strip() for x in args.files_to_plot.split(",")]
    print "File list is %s" % filelist
    hist_factory = helper.getHistFactory(file_info, states, args.selection, filelist)
    branches = UserInput.readJson("/afs/cern.ch/user/k/kelong/work/AnalysisDatasetManager/PlotObjects/WZAnalysis.json").keys() \
        if args.branches == "all" else [x.strip() for x in args.branches.split(",")]
    cut_string = helper.getCutString(args.default_cut, args.channel, args.make_cut)
    for branch in branches:
        print "Branch name is %s" % branch
        canvas = makePlot(args.selection, getStacked(hist_factory, args.selection, branch, cut_string), branch, args)
        savePlot(canvas, branch, plot_path, args)
if __name__ == "__main__":
    main()
