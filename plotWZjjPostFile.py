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
    print hist.Integral()
    return hist

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

        plot_name = "WZjjPostFit"
        hist_stack = ROOT.THStack("stack_postfit", "stack_postfile")
        data_hist = 0
        plot_groups = args.files_to_plot.split(",")
        if not args.no_data:
            plot_groups.append("data")
        for i, plot_group in enumerate(plot_groups):
            central_hist = 0
            for chan in channels:
                hist_name = "/".join(["shapes_fit_s", chan, plot_group])

                hist = rtfile.Get(hist_name)
                if hist.InheritsFrom("TGraph"):
                    hist = histFromGraph(hist, plot_group)
                if not central_hist:
                    central_hist = hist
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
            
            if plot_group != "data":
                hist_stack.Add(central_hist)
            else:
                data_hist = central_hist

        canvas_dimensions = [1200, 800]
        canvas = ROOT.TCanvas("canvas", "canvas", *canvas_dimensions)
        hist_stack.Draw("hist")
        if data_hist:
            if data_hist.InheritsFrom("TGraph"):
                data_hist.Draw("same P")
            else:
                data_hist.Draw("same")
        hist_stack.SetMinimum(central_hist.GetMinimum()*args.scaleymin)
        hist_stack.SetMaximum(central_hist.GetMaximum()*args.scaleymax)
        hist_stack.GetHistogram().GetYaxis().SetTitle("Events / bin")
        hist_stack.GetHistogram().GetYaxis().SetTitleOffset(1.05)

        if args.logy:
            canvas.SetLogy()

        if not args.no_ratio:
            canvas = plotter.splitCanvas(canvas, canvas_dimensions,
                    "Data / Pred.",
                    [float(i) for i in args.ratio_range]
            )
            ratioPad = canvas.FindObject("ratioPad")
            hist = ratioPad.GetListOfPrimitives().FindObject("canvas_central_ratioHist")
            hist.GetXaxis().SetLabelSize(0.175)
            hist.GetXaxis().SetLabelOffset(0.03)
            hist.GetXaxis().SetTitleOffset(1.15)
            canvas.Update()
        helper.savePlot(canvas, plot_path, html_path, plot_name, True, args)
        makeSimpleHtml.writeHTML(html_path.replace("/plots",""), args.selection)

if __name__ == "__main__":
    main()


