# Setup ScaleFactor objects to be "registered" with ROOT,
# allowing them to be called from TTree.Draw(), for example.
# Currently used for lepton scale factors and pileup weights.
#
# Modified from N. Smith, U. Wisconsin
# 

#!/usr/bin/env python
import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.PyConfig.IgnoreCommandLineOptions = True

ROOT.gROOT.LoadMacro("ScaleFactor.C+")

def float2double(hist):
    if hist.ClassName() == 'TH1F':
        new = ROOT.TH1D()
        hist.Copy(new)
    elif hist.ClassName() == 'TH2F':
        new = ROOT.TH2D()
        hist.Copy(new)
    else:
        raise Exception("Bad hist, dummy")
    return new

fScales = ROOT.TFile('scaleFactors.root', 'recreate')

#pileupSF = ROOT.ScaleFactor("pileupSF", "ICHEP 12.9/fb Pileup profile Scale Factor, x=NTruePU")
#pileupSF = ROOT.ScaleFactor("pileupSF", "Run2016G 7.1/fb Pileup profile Scale Factor, x=NTruePU")
#pileupFile = ROOT.TFile.Open('../../PileupWeights/PU_Central.root')
#pileupFileUp = ROOT.TFile.Open('../../PileupWeights/PU_minBiasUP.root')
#pileupFileDown = ROOT.TFile.Open('../../PileupWeights/PU_minBiasDOWN.root')
# TODO figure out how to make this file :)
#pileupSF = ROOT.ScaleFactor("pileupSF", "Run2016BCD nvtx PU Scale Factor, x=nVertices")
#pileupFile = ROOT.TFile.Open('../data/nvtxBCDreweight.root')
#pileupSF.Set1DHist(pileupFile.Get('nvtx'))
#fScales.cd()
#pileupSF.Write()

electronMedIdSF = ROOT.ScaleFactor("electronMedIdSF", "ICHEP Electron Medium WP ID SF, x=Eta, y=Pt")
eidFile = ROOT.TFile.Open('../data/ichepElectronMediumSF.root')
electronMedIdSF.Set2DHist(float2double(eidFile.Get('EGamma_SF2D')))
fScales.cd()
electronMedIdSF.Write()

electronGsfSF = ROOT.ScaleFactor("electronGsfSF", "ICHEP Electron GSF track reco SF, x=Eta, y=Pt")
eleGsfFile = ROOT.TFile.Open('../data/ichepElectronGsfSF.root')
electronGsfSF.Set2DHist(float2double(eleGsfFile.Get('EGamma_SF2D')))
fScales.cd()
electronGsfSF.Write()

muonTightIdSF = ROOT.ScaleFactor("muonTightIdSF", "ICHEP Muon Tight WP ID SF, x=Eta")
midFile = ROOT.TFile.Open('../data/MuonID_Z_RunBCD_prompt80X_7p65.root')
muonTightIdSF.Set1DHist(float2double(midFile.Get('MC_NUM_TightIDandIPCut_DEN_genTracks_PAR_eta/eta_ratio')))
fScales.cd()
muonTightIdSF.Write()

muonTightIsoSF = ROOT.ScaleFactor("muonTightIsoSF", "ICHEP Muon Tight Iso (0.15) WP ID SF, x=abs(Eta), y=Pt")
misoFile = ROOT.TFile.Open('../data/MuonIso_Z_RunBCD_prompt80X_7p65.root')
muonTightIsoSF.Set2DHist(float2double(misoFile.Get('MC_NUM_TightRelIso_DEN_TightID_PAR_pt_spliteta_bin1/abseta_pt_ratio')))
fScales.cd()
muonTightIsoSF.Write()
