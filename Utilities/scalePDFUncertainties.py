import math
def getVariationsFromFile(meta_tree, row_name):
    values = {}
    for row in meta_tree:
        weight_ids = row.LHEweightIDs
        for i, weight_id in enumerate(weight_ids):
            label = ''.join([weight_id[0], "001"]) 
            if label not in values:
                values.update( { label : {}})
            values[label].update({weight_id : getattr(row, "LHEweightSums")[i]})
    return values
def getScaleUncertainty(values):
    scale_info = {}
    central = values["1001"]["1001"]
    scale_info['down'] = (1-min(values["1001"].values())/central)*100
    scale_info['up'] = (max(values["1001"].values())/central - 1)*100
    return scale_info
def getPDFUncertainty(values):
    pdf_unc = {}
    central = values["1001"]["1001"]
    print central
    for unc_set in values:
        if "1001" in unc_set:
            continue
        variance = 0
        for pdf_id, xsec in values[unc_set].iteritems():
            variance += (xsec - central)*(xsec - central)
            num = len(values[unc_set]) - 1
        pdf_unc[unc_set] = math.sqrt(variance/(num))/central*100
    return pdf_unc
