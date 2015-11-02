import ROOT
import WeightInfo

class HistProducer(object):
    def __init__(self, weight_info, weight_branch):
        #self.histChain.SetProof(ROOT.gProof)
        self.event_weight = self.weight_info.getCrossSection()/self.weight_info.getSumOfWeights()
        self.lumi = 1/self.event_weight
    def setWeightBranch(self, weight_branch):
        self.weight_branch = weight_branch
    def getCrossSection(self):
        return self.weight_info.getCrossSection()
    def setLumi(self, lumi):
        self.lumi = lumi if lumi > 0 else 1/self.event_weight
    def produce(self, draw_expr, cut_string="", proof_path=""): 
        proof = ROOT.gProof
        cut_string = ''.join([self.weight_branch, "*(" + cut_string + ")" if cut_string != "" else ""])
        proof.DrawSelect(proof_path, draw_expr, cut_string, "goff")
        hist_name = draw_expr.split(">>")[1].split("(")[0]
        hist = proof.GetOutputList().FindObject(hist_name)
        print "The name is %s and the hist is" % hist_name
        print hist
        hist.Sumw2()
        hist.Scale(self.event_weight*self.lumi)
        return hist
class HistProducer(object):
    def __init__(self, chain, weight_branch):
        self.histChain = chain 
        self.weight_branch = weight_branch
    def setWeightBranch(self, weight_branch):
        self.weight_branch = weight_branch
    def loadHist(self, hist, branch_name, cut_string, append=False):
        hist.GetDirectory().cd() 
        hist_name = "".join(["+" if append else "", hist.GetName()])
        print "name is %s" % hist_name
        old_num = hist.GetEntries()
        num = self.histChain.Draw(branch_name + ">>" + hist_name, cut_string)
        print "this time %i pass" % num
        print "Draw Comand is %s" % branch_name + ">>" + hist_name
        print "With cut string %s" % cut_string
        if append:
            if num < old_num:
                print "Failed to append to hist"
        print hist.GetEntries()
        return num
    def produce(self, hist, branch_name, cut_string="", append=False): 
        if not hist.GetSumw2N():
            hist.Sumw2()
        weight_cut_string = "" # = ''.join([self.weight_branch, 
        #        "*(" + cut_string + ")" if self.weight_branch != "" else ""]),
        #if self.weight_branch == "":
        #    weight_cut_string = weight_cut_string.lstrip("*(").rstrip(")")
        self.loadHist(hist,
            branch_name,
            ''.join(weight_cut_string),
            append
        )
