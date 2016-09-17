class WeightInfo(object):
    def __init__(self, cross_section, sum_of_weights):
        self.cross_section = cross_section
        self.sum_of_weights = sum_of_weights
    def getCrossSection(self):
        return self.cross_section
    def getSumOfWeights(self):
        return self.sum_of_weights

class WeightInfoProducer(object):
    def __init__(self, metaInfoChain, cross_section, sum_weights_branch):
        self.cross_section = cross_section
        self.sum_of_weights = 0
        
        for row in metaInfoChain:
            self.sum_of_weights += getattr(row, sum_weights_branch)
            #print "Now the sum is %e" % self.sum_of_weights
    def produce(self):
        return WeightInfo(self.cross_section, self.sum_of_weights)

