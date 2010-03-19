#!/usr/bin/env python
# File created on 09 Feb 2010
#file make_3d_plots.py

from __future__ import division

__author__ = "Jesse Stombaugh"
__copyright__ = "Copyright 2010, The QIIME project"
__credits__ = ["Jesse Stombaugh", "Rob Knight", "Micah Hamady", "Dan Knights"]
__license__ = "GPL"
__version__ = "0.92-dev"
__maintainer__ = "Jesse Stombaugh"
__email__ = "jesse.stombaugh@colorado.edu"
__status__ = "Pre-release"
 

from qiime.util import parse_command_line_parameters, get_options_lookup
from optparse import make_option
from qiime.make_3d_plots import generate_3d_plots
from qiime.parse import parse_coords,group_by_field,group_by_fields
import shutil
import os
from qiime.colors import sample_color_prefs_and_map_data_from_options
from random import choice
from time import strftime
from qiime.util import get_qiime_project_dir
from qiime.make_3d_plots import get_coord,get_map,remove_unmapped_samples, \
                                get_custom_coords, \
                                process_custom_axes, process_coord_filenames, \
                                remove_nans, scale_custom_coords
from qiime.pycogent_backports.misc import get_random_directory_name
options_lookup = get_options_lookup()

#make_3d_plots.py
script_info={}
script_info['brief_description']="""Make 3D PCoA plots"""
script_info['script_description']="""This script automates the construction of 3D plots (kinemage format) from the PCoA output file generated by principal_coordinates.py (e.g. P1 vs. P2 vs. P3, P2 vs. P3 vs. P4, etc., where P1 is the first component). All plots could also be constructed manually in a user-specified program."""
script_info['script_usage']=[]
script_info['script_usage'].append(("""Default Usage:""","""If you just want to use the default output, you can supply the principal coordinates file (i.e., resulting file from principal_coordinates.py) and a user-generated mapping file, where the default coloring will be based on the SampleID as follows:""","""%prog -i beta_div_coords.txt -m Mapping_file.txt"""))
script_info['script_usage'].append(("","""Additionally, the user can supply their mapping file ("-m") and a specific category to color by ("-b") or any combination of categories. When using the -b option, the user can specify the coloring for multiple mapping labels, where each mapping label is separated by a comma, for example: -b 'mapping_column1,mapping_column2'. The user can also combine mapping labels and color by the combined label that is created by inserting an '&&' between the input columns, for example: -b 'mapping_column1&&mapping_column2'.""",""))
script_info['script_usage'].append(("","""If the user would like to color all categories in their metadata mapping file, they can pass 'ALL' to the '-b' option, as follows:""","""%prog -i beta_div_coords.txt -m Mapping_file.txt -b ALL"""))
script_info['script_usage'].append(("","""As an alternative, the user can supply a preferences (prefs) file, using the -p option. The prefs file allows the user to give specific samples their own columns within a given mapping column. This file also allows the user to perform a color gradient, given a specific mapping column.

If the user wants to color by using the prefs file (e.g. prefs.txt), they can use the following code:""","""%prog -i beta_div_coords.txt -m Mapping_file.txt -p prefs.txt
"""))
script_info['script_usage'].append(("""Output Directory:""","""If you want to give an specific output directory (e.g. "3d_plots"), use the following code:""","""%prog -i principal_coordinates-output_file --o 3d_plots/"""))
script_info['script_usage'].append(("""Background Color Example:""","""If the user would like to color the background white they can use the '-k' option as follows:""","""%prog -i beta_div_coords.txt -m Mapping_file.txt -b ALL -k white"""))

script_info['output_description']="""By default, the script will plot the first three dimensions in your file. Other combinations can be viewed using the "Views:Choose viewing axes" option in the KiNG viewer (Chen, Davis, & Richardson, 2009), which may require the installation of kinemage software. The first 10 components can be viewed using "Views:Paralled coordinates" option or typing "/". The mouse can be used to modify display parameters, to click and rotate the viewing axes, to select specific points (clicking on a point shows the sample identity in the low left corner), or to select different analyses (upper right window). Although samples are most easily viewed in 2D, the third dimension is indicated by coloring each sample (dot/label) along a gradient corresponding to the depth along the third component (bright colors indicate points close to the viewer)."""
script_info['required_options']=[\
make_option('-i', '--coord_fname', dest='coord_fname', \
help='This is the path to the principal coordinates file (i.e., resulting \
file from principal_coordinates.py)'),
make_option('-m', '--map_fname', dest='map_fname', \
     help='This is the metadata mapping file  [default=%default]')
]
script_info['optional_options']=[\
 make_option('-b', '--colorby', dest='colorby',\
     help='This is the categories to color by in the plots from the \
user-generated mapping file. The categories must match the name of a column \
header in the mapping file exactly and multiple categories can be list by \
comma separating them without spaces. The user can also combine columns in the \
mapping file by separating the categories by "&&" without spaces \
[default=%default]'),
 make_option('-a', '--custom_axes',help='This is the category from the \
user-generated mapping file to use as a custom axis in the plot.  For instance,\
there is a pH category and would like to seethe samples plotted on that axis \
instead of PC1, PC2, etc., one can use this option.  It is also useful for \
plotting time-series data [default: %default]'),
 make_option('-p', '--prefs_path',help='This is the user-generated preferences \
file. NOTE: This is a file with a dictionary containing preferences for the \
analysis [default: %default]'),
 make_option('-k', '--background_color',help='This is the background color to \
use in the plots (Options are \'black\' or \'white\'. [default: %default]'),
 options_lookup['output_dir']
]

script_info['version'] = __version__

def main():
    option_parser, opts, args = parse_command_line_parameters(**script_info)

    prefs, data, background_color, label_color= \
                            sample_color_prefs_and_map_data_from_options(opts)
  
    #Open and get coord data
    data['coord'] = get_coord(opts.coord_fname)
    # remove any samples not present in mapping file
    remove_unmapped_samples(data['map'],data['coord'])

    # process custom axes, if present.
    custom_axes = None
    if opts.custom_axes:
        custom_axes = process_custom_axes(opts.custom_axes)
        get_custom_coords(custom_axes, data['map'], data['coord'])
        remove_nans(data['coord'])
        scale_custom_coords(custom_axes,data['coord'])

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
    
    qiime_dir=get_qiime_project_dir()

    jar_path=os.path.join(qiime_dir,'qiime/support_files/jar/')

    data_dir_path = get_random_directory_name(output_dir=dir_path,
                                              return_absolute_path=False)    
    
    try:
        os.mkdir(data_dir_path)
    except OSError:
        pass

    data_file_path=data_dir_path

    jar_dir_path = os.path.join(dir_path,'jar')
    
    try:
        os.mkdir(jar_dir_path)
    except OSError:
        pass
    
    shutil.copyfile(os.path.join(jar_path,'king.jar'), os.path.join(jar_dir_path,'king.jar'))

    filepath=opts.coord_fname
    filename=filepath.strip().split('/')[-1]

    try:
        action = generate_3d_plots
    except NameError:
        action = None

    #Place this outside try/except so we don't mask NameError in action
    if action:
        action(prefs,data,custom_axes,background_color,label_color,dir_path, \
                data_file_path,filename)


if __name__ == "__main__":
    main()
