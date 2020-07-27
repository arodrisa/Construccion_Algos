# %%
# Libraries
import os



import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt
from random import sample

# import sys
# import datetime
# import seaborn as sns
import multiprocessing as mp
import itertools
from functools import partial


# %%
# Variables

filepath = r'C:\Users\arodr\Google Drive\Master_MIAX\Modulo2\Python_libs\Construccion_algos'


# %%
# Set working dir
os.chdir(filepath)
# os.environ['PYTHONHOME'] = r'C:\Users\arodr\AppData\Local\Programs\Python\Python38'
# os.environ['PYTHONPATH'] = r'C:\Users\arodr\AppData\Local\Programs\Python\Python38\Lib\site-packages'
# os.environ['R_HOME'] = r"C:\Program Files\R\R-3.6.3\bin\x64"
# os.environ['R_USER'] = r'C:\Users\arodr\AppData\Local\Programs\Python\Python38\Lib\site-packages\rpy2'
# import rpy2.robjects as ro
# import rpy2.robjects.numpy2ri

# robjects.r['load'](".RData")