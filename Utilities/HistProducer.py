import ROOT
import WeightInfo

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
