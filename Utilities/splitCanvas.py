#Taken and modified from Nick Smith, U-Wisconsin
#https://github.com/nsmith-/ZHinvAnalysis/blob/master/splitCanvas.py
import ROOT

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

def splitCanvas(oldcanvas, histname1, histname2) :
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
    hist1 = stackPad.GetPrimitive(histname1)
    hist2 = stackPad.GetPrimitive(histname2)
    #stack = stackPad.GetPrimitive(name+'_hmcstack')
    ratio = hist1.Clone(name+'_ratio_hist')
    ratio.Divide(hist2)
    ratio.GetXaxis().SetTitle(stack.GetXaxis().GetTitle())
    ratio.GetYaxis().SetTitle('Data / #Sigma MC')
    ratio.GetYaxis().CenterTitle()
    ratio.GetYaxis().SetRangeUser(.4, 1.6)
    ratio.GetYaxis().SetNdivisions(305)
    ratio.GetYaxis().SetTitleSize(ratio.GetYaxis().GetTitleSize()*0.6)
    ratio.Draw()
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
    return canvas

