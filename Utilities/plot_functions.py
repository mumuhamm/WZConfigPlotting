import ROOT
import glob
import os
import logging
import re
from IPython import embed

def getHistFromFile(root_file, name_in_file, rename, path_to_hist):
    if not root_file:
        print 'Failed to open %s' % file
        exit(0)
    hist = ROOT.TH1D()   
    if path_to_hist != "":
        name_in_file = path_to_hist.join(["/", name_in_file]) 
    hist = root_file.Get(name_in_file)
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
# https://gitlab.cern.ch/ncsmith/monoZ/blob/master/plotter/plotting/splitCanvas.py
def splitCanvas(oldcanvas, dimensions, ratio_text, ratio_range):
    stacks = filter(lambda p: type(p) is ROOT.THStack and "signal" not in p.GetName(), oldcanvas.GetListOfPrimitives())
    signal_stacks = filter(lambda p: type(p) is ROOT.THStack and "signal" in p.GetName(), oldcanvas.GetListOfPrimitives())
    data_list = filter(lambda p: type(p) is ROOT.TH1D and 'data' in p.GetName().lower(), oldcanvas.GetListOfPrimitives())
    compareData = True
    stack_hists = [i for s in stacks for i in s.GetHists()]
    signal_hists = [i for s in signal_stacks for i in s.GetHists()]
    if len(data_list) == 0:
        compareData = False
    elif len(stack_hists) < 2:
        print "Can't form ratio from < 2 histograms"
        return oldcanvas
    name = oldcanvas.GetName()
    canvas = ROOT.TCanvas(name+'__new', name, *dimensions)
    ratioPad = ROOT.TPad('ratioPad', 'ratioPad', 0., 0., 1., .3)
    ratioPad.Draw()
    stackPad = ROOT.TPad('stackPad', 'stackPad', 0., 0.3, 1., 1.)
    stackPad.Draw()
    stackPad.cd()
    oldcanvas.DrawClonePad()
    del oldcanvas
    oldBottomMargin = stackPad.GetBottomMargin()
    stackPad.SetBottomMargin(0.)
    stackPad.SetTopMargin(stackPad.GetTopMargin()/0.7)
    canvas.SetName(name)
    ratioPad.cd()
    ratioPad.SetBottomMargin(oldBottomMargin/.3)
    ratioPad.SetTopMargin(0.)
    ratioHists = data_list if compareData else (stack_hists+signal_hists)[1:]
    ratioHists = [h.Clone(h.GetName()+"_ratioHist") for h in ratioHists]
    centralRatioHist = stack_hists[0].Clone(name+'_central_ratioHist')
    if compareData:
        if len(stack_hists) > 1:
            map(centralRatioHist.Add, stack_hists[1:])
    centralRatioHist.SetFillColor(ROOT.TColor.GetColor("#e4e5e5"))
    centralRatioHist.SetMarkerSize(0)
    for ratioHist in ratioHists:
        ratioHist.Divide(centralRatioHist)
        for i in range(ratioHist.GetNbinsX()+2):
            ratioHist.SetBinError(i, ratioHist.GetBinError(i)/max(ratioHist.GetBinContent(i), 1))
    for i in range(centralRatioHist.GetNbinsX()+2):
        centralRatioHist.SetBinError(i, centralRatioHist.GetBinError(i)/max(centralRatioHist.GetBinContent(i), 1))
        centralRatioHist.SetBinContent(i, 1.)
    stack_hists[0].GetXaxis().Copy(centralRatioHist.GetXaxis())
    stack_hists[0].GetXaxis().Copy(centralRatioHist.GetXaxis())
    if len(signal_stacks) > 0:
        signal_stacks[0].GetXaxis().Copy(centralRatioHist.GetXaxis())
        signal_stacks[0].GetXaxis().Copy(centralRatioHist.GetXaxis())
    centralRatioHist.GetYaxis().SetTitle(ratio_text)
    centralRatioHist.GetYaxis().CenterTitle()
    centralRatioHist.GetYaxis().SetRangeUser(*ratio_range)
    centralRatioHist.GetYaxis().SetNdivisions(003)
    centralRatioHist.GetYaxis().SetTitleSize(centralRatioHist.GetYaxis().GetTitleSize()*0.8)
    centralRatioHist.GetYaxis().SetLabelSize(centralRatioHist.GetYaxis().GetLabelSize()*0.8)
    centralRatioHist.Draw("E2")
    for ratioHist in ratioHists:
        ratioHist.Draw("same")
    stacks = filter(lambda p: type(p) is ROOT.THStack, stackPad.GetListOfPrimitives())
    for stack in stacks:
        stack.GetXaxis().SetTitle("")
        stack.GetXaxis().SetLabelOffset(999)
    xaxis = ratioHists[0].GetXaxis()
    line = ROOT.TLine(xaxis.GetBinLowEdge(xaxis.GetFirst()), 1, xaxis.GetBinUpEdge(xaxis.GetLast()), 1)
    line.SetLineStyle(ROOT.kDotted)
    line.Draw()
    recursePrimitives(stackPad, fixFontSize, 1/0.7)
    stackPad.Modified()
    recursePrimitives(ratioPad, fixFontSize, 1/0.3)
    if "unrolled" in name:
        centralRatioHist.GetXaxis().SetLabelSize(0.175)
        centralRatioHist.GetXaxis().SetLabelOffset(0.03)
        centralRatioHist.GetXaxis().SetTitleOffset(1.25)
    ratioPad.Modified()
    canvas.Update()
    ROOT.SetOwnership(stackPad, False)
    # stackPad already owns primitives
    ROOT.SetOwnership(ratioPad, False)
    for obj in ratioPad.GetListOfPrimitives():
        ROOT.SetOwnership(obj, False)
    ratioPad.GetListOfPrimitives().SetOwner(True)
    canvas.cd()
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
