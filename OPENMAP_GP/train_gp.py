from gp_manager import gp_manager
import numpy as np
import sqlite3
import requests
import sys

def process_inputs():
    argList = sys.argv
    argc = len(argList)

    # campaign_name, model_filename, dbname, api_base

    if (argc-1 != 4):
        raise Exception("run with incorrect number of arguments ({} != 4)".format(argc-1))

    return argList[1:]

def extract_from_db(dbname, campaign_name):
    conn = sqlite3.connect(dbname)
    c = conn.cursor()

    # get input variable names
    select_invar = 'SELECT i.name from map_base_mapinput as i'
    select_invar = select_invar + ' JOIN map_base_mapbase AS m ON i.for_map_id=m.id'
    select_invar = select_invar + ' JOIN map_base_campaign AS c ON c.for_map_id=m.id'
    select_invar = select_invar + ' WHERE c.name=?'
    c.execute(select_invar, (campaign_name,))
    invar = c.fetchall()

    select_outvar = 'SELECT o.name from map_base_mapoutput as o'
    select_outvar = select_outvar + ' JOIN map_base_mapbase AS m ON o.for_map_id=m.id'
    select_outvar = select_outvar + ' JOIN map_base_campaign AS c ON c.for_map_id=m.id'
    select_outvar = select_outvar + ' WHERE c.name=?'
    c.execute(select_outvar, (campaign_name,))
    outvar = c.fetchall()


    col_list = 'SELECT e.id'
    tbl_list = ' FROM map_base_campaign AS c JOIN map_base_experiment AS e ON e.campaign_id=c.id'
    nn_list = ''
    sel_args = []

    for i in range( len(invar) ):
        col_list = col_list + ', IFNULL(i{0}.value_actual, i{0}.value_request)'.format(i)
        tbl_list = tbl_list + ' JOIN map_base_expinputval AS i{0} ON i{0}.experiment_id=e.id'.format(i)
        tbl_list = tbl_list + ' JOIN (SELECT * FROM map_base_mapinput WHERE name=?) AS mi{0} ON i{0}.map_input_id=mi{0}.id'.format(i)
        sel_args.append(invar[i][0])

    for i in range( len(outvar) ):
        col_list = col_list + ', o{0}.value'.format(i)
        tbl_list = tbl_list + ' JOIN map_base_expoutputval AS o{0} ON o{0}.experiment_id=e.id'.format(i)
        tbl_list = tbl_list + ' JOIN (SELECT * FROM map_base_mapoutput WHERE name=?) AS mo{0} ON o{0}.map_output_id=mo{0}.id'.format(i)
        nn_list = nn_list + ' AND o{0}.value NOT NULL'.format(i)
        sel_args.append(outvar[i][0])

    select_in_out = col_list + tbl_list + ' WHERE c.name=?' + nn_list

    sel_args.append(campaign_name)
    c.execute(select_in_out, tuple(sel_args) )
    results = c.fetchall()

    inpar = []
    loss = []

    start_inpar = 1
    start_loss = start_inpar + len(invar)
    if ( len(results) > 0 ):
        for row in results:
            inpar.append( list(row[start_inpar:start_loss]) )
            loss.append( list(row[start_loss:]) )

    return (inpar, loss)


if __name__ == "__main__":
    campaign_name, model_file, dbname, api_base = process_inputs()

    inpar, loss = extract_from_db(dbname, campaign_name)

    gp = gp_manager()
    gp.train_model( np.array(inpar), np.array(loss) )
    gp.save_model(model_file)

    url_trained = '{}trained/{}/'.format(api_base, campaign_name)
    header = { 'Authorization': 'token ****************************************' } # generate a client token and place here
    requests.post( url_trained, headers=header )
