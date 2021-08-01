import logging 
import argparse
import sys 

##################
####  logger   ###
##################
# Set up logger
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger('mhw_cv_logger')
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

#Set up args
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
                    help='Enable debug info on consolo')
args = parser.parse_args()

'''
# Print out logging message on console
h_console = logging.StreamHandler()
h_console.setFormatter(formatter)
if args.verbose:
    h_console.setLevel(logging.DEBUG)
else:
    h_console.setLevel(logging.INFO)
logger.addHandler(h_console)
'''

# Record logging message at logging file
h_file = logging.FileHandler("mine_dragonite.log")
h_file.setFormatter(formatter)
h_file.setLevel(logging.INFO)
logger.addHandler(h_file)