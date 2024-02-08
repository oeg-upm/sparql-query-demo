# Developed in Python 3.11.6

from SPARQLWrapper import SPARQLWrapper, JSON, CSV
import pandas as pd
import gradio as gr
from io import StringIO
import os
import argparse

parser = argparse.ArgumentParser(description='Description of your program')

parser.add_argument('-t','--demo_title', help='Title of the demo website.', required=True, type=str)
parser.add_argument('-e','--endpoint', help='Endpoint to which queries point.', required=True, type=str)
parser.add_argument('-f','--return_format', help='Endpoint return format (JSON or CSV).', required=False, type=str, default="XML")
parser.add_argument('-p','--port', help='Port in which the demo will be available.', required=False, default=9900)

parser.add_argument('-x','--include_example', help='Whether or not to include a test query.', required=False, default=True)

parser.add_argument('-r','--requirements_file', help='Path to tabular file with identifier and requirements columns (ID | Req.).', required=True, type=str)
parser.add_argument('-s','--requirements_separator', help='Tabular file separator. By default ",".', required=False, default=',', type=str)
parser.add_argument('-i','--identifier_columname', help='Name of the column of identifiers, the header.', required=True, type=str)
parser.add_argument('-c','--requirement_columname', help='Name of the column of requirements, the header.', required=True, type=str)
parser.add_argument('-n','--requirements_encoding', help='Encoding of the requirements tabular file.', required=False, type=str, default='utf-8')
parser.add_argument('-q','--query_path', help='Folder where all queries are located. Remember that the queries have to end in ".rd" and have the name of the identifier it corresponds to (e.g. "CQ7.rq").', required=True, type=str)

args = parser.parse_args()

if "SD_PORT" in os.environ:
    SD_PORT= int(os.environ['SD_PORT']) #Port for deploying gradio
else:
    SD_PORT= args.port

if "DATA_VOLUME" in os.environ:
    DATA_VOLUME= os.environ['DATA_VOLUME'] #Data parent path, associated to the docker volume
    args.query_path= f"{DATA_VOLUME}/{args.query_path}"
    args.requirements_file= f"{DATA_VOLUME}/{args.requirements_file}"

print(f"Received arguments:\n\t{args}", flush=True)

if args.include_example:
    #It is important that the order of the competency questions and the queries are the same.
    cqs= ["Example to select first 10 entities."]

    #It is important to respect the line break after the triple quotation mark.
    cq_queries= [
        """
        select * where { 
            ?s ?p ?o .
        } limit 10 
        """]
else:
    cqs= []
    cq_queries= []

sparql = SPARQLWrapper(args.endpoint)
if args.return_format == "JSON":
    sparql.setReturnFormat(JSON)
elif args.return_format == "CSV":
    sparql.setReturnFormat(CSV)

requis= pd.read_csv(args.requirements_file, 
                    sep=args.requirements_separator, 
                    encoding=args.requirements_encoding, 
                    on_bad_lines='skip')

print("Requirement dataset loaded:", flush=True)
print(requis.head(), flush=True)
print("--"*25, flush=True)

for index, row in requis.iterrows():
    
    try:
        with open(f"{args.query_path}/{row[args.identifier_columname]}.rq") as fquery:
            cq_queries.append(f"\n{fquery.read()}\n")

        cqs.append(f"{row[args.identifier_columname]}: {row[args.requirement_columname]}")
    except:
        print(f"Fail when loading the query for {row[args.identifier_columname]}. Please check if the file exists.", flush=True)

print(f"Loading of requirements and queries finished (#{len(cqs)}).", flush=True)


def get_sparql_query(cq):
    return cq_queries[cqs.index(cq)]
    
def run_sparql(cq):
    query= get_sparql_query(cq)
    sparql.setQuery(query)
    try:
        results = sparql.queryAndConvert()
        if args.return_format == "CSV":
            decode_results= results.decode(encoding='utf-8', errors='strict')
            df = pd.read_csv(StringIO(decode_results), sep=",")
        if args.return_format == "JSON":
            data= results['results']['bindings']
            keys= results["head"]["vars"]
            rows= []
            for result in data:
                new_row = {}
                for key in keys:
                    if key in result:
                        new_row[key]= result[key]['value']
                    else:
                        new_row[key]= None
                rows.append(new_row)
            df = pd.json_normalize(rows)
        return df.to_html()
    except Exception as e:
        print(e)
    raise Exception

def show_mrkdwn_sparql_query(cq):
    return f'```{get_sparql_query(cq)}```'

def show_mrkdwn_cq(cq):
    return f'## {cq}'

def goto_result_tab():
    return gr.Tabs(selected=1)

with gr.Blocks() as demo:
    gr.Markdown(f"# {args.demo_title}") #Description in mardown
    
    with gr.Tabs() as tabs:
        with gr.TabItem("Query", id=0): #Creation of a tab
            with gr.Row(): # Distribute horizontally the elements inside
                dropdown_input = gr.Dropdown(cqs, 
                                             label="Competency Questions", 
                                             info="Select a competency question to run its SPARQL query")

            exec_query = gr.Button("Run Query")
            with gr.Accordion("Open to see the query"): #Drop-down in which text can be entered
                query_text= gr.Markdown("Here you will see the SPARQL query of the selected Competency Question.")

        with gr.TabItem("Results", id=1):
            cq_text= gr.Markdown("Here you will see the results of the query and the competence question associated with it.")
            text_output = gr.HTML()

    dropdown_input.change(show_mrkdwn_sparql_query, dropdown_input, query_text)
    
    exec_query.click(run_sparql, inputs=dropdown_input, outputs=text_output)
    exec_query.click(goto_result_tab, None, tabs)
    exec_query.click(show_mrkdwn_cq, dropdown_input, cq_text)

# demo.launch(server_port=args.port)
print(f"Using port {SD_PORT}", flush=True)
demo.launch(server_port=SD_PORT, share=False, server_name="0.0.0.0")