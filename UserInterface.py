from flask import Flask, render_template, jsonify, request
from static.python.Backend import openConnection, searchByGene, searchByMesh, searchByGeneIDs
from static.python.dropdownLists import geneIDs, meshTerms
import json
import numpy as np
import math

app = Flask(__name__)
@app.route('/')
def index():
    return render_template('index.html', geneIDs=geneIDs, meshTerms=meshTerms)

@app.route('/results', methods=['GET'])
def results():
    return render_template('results.html')


@app.route('/searchGene', methods=['GET'])
def searchByGene_website():
    geneID = request.args.get('geneID')
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=20, type=int)
    sort_by = request.args.get('sort_by', default='p_Value', type=str)

    if geneID is None:
        return jsonify({'error': 'No parameter in request'}), 400

    dbConnection = openConnection()
    response = searchByGene(geneID, dbConnection, page, per_page, sort_by)
    dbConnection.close()

    return jsonify(response)

@app.route('/searchMesh', methods = ['GET'])
def searchByMesh_website():
    #mesh_term needs to be a header so that the mesh term can contain spaces
    mesh_term = request.headers.get('meshTerm')
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=20, type=int)
    sort_by = request.args.get('sort_by', default='p_Value', type=str)

    if mesh_term is None:
        return jsonify({'error': 'No MeSH term provided'}), 400

    dbConnection = openConnection()
    response = searchByMesh(mesh_term, dbConnection, page, per_page, sort_by)
    dbConnection.close()

    return jsonify(response)

@app.route('/searchMultipleGenes', methods=['GET'])
def searchMultipleGenes_website():
    gene_ids = request.args.get('geneIDs')
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=20, type=int)
    sort_by = request.args.get('sort_by', default='numGenes', type=str)

    if gene_ids is None:
        return jsonify({'error': 'No gene IDs provided'}), 400
    
    if sort_by == "numGenes":
        sort_by = 3
    elif sort_by == "MeSH":
        sort_by = 2
    elif sort_by == "p_Value":
        sort_by = 1
    # else:
    #     sort_by = 3
        

    dbConnection = openConnection()
    response = searchByGeneIDs(gene_ids, dbConnection, page, per_page, sort_by) 
    dbConnection.close()

    return jsonify(response)

@app.route('/networkGraphGene', methods=['GET'])
def network_graph_gene():
    geneID = request.args.get('geneID')
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=100, type=int) 
    sort_by = request.args.get('sort_by', default='GENE.p_Value', type=str)

    if geneID is None:
        return jsonify({'error': 'No gene ID provided'}), 400

    dbConnection = openConnection()
    try:
        # Fetch data using the existing function
        response = searchByGene(geneID, dbConnection, page, per_page, sort_by)
        graph_data = transform_for_network_graph(response['results'])
        return jsonify(graph_data)
    finally:
        dbConnection.close()

@app.route('/networkGraphMesh', methods=['GET'])
def network_graph_mesh():
    meshTerm = request.args.get('meshTerm')
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=100, type=int)  # Adjust per_page for network graph
    sort_by = request.args.get('sort_by', default='p_Value', type=str)

    if meshTerm is None:
        return jsonify({'error': 'No MeSH term provided'}), 400

    dbConnection = openConnection()
    try:
        # Fetch data using the existing function
        response = searchByMesh(meshTerm, dbConnection, page, per_page, sort_by)
        graph_data = transform_for_network_graph(response['results'])
        return jsonify(graph_data)
    finally:
        dbConnection.close()

def calculate_percentiles(values, num_buckets=100):
    """Calculate percentile values to ensure even distribution."""
    percentiles = np.linspace(0, 100, num_buckets + 1)
    percentile_values = np.percentile(values, percentiles)
    return percentile_values

def find_nearest_percentile(value, percentile_values):
    """Find the nearest percentile category for a given value."""
    idx = (np.abs(percentile_values - value)).argmin()
    return idx

def transform_for_network_graph(results):
    nodes = []
    edges = []

    if not results:
        return {'nodes': nodes, 'edges': edges}
    p_vals = [float(result['pVal']) for result in results]
    enrichments = [float(result['enrichment']) for result in results]

    log_p_vals = [-math.log10(p_val) if p_val > 0 else 0 for p_val in p_vals]
    log_p_val_percentiles = calculate_percentiles(log_p_vals)
    enrichment_percentiles = calculate_percentiles(enrichments)

    central_id = results[0]['id']

    nodes.append({
        'id': central_id,
        'label': f"Central Node: {central_id}",
        'size': 25
    })

    for result, log_p_val, enrichment in zip(results, log_p_vals, enrichments):
        peripheral_id = result['mesh']
        p_val_percentile_index = find_nearest_percentile(log_p_val, log_p_val_percentiles)
        enrichment_percentile_index = find_nearest_percentile(enrichment, enrichment_percentiles)

        normalized_thickness = 100 - 90 * (p_val_percentile_index / 100)
        normalized_distance = 100 - 90 * (enrichment_percentile_index / 100)

        nodes.append({
            'id': peripheral_id,
            'label': peripheral_id,
            'size': 10
        })

        edges.append({
            'source': central_id,
            'target': peripheral_id,
            'thickness': normalized_thickness,
            'distance': normalized_distance
        })

    return {
        'nodes': nodes,
        'edges': edges
    }

@app.route('/networkGraphPage')
def network_graph_page():
    geneID = request.args.get('geneID')
    meshTerm = request.args.get('meshTerm')

    if geneID:
        response = searchByGene(geneID, openConnection(), 1, 100, 'p_Value')
    elif meshTerm:
        response = searchByMesh(meshTerm, openConnection(), 1, 100, 'p_Value')
    else:
        return "Invalid Search", 400

    graph_data = transform_for_network_graph(response['results'])
    return render_template('network_graph.html', graph_data=json.dumps(graph_data))


if __name__ == '__main__':
    app.run(debug=True)
