#!/usr/bin/env python
# File created on 09 Feb 2010
#file make_2d_plots.py

from __future__ import division

__author__ = "Jesse Stombaugh"
__copyright__ = "Copyright 2010, The QIIME project"
__credits__ = ["Jesse Stombaugh"]
__license__ = "GPL"
__version__ = "1.2.0-dev"
__maintainer__ = "Jesse Stombaugh"
__email__ = "jesse.stombaugh@colorado.edu"
__status__ = "Development"
 
 
from matplotlib import use
use('Agg',warn=False)
import matplotlib,re
from qiime.util import parse_command_line_parameters, get_options_lookup
from optparse import make_option
from qiime.make_2d_plots import generate_2d_plots
from qiime.parse import parse_coords,group_by_field,group_by_fields
import shutil
import os
from qiime.colors import sample_color_prefs_and_map_data_from_options
from qiime.util import get_qiime_project_dir,load_pcoa_files
from qiime.make_3d_plots import get_coord
from cogent.util.misc import get_random_directory_name

options_lookup = get_options_lookup()

#make_2d_plots.py
script_info={}
script_info['brief_description']="""Make 2D PCoA Plots"""
script_info['script_description']="""This script generates 2D PCoA plots using the principal coordinates file generated by performing beta diversity measures of an OTU table."""
script_info['script_usage']=[]
script_info['script_usage'].append(("""Default Example:""","""If you just want to use the default output, you can supply the principal coordinates file (i.e., resulting file from principal_coordinates.py), where the default coloring will be based on the SampleID as follows:""","""%prog -i beta_div_coords.txt -m Mapping_file.txt"""))
script_info['script_usage'].append(("""Output Directory Usage:""","""If you want to give an specific output directory (e.g. \"2d_plots\"), use the following code.""", """%prog -i beta_div_coords.txt -o 2d_plots/"""))
script_info['script_usage'].append(("""Mapping File Usage:""","""Additionally, the user can supply their mapping file ("-m") and a specific category to color by ("-b") or any combination of categories. When using the -b option, the user can specify the coloring for multiple mapping labels, where each mapping label is separated by a comma, for example: -b \'mapping_column1,mapping_column2\'. The user can also combine mapping labels and color by the combined label that is created by inserting an \'&&\' between the input columns, for example: -b \'mapping_column1&&mapping_column2\'.

If the user wants to color by specific mapping labels, they can use the following code:""","""%prog -i beta_div_coords.txt -m Mapping_file.txt -b 'mapping_column'"""))
script_info['script_usage'].append(("""""","""If the user would like to color all categories in their metadata mapping file, they can pass 'ALL' to the '-b' option, as follows:""","""%prog -i beta_div_coords.txt -m Mapping_file.txt -b ALL"""))
script_info['script_usage'].append(("""Prefs File:""","""The user can supply a prefs file to color by, as follows:""", """%prog -i beta_div_coords.txt -m Mapping_file.txt -p prefs.txt"""))
script_info['script_usage'].append(("""Jackknifed Principal Coordinates (w/ confidence intervals):""","""If you have created jackknifed PCoA files, you can pass the folder containing those files, instead of a single file.  The user can also specify the opacity of the ellipses around each point "--ellipsoid_opacity", which is a value from 0-1. Currently there are two metrics "--ellipsoid_method" that can be used for generating the ellipsoids, which are 'IQR' and 'sdev'. The user can specify all of these options as follows:""", """%prog -i jackknifed_pcoas/ -m Mapping_file.txt -b \'mapping_column1,mapping_column1&&mapping_column2\' --ellipsoid_opacity=0.5 --ellipsoid_method=IQR"""))
script_info['output_description']="""This script generates an output folder, which contains several files. To best view the 2D plots, it is recommended that the user views the _pca_2D.html file."""

script_info['required_options']=[\
make_option('-i', '--coord_fname', dest='coord_fname', \
help='This is the path to the principal coordinates file (i.e., resulting \
file from principal_coordinates.py).  Alternatively, the user can supply a directory containing multiple principal coordinates files.'),
make_option('-m', '--map_fname', dest='map_fname', \
     help='This is the metadata mapping file [default=%default]')
]
script_info['optional_options']=[\
make_option('-b', '--colorby', dest='colorby',\
     help='This is the categories to color by in the plots from the \
user-generated mapping file. The categories must match the name of a column \
header in the mapping file exactly and multiple categories can be list by comma \
separating them without spaces. The user can also combine columns in the \
mapping file by separating the categories by "&&" without spaces \
[default=%default]'),
make_option('-p', '--prefs_path',help='This is the user-generated preferences \
file. NOTE: This is a file with a dictionary containing preferences for the \
analysis [default: %default]'),
make_option('-k', '--background_color',help='This is the background color to \
use in the plots. [default: %default]'),

# summary plot stuff
 make_option('--ellipsoid_opacity',help='Used when plotting ellipsoids for \
a summary plot (i.e. using a directory of coord files instead of a single coord\
file). Valid range is 0-1. A value of 0 produces completely transparent \
(invisible) ellipsoids. A value of 1 produces completely opaque ellipsoids.', \
default=0.33,type=float),
 make_option('--ellipsoid_method',help='Used when plotting ellipsoids for \
a summary plot (i.e. using a directory of coord files instead of a single coord \
file). Valid values are "IQR" and "sdev".',default="IQR"),
 make_option('--master_pcoa',help='If performing averaging on multiple coord \
files, the other coord files will be aligned to this one through procrustes \
analysis. This master file will not be included in the averaging. \
If this master coord file is not provided, one of the other coord files will \
be chosen arbitrarily as the target alignment. [default: %default]',default=None),

options_lookup['output_dir']
]

script_info['version'] = __version__

def main():
    option_parser, opts, args = parse_command_line_parameters(**script_info)

    matplotlib_version = re.split("[^\d]", matplotlib.__version__)
    matplotlib_version_info = tuple([int(i) for i in matplotlib_version if \
                            i.isdigit()])

    if matplotlib_version_info != (0,98,5,3) and \
        matplotlib_version_info != (0,98,5,2):
        print "This code was only tested with Matplotlib-0.98.5.2 and \
              Matplotlib-0.98.5.3"
    data = {}

    prefs,data,background_color,label_color,ball_scale, arrow_colors= \
                            sample_color_prefs_and_map_data_from_options(opts)

    
    data['ellipsoid_method']=opts.ellipsoid_method
   
    if 0.00 <= opts.ellipsoid_opacity <= 1.00:
        data['alpha']=opts.ellipsoid_opacity
    else:
        raise ValueError, 'The opacity must be a value between 0 and 1!'
    
    #Open and get coord data
    if os.path.isdir(opts.coord_fname) and opts.master_pcoa:
        data['coord'],data['support_pcoas'] = load_pcoa_files(opts.coord_fname)
        data['coord']=get_coord(opts.master_pcoa)
    elif os.path.isdir(opts.coord_fname):
        data['coord'],data['support_pcoas'] = load_pcoa_files(opts.coord_fname)
    else:
        data['coord'] = get_coord(opts.coord_fname)

    filepath=opts.coord_fname
    filename='2d_pcoa_plots'

    qiime_dir=get_qiime_project_dir()

    js_path=os.path.join(qiime_dir,'qiime','support_files','js')

    if opts.output_dir:
        if os.path.exists(opts.output_dir):
            dir_path=opts.output_dir
        else:
            try:
                os.mkdir(opts.output_dir)
                dir_path=opts.output_dir
            except OSError:
                pass
    else:
        dir_path='./'
        
    html_dir_path=dir_path
    data_dir_path = get_random_directory_name(output_dir=dir_path)
    try:
        os.mkdir(data_dir_path)
    except OSError:
        pass

    js_dir_path = os.path.join(html_dir_path,'js')
    try:
        os.mkdir(js_dir_path)
    except OSError:
        pass

    shutil.copyfile(os.path.join(js_path,'overlib.js'), \
                                    os.path.join(js_dir_path,'overlib.js'))

    try:
        action = generate_2d_plots
    except NameError:
        action = None
    #Place this outside try/except so we don't mask NameError in action
    if action:
        action(prefs,data,html_dir_path,data_dir_path,filename,background_color,
                label_color)


if __name__ == "__main__":
    main()
