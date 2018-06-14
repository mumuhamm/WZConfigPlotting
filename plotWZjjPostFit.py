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
import logging

def getComLineArgs():
    parser = UserInput.getDefaultParser()
    parser.add_argument("-s", "--selection", type=str, required=True,
                        help="Specificy selection level to run over")
    parser.add_argument("--backgroundOnly", action='store_true',
                        help="Use background only fit rather than s+b")
    parser.add_argument("--noCR", action='store_true',
                        help="Remove control region from fit distribution")
    parser.add_argument("-b", "--branches", type=str, default="all",
                        help="List (separate by commas) of names of branches "
                        "in root and config file to plot") 
    return parser.parse_args()

def histFromGraph(graph, name):
    nentries = graph.GetN()
    hist = ROOT.TH1D(name, name, nentries, 0, nentries)
    for i in range(nentries):
        x = array.array('d', [0])
        y = array.array('d', [0])
        graph.GetPoint(i, x, y)
        hist.Fill(x[0], y[0])
    return hist

def removeControlRegion(hist):
    nbins = hist.GetNbinsX()-1
    name = hist.GetName() +"_noCR"
    new_hist = ROOT.TH1D(name, name, nbins, 0, nbins)
    for i in range(2, hist.GetNbinsX()+1):
        new_hist.SetBinContent(i-1, hist.GetBinContent(i))
        new_hist.SetBinError(i-1, hist.GetBinError(i))
    return new_hist

def main():
    args = getComLineArgs()
    ROOT.gROOT.SetBatch(True)

    (plot_path, html_path) = helper.getPlotPaths(args.selection, args.folder_name, True)

    meta_info = '-'*80 + '\n' + \
        'Script called at %s\n' % datetime.datetime.now() + \
        'The command was: %s\n' % ' '.join(sys.argv) + \
        '-'*80 + '\n'

    rtfile = ROOT.TFile(args.hist_file)

    channels = args.channels.split(",")
    for branch in args.branches.split(","):
        with open("temp.txt", "w") as mc_file:
            mc_file.write(meta_info)
            mc_file.write("Selection: %s" % args.selection)
            mc_file.write("\nPlotting branch: %s\n" % branch)

        plot_name = branch 
        if args.append_to_name:
            plot_name += "_" + args.append_to_name
        hist_stack = ROOT.THStack("stack_postfit", "stack_postfit")
        signal_stack = ROOT.THStack("signalstack_prefit", "sig_prefit")
        data_hist = 0
        plot_groups = args.files_to_plot.split(",")
        if not args.no_data:
            plot_groups.append("data")
        for i, plot_group in enumerate(plot_groups):
            isSignal = False
            central_hist = 0
            for chan in channels:
                folder = "shapes_fit_b" if args.backgroundOnly else "shapes_fit_s"
                if "aqgc" in plot_group:
                    isSignal = True
                    folder = "shapes_prefit"
                hist_name = "/".join([folder, chan, plot_group if plot_group != "wzjj-ewk_filled" else "EW-WZjj"])

                hist = rtfile.Get(hist_name)
                if hist.InheritsFrom("TGraph"):
                    hist = histFromGraph(hist, "_".join([plot_group, chan]))
                if args.noCR:
                    hist = removeControlRegion(hist)
                if "MTWZ" in plot_name:
                    binning = array.array('d', [0,100,200,300,400,500,700,1000,1500,2000]) 
                    tmphist = ROOT.TH1D(hist_name, hist_name, len(binning)-1, binning)
                    for i in range(hist.GetNbinsX()+1):
                        tmphist.SetBinContent(i, hist.GetBinContent(i))
                        tmphist.SetBinError(i, hist.GetBinError(i))
                    hist = tmphist
                if not central_hist:
                    central_hist = hist
                    central_hist.SetName(plot_group)
                else:
                    central_hist.Add(hist)
            path = "/cms/kdlong" if "hep.wisc.edu" in os.environ['HOSTNAME'] else \
                "/afs/cern.ch/user/k/kelong/work"
            config_factory = ConfigHistFactory(
                "%s/AnalysisDatasetManager" % path,
                args.selection.split("_")[0],
            )
            scale_fac = 1
            scale = False
            with open("temp.txt", "a") as mc_file:
                mc_file.write("\nYield for %s is %0.2f" % (plot_group, central_hist.Integral()))
            
            config_factory.setHistAttributes(central_hist, branch, plot_group)
            
            if plot_group != "data" and not isSignal:
                hist_stack.Add(central_hist)
            elif isSignal:
                signal_stack.Add(central_hist)
            else:
                data_hist = central_hist
                data_hist.Sumw2(False)
                data_hist.SetBinErrorOption(ROOT.TH1.kPoisson)
        if not signal_stack.GetHists():
            signal_stack = 0
        canvas = helper.makePlots([hist_stack], [data_hist], plot_name, args, signal_stacks=[signal_stack])
        if "CR" not in plot_name and "unrolled" in plot_name:
            ratioPad = canvas.GetListOfPrimitives().FindObject("ratioPad")
            stackPad = canvas.GetListOfPrimitives().FindObject("stackPad")
            ratiohist = ratioPad.GetListOfPrimitives().FindObject('%s_canvas_central_ratioHist' % plot_name)
            xaxis = hist.GetXaxis()
            maximum = hist_stack.GetHistogram().GetMaximum()
            for i in [4,8]:
                line = ROOT.TLine(xaxis.GetBinUpEdge(i), hist_stack.GetMinimum(), xaxis.GetBinUpEdge(i), maximum)
                line.SetLineStyle(7)
                line.SetLineColor(ROOT.kGray+2)
                line.SetLineWidth(2)
                stackPad.cd()
                line.Draw()
                ROOT.SetOwnership(line, False)
            for i, label in enumerate(["#in [2.5, 4]", "#in [4, 5]", "#geq 5   "]):
                xmin = 0.22 + 0.24*i +0.05*(i==2)
                ymin = 0.15 if i == 2 else 0.5
                ymax = ymin + (0.2 if i ==0 else 0.18)
                xmax = xmin + (0.19 if i ==0 else 0.175)
                text_box = ROOT.TPaveText(xmin, ymin, xmax, ymax, "NDCnb")
                text_box.SetFillColor(0)
                text_box.SetTextFont(42)
                text_box.AddText("#Delta#eta_{jj} %s" % label)
                text_box.Draw()
                ROOT.SetOwnership(text_box, False)

        helper.savePlot(canvas, plot_path, html_path, plot_name, True, args)
        makeSimpleHtml.writeHTML(html_path.replace("/plots",""), args.selection)

if __name__ == "__main__":
    main()


