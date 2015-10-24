import ROOT
import WeightInfo

class WeightedHistProducer(object):
    def __init__(self, weight_info, weight_branch):
        #self.histChain.SetProof(ROOT.gProof)
        self.weight_info = weight_info 
        self.weight_branch = weight_branch
        self.event_weight = self.weight_info.getCrossSection()/self.weight_info.getSumOfWeights()
        self.lumi = 1/self.event_weight
    def setWeightBranch(self, weight_branch):
        self.weight_branch = weight_branch
    def getCrossSection(self):
        return self.weight_info.getCrossSection()
    def setLumi(self, lumi):
        self.lumi = lumi if lumi > 0 else 1/self.event_weight
    def produce(self, hist, branch_name, cut_string="", proof_path=""): 
        proof = ROOT.gProof
        print hist
        hist_name = hist.GetName()
        hist_exp = "%s(%i, %i, %i)" % (hist.GetName(), hist.GetSize() - 2, hist.GetXaxis().GetXmin(), hist.GetXaxis().GetXmax())
        print hist_exp
        cut_string = ''.join([self.weight_branch, "*(" + cut_string + ")" if cut_string != "" else ""])
        proof.DrawSelect(proof_path, ">>".join([branch_name, hist_exp]), cut_string, "goff")
        hist = proof.GetOutputList().FindObject(hist_name)
        print hist
        hist.Sumw2()
        hist.Scale(self.event_weight*self.lumi)
        return hist
# For testing
def main():
    root_file = ROOT.TFile("/afs/cern.ch/user/k/kelong/work/DibosonMCAnalysis/ZZTo4LNu0j_5f_NLO_FXFX/MG5aMCatNLO_ZZTo4LNu0j_muMass_pythia8_TuneCUETP8M1_Ntuple.root")
    metaTree = root_file.Get("analyzeZZ/MetaData")
    weight_info = WeightInfo.WeightInfoProducer(metaTree, "inputXSection", "inputSumWeights").produce()

    ntuple =root_file.Get("analyzeZZ/Ntuple")
    histProducer = WeightedHistProducer(ntuple, weight_info, "weight")  
    
    canvas = ROOT.TCanvas("canvas", "canvas", 600, 800)
    hist = ROOT.TH1F("hist", "hist", 60, 60, 120)
    histProducer.produce(hist, "Z1mass", "", 1000)
    hist.Draw("hist")
    canvas.Print("test1.pdf")
    
    histProducer.produce(hist, "Z1mass", "Z1mass < 120 && Z1mass > 60")
    hist.Draw("hist")
    canvas.Print("test2.pdf")

    histProducer.produce(hist, "Z1mass", "Z1mass < 100")
    hist.Draw("hist")
    canvas.Print("test3.pdf")
if __name__ == "__main__":
    main()
