import CutFlowTools
from collections import OrderedDict

def getWZCutFlow(dataset_manager, cutflow_type):
    wz_full_cutflow = OrderedDict()
    wz_full_cutflow.update({"3 Loose, w/ OSSF pair" : {
            "datatier" : "3LooseLeptons",
            "additional_cut" : ""
        }
    })
    wz_full_cutflow.update({"3 Tight, w/ OSSF pair" : {
            "datatier" : "3LooseLeptons",
            "additional_cut" : "Zlep1IsTight && Zlep2IsTight && WlepIsTight"
                               "&& nWZLooseMuon + nCBVIDVetoElec < 3.5"
        }
    })
    wz_full_cutflow.update({"4th lepton veto" : {
            "datatier" : "3LooseLeptons",
            "additional_cut" : "Zlep1IsTight && Zlep2IsTight && WlepIsTight"
                               "&& nWZLooseMuon + nCBVIDVetoElec < 3.5"
        }
    })
    wz_full_cutflow.update({"M_{l^{+}l^{-}} #in [76, 106] GeV" : {
            "datatier" : "3LooseLeptons",
            "additional_cut" : "nWZLooseMuon + nCBVIDVetoElec < 3.5"
                                "&& Zlep1IsTight && Zlep2IsTight && WlepIsTight"
                                "&& ZMass > 76.1876 && ZMass < 106.1876"
        }
    })
    wz_full_cutflow.update({"p_{T}(l_{1,2}) > 25, 15 GeV" : {
            "datatier" : "3LooseLeptons",
            "additional_cut" : "nWZLooseMuon + nCBVIDVetoElec < 3.5"
                                "&& Zlep1IsTight && Zlep2IsTight && WlepIsTight"
                                "&& ZMass > 76.1876 && ZMass < 106.1876"
                                "&& l1Pt > 25 && l2Pt > 15"
        }
    })
    wz_full_cutflow.update({"M_{3l} > 100 GeV" : {
            "datatier" : "3LooseLeptons",
            "additional_cut" : "nWZLooseMuon + nCBVIDVetoElec < 3.5"
                                "&& Zlep1IsTight && Zlep2IsTight && WlepIsTight"
                                "&& ZMass > 76.1876 && ZMass < 106.1876"
                                "&& Mass > 100"
                                "&& l1Pt > 25 && l2Pt > 15"
        }
    })
    wz_full_cutflow.update({"#slash{E}_{T} > 30 GeV" : {
            "datatier" : "3LooseLeptons",
            "additional_cut" : "nWZLooseMuon + nCBVIDVetoElec < 3.5"
                                "&& Zlep1IsTight && Zlep2IsTight && WlepIsTight"
                                "&& ZMass > 76.1876 && ZMass < 106.1876"
                                "&& Mass > 100"
                                "&& l1Pt > 25 && l2Pt > 15" 
                                "&& MET > 30"
        }
    })
    wz_full_cutflow.update({"b-jet veto" : {
            "datatier" : "3LooseLeptons",
            "additional_cut" : "nWZLooseMuon + nCBVIDVetoElec < 3.5"
                                "&& Zlep1IsTight && Zlep2IsTight && WlepIsTight"
                                "&& ZMass > 76.1876 && ZMass < 106.1876"
                                "&& Mass > 100"
                                "&& l1Pt > 25 && l2Pt > 15" 
                                "&& MET > 30"
                                "&& nJetCSVv2T < 0.5"
        }
    })
    wz_full_cutflow.update({"W selection" : {
            "datatier" : "Wselection",
            "additional_cut" : "Zlep1IsTight && Zlep2IsTight && WlepIsTight"
        }
    })
    #wz_full_cutflow.update({"W selection" : {
    #        "datatier" : "WselectionLooseLeps",
    #        "additional_cut" : ""
    #    }
    #})
    #wz_full_cutflow.update({"NOT W lepton tight" : {
    #        "datatier" : "WselectionLooseLeps",
    #        "additional_cut" : "Zlep1IsTight && Zlep2IsTight && !WlepIsTight"
    #    }
    #})
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
            "datatier" : "Wselection",
            "additional_cut" : ""
        }
    })
    
    cutflow_maker = CutFlowTools.CutFlowHistMaker("CutFlow",
        dataset_manager,
        "WZxsec2016/Wselection"
    )
    if cutflow_type == "basic":
        cutflow_values = wz_basic_cutflow
    else:
        cutflow_values = wz_full_cutflow
    for name, info in cutflow_values.iteritems():
        cutflow_entry = CutFlowTools.CutFlowEntry(name, 
            dataset_manager,
            "WZxsec2016/" + info["datatier"],
        )
        cutflow_entry.addAdditionalCut(info["additional_cut"])
        cutflow_maker.addEntry(cutflow_entry)
    return cutflow_maker
