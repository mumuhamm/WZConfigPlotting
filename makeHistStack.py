#!/usr/bin/env python
import Utilities.plot_functions as plotter
import Utilities.helper_functions as helper
import argparse
import ROOT
import Utilities.config_object as config_object
import Utilities.selection as selection

def getComLineArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output_file", type=str, required=True,
                        help="Name of file to be created (type pdf/png etc.) " \
                        "Note: 'NAME' will be replaced by branch name")
    parser.add_argument("-s", "--scale", type=str, default="xsec",
                        help="Method for scalling hists")
    parser.add_argument("-r", "--make_ratio", action="store_true",
                        help="Add ratio comparison")
    parser.add_argument("--legend_left", action="store_true",
                        help="Put legend left or right")
    parser.add_argument("--no_errors", action="store_true",
                        help="Don't plot error bands")
    parser.add_argument("-b", "--branches", type=str, required=True,
                        help="List (separate by commas) of names of branches "
                        "in root and config file to plot") 
    parser.add_argument("-n", "--max_entries", type=int, default=-1,
                        help="Draw only first n entries of hist "
                        "(useful for huge root files)")
    parser.add_argument("-m", "--make_cut", type=str, default="",
                        help="Enter a valid root cut string to apply")
    parser.add_argument("--nostack", type=str, default="",
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
def getStacked(file_info, branch_name, cut_string, max_entries):
    hist_stack = ROOT.THStack("stack", "")
    for name, entry in file_info.iteritems():
        "Print name is %s entry is %s at plot time" % (name, entry)
        config = config_object.ConfigObject(entry["plot_config"])
        hist_name = ''.join([name, "-", branch_name])
        hist = config.getObject(hist_name, entry["title"])
        for state in ["eee", "eem", "emm", "mmm"]:
            append = False
            print entry["histProducer"]
            producer = entry["histProducer"][state]
            producer.setLumi(225.6) #In picobarns
            producer.produce(hist, branch_name, cut_string, append)
            append = True
            config.setAttributes(hist, hist_name)
        hist_stack.Add(hist, "hist")
    return hist_stack
def plotStack(hist_stack, args):
    canvas = ROOT.TCanvas("canvas", "canvas", 800, 600) 

    hists = hist_stack.GetHists()
    hist_stack.Draw("nostack" if args.nostack else "")
    hist_stack.GetYaxis().SetTitleSize(0.040)    
    hist_stack.GetYaxis().SetTitleOffset(1.3)    
    hist_stack.GetYaxis().SetTitle( 
        hists[0].GetYaxis().GetTitle())
    hist_stack.GetXaxis().SetTitle(
        hists[0].GetXaxis().GetTitle())
    #hist_stack.GetHistogram().SetLabelSize(0.04)
    print "The title should be %s" % hist_stack.GetHistogram().GetXaxis().GetTitle()
    
    xcoords = [.15, .55] if args.legend_left else [.50, .85]
    legend = ROOT.TLegend(xcoords[0], 0.65, xcoords[1], 0.85)
    legend.SetFillColor(0)
    histErrors = []
    
    for hist in hists:
        legend.AddEntry(hist, hist.GetTitle(), "f")
        if not args.no_errors:
            histErrors.append(plotter.getHistErrors(hist, hist.GetLineColor()))
            histErrors[-1].Draw("E2 same")
    legend.Draw()
    
    output_file_name = args.output_file
    if args.make_ratio:
        split_canvas = plotter.splitCanvas(canvas, "stack", "01j FxFx", "incl")
        split_canvas.Print(output_file_name)
    else:
        canvas.Print(output_file_name)
def main():
    #ROOT.gROOT.SetBatch(True)
    args = getComLineArgs()
    states = ['eee', 'eem', 'emm', 'mmm']
    filelist = [x.strip() for x in args.files_to_plot.split(",")]
    hist_factory = helper.getHistFactory("ConfigFiles/file_info.json", states, "preselection", filelist)
    print "Hist factory is %s" % hist_factory
    branches = [x.strip() for x in args.branches.split(",")]
    cut_string = helper.getCutString(args.default_cut, args.channel, args.make_cut)
    for branch in branches:
        plotStack(getStacked(hist_factory, branch, cut_string, args.max_entries), args)
        
if __name__ == "__main__":
    main()
