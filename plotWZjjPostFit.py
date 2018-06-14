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
from collections import OrderedDict
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
    parser.add_argument("--noCR", action='store_true',
                        help="Remove control region from fit distribution")
    parser.add_argument("-b", "--branches", type=str, default="all",
                        help="List (separate by commas) of names of branches "
                        "in root and config file to plot") 
    return parser.parse_args()

def getFormattedYieldAndError(integral, error, sigfigs):
    result = "%0.1f" % round(integral, 1)

    error_digits = 0
    error_string = " $\pm$ %i"
    if len(result.split(".")) == 2:
        error_digits = len(result.split(".")[1])
        error_string = " $\pm$ %.{digits}f".format(digits=error_digits)
    error = round(error, error_digits)

    return result + (error_string % error)

def makeLogFile(channels, hist_info, args):
    with open("temp.txt", "w") as log_file:
        meta_info = '-'*80 + '\n' + \
            'Script called at %s\n' % datetime.datetime.now() + \
            'The command was: %s\n' % ' '.join(sys.argv) + \
            '-'*80 + '\n'
        log_file.write(meta_info)
        log_file.write("Selection: %s" % args.selection)
        log_file.write("\nLuminosity: %0.2f fb^{-1}\n" % (args.luminosity))
        log_file.write('-'*80 + '\n')
    columns = ["Process"] + ["\\"+c for c in channels] + ["Total Yield"]
    yield_table = PrettyTable(columns)
    yield_info = OrderedDict()

    formatted_names = { "wz-powheg" : "WZ (POWHEG)",
        "wz-mgmlm" : "WZ (MG MLM)",
        "QCD-WZjj" : "QCD-WZjj",
        "EW-WZjj" : "EW-WZjj",
        "wzjj-ewk" : "WZjj EWK",
        "wzjj-vbfnlo" : "WZjj EWK (VBFNLO)",
        "nonprompt" : "Nonprompt",
        "top-ewk" : "t+V/VVV",
        "zg" : "Z$\gamma$",
        "vv-powheg" : "VV (POWHEG)",
        "vv" : "VV",
        "wz" : "WZ (MG5\_aMC)",
        "wz-powheg" : "WZ (POWHEG)",
        "predyield" : "Pred. Background",
        "data_2016" : "Data",
        "data" : "Data",
        "data_2016H" : "Data (2016H)",
    }

    sigfigs = 3
    for name, entry in hist_info.iteritems():
        for i, chan in enumerate(channels):
            # Channels should be ordered the same way as passed to the histogram
            # This bin 0 is the underflow, bin 1 is total, and bin 2
            # is the first bin with channel content (mmm/emm/eem/eee by default)
            if name == "data":
                yield_info[chan] = "%i" % entry[chan][0] 
            else:
                yield_info[chan] = getFormattedYieldAndError(entry[chan][0], entry[chan][1], sigfigs)
        if name == "data":
            yield_info["Total Yield"] = "%i" % entry["total"][0] 
        else:
            yield_info["Total Yield"] = getFormattedYieldAndError(entry["total"][0], entry["total"][1], sigfigs)
        yield_table.add_row([formatted_names[name]] + yield_info.values())
    with open("temp.txt", "a") as log_file:
        log_file.write(yield_table.get_latex_string())


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
    hist_info = {}
    hist_info["predyield"] = {"total" : [0,0], "eee" : [0,0], "eem" : [0,0], "emm" : [0,0], "mmm" : [0,0]}
    for branch in args.branches.split(","):
        with open("temp.txt", "w") as mc_file:
            mc_file.write(meta_info)
            mc_file.write("Selection: %s" % args.selection)
            mc_file.write("\nPlotting branch: %s\n" % branch)

        plot_name = "mjj_etajj_unrolled" if args.noCR else "mjj_etajj_unrolled_wCR"
        if args.append_to_name:
            plot_name += "_" + args.append_to_name
        hist_stack = ROOT.THStack("stack_postfit", "stack_postfile")
        data_hist = 0
        plot_groups = args.files_to_plot.split(",")
        if not args.no_data:
            plot_groups.append("data")
        for i, plot_group in enumerate(plot_groups):
            hist_info[plot_group] = {"total" : (0,0), "eee" : (0,0), "eem" : (0,0), "emm" : (0,0), "mmm" : (0,0)}
            central_hist = 0
            for chan in channels:
                hist_name = "/".join(["shapes_fit_s", chan, plot_group])

                hist = rtfile.Get(hist_name)
                if hist.InheritsFrom("TGraph"):
                    hist = histFromGraph(hist, "_".join([plot_group, chan]))
                if args.noCR:
                    hist = removeControlRegion(hist)
                if not central_hist:
                    central_hist = hist
                    central_hist.SetName(plot_group)
                else:
                    central_hist.Add(hist)
                error = array.array('d', [0])
                integral = hist.IntegralAndError(0, hist.GetNbinsX(), error)
                hist_info[plot_group][chan] = (integral, error[0])
                if "data" not in plot_group and plot_group != "EW-WZjj":
                    hist_info["predyield"][chan][0] += integral
                    hist_info["predyield"][chan][1] += error[0]*error[0]
                with open("temp.txt", "a") as mc_file:
                    mc_file.write("\nYield for %s in channel %s is %0.3f $pm$ %0.3f" % 
                            (plot_group, chan, integral, error[0]))
            path = "/cms/kdlong" if "hep.wisc.edu" in os.environ['HOSTNAME'] else \
                "/afs/cern.ch/user/k/kelong/work"
            config_factory = ConfigHistFactory(
                "%s/AnalysisDatasetManager" % path,
                args.selection.split("_")[0],
            )
            scale_fac = 1
            scale = False
            error = array.array('d', [0])

            integral = central_hist.IntegralAndError(0, hist.GetNbinsX(), error)
            hist_info[plot_group]["total"] = (integral, error[0])
            if "data" not in plot_group and plot_group != "EW-WZjj":
                hist_info["predyield"]["total"][0] += integral
                hist_info["predyield"]["total"][1] += error[0]*error[0]
            with open("temp.txt", "a") as mc_file:
                mc_file.write("\nCombined yield for %s is %0.3f $pm$ %0.3f" % (plot_group, integral, error[0]))
            
            config_factory.setHistAttributes(central_hist, branch, plot_group)
            
            if plot_group != "data":
                hist_stack.Add(central_hist)
            else:
                data_hist = central_hist
                data_hist.Sumw2(False)
                data_hist.SetBinErrorOption(ROOT.TH1.kPoisson)
        canvas = helper.makePlots([hist_stack], [data_hist], plot_name, args,)
        if "CR" not in plot_name:
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

        hist_info["predyield"]["total"][1] = math.sqrt(hist_info["predyield"]["total"][1])
        makeLogFile(channels, hist_info, args)
        helper.savePlot(canvas, plot_path, html_path, plot_name, True, args)
        makeSimpleHtml.writeHTML(html_path.replace("/plots",""), args.selection)

if __name__ == "__main__":
    main()


