#!/usr/bin/env python
#
############################################################################
#
# MODULE:      i.landsat.download
# AUTHOR(S):   Veronica Andreo
# PURPOSE:     Downloads Landsat data TM, ETM and OLI from EarthExplorer
#              using landsatxplore Python library.
# COPYRIGHT:   (C) 2020-2021 by Veronica Andreo, and the GRASS development team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################

#%module
#% description: Downloads Landsat data TM, ETM and OLI from EarthExplorer using landsatxplore Python library
#% keyword: imagery
#% keyword: satellite
#% keyword: Landsat
#% keyword: download
#%end
#%option G_OPT_F_INPUT
#% key: settings
#% label: Full path to settings file (user, password)
#% description: '-' for standard input
#%end
#%option G_OPT_M_DIR
#% key: output
#% description: Name for output directory where to store downloaded Landsat data
#% required: no
#% guisection: Output
#%end
#%option G_OPT_V_MAP
#% label: Name of input vector map to define Area of Interest (AOI)
#% description: If not given then current computational extent is used
#% required: no
#% guisection: Region
#%end
#%option
#% key: clouds
#% type: integer
#% description: Maximum cloud cover percentage for Sentinel scene
#% required: no
#% guisection: Filter
#%end
#%option
#% key: dataset
#% type: string
#% description: Landsat dataset to search for
#% required: no
#% options: LANDSAT_TM_C1, LANDSAT_ETM_C1, LANDSAT_8_C1
#% answer: LANDSAT_8_C1
#% guisection: Filter
#%end
#%option
#% key: start
#% type: string
#% description: Start date ('YYYY-MM-DD')
#% guisection: Filter
#%end
#%option
#% key: end
#% type: string
#% description: End date ('YYYY-MM-DD')
#% guisection: Filter
#%end
#%option
#% key: id
#% type: string
#% multiple: yes
#% description: List of IDs to download
#% guisection: Filter
#%end
#%flag
#% key: l
#% description: List filtered products and exit
#% guisection: Print
#%end

import os
import sys
import grass.script as gs
import landsatxplore.api
# from landsatxplore.earthexplorer import EarthExplorer

# bbox - get region in ll
def get_bb(vector = None):
    args = {}
    if vector:
        args['vector'] = vector
    # are we in LatLong location?
    s = gs.read_command("g.proj", flags='j')
    kv = gs.parse_key_val(s)
    if '+proj' not in kv:
        gs.fatal('Unable to get bounding box: unprojected location not supported')
    if kv['+proj'] != 'longlat':
        info = gs.parse_command('g.region', flags='uplg', **args)
        return '({xmin}, {ymin}, {xmax}, {ymax})'.format(
            xmin=info['nw_long'], ymin=info['sw_lat'], xmax=info['ne_long'], ymax=info['nw_lat']
        )
    else:
        info = gs.parse_command('g.region', flags='upg', **args)
        return '({xmin}, {ymin}, {xmax}, {ymax})'.format(
            xmin=info['w'], ymin=info['s'], xmax=info['e'], ymax=info['n']
        )

def main():

    bb = get_bb(options['map'])

    user = password = None

    if options['settings'] == '-':
        # stdin
        import getpass
        user = raw_input(_('Insert username: '))
        password = getpass.getpass(_('Insert password: '))

        landsat_api = landsatxplore.api.API(user, password)

    else:
        try:
            with open(options['settings'], 'r') as fd:
                lines = list(filter(None, (line.rstrip() for line in fd))) # non-blank lines only
                if len(lines) < 2:
                    gs.fatal(_("Invalid settings file"))
                user = lines[0].strip()
                password = lines[1].strip()

                landsat_api = landsatxplore.api.API(user, password)

        except IOError as e:
            gs.fatal(_("Unable to open settings file: {}").format(e))

    if user is None or password is None:
        gs.fatal(_("No user or password given"))

    scenes = landsat_api.search(
        dataset = options['dataset'],
        bbox = print(bb),
        start_date = options['start'],
        end_date = options['end'],
        max_cloud_cover = options['clouds']
    )

    print('{} scenes found.'.format(len(scenes)))

    # Output list of scenes found
    print('ID', 'DisplayID', 'Date', 'Clouds')
    for scene in scenes:
        print(scene['entityId'], scene['displayId'], scene['acquisitionDate'], scene['cloudCover'])

    # # download
    # ee = EarthExplorer(user, password)
    # ee.download(
    #     scene_id=options['id'],
    #     output_dir=options['output']
    #     )

    landsat_api.logout()

if __name__ == '__main__':
    options, flags = gs.parser()
    main()