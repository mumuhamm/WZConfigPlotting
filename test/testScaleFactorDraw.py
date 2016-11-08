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
pileupSF = fScales.Get('pileupSF')
pileupSF.RegisterGlobalFunction(1) # 1D function

mpt_noscalefac= ROOT.TH1F("mpt_noscalefac","mpt_noscalefac", 10, 0, 200)
chain.Draw("mPt>>mpt_noscalefac", "mIsTightMuon")
mpt_noscalefac.SetLineColor(ROOT.kRed)

mpt_allscalefacs= ROOT.TH1F("mpt_allscalefacs","mpt_allscalefacs", 10, 0, 200)
chain.Draw("mPt>>mpt_allscalefacs", "mIsTightMuon*muonTightIsoSF(abs(mEta), mPt)*muonTightIdSF(abs(mEta), mPt)*pileupSF(nvtx)")
mpt_allscalefacs.SetLineColor(ROOT.kBlue)

mpt_pileupscalefacs= ROOT.TH1F("mpt_pileupscalefacs","mpt_pileupscalefacs", 10, 0, 200)
chain.Draw("mPt>>mpt_pileupscalefacs", "mIsTightMuon*pileupSF(nvtx)")
mpt_pileupscalefacs.SetLineColor(ROOT.kGray)

mpt_isoscalefacs= ROOT.TH1F("mpt_isoscalefacs","mpt_isoscalefacs", 10, 0, 200)
chain.Draw("mPt>>mpt_isoscalefacs", "mIsTightMuon*muonTightIsoSF(abs(mEta), mPt)")
mpt_isoscalefacs.SetLineColor(ROOT.kOrange)

mpt_idscalefacs= ROOT.TH1F("mpt_idscalefacs","mpt_idscalefacs", 10, 0, 200)
chain.Draw("mPt>>mpt_idscalefacs", "mIsTightMuon*muonTightIdSF(abs(mEta), mPt)")
mpt_idscalefacs.SetLineColor(ROOT.kGreen)

mpt_noscalefac.Draw()
mpt_allscalefacs.Draw("same e0")
mpt_pileupscalefacs.Draw("same hist")
mpt_isoscalefacs.Draw("same hist")
mpt_idscalefacs.Draw("same hist")

legend = ROOT.TLegend(0.6,0.6,0.9,0.9) 
legend.SetFillColor(0)
legend.AddEntry("mpt_noscalefac", "No Scale Factors", "l")
legend.AddEntry("mpt_idscalefacs", "Tight ID Scale Factors", "l")
legend.AddEntry("mpt_isoscalefacs", "Tight Iso Scale Factors", "l")
legend.AddEntry("mpt_pileupscalefacs", "Pileup Scale Factors", "l")
legend.AddEntry("mpt_allscalefacs", "All Scale Factors", "l")
legend.Draw()

mpt_noscalefac.GetXaxis().SetTitle("Muon p_{T} [GeV] (eem state)")
mpt_noscalefac.GetYaxis().SetTitle("Preselection events in WZ MC file")

canvas.Print("~/www/ScaleFacTests/testMuonScaleFacs.pdf")

canvas = ROOT.TCanvas("ecanvas", "ecanvas")

electronTightIdSF = fScales.Get('electronTightIdSF')
electronTightIdSF.RegisterGlobalFunction(2) # 2D function

ept_noscalefac= ROOT.TH1F("ept_noscalefac","ept_noscalefac", 10, 0, 200)
chain.Draw("e1Pt>>ept_noscalefac", "e1IsCBVIDtight")
ept_noscalefac.SetLineColor(ROOT.kRed)

ept_pileupscalefacs = ROOT.TH1F("ept_pileupscalefacs","ept_pileupscalefac", 10, 0, 200)
chain.Draw("e1Pt>>ept_pileupscalefacs", "e1IsCBVIDtight*pileupSF(nvtx)")
ept_pileupscalefacs.SetLineColor(ROOT.kGray)

ept_idscalefacs = ROOT.TH1F("ept_idscalefacs","ept_idscalefacs", 10, 0, 200)
chain.Draw("e1Pt>>ept_idscalefacs", "e1IsCBVIDtight*electronTightIdSF(abs(e1Eta), e1Pt)")
ept_idscalefacs.SetLineColor(ROOT.kGreen)

ept_allscalefacs = ROOT.TH1F("ept_allscalefacs","ept_allscalefacs", 10, 0, 200)
chain.Draw("e1Pt>>ept_allscalefacs", "e1IsCBVIDtight*electronTightIdSF(abs(e1Eta), e1Pt)*pileupSF(nvtx)")
ept_allscalefacs.SetLineColor(ROOT.kBlue)

ept_noscalefac.Draw("hist")
ept_noscalefac.GetXaxis().SetTitle("Electron 1 p_{T} [GeV] (eem state)")
ept_noscalefac.GetYaxis().SetTitle("Preselection events in WZ MC file")
ept_pileupscalefacs.Draw("same hist")
ept_idscalefacs.Draw("same hist")
ept_allscalefacs.Draw("same hist")

legend = ROOT.TLegend(0.6,0.6,0.9,0.9) 
legend.SetFillColor(0)
legend.AddEntry("ept_noscalefac", "No Scale Factors", "l")
legend.AddEntry("ept_idscalefacs", "Tight ID Scale Factors", "l")
legend.AddEntry("ept_pileupscalefacs", "Pileup Scale Factors", "l")
legend.AddEntry("ept_allscalefacs", "All Scale Factors", "l")
legend.Draw()

canvas.Print("~/www/ScaleFacTests/testElectronScaleFacs.pdf")
