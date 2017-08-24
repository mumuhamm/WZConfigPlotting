#!/usr/bin/env python
import ROOT
from Utilities import CutFlowTools
import Utilities.UserInput as UserInput
import Utilities.helper_functions as helper
from Utilities import CutFlowDefinitions
from Utilities.scripts import makeSimpleHtml
import os

def getMonteCarloStack(name, cutflow_maker, filelist, unc, scale_facs, hist_file):
    hist_stack = ROOT.THStack(name, "")
    for plot_set in filelist:
        if "data" in plot_set.lower():
            continue
        hist = cutflow_maker.getHist(plot_set, unc, hist_file, scale_facs)
        hist_stack.Add(hist)
    return hist_stack

ROOT.gROOT.SetBatch(True)
path = "/cms/kdlong" if "hep.wisc.edu" in os.environ['HOSTNAME'] else \
    "/afs/cern.ch/user/k/kelong/work"
parser = UserInput.getDefaultParser()
parser.add_argument("-s", "--selection", type=str, required=True,
                    help="Specificy selection level to run over")
parser.add_argument("-m", "--make_cut", type=str, default="",
                    help="Enter a valid root cut string to apply")
args = parser.parse_args()
if args.hist_file == "":
    ROOT.TProof.Open('workers=12')

dataset_manager = "%s/AnalysisDatasetManager" % path
cutflow_maker = CutFlowTools.CutFlowHistMaker("YieldByChannel",
    dataset_manager,
    args.selection,
    )
cutflow_maker.setLuminosity(args.luminosity)

cutflow_entry = CutFlowTools.CutFlowEntry("Total",
    dataset_manager,
    args.selection,
)
cutflow_entry.addAdditionalCut(args.make_cut)
cutflow_entry.setStates(args.channels)
cutflow_maker.addEntry(cutflow_entry)
for chan in reversed(sorted(args.channels.split(","))):
    cutflow_entry = CutFlowTools.CutFlowEntry(chan, 
        dataset_manager,
        args.selection,
    )
    cutflow_entry.addAdditionalCut(args.make_cut)
    cutflow_entry.setStates(chan)
    cutflow_maker.addEntry(cutflow_entry)
filelist = UserInput.getListOfFiles(args.files_to_plot, args.selection)
if not args.no_data:
    data_hist = cutflow_maker.getHist("data_2016", "stat", args.hist_file)
    print "Integral is", data_hist.GetBinContent(1)
else:
    data_hist = 0
hist_stack = getMonteCarloStack("stack", cutflow_maker, filelist, 
        args.uncertainties, not args.no_scalefactors, args.hist_file)
signal_stack = 0
if len(args.signal_files) > 0:
    signal_filelist = UserInput.getListOfFiles(args.signal_files, args.selection)
    signal_stack = getMonteCarloStack("signal_stack", cutflow_maker, signal_filelist, 
        args.uncertainties, not args.no_scalefactors, args.hist_file)
hist_stack.Draw()
hist_stack.GetXaxis().SetLabelSize(0.4*8/9)
canvas = helper.makePlots([hist_stack], [data_hist], "YeildByChan", args, [signal_stack])
canvas.SetRightMargin(0.3)
print canvas

plot_name = 'yieldByChannel'
if args.append_to_name != "":
    plot_name += "_"+ args.append_to_name
(plot_path, html_path) = helper.getPlotPaths(args.selection, args.folder_name)
helper.savePlot(canvas, plot_path, html_path, plot_name, False, args)
makeSimpleHtml.writeHTML(html_path, args.selection)
