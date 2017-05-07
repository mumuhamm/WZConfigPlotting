import ROOT
import plot_functions as plotter
import Utilities.WeightInfo as WeightInfo
from Utilities.WeightedHistProducer import WeightedHistProducer
from Utilities.FromFileHistProducer import FromFileHistProducer
from Utilities.ConfigHistFactory import ConfigHistFactory 
from collections import OrderedDict
import os
import subprocess
import glob
import logging
import datetime
import shutil
import errno
import math
from IPython import embed

#logging.basicConfig(level=logging.DEBUG)

def makePlot(hist_stack, data_hist, branch_name, args, signal_stack=0):
    stack_drawexpr = " ".join(["hist"] + 
        ["nostack" if args.nostack else ""] +
        ["same" if signal_stack != 0 else ""]
    )
    canvas = ROOT.TCanvas("%s_canvas" % branch_name, branch_name, 1600, 1200) 
    hists = hist_stack.GetHists()
    if signal_stack != 0:
        sum_stack = hists[0].Clone()
        for hist in hists[1:]:
            sum_stack.Add(hist)
        for i,hist in enumerate(signal_stack.GetHists()):
            hist.Add(sum_stack)
        signal_stack.Draw("hist nostack")
    hist_stack.Draw(stack_drawexpr)
    first_stack = hist_stack if signal_stack == 0 else signal_stack
    if data_hist:
        data_hist.Draw("e1 same")
    if not args.no_decorations:
        ROOT.dotrootImport('kdlong/CMSPlotDecorations')
        scale_label = "Normalized to Unity" if args.luminosity < 0 else \
            "%0.1f fb^{-1}" % args.luminosity
        ROOT.CMSlumi(canvas, 0, 11, "%s (13 TeV)" % scale_label,
                "Preliminary Simulation" if args.simulation else "Preliminary")
    first_stack.GetYaxis().SetTitleSize(hists[0].GetYaxis().GetTitleSize())    
    first_stack.GetYaxis().SetTitleOffset(hists[0].GetYaxis().GetTitleOffset())    
    first_stack.GetYaxis().SetTitle(
        hists[0].GetYaxis().GetTitle())
    first_stack.GetHistogram().GetXaxis().SetTitle(
        hists[0].GetXaxis().GetTitle())
    first_stack.GetHistogram().SetLabelSize(0.04)
    first_stack.SetMinimum(hists[0].GetMinimum()*args.scaleymin)
    ## Adding an arbirary factor of 100 here so the scaling doesn't cut off info from
    ## Hists. Not applied when lumi < 1. This should be fixed
    scale = args.luminosity/100 if args.luminosity > 0 else 1
    first_stack.SetMaximum(hists[0].GetMaximum()*args.scaleymax*scale)
    if "none" not in args.uncertainties:
        histErrors = getHistErrors(hist_stack, args.nostack)
        for error_hist in histErrors:
            error_hist.Draw("same e2")
            error_title = "Stat. Unc."
            if "all" in args.uncertainties:
                error_title = "Stat.#oplusSyst."
            elif "scale" in args.uncertainties:
                error_title = "Stat.#oplusScale"
            error_hist.SetTitle(error_title)
    else:
        histErrors = []
    offset = ROOT.gPad.GetLeftMargin() - 0.04 if args.legend_left else \
        ROOT.gPad.GetRightMargin() - 0.04 
    if hasattr(args, "selection"):
        width = .2 if "WZxsec" in args.selection else 0.33
    else: 
        width = .33
    xcoords = [.10+offset, .1+width+offset] if args.legend_left \
        else [.92-width-offset, .92-offset]
    unique_entries = min(len(hists), 8)
    ymax = 0.8 if args.legend_left else 0.9
    ycoords = [ymax, ymax - 0.08*unique_entries*args.scalelegy]
    coords = [xcoords[0], ycoords[0], xcoords[1], ycoords[1]]
    if args.logy:
        canvas.SetLogy()
    if args.extra_text != "":
        lines = [x.strip() for x in args.extra_text.split(";")]
        ymax = coords[3]
        box_size = 0.05*len(lines)
        if args.extra_text_above:
            ymax = coords[1] 
            coords[1] -= box_size
            coords[3] -= box_size
        ymin = ymax - box_size
        text_box = ROOT.TPaveText(coords[0], ymin, coords[2], ymax, "NDCnb")
        text_box.SetFillColor(0)
        text_box.SetTextFont(42)
        for i, line in enumerate(lines):
            text_box.AddText(line)
        text_box.Draw()
        ROOT.SetOwnership(text_box, False)
    legend = getPrettyLegend(hist_stack, data_hist, signal_stack, histErrors, coords)
    legend.Draw()
    if not args.no_ratio:
        canvas = plotter.splitCanvas(canvas,
                "Data / SM" if data_hist else args.ratio_text,
                [float(i) for i in args.ratio_range]
        )
    return canvas
def getHistErrors(hist_stack, separate):
    histErrors = []
    for hist in hist_stack.GetHists():
        error_hist = plotter.getHistErrors(hist)
        if separate:
            error_hist.SetFillColor(hist.GetLineColor())
            error_hist.SetLineColor(hist.GetLineColor())
            histErrors.append(error_hist)
        else:
            error_hist.SetFillColor(ROOT.kBlack)
            error_hist.SetLineColor(ROOT.kBlack)
            if len(histErrors) == 0:
                histErrors.append(error_hist)
            else:
                histErrors[0].Add(error_hist)
    return histErrors
def getPrettyLegend(hist_stack, data_hist, signal_stack, error_hists, coords):
    hists = hist_stack.GetHists()
    if signal_stack != 0:
        hists += signal_stack.GetHists()
    legend = ROOT.TLegend(coords[0], coords[1], coords[2], coords[3])
    ROOT.SetOwnership(legend, False)
    legend.SetName("legend")
    legend.SetFillStyle(0)
    if data_hist:
        legend.AddEntry(data_hist, data_hist.GetTitle(), "lp")
    hist_names = []
    for hist in reversed(hists):
        if hist.GetTitle() not in hist_names:
            legend.AddEntry(hist, hist.GetTitle(), "f")
        hist_names.append(hist.GetTitle())
    for error_hist in error_hists:
        legend.AddEntry(error_hist, error_hist.GetTitle(), "f")
    return legend
def getHistFactory(config_factory, selection, filelist, luminosity=1, hist_file=None):
    if "Gen" not in selection:
        metaTree_name = "metaInfo/metaInfo"
        sum_weights_branch = "summedWeights"
        weight_branch = "genWeight"
    else:
        metaTree_name = "analyze%s/MetaData" % ("ZZ" if "ZZ" in selection else "WZ")
        sum_weights_branch = "initSumWeights"
        weight_branch = "weight"
    mc_info = config_factory.getMonteCarloInfo()
    all_files = config_factory.getFileInfo()
    hist_factory = OrderedDict() 
    for name in filelist:
        if name not in all_files.keys():
            logging.warning("%s is not a valid file name (must match a definition in FileInfo/%s.json)" % \
                (name, selection))
            continue
        hist_factory[name] = dict(all_files[name])
        if "data" not in name.lower() and name != "nonprompt":
            base_name = name.split("__")[0]
            metaTree = ROOT.TChain(metaTree_name)
            metaTree.Add(hist_factory[name]["file_path"])
            kfac = 1. if 'kfactor' not in mc_info[base_name].keys() else mc_info[base_name]['kfactor']
            weight_info = WeightInfo.WeightInfoProducer(metaTree, 
                    mc_info[base_name]['cross_section']*kfac,
                    sum_weights_branch).produce()
        else:
            weight_info = WeightInfo.WeightInfo(1, 1)
            weight_branch = ""
        if not hist_file:
            histProducer = WeightedHistProducer(weight_info, weight_branch)  
        else:
            histProducer = FromFileHistProducer(weight_info, hist_file)  
        if "data" not in name.lower() and name != "nonprompt":
            histProducer.setLumi(luminosity)
        hist_factory[name].update({"histProducer" : histProducer})
        hist_factory[name].update({"configFactory" : config_factory})
        hist_factory[name].update({"fromFile" : hist_file is not None})
    return hist_factory
def getConfigHist(hist_factory, branch_name, bin_info, plot_group, selection, states, 
        uncertainties="none", cut_string="", addOverflow=True):
    hist_name = "_".join([plot_group, selection.replace("/", "_"), branch_name.split("_")[0]])
    rootdir = "gProof" if hasattr(ROOT, "gProof") else "gROOT"
    hist = getattr(ROOT, rootdir).FindObject(hist_name)
    if hist:
        hist.Delete()
    if not hist_factory.itervalues().next()["fromFile"]:
        hist = ROOT.TH1D(hist_name, hist_name, bin_info['nbins'], bin_info['xmin'], bin_info['xmax'])
    log_info = "" 
    final_counts = {c : 0 for c in states}
    for name, entry in hist_factory.iteritems():
        log_info += "_"*80 + "\n"
        log_info += "Results for file %s in plot group %s\n" % (name, plot_group)
        producer = entry["histProducer"]
        config_factory = entry["configFactory"]
        for state in states:
            if entry["fromFile"]:
                chan = state
                hist_name = str("%s/%s_%s" % (name, branch_name, state))
                if "nonprompt" in str(plot_group).lower():
                    hist_name = hist_name.replace(state, "Fakes_"+state)
                args = [hist_name, addOverflow]
            else:
                chan = state.split("/")[0] if "ntuple" in state else ""
                config_factory.setProofAliases(chan)
                draw_expr = config_factory.getHistDrawExpr(branch_name, name, chan)
                proof_name = "_".join([name, "%s#/%s" % (selection.replace("/", "_"), state)])
                producer.setCutString(cut_string)
                args = [draw_expr, proof_name, addOverflow]
            
            try:
                state_hist = producer.produce(*args)
            except ValueError as error:
                logging.warning(error)
                log_info += "Number of events in %s channel: 0.0\n"  % state
                continue
            if not hist:
                hist = state_hist
                hist.SetName(hist_name)
                if state_hist.InheritsFrom("TH1"):
                    hist.SetTitle(hist_name)
            else:
                hist.Add(state_hist)
            final_counts[state] += state_hist.Integral()
            log_info += "Number of events in %s channel: %0.2f\n" % (state, state_hist.Integral())
        log_info += "Total number of events: %0.2f\n" % (hist.Integral() if hist and hist.InheritsFrom("TH1") else 0)
        log_info += "Cross section is %0.2f\n" % producer.getCrossSection()
    logging.debug(log_info)
    logging.debug("Hist has %i entries" % (hist.GetEntries() if hist and hist.InheritsFrom("TH1") else 0) )
    log_info += "*"*80 + "\n"
    log_info += "    Summary for plot group %s\n" % plot_group
    log_info += "    Total entries in all states: %0.2f\n" % (hist.Integral() if hist and hist.InheritsFrom("TH1") else 0)
    for state in states:
        log_info += "    %0.2f events in state %s\n" % (final_counts[state], state)
    log_info += "*"*80 + "\n"
    with open("temp-verbose.txt", "a") as log_file:
        log_file.write(log_info)
    if not hist or not hist.InheritsFrom("TH1"):
        raise RuntimeError("Invalid histogram %s for selection %s" % (branch_name, selection))
    return hist

def getConfigHistFromFile(filename, config_factory, plot_group, selection, branch_name, channels,
        luminosity=1, addOverflow=True, uncertainties="none"):
    try:
        filelist = config_factory.getPlotGroupMembers(plot_group)
    except ValueError as e:
        logging.warning(e.message)
        logging.warning("Treating %s as file name" % plot_group)
        filelist = [plot_group]
    if branch_name not in config_factory.getListOfPlotObjects():
        raise ValueError("Invalid histogram %s for selection %s" % (branch_name, selection))
    hist_file = ROOT.TFile(filename)
    ROOT.SetOwnership(hist_file, False)
    hist_factory = getHistFactory(config_factory, selection, filelist, luminosity, hist_file)
    bin_info = config_factory.getHistBinInfo(branch_name)
    states = channels.split(",")
    hist = getConfigHist(hist_factory, branch_name, bin_info, plot_group, selection, states, uncertainties)
    config_factory.setHistAttributes(hist, branch_name, plot_group)
    
    return hist

def getConfigHistFromTree(config_factory, plot_group, selection, branch_name, channels, blinding=[],
    addOverflow=True, cut_string="", luminosity=1, no_scalefacs=False, uncertainties="none"):
    if "Gen" not in selection:
        states = [x.strip() for x in channels.split(",")]
        scale_weight_expr = "scaleWeights/scaleWeights[0]"
        trees = ["%s/ntuple" % state for state in states]
    else:
        trees = ["analyze%s/Ntuple" % ("ZZ" if "ZZ" in selection else "WZ")]
        scale_weight_expr = "LHEweights/LHEweights[0]"
        if channels != "eee,mmm,eem,emm":
            chan_cuts = []
            for chan in channels.split(","): 
                chan_cuts.append(getGenChannelCut(chan))
            cut_string = appendCut(cut_string, " || ".join(chan_cuts))
    try:
        filelist = config_factory.getPlotGroupMembers(plot_group)
    except ValueError as e:
        logging.warning(e.message)
        logging.warning("Treating %s as file name" % plot_group)
        filelist = [plot_group]
    hist_factory = getHistFactory(config_factory, selection, filelist, luminosity)
    bin_info = config_factory.getHistBinInfo(branch_name)
    
    if "data" in plot_group: 
        for blind in blinding: 
            if branch_name in blind:
                cut_string = appendCut(cut_string, blind)
#    scale_unc = False
#    scalebins = [8,0,8]
#    group_sum_hist = ROOT.TH1D(hist_name, hist_name, bin_info['nbins'], bin_info['xmin'], bin_info['xmax'])
#    no_weights = ["st-tchan-tbar","st-tchan-t","st-schan", "ggZZ4e", "ggZZ4m", "ggZZ2e2mu", "st-tw", "st-tbarw"]
#
#    if "scale" in uncertainties or uncertainties == "all":
#        scale_unc = True
#        scale_name = hist_name + "_lheWeights"
#    original_cut_string = cut_string
    
    hist = getConfigHist(hist_factory, branch_name, bin_info, plot_group, selection, trees, uncertainties, cut_string)
    config_factory.setHistAttributes(hist, branch_name, plot_group)
    return hist

#    for name, entry in hist_info.iteritems():   
#        log_info += "_"*80 + "\n"
#        log_info += "Results for file %s in plot group %s\n" % (name, plot_group)
#        sum_hist = group_sum_hist
#        if scale_unc and name not in no_weights:
#            sum_hist = ROOT.TH2D(scale_name, scale_name, 8, 0, 8, bin_info['nbins'], bin_info['xmin'], bin_info['xmax'])
#        producer = entry["histProducer"]
#        weight = config_factory.getPlotGroupWeight(plot_group)
#        if weight != 1:
#            producer.addWeight(weight)
#        for tree in trees:
#            state = tree.split("/")[0] if "ntuple" in tree else ""
#            config_factory.setProofAliases(state)
#            # Don't enter an infinite loop of adding aliases
#            if cut_string == original_cut_string:
#                cut_string = config_factory.hackInAliases(cut_string)
#            if "WZxsec2016" in selection and not is_data and not no_scalefacs:
#                scale_expr = getScaleFactorExpression(state, "medium", "tightW")
#                weighted_cut_string = appendCut(cut_string, scale_expr)
#            else:
#                weighted_cut_string = cut_string 
#            draw_expr = config_factory.getHistDrawExpr(branch_name, name, state)
#            print "NAME IS", name
#            if scale_unc and name not in no_weights:
#                draw_expr = config_factory.getHist2DWeightrawExpr(branch_name, name, state, scalebins)
#                weighted_cut_string = appendCut(cut_string, scale_weight_expr)
#            producer.setCutString(weighted_cut_string)
#            logging.debug("Draw expression was %s" % draw_expr)
#            proof_name = "_".join([name, "%s#/%s" % (selection.replace("/", "_"), tree)])
#            logging.debug("Proof path was %s" % proof_name)
#            chan = tree.split("/")[0]
#            try:
#                state_hist = producer.produce(draw_expr, proof_name)
#                sum_hist.Add(state_hist)
#                log_info += "Number of events in %s channel: %0.2f\n" % (chan, state_hist.Integral())
#            except ValueError as error:
#                logging.warning(error)
#                log_info += "Number of events: 0.0\n" 
#        # Just symmetric errors for now
#        if scale_unc and not name in no_weights:
#            scale_hist = histWithScaleUnc(sum_hist, 8, hist_name+"_scale")
#            log_info += "Number of events in %s channel: %0.2f\n" % (chan, scale_hist.Integral())
#            sum_hist.Delete()
#            group_sum_hist.Add(scale_hist)
#    final_hist = group_sum_hist
#    log_info += "*"*80 + "\n\n"
#    log_info += "Total number of weighted events for plot group %s: %0.2f\n" % (plot_group, final_hist.Integral())
#    log_info += "\n" + "*"*80 + "\n"
#    config_factory.setHistAttributes(final_hist, branch_name, plot_group)
#    #if "scale" in uncertainties or "all" in uncertainties:
#    if uncertainties == "all":
#        config_factory.addErrorToHist(final_hist, plot_group)
#    logging.debug(log_info)
#    logging.debug("Hist has %i raw entries" % final_hist.GetEntries())
#    with open("temp-verbose.txt", "a") as log_file:
#        log_file.write(log_info)
#    if addOverflow:
#        # Returns num bins + overflow + underflow
#        num_bins = final_hist.GetSize() - 2
#        add_overflow = final_hist.GetBinContent(num_bins) + final_hist.GetBinContent(num_bins + 1)
#        final_hist.SetBinContent(num_bins, add_overflow)
#    return final_hist

def histWithScaleUnc(scale_hist2D, entries, name):
    if not isinstance(scale_hist2D, ROOT.TH2):
        raise ValueError("Scale uncertainties require 2D histogram")
    scale_hist = scale_hist2D.ProjectionY("temp", 1, 1, "e")
    scale_hist.SetName(name)
    ROOT.SetOwnership(scale_hist, False)
    hists = []
    for i in range(2, entries+1):
        hist = scale_hist2D.ProjectionY(name+"_weight%i" % i, i, i, "e")
        hist.Sumw2()
        hists.append(hist)
    # Choose max variation between scale choices by bin
    for i in range(1, scale_hist.GetNbinsX()+1):
        try:
            maxScale = max([h.GetBinContent(i) for h in hists \
                    if not h.GetBinContent(i) == 0])
            minScale = min([h.GetBinContent(i) for h in hists \
                    if not h.GetBinContent(i) == 0])
            scaleUp_diff = maxScale - scale_hist.GetBinContent(i)
            scaleDown_diff = scale_hist.GetBinContent(i) - minScale
            maxScaleErr = max(scaleUp_diff, scaleDown_diff)
        except:
            maxScaleErr = 0
        # Just symmetric errors for now
        err = math.sqrt(scale_hist.GetBinError(i)**2 + maxScaleErr**2)
        scale_hist.SetBinError(i, err)
    return scale_hist 

def appendCut(cut_string, add_cut):
    if cut_string != "" and add_cut not in cut_string:
        append_cut = lambda x: "*(%s)" % x if x not in ["", None] else x
        return "(" + cut_string + ")" + append_cut(add_cut)
    else:
        return add_cut

def getScaleFactorExpression(state, muonId, electronId):
    if muonId == "tight" and electronId == "tight":
        return getScaleFactorExpressionAllTight(state)
    elif muonId == "medium" and electronId == "tightW":
        return getScaleFactorExpressionMedTightWElec(state)
    else:
        return "1"

def getScaleFactorExpressionMedTightWElec(state):
    if state == "eee":
        return "e1MediumIDSF*" \
                "e2MediumIDSF*" \
                "e3TightIDSF*" \
                "pileupSF"
    elif state == "eem":
        return "e1MediumIDSF*" \
                "e2MediumIDSF*" \
                "mTightIsoSF*" \
                "mMediumIDSF*" \
                "pileupSF"
    elif state == "emm":
        return "eTightIDSF*" \
                "m1MediumIDSF*" \
                "m1TightIsoSF*" \
                "m2TightIsoSF*" \
                "m2MediumIDSF*" \
                "pileupSF"
    elif state == "mmm":
        return "m1TightIsoSF*" \
                "m1MediumIDSF*" \
                "m2TightIsoSF*" \
                "m2MediumIDSF*" \
                "m3TightIsoSF*" \
                "m3MediumIDSF*" \
                "pileupSF"
def getScaleFactorExpressionAllTight(state):
    if state == "eee":
        return "e1TightIDSF*" \
                "e2TightIDSF*" \
                "e3TightIDSF*" \
                "pileupSF"
    elif state == "eem":
        return "e1TightIDSF*" \
                "e2TightIDSF*" \
                "mTightIsoSF*" \
                "mTightIDSF*" \
                "pileupSF"
    elif state == "emm":
        return "eTightIDSF*" \
                "m1TightIDSF*" \
                "m1TightIsoSF*" \
                "m2TightIsoSF*" \
                "m2TightIDSF*" \
                "pileupSF"
    elif state == "mmm":
        return "m1TightIsoSF*" \
                "m1TightIDSF*" \
                "m2TightIsoSF*" \
                "m2TightIDSF*" \
                "m3TightIsoSF*" \
                "m3TightIDSF*" \
                "pileupSF"
def getPlotPaths(selection, folder_name, write_log_file=False):
    if "hep.wisc.edu" in os.environ['HOSTNAME']:
        storage_area = "/nfs_scratch/kdlong"
        html_area = "/afs/hep.wisc.edu/home/kdlong/public_html"
    else:
        storage_area = "/data/kelong"
        html_area = "/afs/cern.ch/user/k/kelong/www"
    base_dir = "%s/DibosonAnalysisData/PlottingResults" % storage_area
    plot_path = "/".join([base_dir, selection] +
        (['{:%Y-%m-%d}'.format(datetime.datetime.today()),
        '{:%Hh%M}'.format(datetime.datetime.today())] if folder_name == "" \
            else [folder_name])
    )
    makeDirectory(plot_path)
    if write_log_file:
        makeDirectory("/".join([plot_path, "logs"]))
    html_path = plot_path.replace(storage_area, html_area)
    return (plot_path, html_path)
def getGenChannelCut(channel):
    cut_string = ""
    if channel == "eem":
        cut_string = "((abs(l1pdgId) == 11 && abs(l2pdgId) == 11 && abs(l3pdgId) == 13)" \
            " || (abs(l1pdgId) == 11 && abs(l2pdgId) == 13 && abs(l3pdgId) == 11)" \
            " || (abs(l1pdgId) == 13 && abs(l2pdgId) == 11 && abs(l3pdgId) == 11))"
    elif channel == "emm":
        cut_string = "((abs(l1pdgId) == 13 && abs(l2pdgId) == 13 && abs(l3pdgId) == 11)" \
            " || (abs(l1pdgId) == 13 && abs(l2pdgId) == 11 && abs(l3pdgId) == 13)" \
            " || (abs(l1pdgId) == 11 && abs(l2pdgId) == 13 && abs(l3pdgId) == 13))"
    elif channel == "eee":
        cut_string = "(abs(l1pdgId) == 11 && abs(l2pdgId) == 11 && abs(l3pdgId) == 11)"
    elif channel == "mmm":
        cut_string = "(abs(l1pdgId) == 13 && abs(l2pdgId) == 13 && abs(l3pdgId) == 13)"
    return cut_string
def savePlot(canvas, plot_path, html_path, branch_name, write_log_file, args):
    if args.output_file != "":
        canvas.Print(args.output_file)
        return
    if write_log_file:
        log_file = "/".join([plot_path, "logs", "%s_event_info.log" % branch_name])
        verbose_log = log_file.replace("event_info", "event_info-verbose")
        shutil.move("temp.txt", log_file) 
        shutil.move("temp-verbose.txt", verbose_log) 
    output_name ="/".join([plot_path, branch_name]) 
    canvas.Print(output_name + ".root")
    canvas.Print(output_name + ".C")
    if not args.no_html:
        makeDirectory(html_path)
        output_name ="/".join([html_path, branch_name])
        canvas.Print(output_name + ".png")
        canvas.Print(output_name + ".eps")
        subprocess.call(["epstopdf", "--outfile=%s" % output_name+".pdf", output_name+".eps"])
        os.remove(output_name+".eps")
        if write_log_file:
            makeDirectory("/".join([html_path, "logs"]))
            shutil.copy(log_file, log_file.replace(plot_path, html_path))
            shutil.copy(verbose_log, verbose_log.replace(plot_path, html_path))
    del canvas

def makeDirectory(path):
    '''
    Make a directory, don't crash
    '''
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: 
            raise
