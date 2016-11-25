import ROOT
class ScaleFactorsHelper(object):
    def __init__(self, scale_file):
        ROOT.gROOT.LoadMacro("ScaleFactors/ScaleFactor.C+")
        self.scale_file = ROOT.TFile(scale_file)
        print self.scale_file
        print self.scale_file.ls()
    def registerElectronCBVIDs(self):
        electronTightIdSF = self.scale_file.Get('electronTightIdSF')
        print electronTightIdSF
        electronTightIdSF.RegisterGlobalFunction(2) # 2D function
    def registerMuonPOGIDs(self):
        muonIsoSF = self.scale_file.Get('muonTightIsoSF')
        muonIsoSF.RegisterGlobalFunction(2) # 2D function
        muonIdSF = self.scale_file.Get('muonTightIdSF')
        muonIdSF.RegisterGlobalFunction(2) # 2D function
    def registerPilupSFs(self):
        pileupSF = self.scale_file.Get('pileupSF')
        pileupSF.RegisterGlobalFunction(1) # 1D function
    def registerAllSFs(self):
        self.registerElectronCBVIDs()
        self.registerMuonPOGIDs()
        self.registerPilupSFs()
    @staticmethod
    def getScaleFactorExpression(self, state, muonId="tight", electronId="tight"):
        if muonId != "tight" and electronId != "tight":
            return "1"
        if state == "eem":
            return "electronTightIdSF(abs(e1Eta), e1Pt)*" \
                    "electronTightIdSF(abs(e2Eta), e2Pt)*" \
                    "muonTightIsoSF(abs(mEta), mPt)*" \
                    "muonTightIdSF(abs(mEta), mPt)*" \
                    "pileupSF(nvtx)"
        elif state == "emm":
            return "electronTightIdSF(abs(eEta), ePt)*" \
                    "muonTightIsoSF(abs(m1Eta), m1Pt)*" \
                    "muonTightIdSF(abs(m1Eta), m1Pt)*" \
                    "muonTightIsoSF(abs(m2Eta), m2Pt)*" \
                    "muonTightIdSF(abs(m2Eta), m2Pt)*" \
                    "pileupSF(nvtx)"
        elif state == "mmm":
            return "muonTightIsoSF(abs(m1Eta), m1Pt)*" \
                    "muonTightIdSF(abs(m1Eta), m1Pt)*" \
                    "muonTightIsoSF(abs(m2Eta), m2Pt)*" \
                    "muonTightIdSF(abs(m2Eta), m2Pt)*" \
                    "muonTightIsoSF(abs(m3Eta), m3Pt)*" \
                    "muonTightIdSF(abs(m3Eta), m3Pt)*" \
                    "pileupSF(nvtx)"
