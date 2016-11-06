/* Scale Factor class for applying scale factors in ROOT hists etc.
 *
 * By N. Smith, U. Wisconsin
 * 
 */
#include "ScaleFactor.h"
#include "TInterpreter.h"

ScaleFactor::~ScaleFactor()
{
  SafeDelete(histCentral1D_);
  SafeDelete(histShiftUp1D_);
  SafeDelete(histShiftDown1D_);
  SafeDelete(histCentral2D_);
  SafeDelete(histShiftUp2D_);
  SafeDelete(histShiftDown2D_);
}

void ScaleFactor::Set1DHist(TH1D * central, TH1D * shiftUp, TH1D * shiftDown, OverflowBehavior b)
{
  histCentral1D_ = (TH1D *) central->Clone("Central1D");
  histCentral1D_->SetDirectory(0);
  SetOverflowBins(histCentral1D_, b);
  if ( shiftUp != nullptr ) {
    histShiftUp1D_ = (TH1D *) shiftUp->Clone("Up1D");
    histShiftUp1D_->SetDirectory(0);
    SetOverflowBins(histShiftUp1D_, b);
  }
  if ( shiftDown != nullptr ) {
    histShiftDown1D_ = (TH1D *) shiftDown->Clone("Down1D");
    histShiftDown1D_->SetDirectory(0);
    SetOverflowBins(histShiftDown1D_, b);
  }
}

TH1D * ScaleFactor::Get1DHist(Variation var)
{
  switch (var) {
    case CentralValue:
      return histCentral1D_;
    case ShiftUp:
      return histShiftUp1D_;
    case ShiftDown:
      return histShiftDown1D_;
  }
  return nullptr;
}

void ScaleFactor::Set2DHist(TH2D * central, TH2D * shiftUp, TH2D * shiftDown, OverflowBehavior b)
{
  histCentral2D_ = (TH2D *) central->Clone("Central2D");
  histCentral2D_->SetDirectory(0);
  SetOverflowBins(histCentral2D_, b);
  if ( shiftUp != nullptr ) {
    histShiftUp2D_ = (TH2D *) shiftUp->Clone("Up2D");
    histShiftUp2D_->SetDirectory(0);
    SetOverflowBins(histShiftUp2D_, b);
  }
  if ( shiftDown != nullptr ) {
    histShiftDown2D_ = (TH2D *) shiftDown->Clone("Down2D");
    histShiftDown2D_->SetDirectory(0);
    SetOverflowBins(histShiftDown2D_, b);
  }
}

TH2D * ScaleFactor::Get2DHist(Variation var)
{
  switch (var) {
    case CentralValue:
      return histCentral2D_;
    case ShiftUp:
      return histShiftUp2D_;
    case ShiftDown:
      return histShiftDown2D_;
  }
  return nullptr;
}

double ScaleFactor::Evaluate1D(double x, Variation var) const
{
  if ( var == CentralValue && histCentral1D_ != nullptr ) {
    auto bin = histCentral1D_->FindBin(x);
    return histCentral1D_->GetBinContent(bin);
  }
  else if ( var == ShiftUp && histShiftUp1D_ != nullptr ) {
    auto bin = histShiftUp1D_->FindBin(x);
    return histShiftUp1D_->GetBinContent(bin);
  }
  else if ( var == ShiftUp && histCentral1D_ != nullptr ) {
    auto bin = histCentral1D_->FindBin(x);
    return histCentral1D_->GetBinContent(bin) + histCentral1D_->GetBinError(bin);
  }
  else if ( var == ShiftDown && histShiftDown1D_ != nullptr ) {
    auto bin = histShiftDown1D_->FindBin(x);
    return histShiftDown1D_->GetBinContent(bin);
  }
  else if ( var == ShiftDown && histCentral1D_ != nullptr ) {
    auto bin = histCentral1D_->FindBin(x);
    return histCentral1D_->GetBinContent(bin) - histCentral1D_->GetBinError(bin);
  }
  // If here, we probably forgot to add the hist
  return 1.;
}

double ScaleFactor::Evaluate2D(double x, double y, Variation var) const
{
  if ( var == CentralValue && histCentral2D_ != nullptr ) {
    auto bin = histCentral2D_->FindBin(x, y);
    return histCentral2D_->GetBinContent(bin);
  }
  else if ( var == ShiftUp && histShiftUp2D_ != nullptr ) {
    auto bin = histShiftUp2D_->FindBin(x, y);
    return histShiftUp2D_->GetBinContent(bin);
  }
  else if ( var == ShiftUp && histCentral2D_ != nullptr ) {
    auto bin = histCentral2D_->FindBin(x, y);
    return histCentral2D_->GetBinContent(bin) + histCentral2D_->GetBinError(bin);
  }
  else if ( var == ShiftDown && histShiftDown2D_ != nullptr ) {
    auto bin = histShiftDown2D_->FindBin(x, y);
    return histShiftDown2D_->GetBinContent(bin);
  }
  else if ( var == ShiftDown && histCentral2D_ != nullptr ) {
    auto bin = histCentral2D_->FindBin(x, y);
    return histCentral2D_->GetBinContent(bin) - histCentral2D_->GetBinError(bin);
  }
  // If here, we probably forgot to add the hist
  return 1.;
}

void ScaleFactor::RegisterGlobalFunction(int dimension)
{
  TObject * prev = gROOT->GetListOfSpecials()->FindObject(GetName());
  if ( prev != nullptr && prev != (TObject *) this ) {
    Error("ScaleFactor", "RegisterGlobalFunction(): There is an object with this name already in global specials");
    return;
  }
  else if ( prev == nullptr ) {
    gROOT->GetListOfSpecials()->Add(this);
  }

  auto interpreter = gROOT->GetInterpreter();
  if ( interpreter == nullptr ) {
    Error("ScaleFactor", "RegisterGlobalFunction() only works in interactive ROOT context");
  }

  if ( dimension == 1 ) {
    TString fDecl(Form("double %s(double x) { auto ptr = (ScaleFactor*) gROOT->GetListOfSpecials()->FindObject(\"%s\"); return ptr->Evaluate1D(x); }", GetName(), GetName()));
    interpreter->Declare(fDecl);
  }
  else if ( dimension == 2 ) {
    TString fDecl(Form("double %s(double x, double y) { auto ptr = (ScaleFactor*) gROOT->GetListOfSpecials()->FindObject(\"%s\"); return ptr->Evaluate2D(x, y); }", GetName(), GetName()));
    interpreter->Declare(fDecl);
  }
  else {
    Error("ScaleFactor", "Called RegisterGlobalFunction() with unsupported dimension (%d)", dimension);
  }
}

void ScaleFactor::SetOverflowBins(TH1D * hist, OverflowBehavior b)
{
  if ( b == AsInHist ) return;
  else if ( b == NearestEntry ) {
    hist->SetBinContent(0, hist->GetBinContent(1));
    hist->SetBinError(0, hist->GetBinError(1));
    auto lastBin = hist->GetNbinsX();
    hist->SetBinContent(lastBin+1, hist->GetBinContent(lastBin));
    hist->SetBinError(lastBin+1, hist->GetBinError(lastBin));
  }
  else if ( b == Unity ) {
    hist->SetBinContent(0, 1.);
    hist->SetBinError(0, 0.);
    auto lastBin = hist->GetNbinsX();
    hist->SetBinContent(lastBin+1, 1.);
    hist->SetBinError(lastBin+1, 0.);
  }
}

void ScaleFactor::SetOverflowBins(TH2D * hist, OverflowBehavior b)
{
  if ( b == AsInHist ) return;
  else if ( b == NearestEntry ) {
    // TODO: a fair bit of work
  }
  else if ( b == Unity ) {
    for(int bin=0; bin<hist->GetNcells(); ++bin) {
      if ( hist->IsBinUnderflow(bin) || hist->IsBinOverflow(bin) ) {
        hist->SetBinContent(bin, 1.);
        hist->SetBinError(bin, 0.);
      }
    }
  }
}
