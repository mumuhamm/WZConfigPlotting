#!/usr/bin/env python
import Utilities.plot_functions as plotter
import Utilities.helper_functions as helper
import argparse
import ROOT
import Utilities.config_object as config_object
#import Utilities.selection as selection
import Utilities.UserInput as UserInput
from Utilities.ConfigHistFactory import ConfigHistFactory 

states = ['eee', 'eem', 'emm', 'mmm']
#states = ["eee"]
def getComLineArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output_file", type=str, required=True,
                        help="Name of file to be created (type pdf/png etc.) " \
                        "Note: 'NAME' will be replaced by branch name")
    parser.add_argument("-s", "--scale", type=str, default="xsec",
                        help="Method for scalling hists")
    parser.add_argument("-t", "--selection", type=str, required=True,
                        help="Specificy selection level to run over")
    parser.add_argument("-r", "--make_ratio", action="store_true",
                        help="Add ratio comparison")
    parser.add_argument("--legend_left", action="store_true",
                        help="Put legend left or right")
    parser.add_argument("--errors", action="store_true",
                        help="Don't plot error bands")
    parser.add_argument("-b", "--branches", type=str, required=True,
                        help="List (separate by commas) of names of branches "
                        "in root and config file to plot") 
    parser.add_argument("-n", "--max_entries", type=int, default=-1,
                        help="Draw only first n entries of hist "
                        "(useful for huge root files)")
    parser.add_argument("-m", "--make_cut", type=str, default="",
                        help="Enter a valid root cut string to apply")
    parser.add_argument("--nostack", action='store_true',
                        help="Don't stack hists")
    parser.add_argument("-d","--default_cut", type=str, default="",
                        choices=['', 'WZ', 'zMass'],
                        help="Apply default cut string.")
    parser.add_argument("-c","--channel", type=str, default="",
                        choices=['eee', 'eem', 'emm', 'mmm',
                                 'eeee', 'eemm', 'mmmm'],
                        help="Select only one channel")
    parser.add_argument("-f", "--files_to_plot", type=str, required=False,
                        default="", help="Files to make plots from, "
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
            producer.setLumi(1280.23) #In picobarns
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
def plotStack(selection, hist_stack, branch_name, args):
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
    print "Now the offset is %s" % hist_stack.GetYaxis().GetTitleOffset()
    hist_stack.GetYaxis().SetTitle( 
        hists[0].GetYaxis().GetTitle())
    hist_stack.GetXaxis().SetTitle(
        hists[0].GetXaxis().GetTitle())
    hist_stack.GetHistogram().SetLabelSize(0.04)
    
    xcoords = [.15, .35] if args.legend_left else [.70, .90]
    ycoords = [.85, .85 - 0.05*len(hists)]
    legend = ROOT.TLegend(xcoords[0], ycoords[0], xcoords[1], ycoords[1])
    legend.SetFillColor(0)
    legend.AddEntry(data_hist, data_hist.GetTitle(), "lp")
    histErrors = []
    hist_names = []
    for hist in reversed(hists):
        if hist.GetTitle() not in hist_names:
            legend.AddEntry(hist, hist.GetTitle(), "f")
        hist_names.append(hist.GetTitle())
        if args.errors:
            error_hist = plotter.getHistErrors(hist)
            if args.nostack:
                error_hist.SetFillColor(hist.GetFillColor())
                histErrors.append(error_hist)
            else:
                error_hist.SetFillColor(ROOT.kBlack)
                if len(histErrors) == 0:
                    histErrors.append(error_hist)
                else:
                    histErrors[0].Add(error_hist)
    for error_hist in histErrors:
        error_hist.Draw("E2 same")

    legend.Draw()
    
    output_file_name = args.output_file
    if args.make_ratio:
        split_canvas = plotter.splitCanvas(canvas, "stack", ("#Sigma MC", "Data"))
        split_canvas.Print(output_file_name)
    else:
        canvas.Print(output_file_name)
def main():
    args = getComLineArgs()
    ROOT.gROOT.SetBatch(True)
    ROOT.TProof.Open('workers=12')
    file_info = UserInput.readJson("/afs/cern.ch/user/k/kelong/work/AnalysisDatasetManager/FileInfo/montecarlo.json")
    filelist = [x.strip() for x in args.files_to_plot.split(",")]
    hist_factory = helper.getHistFactory(file_info, states, args.selection, filelist)
    branches = [x.strip() for x in args.branches.split(",")]
    cut_string = helper.getCutString(args.default_cut, args.channel, args.make_cut)
    for branch in branches:
        print "Branch name is %s" % branch
        plotStack(args.selection, getStacked(hist_factory, args.selection, branch, cut_string), branch, args)
        
if __name__ == "__main__":
    main()
