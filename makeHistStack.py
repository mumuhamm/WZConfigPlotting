#!/usr/bin/env python
import Utilities.plot_functions as plotter
import Utilities.helper_functions as helper
import argparse
import ROOT
import Utilities.config_object as config_object
import Utilities.selection as selection
import Utilities.UserInput as UserInput

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
def getDataHist(branch_name, cut_string):
    states = ['eee', 'eem', 'emm', 'mmm']
    filelist = ['data_EE_2015C', 'data_EE_2015D']#,'data_ME_2015C', 'data_ME_2015D','data_MM_2015C', 'data_MM_2015D']
    hist_factory = helper.getHistFactory("ConfigFiles/file_info.json", states, args.selection, filelist)
    config = config_object.ConfigObject("ConfigFiles/data_config.json")
    hist_name = ''.join(['data', "-", branch_name])
    hist = config.getObject(hist_name, "Data")
    for name, entry in hist_factory.iteritems():
        for state in states: 
            producer = entry["histProducer"][state]
            hist = producer.produce(hist, branch_name, cut_string, append)
    config.setAttributes(hist, hist_name)
    return hist

def getStacked(file_info, branch_name, cut_string):
    hist_stack = ROOT.THStack("stack", "")
    print "Hello there"
    print "Now the hist factory is %s" % file_info
    styles = UserInput.readJson("/afs/cern.ch/user/k/kelong/work/AnalysisDatasetManager/Styles/styles.json")
    for name, entry in file_info.iteritems():
        print "name is %s entry is %s at plot time" % (name, entry)
        
        config = config_object.ConfigObject(entry)
        hist_name = ''.join([name, "-", branch_name])
        #hist = config.getObject(name, entry["title"])
        hist = ROOT.TH1F(hist_name, hist_name, 20, 0, 120)
        print "entry is %s" % entry
        for state in ["eee"]:#, "eem", "emm", "mmm"]:
            producer = entry["histProducer"][state]
            producer.setLumi(225.6) #In picobarns
            proof_name = "-".join([name, "wz_%s#/%s/final/Ntuple" % ("Zselection", state)])
            hist = producer.produce(hist, branch_name, cut_string, proof_name)
        config.setAttributes(hist, styles['fill-blue'])
        hist_stack.Add(hist, "hist")
    return hist_stack
def plotStack(hist_stack, branch_name, args):
    canvas = ROOT.TCanvas("canvas", "canvas", 800, 600) 
    #data_hist = getDataHist(branch_name, "")#cut_string)
    #data_hist.Draw("SAME") 

    hists = hist_stack.GetHists()
    hist_stack.Draw("nostack" if args.nostack else "")
    hist_stack.GetYaxis().SetTitleSize(0.040)    
    hist_stack.GetYaxis().SetTitleOffset(1.3)    
    hist_stack.GetYaxis().SetTitle( 
        hists[0].GetYaxis().GetTitle())
    hist_stack.GetXaxis().SetTitle(
        hists[0].GetXaxis().GetTitle())
    hist_stack.GetHistogram().SetLabelSize(0.04)
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
    #legend.AddEntry(data_hist, data_hist.GetTitle(), "l")
    legend.Draw()
    
    output_file_name = args.output_file
    if args.make_ratio:
        split_canvas = plotter.splitCanvas(canvas, "stack", "01j FxFx", "incl")
        split_canvas.Print(output_file_name)
    else:
        canvas.Print(output_file_name)
def main():
    args = getComLineArgs()
    ROOT.gROOT.SetBatch(True)
    ROOT.TProof.Open('workers=12')
    states = ['eee']#, 'eem', 'emm', 'mmm']
    file_info = UserInput.readJson("/afs/cern.ch/user/k/kelong/work/AnalysisDatasetManager/FileInfo/montecarlo.json")
    filelist = [x.strip() for x in args.files_to_plot.split(",")]
    hist_factory = helper.getHistFactory(file_info, states, args.selection, filelist)
    branches = [x.strip() for x in args.branches.split(",")]
    cut_string = helper.getCutString(args.default_cut, args.channel, args.make_cut)
    for branch in branches:
        print "Branch name is %s" % branch
        plotStack(getStacked(hist_factory, branch, cut_string), branch, args)
        
if __name__ == "__main__":
    main()
