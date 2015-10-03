#!/usr/bin/env python
import Utilities.plot_functions as plotter
import Utilities.helper_functions as helper
import argparse
import ROOT
import config_object
import Utilities.selection as selection

def getComLineArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output_file", type=str, required=True,
                        help="Name of file to be created (type pdf/png etc.)")
    parser.add_argument("-s", "--scale", type=str, default="xsec",
                        help="Method for scalling hists")
    parser.add_argument("--fiducial_cuts", action="store_true",
                        help="Apply fiducial cuts before plotting")
    plot_group = parser.add_mutually_exclusive_group()
    plot_group.add_argument("-b", "--branch", type=str,
                        help="Name of branch in root and config file")
    plot_group.add_argument("-a", "--all", action="store_true")
    parser.add_argument("-c", "--cut_string", type=str, default="",
                        help="Root cut string to apply when drawing hist")
    parser.add_argument("-n", "--max_entries", type=int, default=-1,
                        help="Draw only first n entries of hist "
                        "(useful for huge root files)")
    parser.add_argument("-f", "--file_to_plot", type=str, required=True,
                        default="", help="Files to make plots from, "
                        "separated by a comma (match name in file_info.json)")
    return parser.parse_args()

def getHist(file_info, file_to_plot, path_to_tree, branch_name, 
        cut_string, scale, max_entries):
    for name, entry in file_info.iteritems():
        if name != file_to_plot.strip():
            continue
        else:
            print "Found it"
        config = config_object.ConfigObject(
                "./config_files/" + entry["plot_config"])
        histname = ''.join([name, "-", branch_name])
        hist = config.getObject(histname, entry["title"]) 
        if "zz" in name:
            path_to_tree = path_to_tree.replace("W", "Z")
        helper.loadHistFromTree(hist,
                entry["filename"], 
                path_to_tree,
                branch_name,
                cut_string,
                max_entries
            )
        config.setAttributes(hist, histname)
        print "Title is %s" % hist.GetTitle()
#        if scale == "xsec":
#            scaleHistByXsec(hist, root_file, 1000)
#        elif scale == "unity":
#            print "Scalling hists in stack to unity"
#            hist.Sumw2()
#            hist.Scale(1/hist.GetEntries())
#        else:
#            print "No scalling applied!"
        return hist
    print "Failed to find file"
    exit(0)

def main():
    #ROOT.gROOT.SetBatch(True)
    args = getComLineArgs()
    file_info = helper.getFileInfo("config_files/file_info.json")
    
    canvas = ROOT.TCanvas("canvas", "canvas", 1000, 600) 
    legendPad = ROOT.TPad('legendPad', 'ratioPad', 0.8, 0, 1., 1.)
    legendPad.Draw()
    histPad = ROOT.TPad('histPad', 'stackPad', 0., 0, 0.8, 1.)
    histPad.Draw()
    
    histPad.cd()
    cut_string = args.cut_string
    if "j1" in args.branch:
        cut_string = "j1Pt > 0"
    elif "j2" in args.branch:
        cut_string = "j2Pt > 0"
    if args.fiducial_cuts:
        if cut_string != "":
            cut_string += " && " 
        cut_string += selection.getFiducialCutString("WZ")

    hist = getHist(file_info, args.file_to_plot, 
        "analyzeWZ/Ntuple", args.branch, cut_string, args.scale, args.max_entries)
    hist.Draw("hist")
    histErrors = []
    histErrors.append(plotter.getHistErrors(hist, hist.GetLineColor()))
    histErrors[-1].Draw("E2 same")
    
    legendPad.cd()
    legend = ROOT.TLegend(0, 0.45, 1, 0.55)

    legend.AddEntry(hist, hist.GetTitle(), "f")
    legend.SetFillColor(0)
    legend.Draw()
    canvas.Print(args.output_file)

if __name__ == "__main__":
    main()
