def getEtaCutString(numLeptons):
    cut_string = ""
    for i in range(1, numLeptons+1):
        if i != 1:
            cut_string += " && "
        cut_string +=  "(abs(l%ipdgId) == 11 ? abs(l%iEta) < 2.5 : abs(l%iEta) < 2.5)" % (i, i, i)
    return cut_string
def getPtCutString(pt_cuts):
    cut_string = ""
    for i, cut in enumerate(pt_cuts):
        if i != 0:
            cut_string += " && "
        cut_string += "l%iPt > %s " % ((i +1), str(cut))
    return cut_string
def getZMassCutString(analysis, requireTrue):
    if analysis == "WZ":
        if requireTrue:
            return "((Z1mass < 120 && Z1mass > 60 && Z1isTrueZ) || " \
                   "(Z2mass < 120 && Z2mass > 60 && Z2isTrueZ))"
        else:
            return "(Z1mass < 120 && Z2mass > 60"
    elif analysis == "ZZ":
        return "((Z1mass < 120 && Z1mass > 60 && Z1isTrueZ) || " \
                 "(Z2mass < 120 && Z2mass > 60 && Z2isTrueZ))"

#    for i in range(1, numZs+1):
#        cut_string += "("
#        cut_string += " && " if i > 1 else ""
#        for j in range(1, numSavedZs+1):
#            cut_string += " || " if j > 1 else ""
#            cut_string += "(Z%imass > 60 && Z%imass < 120" % (j, j)
#            cut_string += " && Z%iisTrueZ" % j
#            append = ""
#            for n in range(1, j):
#                append += " && !Z%iisTrueZ " % n
#            cut_string += append + ")"
#        cut_string += ")"
    return cut_string
def getChannelEEMCutString():
    cut_string = "((abs(l1pdgId) == 11 && abs(l2pdgId) == 11 && abs(l3pdgId) == 13)" \
        " || (abs(l1pdgId) == 11 && abs(l2pdgId) == 13 && abs(l3pdgId) == 11)" \
        " || (abs(l1pdgId) == 13 && abs(l2pdgId) == 11 && abs(l3pdgId) == 11))"
    return cut_string
def getChannelEMMCutString():
    cut_string = "((abs(l1pdgId) == 13 && abs(l2pdgId) == 13 && abs(l3pdgId) == 11)" \
        " || (abs(l1pdgId) == 13 && abs(l2pdgId) == 11 && abs(l3pdgId) == 13)" \
        " || (abs(l1pdgId) == 11 && abs(l2pdgId) == 13 && abs(l3pdgId) == 13))"
    return cut_string
def getChannelEEECutString():
    cut_string = "(abs(l1pdgId) == 11 && abs(l2pdgId) == 11 && abs(l3pdgId) == 11)"
    return cut_string
def getChannelMMMCutString():
    cut_string = "(abs(l1pdgId) == 13 && abs(l2pdgId) == 13 && abs(l3pdgId) == 13)"
    return cut_string
def getChannelEEEECutString():
    cut_string = "(abs(l1pdgId) == 11 && abs(l2pdgId) == 11 && abs(l3pdgId) == 11 && abs(l4pdgId) == 11)"
    return cut_string
def getChannelMMMMCutString():
    cut_string = "(abs(l1pdgId) == 13 && abs(l2pdgId) == 13 && abs(l3pdgId) == 13 && abs(l4pdgId) == 13)"
    return cut_string
def getChannelEEMMCutString():
    cut_string = "((abs(l1pdgId) == 11 && abs(l2pdgId) == 11 && abs(l3pdgId) == 13 && abs(l4pdgId) == 13)" \
        " || (abs(l1pdgId) == 13 && abs(l2pdgId) == 13 && abs(l3pdgId) == 11 && abs(l4pdgId) == 11)" \
        " || (abs(l1pdgId) == 13 && abs(l2pdgId) == 11 && abs(l3pdgId) == 13 && abs(l4pdgId) == 11)" \
        " || (abs(l1pdgId) == 13 && abs(l2pdgId) == 11 && abs(l3pdgId) == 11 && abs(l4pdgId) == 13)" \
        " || (abs(l1pdgId) == 11 && abs(l2pdgId) == 13 && abs(l3pdgId) == 13 && abs(l4pdgId) == 11)" \
        " || (abs(l1pdgId) == 11 && abs(l2pdgId) == 13 && abs(l3pdgId) == 11 && abs(l4pdgId) == 13))"
    return cut_string
def getFiducialCutString(analysis, trueZ):
    if analysis is "WZ":
        numLeptons = 3
        pt_cuts = [20, 10, 10]
        numZs = 1
        numStoredZs = 2
    else:
        numLeptons = 4
        pt_cuts = [20, 10, 10]
        numZs = 2
        numStoredZs = 4
    cut_string = getEtaCutString(numLeptons)
    cut_string += " && " + getPtCutString(pt_cuts)
    cut_string += " && " + getZMassCutString(analysis, trueZ)
    return cut_string
