import numpy as np
import sys


with open(sys.argv[1], 'r') as f:
    orgcontent = f.read()

weights = np.linspace(float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]))
biasfactors = np.linspace(float(sys.argv[5]), float(sys.argv[6]), int(sys.argv[7]))

wstring = '[' + ', '.join(str(w) for w in weights) + ']'
bstring = '[' + ', '.join(str(b) for b in biasfactors) + ']'

with open('new' + sys.argv[1], 'w') as f:
    f.write(orgcontent.format(weights=wstring, biasfactors=bstring, number=int(sys.argv[8]), synapse=sys.argv[9]))
