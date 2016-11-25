#!/usr/bin/env python
import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.PyConfig.IgnoreCommandLineOptions = True

ROOT.gROOT.LoadMacro("ScaleFactor.C+")
ROOT.TProof.Open('workers=6')
proof = ROOT.gProof

canvas = ROOT.TCanvas("canvas", "canvas")

#proof_path="wz3lnu-mg5amcnlo-WZxsec2016-FinalSelection#/emm/ntuple"
#draw_expr="ePt>>wz3lnu-mg5amcnlo_emm_ePt(20,0.000000,200.000000)"
#draw_cut="1.42441303156e-07*12900.0*genWeight"
#proof.DrawSelect(proof_path, draw_expr, draw_cut, "goff")
#hist_name = draw_expr.split(">>")[1].split("(")[0]
#hist = proof.GetOutputList().FindObject(hist_name)
#hist.Draw("hist")
#canvas.Print("~/www/ScaleFacTests/testElectronScaleFacsNoProof.pdf")
#
ROOT.gProof.Load("ScaleFactor.C+")
#ROOT.gProof.Exec("gSystem->Load(\"../ScaleFactors/ScaleFactors_C.so\"")
fScales = ROOT.TFile('../ScaleFactors/scaleFactors.root')
pileupSF = fScales.Get('pileupSF')
#pileupSF.SetName('pileupSF')
#pileupSF.RegisterGlobalFunction(1) # 1D function

#proof.AddInput(pileupSF)
#'gROOT->GetInterpreter()->Declare("double pileupSF(double x) { return 1;}");')
#proof.GetInputList().FindObject("pileupSF").RegisterGlobalFunction(1)
proof_path="wz3lnu-mg5amcnlo-WZxsec2016-FinalSelection#/emm/ntuple"
draw_expr="ePt>>wz3lnu-mg5amcnlo_emm_ePt(20,0.000000,200.000000)"
draw_cut="1.42441303156e-07*12900.0*genWeight*pileupSF(nvtx)"

proof.DrawSelect(proof_path, draw_expr, draw_cut, "goff")
hist_name = draw_expr.split(">>")[1].split("(")[0]
pileup_hist = proof.GetOutputList().FindObject(hist_name)
pileup_hist.Draw("hist")
canvas.Print("~/www/ScaleFacTests/testElectronScaleFacsPileupProof.pdf")
