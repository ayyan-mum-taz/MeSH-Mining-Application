from psycopg2 import connect
import csv
import math
import scipy
from decimal import Decimal, getcontext


def openConnection(dbName: str = None):
    conn = connect(
            host='seniordesign.cyzdvv3sqno4.us-east-1.rds.amazonaws.com',
            port='5432',
            database='sdp152024' if dbName is None else dbName,
            user='postgres',
            password='Uconn!2024'
    )
    return conn


def searchByGene(gene: str, connection: type(connect()), page: int, per_page: int, sortBy: str) -> dict:
    cursor = connection.cursor()
    offset = (page - 1) * per_page

    # query to search for single gene ID
    query = f"""
        SELECT * FROM "GENE" WHERE "GeneID" = {gene}
        ORDER BY "{sortBy}" ASC LIMIT
        {per_page} OFFSET {offset};"""
    
    cursor.execute(query)

    # Fetching the results for the current page
    output = cursor.fetchall()

    # Fetching the total number of records for pagination
    cursor.execute(f"SELECT COUNT(*) FROM \"GENE\" WHERE \"GeneID\" = '{gene}'")
    total_records = cursor.fetchone()[0]

    # Constructing the response
    results = [{
        'id': row[0],
        'mesh': row[1],
        'pVal': row[2],
        'enrichment': row[3],
        'references': row[4].split(',') if row[4] else []
    } for row in output]

    return {
        'results': results,
        'total': total_records,
        'page': page,
        'per_page': per_page,
        'total_pages': math.ceil(total_records / per_page)
    }


def searchByMesh(mesh: str, connection: type(connect()), page: int, per_page: int, sortBy: str) -> dict:
    cursor = connection.cursor()
    offset = (page - 1) * per_page

    # Adjusted query using the 'MeSH' column
    query = f"""
        SELECT * FROM "GENE" WHERE "MeSH" = '{mesh}'
        ORDER BY "{sortBy}" ASC LIMIT {per_page} 
        OFFSET {offset};"""
    
    cursor.execute(query)
    output = cursor.fetchall()

    # Counting records for pagination
    cursor.execute("SELECT COUNT(*) FROM \"GENE\" WHERE \"MeSH\" = %s", (f"%{mesh}%",))
    total_records = cursor.fetchone()[0]

    results = [{
        'id': row[0],
        'mesh': row[1],
        'pVal': row[2],
        'enrichment': row[3],
        'references': row[4].split(',') if row[4] else []
    } for row in output]

    return {
        'results': results,
        'total': total_records,
        'page': page,
        'per_page': per_page,
        'total_pages': math.ceil(total_records / per_page)
    }


def searchByGeneIDs(gene_ids_str: str, connection: type(connect()), page: int = 0, per_page: int = 0, sortBy: int = 3) -> dict:
    cursor = connection.cursor()
    offset = (page - 1) * per_page

    # Process input string to create a list of gene IDs
    geneList = [x.strip() for x in gene_ids_str.split(',')]
    geneIDs = tuple(geneList)

    # Constructing the query

    query="""
    SELECT DISTINCT ARRAY_AGG("p_Value")AS pVals,"MeSH",COUNT(DISTINCT "GeneID")AS numGenes,ARRAY_AGG("GeneID" ORDER BY A."GeneID")AS listGenes
    FROM "GENE"AS A
    WHERE A."GeneID" IN %s
    GROUP BY A."MeSH"
    ORDER BY %s
    DESC LIMIT %s OFFSET %s;"""

    cursor.execute(query, (geneIDs, sortBy, per_page, offset) )
    queryResult = cursor.fetchall()
    output = []
    
    # formatting results
    for row in queryResult:
        row = list(row)
        row[0] = multipleByGeneHelp(row[0])

        # limiting the number of genes shown
        if (len(row[3]) > 5 ):
            ids = ""
            for i in range(6):
                ids += str(row[3][i]) + ","
            ids += " . . ."
            row[3] = ids

        output.append(row)
    

    # Counting records for pagination
    cursor.execute("SELECT COUNT(*) FROM \"GENE\" WHERE \"GeneID\" IN %s", (tuple(geneList),))
    total_records = cursor.fetchone()[0]

    # Constructing results
    results = [{
        'combined_pval': row[0],
        'mesh': row[1],
        'num_genes': row[2],
        'genes': row[3]
    } for row in output]

    return {
        'results': results,
        'total': total_records,
        'page': page,
        'per_page': per_page,
        'total_pages': math.ceil(total_records / per_page)
    }


def multipleByGeneHelp(curCol):
    size = len(curCol)

    if(size>1):
        #curcol is a list of multiple pvalues which we need to combine
        return fishers_method(curCol)
    else:
        #See sql query *array_agg: curCol is a list with just one element, return that element
        return curCol[0]
    

def fishers_method(p_values: list) -> str:
    #Precision set based on smallest value i.e. ~1.0e-319
    getcontext().prec = 319

    #cast trickery frontloads decimal places otherwise it would approximate to 0
    p_values_decimal = [Decimal(p) for p in p_values]
    p_values_float = [float(p) for p in p_values_decimal]
    try:
        combined_result = scipy.stats.combine_pvalues(p_values_float, method="fisher")

        #returns as string -- can be changed with 
        combined_p_value = str(float(combined_result[1]))
        return combined_p_value
    except Exception as e:
        return str(0.0) #change this cast if changing to float
    

def writeJsonToTxt(data: list, fileName: str = 'Demo.txt') -> None:
    with open(f"{fileName}","w") as f:
        f.write(str(data))

    return 


def writeToCsvFile(data: list, fileName: str = 'Demo.csv') -> None:
    with open(f"{fileName}","w") as f:
        csv_out = csv.writer(f)
        csv_out.writerow(["GeneID", "MeSH", "p_value", "Enrich", "PMIDs"])
        csv_out.writerows(data)

    return 


def console() -> None:
    connection = openConnection()

    print("\nDemo 1")

    userInput = input("Enter Gene to search by: ").strip()
    output = searchByGene(gene=userInput, connection=connection) 
    
    writeToCsvFile(data=output[0])
    writeJsonToTxt(data=output[1])

    print("Done")


    return None