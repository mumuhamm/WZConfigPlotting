#!/usr/bin/env python
import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.PyConfig.IgnoreCommandLineOptions = True

if ROOT.gSystem.ClassName() == 'TMacOSXSystem':
    # At least on my install, this fixes the linker error:
    # ld: library not found for -lRint -lCore -L/Applications/root_v6.06.08/lib
    ROOT.gSystem.SetLinkedLibs("{0}/lib/libRint.so {0}/lib/libCore.so".format(ROOT.gRootDir))

ROOT.gROOT.LoadMacro("ScaleFactor.C+")

dummyTree = ROOT.TTree("dummy", "test")
import array
randVal = array.array('f', [0.])
randB = dummyTree.Branch('randVal', randVal, 'randVal/f')
randVal2 = array.array('f', [0.])
randB2 = dummyTree.Branch('randVal2', randVal2, 'randVal/f')
for i in range(100) :
    randVal[0] = ROOT.gRandom.Gaus()
    randVal2[0] = ROOT.gRandom.Gaus()
    dummyTree.Fill()

ROOT.gInterpreter.Declare("double globalFunc(double x) { return 1/(100+x); }")
print "globalFunc(3) = ", ROOT.globalFunc(3)
dummyTree.Scan('randVal : globalFunc(randVal)', '', '', 10)

# Generate with setupScaleFactors.py
# Will need appropriate files in ../data/
fScales = ROOT.TFile('scaleFactors.root')
pu = fScales.Get('pileupSF')
muon = fScales.Get('muonIsoSF')
del fScales # Make sure we don't rely on file being open

#pu.RegisterGlobalFunction()
#print "pileupSF(3) = ", ROOT.pileupSF(3)
#dummyTree.Scan('10+10*randVal : pileupSF(10+10*randVal)', '', '', 10)

muon.RegisterGlobalFunction(2) # 2D function
print "muonIsoSF(1.1, 30) = ", ROOT.muonIsoSF(1.1, 30)
dummyTree.Scan('abs(randVal*2) : randVal2*5+30 : muonIsoSF(abs(randVal*2), randVal2*5+30)', '', '', 10)
