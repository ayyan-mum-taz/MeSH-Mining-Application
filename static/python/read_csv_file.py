import pandas as pd
import json

def get_geneIDs(csv_data):
    print("getting IDs")
    counter = 0
    geneIDs = []
    for id in csv_data.GeneID:
        if id not in geneIDs:
            geneIDs.append(id)
        counter += 1
        if counter % 100000 == 0:
            print("looped %(count)d times" % {"count": counter})
    return geneIDs

def get_mesh(csv_data):
    print("getting meshes")
    counter = 0
    meshes = []
    for mesh in csv_data.MeSH:
        if mesh not in meshes:
            meshes.append(mesh)
        counter += 1
        if counter % 100000 == 0:
            print("looped %(count)d times" % {"count": counter})
    return meshes

def write_to_json(data, outfileName):
    with open(outfileName, "w") as output:
        json.dump(data, output)

if __name__ == '__main__':
    geneData = pd.read_csv('../../BoehringerProvidedPackages/combined.csv')
    # geneData = pd.read_csv('BoehringerProvidedPackages/combined_testset.csv')
    geneIDs = get_geneIDs(geneData)
    geneIDs.sort()
    geneDict = {
        "geneIDs": geneIDs
    }
    write_to_json(geneDict, "geneIDs.json")
   
   # print(get_mesh(geneData))
    meshes = get_mesh(geneData)
    meshes.sort()
    meshDict = {
        "meshes": meshes
    }
    write_to_json(meshDict, "meshes.json")
