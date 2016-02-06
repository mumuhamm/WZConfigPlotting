#!/usr/bin/env python
import ROOT
from Utilities import CutFlowTools
import Utilities.UserInput as UserInput
import Utilities.helper_functions as helper
from Utilities import CutFlowDefinitions
import os

def getMonteCarloStack(cutflow_maker, filelist):
    hist_stack = ROOT.THStack("cutflow", "")
    for plot_set in filelist:
        hist = cutflow_maker.getHist(plot_set)
        hist_stack.Add(hist)
    return hist_stack

ROOT.gROOT.SetBatch(True)
ROOT.TProof.Open('workers=12')
path = "/cms/kdlong" if "hep.wisc.edu" in os.environ['HOSTNAME'] else \
    "/afs/cern.ch/user/k/kelong/work"
parser = UserInput.getDefaultParser()
args = parser.parse_args()
cutflow_maker = CutFlowDefinitions.getWZCutFlow(
    "%s/AnalysisDatasetManager" % path,
    "full"
)
cutflow_maker.setLuminosity(1340)
cutflow_maker.setStates(["eee", "mmm", "emm", "eem"])
filelist = ["ttbar", "st", "ttv", "vvv", "ww", "zz", "dy-filt", "zg-filt",
        "wz"] if args.files_to_plot == "all" else \
        [x.strip() for x in args.files_to_plot.split(",")]
data_hist = cutflow_maker.getHist("data")
hist_stack = getMonteCarloStack(cutflow_maker, filelist)
hist_stack.Draw()
hist_stack.GetXaxis().SetLabelSize(0.4*8/9)
print "Now stack is %s" % hist_stack
canvas = helper.makePlot(hist_stack, data_hist, "CutFlow", args)
canvas.SetRightMargin(0.3)
(plot_path, html_path) = helper.getPlotPaths("CutFlow", False)
helper.savePlot(canvas, plot_path, html_path, "CutFlow", False, args)
