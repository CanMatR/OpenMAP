from gp_manager import gp_manager
import numpy as np
import sqlite3
import requests
import sys

def process_inputs():
    argList = sys.argv
    argc = len(argList)

    # campaign_name, model_filename, dbname, num_samples, api_base

    if (argc-1 != 5):
        raise Exception("run with incorrect number of arguments ({} != 5)".format(argc-1))

    return (argList[1], argList[2], argList[3], int(argList[4]), argList[5])

def extract_var_limits(dbname, campaign_name):
    conn = sqlite3.connect(dbname)
    c = conn.cursor()

    domain = []

    select_invar = 'SELECT i.name, i.min_val, i.max_val FROM map_base_mapinput AS i'
    select_invar = select_invar + ' JOIN map_base_mapbase AS m ON i.for_map_id=m.id'
    select_invar = select_invar + ' JOIN map_base_campaign AS c ON c.for_map_id=m.id'
    select_invar = select_invar + ' WHERE c.name=?'
    for row in c.execute(select_invar, (campaign_name,)):
        domain.append( { 'name': row[0], 'type': 'continuous', 'domain': (row[1],row[2]) } )

    return domain

if __name__ == "__main__":
    campaign_name, model_file, dbname, n_probes, api_base = process_inputs()

    gp = gp_manager()
    gp.load_model(model_file)

    domain = extract_var_limits(dbname, campaign_name)
    gp.pre_suggest(domain)

    if (n_probes > 1):
        points = gp.suggest_multi(n_probes)
    else:
        points = gp.suggest_single(n_probes)

    url_propose = '{}proposeExperiment/{}/'.format(api_base, campaign_name)
    header = { 'Authorization': 'token ****************************************' } # generate a client token and place here
    for pt in points:
        data_propose = {
                'mode': 'gp',
                'inputs': [ {'name': d['name'], 'value': p} for d, p in zip(domain,pt)  ]
                }
        requests.post( url_propose, json=data_propose, headers=header )
