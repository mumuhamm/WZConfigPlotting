#!/usr/bin/env python
import ROOT
from Utilities import CutFlowTools
import Utilities.UserInput as UserInput
import Utilities.helper_functions as helper
from Utilities import CutFlowDefinitions
import os

def getMonteCarloStack(cutflow_maker, filelist, unc, scale_facs):
    hist_stack = ROOT.THStack("cutflow", "")
    for plot_set in filelist:
        hist = cutflow_maker.getHist(plot_set, unc, scale_facs)
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
cutflow_maker.setLuminosity(args.luminosity)
cutflow_maker.setStates(args.channels)
filelist = UserInput.getListOfFiles(args.files_to_plot, "Wselection")
if not args.no_data:
    data_hist = cutflow_maker.getHist("data_2016", "stat")
else:
    data_hist = 0
hist_stack = getMonteCarloStack(cutflow_maker, filelist, 
        args.uncertainties, not args.no_scalefactors)
hist_stack.Draw()
hist_stack.GetXaxis().SetLabelSize(0.4*8/9)
canvas = helper.makePlot(hist_stack, data_hist, "CutFlow", args)
canvas.SetRightMargin(0.3)
(plot_path, html_path) = helper.getPlotPaths("WZxsec2016/CutFlow", args.folder_name)
helper.savePlot(canvas, plot_path, html_path, "CutFlow", False, args)
