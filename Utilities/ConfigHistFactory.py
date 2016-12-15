import ROOT
import math
import UserInput
import config_object
import logging
import os
import glob

class ConfigHistFactory(object):
    def __init__(self, dataset_manager_path, dataset_name, object_restrict=""):
        self.manager_path = dataset_manager_path
        self.dataset_name = dataset_name
        self.info = self.readAllInSet("FileInfo", self.dataset_name)
        self.config = config_object.ConfigObject(self.info)
        self.mc_info = UserInput.readAllJson('/'.join([self.manager_path, "FileInfo", "montecarlo/*.json"]))
        self.data_info = UserInput.readAllJson('/'.join([self.manager_path, "FileInfo", "data/*.json"]))
        self.styles = UserInput.readJson('/'.join([self.manager_path, 
            "Styles", "styles.json"]))
        base_name = self.dataset_name.split("/")[0]
        self.plot_groups = self.readAllInSet("PlotGroups", base_name)
        object_file = '/'.join([self.manager_path,  "PlotObjects", 
            ("_".join([self.dataset_name, object_restrict])
                if object_restrict != "" else self.dataset_name) + ".json"])
        self.aliases = UserInput.readJson('/'.join([self.manager_path, 
            "Aliases", "%s.json" % base_name]))
        # Objects can be defined by the default dataset-wide file, 
        # or by specific selection files
        print "THE PLOT OBJECT FILE IS %s " % object_file
        if not os.path.isfile(object_file): object_file = object_file.replace(
                 self.dataset_name, base_name)
        print "THE PLOT OBJECT FILE IS %s " % object_file
        self.plot_objects = UserInput.readJson(object_file)
    def readAllInSet(self, object_type, base_name):
        info = {}
        for file_name in glob.glob('/'.join([self.manager_path, 
            object_type, "%s*.json" % base_name])):
            info.update(UserInput.readJson(file_name))
        return info
    def getHistDrawExpr(self, object_name, dataset_name, channel):
        hist_name = '_'.join([x for x in [dataset_name, channel, object_name] 
            if x != ""])
        object_name = object_name if object_name in self.plot_objects else object_name.split("_")[0]
        hist_info = self.plot_objects[object_name]['Initialize']
        draw_expr = '>>'.join([object_name, hist_name])
        draw_expr += "(%i,%f,%f)" % (hist_info['nbins'], hist_info['xmin'], hist_info['xmax'])
        return draw_expr
    def getHistBinInfo(self, object_name):
        bin_info = {}
        object_name = object_name if object_name in self.plot_objects else object_name.split("_")[0]
        hist_info = self.plot_objects[object_name]['Initialize']
        for key in ['nbins', 'xmin', 'xmax']:
            bin_info.update({key : hist_info[key]})
        return bin_info
    def setProofAliases(self, channel):
        proof = ROOT.gProof
        proof.ClearInput()
        alias_list = []
        if channel != "":
            for name, value in self.aliases['State'][channel].iteritems():
                alias_list.append(name)
                proof.AddInput(ROOT.TNamed("alias:%s" % name, value))
        for name, value in self.aliases['Event'].iteritems():
            alias_list.append(name)
            proof.AddInput(ROOT.TNamed("alias:%s" % name, value))
        proof.AddInput(ROOT.TNamed("PROOF_ListOfAliases", ','.join(alias_list)))
    def hackInAliases(self, expr, channel=""):
        if channel != "":
            for name, value in self.aliases['State'][channel].iteritems():
                expr = expr.replace(name, value)
        for name, value in self.aliases['Event'].iteritems():
            expr = expr.replace(name, value)
        print "With aliases it's: %s" % expr
        return expr
    def setHistAttributes(self, hist, object_name, plot_group):
        config = self.config
        info = self.info
        # If not a valid plot group, try treating it as file entry
        plot_group = self.plot_groups[info[plot_group]['plot_group']] \
                if plot_group not in self.plot_groups.keys() else self.plot_groups[plot_group]
        hist.SetTitle(plot_group['Name'])
        config.setAttributes(hist, self.styles[plot_group['Style']])
        object_name = object_name if object_name in self.plot_objects else object_name.split("_")[0]
        config.setAttributes(hist, self.plot_objects[object_name]['Attributes'])
    def addErrorToHist(self, hist, plot_group_name):
        # If not a valid plot group, try treating it as file entry
        plot_group = self.plot_groups[self.info[plot_group_name]['plot_group']] \
                if plot_group_name not in self.plot_groups.keys() else self.plot_groups[plot_group_name]
        if "add_perc_error" in plot_group.keys():
            for i in range(1, hist.GetNbinsX()+1):
                scale_fac = hist.GetBinContent(i)
                if scale_fac < 0:
                    scale_fac = 0
                add_error = math.sqrt(scale_fac*plot_group["add_perc_error"])
                error = math.sqrt(hist.GetBinError(i)**2 + add_error**2)
                hist.SetBinError(i, error)
    def getPlotGroupMembers(self, plot_group):
        logging.debug("Plot Groups are %s" % self.plot_groups.keys())
        if plot_group in self.plot_groups.keys():
            return self.plot_groups[plot_group]["Members"]
        else:
            raise ValueError("%s is not a valid PlotGroup" % plot_group)
    def getFileInfo(self):
        return self.info
    def getDataInfo(self):
        return self.data_info
    def getMonteCarloInfo(self):
        return self.mc_info
    def getListOfPlotObjects(self):
        return self.plot_objects.keys()
def main():
    test = ConfigHistFactory("/afs/cern.ch/user/k/kelong/work/AnalysisDatasetManager",
        "WZAnalysis", "Zselection")
    draw_expr = test.getHistDrawExpr("l1Pt", "wz3lnu-powheg", "eee")
    hist_name = draw_expr.split(">>")[1].split("(")[0]

if __name__ == "__main__":
    main()
