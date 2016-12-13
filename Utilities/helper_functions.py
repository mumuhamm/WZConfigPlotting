import ROOT
import plot_functions as plotter
import Utilities.WeightInfo as WeightInfo
import Utilities.WeightedHistProducer as WeightedHistProducer
from Utilities.ConfigHistFactory import ConfigHistFactory 
from collections import OrderedDict
import os
import glob
import logging
import datetime
import shutil
import errno
import math

def makePlot(hist_stack, data_hist, branch_name, args):
    canvas = ROOT.TCanvas("%s_canvas" % branch_name, branch_name, 1600, 1200) 
    hists = hist_stack.GetHists()
    hist_stack.Draw("nostack hist" if args.nostack else "hist")
    if data_hist:
        data_hist.Draw("same")
        #hist_stack.Add(data_hist)
    if not args.no_decorations:
        ROOT.dotrootImport('kdlong/CMSPlotDecorations')
        scale_label = "Normalized to Unity" if args.luminosity < 0 else \
            "%0.1f fb^{-1}" % args.luminosity
        ROOT.CMSlumi(canvas, 0, 11, "%s (13 TeV)" % scale_label,
                "Preliminary Simulation" if args.simulation else "Preliminary")
    hist_stack.GetYaxis().SetTitleSize(hists[0].GetYaxis().GetTitleSize())    
    hist_stack.GetYaxis().SetTitleOffset(hists[0].GetYaxis().GetTitleOffset())    
    hist_stack.GetYaxis().SetTitle(
        hists[0].GetYaxis().GetTitle())
    hist_stack.GetHistogram().GetXaxis().SetTitle(
        hists[0].GetXaxis().GetTitle())
    hist_stack.GetHistogram().SetLabelSize(0.04)
    hist_stack.SetMinimum(hists[0].GetMinimum()*args.scaleymin)
    #if hist_stack.GetMaximum() < hists[0].GetMaximum():
    # Adding an arbirary factor of 100 here so the scaling doesn't cut off info from
    # Hists. Not applied when lumi < 1This should be fixed
    lumi = args.luminosity/100 if args.luminosity > 0 else 1
    hist_stack.SetMaximum(hists[0].GetMaximum()*args.scaleymax*lumi)
    #else:
    #    new_max = 1.1*hist_stack.GetMaximum() if not data_hist else \
    #            1.1*max(data_hist.GetMaximum(), hist_stack.GetMaximum()) 
    #    hist_stack.SetMaximum(new_max)
    if not args.no_errors:
        histErrors = getHistStatErrors(hist_stack, args.nostack)
        for error_hist in histErrors:
            error_hist.Draw("same e2")
    offset = ROOT.gPad.GetLeftMargin() - 0.04 if args.legend_left else \
        ROOT.gPad.GetRightMargin() - 0.04 
    width = .2 if "WZxsec" in args.selection else 0.33
    xcoords = [.10+offset, .1+width+offset] if args.legend_left \
        else [.92-width-offset, .92-offset]
    unique_entries = len(set([x.GetFillColor() for x in hists]))
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
    legend = getPrettyLegend(hist_stack, data_hist, coords)
    legend.Draw()
    if not args.no_ratio:
        canvas = plotter.splitCanvas(canvas, hist_stack.GetName(), 
                "" if not data_hist else data_hist.GetName(), 
                "Data / #Sigma MC" if data_hist else args.ratio_text,
                args.ratio_range
        )
    return canvas
def getHistStatErrors(hist_stack, separate):
    histErrors = []
    for hist in hist_stack.GetHists():
        error_hist = plotter.getHistStatErrors(hist)
        if separate:
            error_hist.SetFillColor(hist.GetLineColor())
            histErrors.append(error_hist)
        else:
            error_hist.SetFillColor(ROOT.kBlack)
            if len(histErrors) == 0:
                histErrors.append(error_hist)
            else:
                histErrors[0].Add(error_hist)
    return histErrors
def getPrettyLegend(hist_stack, data_hist, coords):
    hists = hist_stack.GetHists()
    legend = ROOT.TLegend(coords[0], coords[1], coords[2], coords[3])
    legend.SetFillColor(0)
    if data_hist:
        legend.AddEntry(data_hist, data_hist.GetTitle(), "lp")
    hist_names = []
    for hist in reversed(hists):
        if hist.GetTitle() not in hist_names:
            legend.AddEntry(hist, hist.GetTitle(), "f")
        hist_names.append(hist.GetTitle())
    return legend
def getHistFactory(config_factory, selection, filelist, luminosity=1):
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
        if "data" not in name:
            base_name = name.split("__")[0]
            metaTree = ROOT.TChain(metaTree_name)
            metaTree.Add(hist_factory[name]["file_path"])
            kfac = 1. if 'kfactor' not in mc_info[base_name].keys() else mc_info[base_name]['kfactor']
            weight_info = WeightInfo.WeightInfoProducer(metaTree, 
                    mc_info[base_name]['cross_section']*kfac,
                    sum_weights_branch).produce()
            histProducer = WeightedHistProducer.WeightedHistProducer(weight_info, weight_branch)  
            histProducer.setLumi(luminosity)
        else:
            histProducer = WeightedHistProducer.WeightedHistProducer(
                    WeightInfo.WeightInfo(1, 1,), "")  
        hist_factory[name].update({"histProducer" : histProducer})
    return hist_factory
def getConfigHist(config_factory, plot_group, selection, branch_name, channels,
    addOverflow, cut_string="", luminosity=1, no_scalefacs=False, scaleUncertainties=True):
    if "Gen" not in selection:
        states = [x.strip() for x in channels.split(",")]
        trees = ["%s/ntuple" % state for state in states]
    else:
        trees = ["analyze%s/Ntuple" % ("ZZ" if "ZZ" in selection else "WZ")]
    try:
        filelist = config_factory.getPlotGroupMembers(plot_group)
    except ValueError as e:
        logging.warning(e.message)
        logging.warning("Treating %s as file name" % plot_group)
        filelist = [plot_group]
    hist_info = getHistFactory(config_factory, selection, filelist, luminosity)
    bin_info = config_factory.getHistBinInfo(branch_name)
    hist_name = "_".join([plot_group, selection.replace("/", "_"), branch_name.split("_")[0]])
    hist = ROOT.gProof.GetOutputList().FindObject(hist_name)
    hist = ROOT.gProof.GetOutputList().FindObject(hist_name)
    if hist:
        hist.Delete()
    hist = ROOT.TH1D(hist_name, hist_name, bin_info['nbins'], bin_info['xmin'], bin_info['xmax'])
    scaleUp_hist = ROOT.TH1D(hist_name+"_scaleUp", hist_name, bin_info['nbins'], bin_info['xmin'], bin_info['xmax'])
    scaleDown_hist = ROOT.TH1D(hist_name+"_scaleDown", hist_name, bin_info['nbins'], bin_info['xmin'], bin_info['xmax'])
    log_info = ""
    for name, entry in hist_info.iteritems():
        producer = entry["histProducer"]
        if "weight" in entry.keys():
            producer.addWeight(entry["weight"])
        log_info += "\n" + "-"*70 +"\nName is %s entry is %s" % (name, entry)
        for tree in trees:
            state = tree.split("/")[0] if "ntuple" in tree else ""
            log_info += "\nFor state %s" % state
            config_factory.setProofAliases(state)
            cut_string = config_factory.hackInAliases(cut_string)
            if "WZxsec2016" in selection and not "data" in name and not no_scalefacs:
                scale_expr = getScaleFactorExpression(state, "medium", "tightW")
                weighted_cut_string = appendCut(cut_string, scale_expr)
            else:
                weighted_cut_string = cut_string
            producer.setCutString(weighted_cut_string)
            draw_expr = config_factory.getHistDrawExpr(branch_name, name, state)
            logging.debug("Draw expression was %s" % draw_expr)
            proof_name = "_".join([name, "%s#/%s" % (selection.replace("/", "_"), tree)])
            logging.debug("Proof path was %s" % proof_name)
            try:
                state_hist = producer.produce(draw_expr, proof_name, overflow=addOverflow)
                if scaleUncertainties and not "data" in name:
                    producer.setCutString(appendCut(weighted_cut_string,
                        getQCDScaleUpExpression(selection))
                    )
                    scaleUp_statehist = producer.produce(draw_expr, proof_name, overflow=addOverflow)
                    producer.setCutString(appendCut(weighted_cut_string,
                        getQCDScaleDownExpression(selection))
                    )
                    scaleDown_statehist = producer.produce(draw_expr, proof_name, overflow=addOverflow)
                    # Ignore scale uncertainties for samples without weights
                    if scaleUp_statehist.GetEntries() == 0:
                        scaleUp_statehist = state_statehist
                    if scaleDown_statehist.GetEntries() == 0:
                        scaleDown_statehist = state_statehist
                else:
                    scaleUp_statehist = state_hist
                    scaleDown_statehist = state_hist
                log_info += "\nNumber of events: %f" % state_hist.Integral()
                hist.Add(state_hist)
                scaleUp_hist.Add(scaleUp_statehist)
                scaleDown_hist.Add(scaleDown_statehist)
            except ValueError as error:
                logging.warning(error)
                log_info += "\nNumber of events: 0.0" 
        log_info += "total number of events: %f" % hist.Integral()
        config_factory.setHistAttributes(hist, branch_name, plot_group)
    for i in range(1, hist.GetNbinsX()+1):
        scaleUp_diff = abs(hist.GetBinContent(i)
                            - scaleUp_hist.GetBinContent(i))
        scaleDown_diff = abs(hist.GetBinContent(i)
                            - scaleDown_hist.GetBinContent(i))
        maxScaleErr = max(scaleUp_diff, scaleDown_diff)
        err = math.sqrt(hist.GetBinError(i)**2 + maxScaleErr**2)
        hist.SetBinError(i, err)
    config_factory.addErrorToHist(hist, plot_group)
    logging.debug(log_info)
    logging.debug("Hist has %i entries" % hist.GetEntries())
    return hist
def appendCut(cut_string, add_cut):
    if cut_string != "":
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
def getQCDScaleUpExpression(selection):
    if "WZxsec2016" in selection:
        return "maxScaleWeight/scaleWeights[0]"
    else:
        return "max(LHEweights)"
def getQCDScaleDownExpression(selection):
    if "WZxsec2016" in selection:
        return "minScaleWeight/scaleWeights[0]"
    else:
        return "min(LHEweights)"
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
def getPlotPaths(selection, folder_name, write_log_file):
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
def savePlot(canvas, plot_path, html_path, branch_name, write_log_file, args):
    if args.output_file != "":
        canvas.Print(args.output_file)
        return
    if write_log_file:
        log_file = "/".join([plot_path, "logs", "%s_event_info.log" % branch_name])
        shutil.move("temp.txt", log_file) 
    canvas.Print("/".join([plot_path, branch_name + ".root"]))
    canvas.Print("/".join([plot_path, branch_name + ".C"]))
    canvas.Print("/".join([plot_path, branch_name + ".pdf"]))
    if not args.no_html:
        makeDirectory(html_path)
        canvas.Print("/".join([html_path, branch_name + ".pdf"]))
        canvas.Print("/".join([html_path, branch_name + ".png"]))
        if write_log_file:
            makeDirectory("/".join([html_path, "logs"]))
            shutil.copy(log_file, log_file.replace(plot_path, html_path))
    del canvas
    ROOT.gROOT.Reset()
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
