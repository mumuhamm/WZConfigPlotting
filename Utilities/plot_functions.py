import ROOT
import glob
import os
import logging
import re

def getHistFromFile(root_file, name_in_file, rename, path_to_hist):
    if not root_file:
        print 'Failed to open %s' % file
        exit(0)
    hist = ROOT.TH1D()   
    if path_to_hist != "":
        name_in_file = path_to_hist.join(["/", name_in_file]) 
    hist = root_file.Get(name_in_file)
    print hist
    if not hist:
        print 'Failed to get hist %s from file' % name_in_file
        exit(0)
    hist.SetDirectory(ROOT.gROOT) # detach "hist" from the file
    if rename != "":
        hist.SetName(rename)
    return hist
def loadHistFromChain(hist, file_list, path_to_tree, branch_name,
                     cut_string, max_entries, append=False):
    tree = ROOT.TChain(path_to_tree)
    for file_name in file_list:
        tree.Add(file_name)
    loadHist(hist, tree, branch_name, cut_string, max_entries, append)
def loadHistFromTree(hist, root_file, path_to_tree, branch_name, 
                     cut_string, max_entries, append=False):
    if not root_file:
        print 'Failed to open %s' % root_file
        exit(0)
    tree = root_file.Get(path_to_tree)
    loadHist(hist, tree, branch_name, cut_string, max_entries, append)
def loadHist(hist, tree, branch_name, cut_string, max_entries, append=False):
    if not tree:
        print 'Failed to get tree from file'
        exit(0)
    hist.GetDirectory().cd() 
    hist_name = "".join(["+ " if append else "", hist.GetName()])
    print "name is %s" % hist_name
    old_num = hist.GetEntries()
    num = tree.Draw(branch_name + ">>" + hist_name, 
            cut_string,
            "",
            max_entries if max_entries > 0 else 1000000000)
    print "Draw Comand is %s" % branch_name + ">>" + hist_name
    print "With cut string %s" % cut_string
    if append:
        if num < old_num:
            print "Failed to append to hist"
    #else:
    #    hist.SetDirectory(ROOT.gROOT) # detach "hist" from the file
    print hist.GetEntries()
    return num
# Modified from Nick Smith, U-Wisconsin
# https://github.com/nsmith-/ZHinvAnalysis/blob/master/splitCanvas.py
def splitCanvas(oldcanvas, stack_name, data_name, ratio_text, ratio_range):
    name = oldcanvas.GetName()

    canvas = ROOT.TCanvas(name+'__new', name)
    ratioPad = ROOT.TPad(name+'_ratioPad', 'ratioPad', 0., 0., 1., .3)
    ratioPad.Draw()
    stackPad = ROOT.TPad(name+'_stackPad', 'stackPad', 0., 0.3, 1., 1.)
    stackPad.Draw()

    stackPad.cd()
    oldcanvas.DrawClonePad()
    del oldcanvas
    oldBottomMargin = stackPad.GetBottomMargin()
    stackPad.SetBottomMargin(0.)
    canvas.SetName(name)

    ratioPad.cd()
    ratioPad.SetBottomMargin(oldBottomMargin/.3)
    ratioPad.SetTopMargin(0.)
    
    hist_stack = stackPad.GetPrimitive(stack_name)
    hists = hist_stack.GetHists()
    
    hist1 = hists[0].Clone()
    hist2 = stackPad.GetPrimitive(data_name).Clone()
    compare_data = False
    if not isinstance(hist2, ROOT.TH1):
        if len(hists) < 2 and not compare_data:
            logging.warning("Cannot form ratio from < 2 hists in stack.")
            return canvas
        hist2 = hists[1]
    else:
        compare_data = True
        for hist in hists[1:]:
            hist1.Add(hist)
        if not hist2:
            logging.warning("No data hist found. Cannot form ratio")
            return canvas
    ratio = hist2.Clone(name+'_ratio_hist')
    ratio.SetLineColor(ROOT.kBlack)
    ratio.SetLineStyle(1)
    ratio.SetLineWidth(2)
    ratio.Divide(hist1)
    if compare_data:
        ratio.Draw("e1")
    else:
        ratio.Draw()
    if "cutflow" in stack_name:
        for i in range(ratio.GetXaxis().GetNbins()) :
            ratio.GetXaxis().SetBinLabel(i+1, hist_stack.GetXaxis().GetBinLabel(i+1))
        ratio.GetXaxis().SetLabelOffset(0.025)
        ratioPad.SetRightMargin(stackPad.GetRightMargin())
    ratio.GetXaxis().SetTitle(hist_stack.GetXaxis().GetTitle())
    hist_stack.GetXaxis().SetTitle("")
    hist_stack.GetXaxis().SetLabelOffset(999)
    
    ratio.GetYaxis().SetTitle(ratio_text)
    ratio.GetYaxis().SetTitleOffset(1.4)
    ratio.GetYaxis().CenterTitle()
    ratio.GetYaxis().SetRangeUser(float(ratio_range[0]), float(ratio_range[1]))
    ratio.GetYaxis().SetNdivisions(305)
    ratio.GetYaxis().SetTitleSize(ratio.GetYaxis().GetTitleSize()*0.6)
    ratio.GetXaxis().SetTitleSize(ratio.GetXaxis().GetTitleSize()*0.8)
    line = ROOT.TLine(ratio.GetBinLowEdge(1), 1, ratio.GetBinLowEdge(ratio.GetNbinsX()+1), 1)
    line.SetLineStyle(ROOT.kDotted)
    line.Draw()

    recursePrimitives(stackPad, fixFontSize, 1/0.7)
    stackPad.Modified()
    recursePrimitives(ratioPad, fixFontSize, 1/0.3)
    ratioPad.Modified()
    canvas.Update()

    for item in [stackPad, ratioPad, ratio, line] :
        ROOT.SetOwnership(item, False)
    canvas.GetListOfPrimitives().SetOwner(True)
    return canvas
# Also from Nick Smith
def recursePrimitives(tobject, function, *fargs) :
    function(tobject, *fargs)
    if hasattr(tobject, 'GetListOfPrimitives') :
        primitives = tobject.GetListOfPrimitives()
        if primitives :
            for item in primitives :
                recursePrimitives(item, function, *fargs)
    other_children = ['Xaxis', 'Yaxis', 'Zaxis']
    for child in other_children :
        if hasattr(tobject, 'Get'+child) :
            childCall = getattr(tobject, 'Get'+child)
            recursePrimitives(childCall(), function, *fargs)
def fixFontSize(item, scale) :
    if 'TH' in item.ClassName() :
        return
    if item.GetName() == 'yaxis' :
        item.SetTitleOffset(item.GetTitleOffset()/scale)
    sizeFunctions = ['LabelSize', 'TextSize', 'TitleSize']
    for fun in sizeFunctions :
        if hasattr(item, 'Set'+fun) :
            getattr(item, 'Set'+fun)(getattr(item, 'Get'+fun)()*scale)

def readStyle(canvas) :
    style = ROOT.TStyle(canvas.GetName()+"_style", "Read style")
    style.cd()
    style.SetIsReading()
    canvas.UseCurrentStyle()
    style.SetIsReading(False)
    return style
def getHistErrors(hist):
    histErrors = hist.Clone()
    histErrors.SetName(hist.GetName() + "_errors")
    histErrors.SetDirectory(0)
    if not histErrors.GetSumw2(): histErrors.Sumw2()
    histErrors.SetFillStyle(3013)
    histErrors.SetMarkerSize(0) 
    return histErrors
