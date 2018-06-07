import ROOT
from HistProducer import HistProducer
import logging
from IPython import embed

class WeightedHistProducer(HistProducer):
    def __init__(self, weight_info, weight_branch=""):
        super(WeightedHistProducer, self).__init__(weight_info)
        self.event_weight = self.weight_info.getCrossSection()/self.weight_info.getSumOfWeights() \
            if self.weight_info.getSumOfWeights() > 0 else 0
        self.cut_string = ""
        self.weight_branch = weight_branch

    def setWeightBranch(self, weight_branch):
        self.weight_branch = weight_branch
    
    def setCutString(self, cut_string):
        self.cut_string = cut_string

    def addWeight(self, weight):
        append_cut = lambda x: "*(%s)" % x if x not in ["", None] else x
        if self.weight_branch not in ["", None]:
            self.weight_branch += append_cut(weight)
        else:
            self.weight_branch = weight

    def produce(self, draw_expr, proof_path="", overflow=False, cut_string=""): 
        proof = ROOT.gProof
        print "PROOF PATH IS", proof_path
        if cut_string == "":
            cut_string = self.cut_string
        append_cut = lambda x: "*(%s)" % x if x != "" else x
        weight_string = "*".join([str(self.event_weight), str(self.lumi)] +
            ([self.weight_branch] if self.weight_branch != "" else []))
        draw_cut = weight_string + append_cut(cut_string)
        logging.debug("Draw cut is %s" % draw_cut)
        logging.debug("Draw expression is %s" % draw_expr)
        logging.debug("Proof path is %s" % proof_path)
        proof.DrawSelect(proof_path, draw_expr, draw_cut, "goff", -1)
        hist_name = draw_expr.split(">>")[1].split("(")[0]
        hist = proof.GetOutputList().FindObject(hist_name)
        ROOT.SetOwnership(hist,False)
        #embed()
        if not hist:
            raise ValueError('\n'.join(["Empty histogram produced!",
                "\tProof path was %s:" % proof_path,
                "\tDraw expression was: %s" % draw_expr,
                "\tCut string was: %s" % cut_string,
                "\tWeight string was: %s" % weight_string]))
        if not hist.GetSumw2(): hist.Sumw2()
        if overflow:
            # Returns num bins + overflow + underflow
            num_bins = hist.GetSize() - 2
            add_overflow = hist.GetBinContent(num_bins) + hist.GetBinContent(num_bins + 1)
            hist.SetBinContent(num_bins, add_overflow)
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
