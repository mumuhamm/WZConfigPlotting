import ROOT
import UserInput
import config_object

class ConfigHistFactory(object):
    def __init__(self, dataset_manager_path, dataset_name, fileset):
        self.manager_path = dataset_manager_path
        self.dataset_name = dataset_name
        self.info = UserInput.readJson('/'.join([self.manager_path, "FileInfo", 
            dataset_name, "%s.json" % fileset]))
        self.config = config_object.ConfigObject(self.info)
        self.file_info = UserInput.readJson('/'.join([self.manager_path, "FileInfo", "montecarlo.json"]))
        self.styles = UserInput.readJson('/'.join([self.manager_path, 
            "Styles", "styles.json"]))
        self.plot_groups = UserInput.readJson('/'.join([self.manager_path, 
            "PlotGroups", "%s.json" % dataset_name]))
        self.plot_objects = UserInput.readJson('/'.join([self.manager_path, 
            "PlotObjects", "%s.json" % dataset_name]))
        self.aliases = UserInput.readJson('/'.join([self.manager_path, 
            "Aliases", "%s.json" % dataset_name]))
    def getHistDrawExpr(self, object_name, dataset_name, channel):
        hist_name = '-'.join([dataset_name, channel, object_name])
        hist_info = self.plot_objects[object_name]['Initialize']
        draw_expr = '>>'.join([object_name, hist_name])
        draw_expr += "(%i,%f,%f)" % (hist_info['nbins'], hist_info['xmin'], hist_info['xmax'])
        return draw_expr
    def getHistBinInfo(self, object_name):
        bin_info = {}
        hist_info = self.plot_objects[object_name]['Initialize']
        for key in ['nbins', 'xmin', 'xmax']:
            bin_info.update({key : hist_info[key]})
        return bin_info
    def setProofAliases(self, channel):
        proof = ROOT.gProof
        proof.ClearInput()
        alias_list = []
        for name, value in self.aliases['State'][channel].iteritems():
            alias_list.append(name)
            proof.AddInput(ROOT.TNamed("alias:%s" % name, value))
        proof.AddInput(ROOT.TNamed("PROOF_ListOfAliases", ','.join(alias_list)))
    def setHistAttributes(self, hist, object_name, dataset_name):
        config = self.config
        info = self.info
        plot_group = self.plot_groups[info[dataset_name]['plot_group']]
        hist.SetTitle(plot_group['Name'])
        config.setAttributes(hist, self.styles[plot_group['Style']])
        config.setAttributes(hist, self.plot_objects[object_name]['Attributes'])
def main():
    test = ConfigHistFactory("/afs/cern.ch/user/k/kelong/work/AnalysisDatasetManager",
        "WZAnalysis", "Zselection")
    draw_expr = test.getHistDrawExpr("l1Pt", "wz3lnu-powheg", "eee")
    hist_name = draw_expr.split(">>")[1].split("(")[0]
    print "Draw expression was %s hist name is %s" % (draw_expr, hist_name)

if __name__ == "__main__":
    main()
