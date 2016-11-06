import CutFlowTools
from collections import OrderedDict

def getWZCutFlow(dataset_manager, cutflow_type):
    wz_full_cutflow = OrderedDict()
    #wz_full_cutflow.update({"#geq 3 tight e/#mu" : {
    #        "datatier" : "loosepreselection",
    #        "additional_cut" : ""
    #    }
    #})
    #wz_full_cutflow.update({"4th lepton veto" : {
    #        "datatier" : "loosepreselection",
    #        "additional_cut" : "lepVeto"
    #    }
    #})
    wz_full_cutflow.update({"Require OSSF pair" : {
            "datatier" : "preselection",
            "additional_cut" : ""
        }
    })
    #wz_full_cutflow.update({"M_{3l} > 100 GeV" : {
    #        "datatier" : "Mass3l",
    #        "additional_cut" : ""
    #    }
    #})
    #wz_full_cutflow.update({"M_{l^{+}l^{-}} #in [60, 120] GeV" : {
    #        "datatier" : "Mass3l",
    #        "additional_cut" : "ZMass > 60 && ZMass < 120"
    #    }
    #})
    wz_full_cutflow.update({"p_{T}(l_{1}) > 20 GeV" : {
            "datatier" : "Zselection",
            "additional_cut" : ""
        }
    })
    wz_full_cutflow.update({"#Delta R(l,l') > 0.1" : {
            "datatier" : "Zselection",
            "additional_cut" : "dR_Wlep_Zlep1 > 0.1 && dR_Wlep_Zlep2 > 0.1"
        }
    })
    wz_full_cutflow.update({"#slash{E}_{T} > 30 GeV" : {
            "datatier" : "Zselection",
            "additional_cut" : "dR_Wlep_Zlep1 > 0.1 && dR_Wlep_Zlep2 > 0.1 && MET > 30"
        }
    })
    wz_full_cutflow.update({"p_{T}(l_{3}) > 20 GeV" : {
            "datatier" : "FinalSelection",
            "additional_cut" : ""
        }
    })
    wz_basic_cutflow = OrderedDict()
    wz_basic_cutflow.update({"> 3 tight e/#mu" : {
            "datatier" : "loosepreselection",
            "additional_cut" : ""
        }
    })
    wz_basic_cutflow.update({"Preselection" : {
            "datatier" : "preselection",
            "additional_cut" : ""
        }
    })
    wz_basic_cutflow.update({"Z selection" : {
            "datatier" : "Zselection",
            "additional_cut" : ""
        }
    })
    wz_basic_cutflow.update({"M_{3l} > 100 GeV" : {
            "datatier" : "Mass3l",
            "additional_cut" : ""
        }
    })
    wz_basic_cutflow.update({"W selection" : {
            "datatier" : "FinalSelection",
            "additional_cut" : ""
        }
    })
    
    cutflow_maker = CutFlowTools.CutFlowHistMaker(
        dataset_manager,
        "WZxsec2016"
    )
    if cutflow_type == "basic":
        cutflow_values = wz_basic_cutflow
    else:
        cutflow_values = wz_full_cutflow
    for name, info in cutflow_values.iteritems():
        cutflow_entry = CutFlowTools.CutFlowEntry(name, 
            info["datatier"],
            dataset_manager,
            "WZxsec2016/CutFlow"
        )
        cutflow_entry.addAdditionalCut(info["additional_cut"])
        cutflow_maker.addEntry(cutflow_entry)
    return cutflow_maker
