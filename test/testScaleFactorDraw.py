#!/usr/bin/env python
import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.PyConfig.IgnoreCommandLineOptions = True

ROOT.gROOT.LoadMacro("../ScaleFactors/ScaleFactor.C+")

chain = ROOT.TChain("eem/ntuple")
chain.Add("data/preselectionWZ_MCtest.root")

canvas = ROOT.TCanvas("canvas", "canvas")

fScales = ROOT.TFile('../ScaleFactors/scaleFactors.root')
muonIsoSF = fScales.Get('muonTightIsoSF')
muonIsoSF.RegisterGlobalFunction(2) # 2D function
muonIdSF = fScales.Get('muonTightIdSF')
muonIdSF.RegisterGlobalFunction(2) # 2D function
mpt_noscalefac= ROOT.TH1F("mpt_noscalefac","mpt_noscalefac", 10, 0, 200)
chain.Draw("mPt>>mpt_noscalefac")
mpt_noscalefac.SetLineColor(ROOT.kRed)

mpt_scalefac= ROOT.TH1F("mpt_scalefac","mpt_scalefac", 10, 0, 200)
chain.Draw("mPt>>mpt_scalefac", "muonTightIsoSF(abs(mEta), mPt)*muonTightIdSF(abs(mEta), mPt)")
mpt_scalefac.SetLineColor(ROOT.kBlue)
mpt_noscalefac.Draw()
mpt_scalefac.Draw("same e0")

canvas.Print("testMuonScaleFacs.pdf")
