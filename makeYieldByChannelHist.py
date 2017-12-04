#!/usr/bin/env python
import ROOT
from Utilities import CutFlowTools
import Utilities.UserInput as UserInput
import Utilities.helper_functions as helper
from Utilities import CutFlowDefinitions
from Utilities.scripts import makeSimpleHtml
from Utilities.prettytable import PrettyTable
from collections import OrderedDict
import datetime
import os
import array

def getMonteCarloStack(name, cutflow_maker, filelist, unc, scale_facs, hist_file):
    hist_stack = ROOT.THStack(name, "")
    for plot_set in filelist:
        if "data" in plot_set.lower():
            continue
        hist = cutflow_maker.getHist(plot_set, unc, hist_file, scale_facs)
        hist_stack.Add(hist)
    return hist_stack

def getFormatedYieldAndError(hist, bin_num, digits):
    error = round(hist.GetBinError(bin_num), digits)
    weighted_events = round(hist.GetBinContent(bin_num), digits)
    return "%0.2f $\pm$ %0.2f" % (weighted_events, error)

def makeLogFile(channels, hist_stack, data_hist, signal_stack):
    with open("temp.txt", "w") as log_file:
        meta_info = '-'*80 + '\n' + \
            'Script called at %s\n' % datetime.datetime.now() + \
            'The command was: %s\n' % ' '.join(sys.argv) + \
            '-'*80 + '\n'
        log_file.write(meta_info)
        log_file.write("Selection: %s" % args.selection)
        log_file.write("\nLuminosity: %0.2f fb^{-1}\n" % (args.luminosity))
        log_file.write('-'*80 + '\n')
    columns = ["Process", "Total Yield"] + \
                    ['$'+c.replace("m","\mu")+'$' for c in channels]
    yield_table = PrettyTable(columns)
    yield_info = OrderedDict()
    hists = hist_stack.GetHists() 
    if signal_stack:
        hists += signal_stack.GetHists()
    if data_hist:
        hists.Add(data_hist)
    for hist in hists:
        yield_info["Total Yield"] = getFormatedYieldAndError(hist, 1, 2)
        for i, chan in enumerate(channels):
            # Channels should be ordered the same way as passed to the histogram
            # This bin 0 is the underflow, bin 1 is total, and bin 2
            # is the first bin with channel content (mmm/emm/eem/eee by default)
            yield_info[chan] = getFormatedYieldAndError(hist, i+2, 2)
        yield_table.add_row([hist.GetName()] + yield_info.values())
    with open("temp.txt", "a") as log_file:
        log_file.write(yield_table.get_latex_string())

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
    args.selection.split("_")[0],
)
cutflow_entry.addAdditionalCut(args.make_cut)
cutflow_entry.setStates(args.channels)
cutflow_maker.addEntry(cutflow_entry)
channels = list(reversed(sorted(args.channels.split(","))))

channel_names = {"eee" : "eee", "eem" : "ee#mu", "emm" : "#mu#mue", "mmm" : "#mu#mu#mu"}
for chan in channels:
    cutflow_entry = CutFlowTools.CutFlowEntry(channel_names[chan], 
        dataset_manager,
        args.selection.split("_")[0],
    )
    cutflow_entry.addAdditionalCut(args.make_cut)
    cutflow_entry.setStates(chan)
    cutflow_maker.addEntry(cutflow_entry)
filelist = UserInput.getListOfFiles(args.files_to_plot, args.selection)
if not args.no_data:
    data_hist = cutflow_maker.getHist("data_2016", "stat", args.hist_file)
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
canvas = helper.makePlots([hist_stack], [data_hist], "YieldByChan", args, [signal_stack])
canvas.SetRightMargin(0.3)
ratioPad = ROOT.gPad.GetListOfPrimitives().FindObject("ratioPad")
hist = ratioPad.GetListOfPrimitives().FindObject('YieldByChan_canvas_central_ratioHist')
hist.GetXaxis().SetLabelSize(0.2)
makeLogFile(channels, hist_stack, data_hist, signal_stack)

plot_name = 'yieldByChannel'
if args.append_to_name != "":
    plot_name += "_"+ args.append_to_name
(plot_path, html_path) = helper.getPlotPaths(args.selection, args.folder_name)
helper.savePlot(canvas, plot_path, html_path, plot_name, True, args)
