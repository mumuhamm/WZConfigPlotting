#!/usr/bin/env python
import ROOT
from Utilities import CutFlowTools
import Utilities.UserInput as UserInput
import Utilities.helper_functions as helper
import os

def getMonteCarloStack(cutflow_maker, filelist):
    hist_stack = ROOT.THStack("stack", "")
    for plot_set in filelist:
        hist = cutflow_maker.getHist(plot_set)
        hist_stack.Add(hist)
    return hist_stack

ROOT.gROOT.SetBatch(True)
ROOT.TProof.Open('workers=12')
path = "/cms/kdlong" if "hep.wisc.edu" in os.environ['HOSTNAME'] else \
    "/afs/cern.ch/user/k/kelong/work"
cutflow_maker = CutFlowTools.CutFlowHistMaker(
    "%s/AnalysisDatasetManager" % path,
    "WZAnalysis"
)
cutflow_maker.setLuminosity(1340)
cutflow_maker.setStates(["eee", "eem", "emm", "mmm"])
for selection in ["preselection", "Zselection", "Mass3l", "Wselection"]:
    cutflow_entry = CutFlowTools.CutFlowEntry(selection, 
        selection,
        "%s/AnalysisDatasetManager" % path,
        "WZAnalysis"
    )
    cutflow_maker.addEntry(cutflow_entry)
parser = UserInput.getDefaultParser()
args = parser.parse_args()
filelist = ["ttbar", "st", "ttv", "vvv", "ww", "zz", "zg", "dy",
        "wz"] if args.files_to_plot == "all" else \
        [x.strip() for x in args.files_to_plot.split(",")]
hist_stack = getMonteCarloStack(cutflow_maker, filelist)
data_hist = cutflow_maker.getHist("data")
canvas = helper.makePlot(hist_stack, data_hist, "CutFlow", args)
(plot_path, html_path) = helper.getPlotPaths("CutFlow", False)
helper.savePlot(canvas, plot_path, html_path, "CutFlow", False, args)
canvas.Print("test.pdf")
